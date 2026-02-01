class DebugMixin:
    def __init__(self, *, debug: bool = False, **kwargs):
        self._debug = debug
