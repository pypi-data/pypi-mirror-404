"""Module containing low-level drawing marks."""

class MarksMixin:
    """Mixin class for drawing marks on the map."""

    def outline(self, **kwargs):
        """
        Add an outline to the map (graticule sphere).
        
        Args:
            fill (string): Fill color.
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
        """
        return self._add_command("outline", kwargs)

    def graticule(self, **kwargs):
        """
        Add a graticule to the map.
        
        Args:
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
            step (list): Step [x, y] in degrees.
        """
        return self._add_command("graticule", kwargs)

    def path(self, **kwargs):
        """
        Draw a path (geometry) on the map.
        
        Args:
            datum (object): GeoJSON Feature or FeatureCollection.
            fill (string): Fill color.
            stroke (string): Stroke color.
            strokeWidth (number): Stroke width.
        """
        return self._add_command("path", kwargs)

    def header(self, **kwargs):
        """
        Add a header (title) to the map.
        
        Args:
            text (string): Title text.
            fontSize (number): Font size.
            fontFamily (string): Font family.
            fill (string): Text color.
            anchor (string): Text anchor ("start", "middle", "end").
        """
        return self._add_command("header", kwargs)

    def footer(self, **kwargs):
        """
        Add a footer (source, author) to the map.
        
        Args:
            text (string): Footer text.
            fontSize (number): Font size.
            fill (string): Text color.
            anchor (string): Text anchor.
        """
        return self._add_command("footer", kwargs)

    def circle(self, **kwargs):
        """
        Draw circles on the map (low-level mark).
        For proportional circles with legend, use prop().
        
        Args:
            data (object): GeoJSON FeatureCollection.
            r (string|number): Radius value or property name.
            fill (string): Fill color.
            stroke (string): Stroke color.
            tip (string|bool): Tooltip content.
        """
        return self._add_command("circle", kwargs)

    def square(self, **kwargs):
        """
        Draw squares on the map (low-level mark).
        For proportional squares with legend, use prop(symbol="square").
        
        Args:
            data (object): GeoJSON FeatureCollection.
            side (string|number): Side length or property name.
            fill (string): Fill color.
        """
        return self._add_command("square", kwargs)

    def spike(self, **kwargs):
        """
        Draw spikes on the map (low-level mark).
        
        Args:
            data (object): GeoJSON FeatureCollection.
            height (string|number): Height value or property name.
            width (number): Width of the spike.
            fill (string): Fill color.
        """
        return self._add_command("spike", kwargs)

    def text(self, **kwargs):
        """
        Add text labels to the map.
        
        Args:
            data (object): GeoJSON FeatureCollection.
            text (string): Property name for the text.
            fontSize (number): Font size.
            fill (string): Text color.
        """
        return self._add_command("text", kwargs)

    def tile(self, **kwargs):
        """
        Add a tile layer (basemap).
        
        Args:
            url (string): URL template or keyword (e.g., "worldStreet", "openstreetmap").
            opacity (number): Opacity (0 to 1).
        """
        return self._add_command("tile", kwargs)

    def scalebar(self, **kwargs):
        """
        Add a scale bar.
        
        Args:
            x (number): X position.
            y (number): Y position.
            units (string): "km" or "mi".
        """
        return self._add_command("scalebar", kwargs)

    def north(self, **kwargs):
        """
        Add a north arrow.
        
        Args:
            x (number): X position.
            y (number): Y position.
            width (number): Width of the arrow.
        """
        return self._add_command("north", kwargs)

    def plot(self, **kwargs):
        """
        Generic plot function.
        
        Args:
            type (string): Type of plot ("choro", "prop", "typo", etc.).
            data (object): GeoJSON data.
            var (string): Variable to map.
        """
        return self._add_command("plot", kwargs)

    def tissot(self, **kwargs):
        """Draw Tissot's indicatrix to visualize distortion."""
        return self._add_command("tissot", kwargs)

    def rhumbs(self, **kwargs):
        """Draw rhumb lines."""
        return self._add_command("rhumbs", kwargs)

    def earth(self, **kwargs):
        """Draw the earth (background)."""
        return self._add_command("earth", kwargs)

    def empty(self, **kwargs):
        """Create an empty layer."""
        return self._add_command("empty", kwargs)

    def halfcircle(self, **kwargs):
        """Draw half-circles."""
        return self._add_command("halfcircle", kwargs)

    def symbol(self, **kwargs):
        """Draw symbols."""
        return self._add_command("symbol", kwargs)

    def grid(self, **kwargs):
        """Draw a grid."""
        return self._add_command("grid", kwargs)
