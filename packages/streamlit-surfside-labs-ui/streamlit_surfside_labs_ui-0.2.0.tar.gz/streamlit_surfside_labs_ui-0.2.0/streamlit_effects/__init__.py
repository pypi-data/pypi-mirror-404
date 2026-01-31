"""
Streamlit Effects
=================

A library of animated background effects for Streamlit applications.

This package provides easy-to-use visual effects that can be added to
Streamlit apps with just a single function call. Effects include snow,
confetti, fireworks, floating hearts, and matrix rain.

Usage:
    ```python
    import streamlit as st
    from streamlit_effects import snow, confetti, fireworks, auto_effect

    st.title("My App")

    # Add falling snow
    snow()

    # Celebrate with confetti
    if st.button("Celebrate!"):
        confetti(duration=5)

    # Auto-apply seasonal effects
    auto_effect()
    ```

Available Effects:
    - snow: Falling snowflakes
    - confetti: Celebration confetti burst
    - fireworks: Fireworks explosions
    - floating_hearts: Rising hearts
    - matrix_rain: Matrix-style falling code
    - neon_heart: WebGL-based animated neon glowing heart
    - auto_effect: Automatically apply seasonal/holiday effects

For detailed documentation on each effect, see their individual docstrings.
"""

from ._version import __version__

# Import all effect functions
from .effects.snow import snow
from .effects.confetti import confetti
from .effects.fireworks import fireworks
from .effects.hearts import floating_hearts
from .effects.matrix import matrix_rain
from .effects.neon_heart import neon_heart

# Import utility functions
from .utils.auto_detect import auto_effect, get_holiday_name, get_season

# Define public API
__all__ = [
    "__version__",
    # Effects
    "snow",
    "confetti",
    "fireworks",
    "floating_hearts",
    "matrix_rain",
    "neon_heart",
    # Utilities
    "auto_effect",
    "get_holiday_name",
    "get_season",
]
