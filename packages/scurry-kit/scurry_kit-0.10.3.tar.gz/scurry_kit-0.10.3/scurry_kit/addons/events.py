import logging

logger = logging.getLogger('scurrypy')

from scurrypy import (
    Addon,
    Client,
    DiscordError,
    Event
)

def _check_func_params(func: callable):
    import inspect
    
    params_len = len(inspect.signature(func).parameters)

    if params_len != 2:
        raise TypeError(f"Event handler '{func.__name__}' must accept exactly two parameters (bot, event).")

class EventsAddon(Addon):
    """Addon that implements automatic registering and decorating events."""

    def __init__(self, client: Client):
        """
        Args:
            client (Client): the Client object
        """
        self.bot = client

        self._events: dict[str, list[tuple[int, callable]]] = {}
        """Maps EVENT_NAME to handlers."""

        client.add_startup_hook(self.on_startup)

    def on_startup(self):
        """Adds registered events to client's event listener."""

        # lead all registered events to this dispatch
        for dispatch_type in self._events.keys():
            self.bot.add_event_listener(dispatch_type, self.dispatch)
        
    def listen(self, event_name: str):
        """Decorator to listen for an event with params (bot, event).

        Args:
            event_name (str): event name
        """
        def decorator(func):
            _check_func_params(func)
            self._events.setdefault(event_name, []).append(func)
        return decorator
    
    def register_event(self, event_name: str, handler):
        """Register a callback for an event.

        Args:
            event_name (str): event name
            handler (callable): function callback
        """
        _check_func_params(handler)
        self._events.setdefault(event_name, []).append(handler)

    async def dispatch(self, event: Event):
        """Addon's entry point.

        Args:
            event (Event): event data object
        """
        handlers = self._events.get(event.name)

        if not handlers:
            return
    
        try:
            for handler in handlers:
                await handler(self.bot, event)
        except DiscordError as e:
            logger.error(f"Error in event '{handler}': {e}")
        except Exception as e:
            logger.error(f"Unhandled error in event '{handler.__name__}': {e}")
