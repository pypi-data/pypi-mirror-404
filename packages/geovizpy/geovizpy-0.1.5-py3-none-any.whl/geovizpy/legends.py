"""Module for map legends."""

class LegendsMixin:
    """Mixin class for map legends."""

    def legend_circles_nested(self, **kwargs):
        """Draw a nested circles legend."""
        return self._add_command("legend.circles_nested", kwargs)

    def legend_circles(self, **kwargs):
        """Draw a circles legend."""
        return self._add_command("legend.circles", kwargs)

    def legend_squares(self, **kwargs):
        """Draw a squares legend."""
        return self._add_command("legend.squares", kwargs)

    def legend_squares_nested(self, **kwargs):
        """Draw a nested squares legend."""
        return self._add_command("legend.squares_nested", kwargs)

    def legend_circles_half(self, **kwargs):
        """Draw a half-circles legend."""
        return self._add_command("legend.circles_half", kwargs)

    def legend_spikes(self, **kwargs):
        """Draw a spikes legend."""
        return self._add_command("legend.spikes", kwargs)

    def legend_mushrooms(self, **kwargs):
        """Draw a mushrooms legend."""
        return self._add_command("legend.mushrooms", kwargs)

    def legend_choro_vertical(self, **kwargs):
        """Draw a vertical choropleth legend."""
        return self._add_command("legend.choro_vertical", kwargs)

    def legend_choro_horizontal(self, **kwargs):
        """Draw a horizontal choropleth legend."""
        return self._add_command("legend.choro_horizontal", kwargs)

    def legend_typo_vertical(self, **kwargs):
        """Draw a vertical typology legend."""
        return self._add_command("legend.typo_vertical", kwargs)

    def legend_typo_horizontal(self, **kwargs):
        """Draw a horizontal typology legend."""
        return self._add_command("legend.typo_horizontal", kwargs)

    def legend_symbol_vertical(self, **kwargs):
        """Draw a vertical symbol legend."""
        return self._add_command("legend.symbol_vertical", kwargs)

    def legend_symbol_horizontal(self, **kwargs):
        """Draw a horizontal symbol legend."""
        return self._add_command("legend.symbol_horizontal", kwargs)

    def legend_box(self, **kwargs):
        """Draw a box legend."""
        return self._add_command("legend.box", kwargs)
