"""
Component registry for managing Streamlit component declaration.

This module handles the declaration of the streamlit-effects component
and provides the core render function for all effects.
"""

import os
import streamlit.components.v1 as components
from typing import Any, Optional

# Determine if we're in development or release mode
# Set _RELEASE = False during active development to use React dev server
_RELEASE = True

if not _RELEASE:
    # Development mode: use React dev server (npm start)
    _component_func = components.declare_component(
        "streamlit_effects",
        url="http://localhost:3001",
    )
else:
    # Production mode: use built frontend artifacts
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component(
        "streamlit_effects",
        path=build_dir,
    )


def render_effect(effect_type: str, key: Optional[str] = None, **kwargs: Any) -> None:
    """
    Internal function to render any effect through the component.

    Args:
        effect_type: Type of effect ("snow", "confetti", "fireworks", "hearts", "matrix")
        key: Unique component key for multiple instances
        **kwargs: Effect-specific parameters passed to the frontend

    Returns:
        None (visual effects don't return values)
    """
    print(f"[render_effect] Called with effect_type={effect_type}, key={key}")
    print(f"[render_effect] kwargs={kwargs}")

    component_value = _component_func(
        effect_type=effect_type, key=key, default=None, **kwargs
    )

    print(f"[render_effect] Component returned: {component_value}")
    return component_value
