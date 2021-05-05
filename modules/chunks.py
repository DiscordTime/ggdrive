import asyncio
import io
import math
import os
from asyncio import Task, Event, BaseEventLoop, Future
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Callable, Tuple

from modules import logger
from modules.backports import to_thread_compat
from modules.progresslogger import Progress
from modules.util import current_is_python36, create_dir, remove_dir, remove_file, copy_file_contents, python38, \
    current_python_version


@dataclass
class ChunksDir:
    """A temporary directory that gets deleted after use"""
    path: str

    def __enter__(self):
        create_dir(self.path)
        return self.path

    def __exit__(self, exc_type, exc_val, exc_tb):
        remove_dir(self.path)


@dataclass
class Chunk:
    """A single chunk of a download."""
    file_name: str
    file_dir: str
    number: int
    start: int
    end: int
    executor: ThreadPoolExecutor
    downloader: Callable[[int, int], bytes]
    loop: BaseEventLoop = field(default_factory=asyncio.get_event_loop)
    _task: Future = field(init=False)
    # Must be init afterwards: 'got Future <Future pending> attached to a different loop'
    _download_interrupted: Event = field(init=False)
    _task_really_finished: Event = field(init=False)

    def __post_init__(self):
        self._download_interrupted = Event(loop=self.loop)
        self._task_really_finished = Event(loop=self.loop)
        self._task = self.loop.run_in_executor(self.executor, self.download)

    @staticmethod
    def create_from(file_downloader: Callable[[int, int], bytes], file_name: str, file_dir: str, file_size: int,
                    chunk_size: int, number: int, loop: BaseEventLoop, executor: ThreadPoolExecutor):
        start = chunk_size * number
        end = min(file_size - 1, start + chunk_size - 1)
        return Chunk(file_name, file_dir, number, start, end, executor, file_downloader, loop)

    @property
    def file_name_with_number(self) -> str:
        return f'{self.file_name}.{self.number}'

    @property
    def file_path(self) -> str:
        return os.path.join(self.file_dir, self.file_name_with_number)

    @property
    def task(self) -> Future:
        return self._task

    @property
    def interrupted(self):
        return self._download_interrupted.is_set()

    @property
    def done(self):
        return self._task.done()

    @property
    def size(self):
        return self.end - self.start + 1

    def __await__(self):
        yield from self.await_it().__await__()

    # Python 3.6
    async def await_it(self):
        await self._task
        await self._task_really_finished.wait()
        logger.d(f"Task {self.number} finished")

    def download(self) -> 'Chunk':
        logger.d(f"Started task for chunk #{self.number}...")
        try:
            # Cancelling the task returned by run_in_executor does not actually remove the task from the executor if
            # the argument 'cancel_futures=True' is not passed, and Python 3.6 does not support cancel_futures argument.
            # So, we check for interruption before actually doing any work.
            if self.interrupted:
                raise asyncio.CancelledError
            logger.d(f"Task for chunk #{self.number} not interrupted. Starting work...")
            file_handler = io.BytesIO(self.downloader(self.start, self.end))
            with open(self.file_path, 'wb') as f:
                logger.d(f"Writing file handler buffer to file '{f.name}'")
                # noinspection PyTypeChecker
                f.write(file_handler.getbuffer())
            logger.d(f"Task for chunk #{self.number} finished...")
            # Check again after the (blocking) work is done.
            if self.interrupted:
                raise asyncio.CancelledError
            return self
        except asyncio.CancelledError:
            logger.d(f"Task for chunk #{self.number} got interrupted. Cleaning up...")
            remove_file(self.file_path)
        except BaseException as e:
            logger.d(f"Failed downloading file {self.file_path}")
            logger.d(e)
            remove_file(self.file_path)
            raise
        finally:
            self._task_really_finished.set()

    def cancel(self):
        """Cancel the download work of this chunk.

        Blocking tasks cannot be cancelled after started the way coroutines can, as coroutines cancel at their
        suspension points and blocking tasks do not have such. The solution for gracefully cancelling blocking tasks
        is setting a flag, and have the task clean up itself if the flag is set
        """
        logger.d(f"Cancelling task for chunk #{self.number}")
        self._download_interrupted.set()
        result = self._task.cancel()
        logger.d(f"Cancellation of task {self._task} for chunk #{self.number} returned {result}")


@dataclass
class Chunks:
    file_name: str
    file_size: int
    chunk_size: int
    file_downloader: Callable[[int, int], bytes]
    loop: BaseEventLoop = field(default_factory=asyncio.get_event_loop)
    executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=5)
    chunks: Tuple[Chunk, ...] = field(init=False)
    join_partial_files_task: Task = field(init=False)

    def __post_init__(self):
        async def write_files():
            async def await_chunks():
                for chunk in self.chunks:
                    if current_is_python36():
                        await chunk.await_it()
                    else:
                        await chunk

            chunk_files = tuple(chunk.file_path for chunk in self.chunks)
            with self.file_dir:  # Removes directory afterwards
                try:
                    await await_chunks()
                    await to_thread_compat(copy_file_contents, self.file_name, *chunk_files)
                finally:
                    logger.d("Reached finally block, removing already downloaded partial files")
                    await to_thread_compat(remove_file, *chunk_files)

        def create_chunk(number):
            return Chunk.create_from(self.file_downloader, self.file_name, self.file_dir.path, self.file_size,
                                     self.chunk_size, number, self.loop, self.executor)

        number_of_chunks = Chunks.calculate_number_of_chunks(self.file_size, self.chunk_size)
        self.chunks = tuple(map(create_chunk, range(number_of_chunks)))
        self.join_partial_files_task = self.loop.create_task(write_files())

    def __await__(self):
        yield from self.await_it().__await__()

    async def await_it(self):
        await asyncio.gather(self.join_partial_files_task)
        logger.d("Chunks finished work, shutting down executor.")
        if current_python_version() <= python38():
            self.executor.shutdown()
        else:
            self.executor.shutdown(cancel_futures=True)

    def __len__(self):
        return len(self.chunks)

    def __iter__(self):
        yield from self.chunks

    def __getitem__(self, item):
        return self.chunks[item]

    async def completed_chunks(self):
        for chunk in asyncio.as_completed(self.chunk_tasks):
            yield await chunk

    async def progresses(self):
        """Generator for progress."""
        received = 0
        async for chunk in self.completed_chunks():
            received += chunk.size
            yield Progress(received, self.file_size)

    @property
    def file_dir(self) -> ChunksDir:
        return ChunksDir(f'.{self.file_name}')

    @property
    def chunk_tasks(self) -> Tuple[Future, ...]:
        return tuple(chunk.task for chunk in self.chunks)

    @property
    def all_tasks(self):
        return (self.join_partial_files_task,) + self.chunk_tasks

    @property
    def all_tasks_are_done(self) -> bool:
        return all(map(lambda task: task.done(), self.all_tasks))

    def cancel(self):
        print("Cleaning up...")
        logger.d(f"Cancelling task for all chunks")
        for chunk in self.chunks:
            chunk.cancel()
        self.join_partial_files_task.cancel()
        if current_python_version() <= python38():
            self.executor.shutdown()
        else:
            self.executor.shutdown(cancel_futures=True)
        logger.d(f"Cancelled task for all chunks")

    @staticmethod
    def calculate_number_of_chunks(file_size, chunk_size):
        return math.ceil(int(file_size) / chunk_size)
