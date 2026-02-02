"""Main Geoviz class that assembles all modules."""

from .marks import MarksMixin
from .plots import PlotsMixin
from .legends import LegendsMixin
from .effects import EffectsMixin
from .controls import ControlsMixin
from .renderer import RendererMixin

class Geoviz(
    MarksMixin,
    PlotsMixin,
    LegendsMixin,
    EffectsMixin,
    ControlsMixin,
    RendererMixin
):
    """
    A Python wrapper for the geoviz JavaScript library.
    Allows creating maps by chaining commands and rendering them to an HTML file.
    """
    def __init__(self, **kwargs):
        """
        Initialize the Geoviz object.
        
        Args:
            width (int): Width of the SVG.
            height (int): Height of the SVG.
            margin (list): Margins [top, right, bottom, left].
            domain (object): GeoJSON to define the domain.
            projection (string): Projection name (e.g., "mercator", "EqualEarth").
            zoomable (bool): If True, the map is zoomable.
            background (string): Background color.
        """
        self.commands = []
        self.commands.append({"name": "create", "args": kwargs})
        self.layer_control_config = None
        self.export_control_config = None

    def _add_command(self, name, args):
        """Add a command to the list of commands to be executed."""
        self.commands.append({"name": name, "args": args})
        return self
