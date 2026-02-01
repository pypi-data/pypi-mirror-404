"""Module for interactive map controls."""

class ControlsMixin:
    """Mixin class for interactive map controls."""

    def add_layer_control(self, layers=None, pos=None, x=10, y=10, title="Layers"):
        """
        Add a collapsible layer control widget (expands on hover).
        
        Args:
            layers (list): List of layer IDs to control. If None, finds all layers with IDs.
            pos (string): Predefined position ("top-right", "top-left", etc.). Overrides x, y.
            x (int): X position of the control.
            y (int): Y position of the control.
            title (string): Title of the control panel.
        """
        self.layer_control_config = {"layers": layers, "pos": pos, "x": x, "y": y, "title": title}
        return self

    def add_export_control(self, pos=None, x=10, y=50, title="Export"):
        """
        Add a download button to export the map as SVG or PNG (expands on hover).
        
        Args:
            pos (string): Predefined position ("top-right", "top-left", etc.). Overrides x, y.
            x (int): X position of the control.
            y (int): Y position of the control.
            title (string): Title of the button.
        """
        self.export_control_config = {"pos": pos, "x": x, "y": y, "title": title}
        return self
