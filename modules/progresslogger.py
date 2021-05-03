import asyncio
import time
from asyncio import Queue, Task
from dataclasses import dataclass, astuple, field

from modules import logger
from modules.util import to_human_readable


@dataclass
class Progress:
    """A file transfer progress, with bytes received, bytes total, and a percentage calculus."""
    bytes_received: int
    bytes_total: int

    def __iter__(self):
        return iter(astuple(self) + (self.percentage,))

    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)

    @property
    def percentage(self) -> int:
        return int((float(self.bytes_received) / float(self.bytes_total)) * 100)


@dataclass
class Channel:
    """A queue supporting async iteration, async adding and async receiving."""
    queue: Queue
    _open: bool

    def __init__(self):
        self.queue = Queue()
        self._open = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.is_open or not self.queue.empty():
            return await self.queue.get()
        else:
            raise StopAsyncIteration

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    async def send(self, item):
        if self.is_open:
            await self.queue.put(item)
        else:
            raise RuntimeError("Trying to send to a closed Channel.")

    @property
    def is_open(self):
        return self._open

    @property
    def is_closed(self):
        return not self.is_open

    def open(self):
        self._open = True

    def close(self):
        self._open = False


@dataclass
class ProgressLogger:
    """A progress logger.

    Usage:

    with ProgressLogger(title) as progress_logger:
        async for progress in progresses:
            await progress_logger.send(progress)
    """
    operation: str
    _task: Task = field(init=False)
    _channel: Channel = field(init=False)
    _start_time: float = field(init=False)

    def __post_init__(self):
        self._channel = Channel()
        self._start_time = time.time()

    # Support for use in with-statement
    def __enter__(self):
        self.start()
        return self

    # Support for use in with-statement
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __await__(self):
        yield from self.await_it().__await__()

    # Python 3.6
    async def await_it(self):
        await self._task
        logger.d(f"Progress logger task finished: {self._task}")

    def start(self):
        """Start the task"""
        self._task = asyncio.get_event_loop().create_task(self._work())
        logger.d(f"Progress logger task started: {self._task}")

    def close(self):
        """Close the channel.

         Does NOT await for completion. If you want to do that, use:
         await progress_logger
         """
        self._channel.close()
        logger.d(f"Progress logger closed. Channel={self._channel}. Task={self._task}.")

    async def send(self, status: Progress):
        """Try to send a new value to the channel."""
        await self._channel.send(status)

    async def _work(self):
        """Print logs while the channel is open and receiving values, or closed, but still has items."""
        async for progress in self._channel:
            self._log_progress(progress)

    def _log_progress(self, progress: Progress):
        """Print log from status."""
        current_size, total_size, percentage = progress
        elapsed_time = time.time() - self._start_time
        speed = current_size / elapsed_time
        estimated_time = (total_size - current_size) / speed
        readable_current_size, readable_total_size, readable_speed = to_human_readable(current_size, total_size, speed)
        timer = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        eta = time.strftime("%H:%M:%S", time.gmtime(estimated_time))
        print(
            "%s %d%% - %s/%s - %s/s - %s - ETA: %s             " %
            (self.operation, percentage, readable_current_size, readable_total_size, readable_speed, timer, eta),
            end='\r'
        )
