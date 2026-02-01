"""Module for thematic map plots."""

class PlotsMixin:
    """Mixin class for thematic map plots."""

    def choro(self, **kwargs):
        """
        Draw a choropleth map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing numeric values.
            method (string): Classification method ('quantile', 'jenks', 'equal', etc.).
            nb (int): Number of classes.
            colors (string|list): Color palette name or list of colors.
            legend (bool): Whether to show the legend (default: True).
            leg_pos (list): Legend position [x, y].
            leg_title (string): Legend title.
        """
        return self._add_command("plot", {"type": "choro", **kwargs})

    def typo(self, **kwargs):
        """
        Draw a typology map (categorical data).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing categories.
            colors (string|list): Color palette or list.
            legend (bool): Show legend.
        """
        return self._add_command("plot", {"type": "typo", **kwargs})

    def prop(self, **kwargs):
        """
        Draw a proportional symbol map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name containing numeric values.
            symbol (string): Symbol type ("circle", "square", "spike").
            k (number): Size of the largest symbol.
            fill (string): Fill color.
            legend (bool): Show legend.
            leg_type (string): Legend style ("nested", "separate").
        """
        return self._add_command("plot", {"type": "prop", **kwargs})

    def propchoro(self, **kwargs):
        """
        Draw proportional symbols colored by a choropleth variable.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable for symbol size.
            var2 (string): Variable for color.
            method (string): Classification method for color.
            colors (string|list): Color palette.
        """
        return self._add_command("plot", {"type": "propchoro", **kwargs})

    def proptypo(self, **kwargs):
        """
        Draw proportional symbols colored by categories.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable for symbol size.
            var2 (string): Variable for category color.
        """
        return self._add_command("plot", {"type": "proptypo", **kwargs})

    def picto(self, **kwargs):
        """Draw a pictogram map."""
        return self._add_command("plot", {"type": "picto", **kwargs})

    def bertin(self, **kwargs):
        """
        Draw a Bertin map (dots).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            var (string): Variable name.
            n (int): Number of dots per unit.
        """
        return self._add_command("plot", {"type": "bertin", **kwargs})
