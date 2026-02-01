"""Module for visual effects."""

class EffectsMixin:
    """Mixin class for visual effects."""

    def effect_blur(self, **kwargs):
        """
        Apply a blur effect.
        
        Args:
            id (string): ID of the effect.
            stdDeviation (number): Standard deviation of the blur.
        """
        return self._add_command("effect.blur", kwargs)

    def effect_shadow(self, **kwargs):
        """
        Apply a shadow effect.
        
        Args:
            id (string): ID of the effect.
            dx (number): X offset.
            dy (number): Y offset.
            stdDeviation (number): Blur amount.
            opacity (number): Opacity of the shadow.
            color (string): Color of the shadow.
        """
        return self._add_command("effect.shadow", kwargs)

    def effect_radialGradient(self, **kwargs):
        """
        Apply a radial gradient effect.
        
        Args:
            id (string): ID of the effect.
            stops (list): List of stops (e.g., [{"offset": "0%", "color": "white"}, ...]).
        """
        return self._add_command("effect.radialGradient", kwargs)

    def effect_clipPath(self, **kwargs):
        """
        Apply a clip path effect.
        
        Args:
            id (string): ID of the effect.
            datum (object): GeoJSON to use as clip path.
        """
        return self._add_command("effect.clipPath", kwargs)
