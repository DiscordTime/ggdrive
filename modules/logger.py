import traceback

_DEBUG = False


def d(*args):
    if _DEBUG:
        print(f"DEBUG:", *args)


def stacktrace():
    if _DEBUG:
        traceback.print_exc()
