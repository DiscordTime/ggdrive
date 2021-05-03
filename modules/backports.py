import asyncio
# noinspection PyCompatibility
import contextvars
import functools


async def py36_asyncio_to_thread(func, *args, **kwargs):
    """Asynchronously run function *func* in a separate thread.

    Any *args and **kwargs supplied for this function are directly passed
    to *func*. Also, the current :class:`contextvars.Context` is propogated,
    allowing context variables from the main thread to be accessed in the
    separate thread.

    Return a coroutine that can be awaited to get the eventual result of *func*.
    """
    loop = asyncio.get_event_loop()  # No .get_running_loop() in 3.6
    ctx = contextvars.copy_context()  # contextvars must be imported in requirements for 3.6
    func_call = functools.partial(ctx.run, func, *args, **kwargs)
    return await loop.run_in_executor(None, func_call)


def py36_asyncio_run(main, *, debug=None):
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        if debug is not None:
            loop.set_debug(debug)
        return loop.run_until_complete(main)
    finally:
        try:
            py36_asyncio_cancel_all_tasks(loop)
            loop.run_until_complete(loop.shutdown_asyncgens())
            # TODO: 3.9 introduces loop.shutdown_default_executor(). How to backport?
            # loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.set_event_loop(None)
            loop.close()


def py36_asyncio_cancel_all_tasks(loop):
    to_cancel = py36_asyncio_all_tasks(loop)
    if not to_cancel:
        return

    for task in to_cancel:
        task.cancel()

    loop.run_until_complete(
        asyncio.gather(*to_cancel, loop=loop, return_exceptions=True))

    for task in to_cancel:
        if task.cancelled():
            continue
        if task.exception() is not None:
            loop.call_exception_handler({
                'message': 'unhandled exception during asyncio.run() shutdown',
                'exception': task.exception(),
                'task': task,
            })


def py36_asyncio_all_tasks(loop=None):
    """Return a set of all tasks for the loop."""
    if loop is None:
        loop = asyncio.get_event_loop()  # No get_running_loop in 3.6
    # Looping over a WeakSet (_all_tasks) isn't safe as it can be updated from another
    # thread while we do so. Therefore we cast it to list prior to filtering. The list
    # cast itself requires iteration, so we repeat it several times ignoring
    # RuntimeErrors (which are not very likely to occur). See issues 34970 and 36607 for
    # details.
    i = 0
    while True:
        try:
            tasks = [task for task in asyncio.Task.all_tasks(loop) if not task.done()]
        except RuntimeError:
            i += 1
            if i >= 1000:
                raise
        else:
            break
    return {t for t in tasks}


def compat(compat_fn, module, non_compat_attr):
    return getattr(module, non_compat_attr) if hasattr(module, non_compat_attr) else compat_fn


to_thread_compat = compat(py36_asyncio_to_thread, asyncio, 'to_thread')
asyncio_run_compat = compat(py36_asyncio_run, asyncio, 'run')
