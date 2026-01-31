from scurrypy import (
    Addon,
    SeparatorPart, SeparatorTypes
)

class ContainerBuilder(Addon):
    """Common Container Helpers."""
    
    @staticmethod
    def small_separator(divider: bool = True):
        """Builds a separator with a small padding.

        Args:
            divider (bool, optional): Whether a visual divider should appear. Defaults to True.

        Returns:
            (SeparatorPart): the separator object
        """
        return SeparatorPart(divider, SeparatorTypes.SMALL_PADDING)
    
    @staticmethod
    def large_separator(divider: bool = True):
        """Builds a separator with a large padding.

        Args:
            divider (bool, optional): Whether a visual divider should appear. Defaults to True.

        Returns:
            (SeparatorPart): the separator object
        """
        return SeparatorPart(divider, SeparatorTypes.LARGE_PADDING)
