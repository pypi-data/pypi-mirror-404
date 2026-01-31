from scurrypy import (
    Addon,
    Client
)

import inspect

def _check_start_params(func: callable):
    import inspect
    
    params_len = len(inspect.signature(func).parameters)

    if params_len != 1:
        raise TypeError(
            f"Startup hook handler '{func.__name__}' must accept exactly one parameter (bot)."
        )

def _check_end_params(func: callable):
    import inspect
    
    params_len = len(inspect.signature(func).parameters)

    if params_len != 1:
        raise TypeError(
            f"Shutdown hook handler '{func.__name__}' must accept exactly one parameter (bot)."
        )

class HooksAddon(Addon):
    """Defines registering startup and shutdown hooks with decorators."""

    def __init__(self, client: Client):
        self.bot = client

        self._start_hooks = []
        self._end_hooks = []

        client.add_startup_hook(self._run_start_hooks)
        client.add_shutdown_hook(self._run_end_hooks)

    def on_start(self, func):
        """Decorator to register startup hooks with params (bot)."""
        _check_start_params(func)
        self._start_hooks.append(func)
        return func
    
    def on_shutdown(self, func):
        """Decorator to register shutdown hooks with params (bot)."""
        _check_end_params(func)
        self._end_hooks.append(func)
        return func
    
    async def _run_start_hooks(self):
        for hook in self._start_hooks:
            result = hook(self.bot)
            if inspect.isawaitable(result):
                await result

    async def _run_end_hooks(self):
        for hook in self._end_hooks:
            result = hook(self.bot)
            if inspect.isawaitable(result):
                await result
