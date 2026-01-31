"""
Snow Effect
===========

Falling snowflake animation for Streamlit pages using CSS overlay.
Creates a full-page overlay with animated snowflakes covering the entire viewport.
"""

from typing import Optional
import streamlit as st
import random


def snow(
    intensity: str = "medium",
    speed: float = 1.0,
    color: str = "#FFFFFF",
    particle_count: Optional[int] = None,
    z_index: int = 999999,
    duration: Optional[int] = None,
    key: Optional[str] = None,
) -> None:
    """
    Display falling snow effect as a full-page background overlay.

    Creates an animated snowfall effect with particles falling at varying speeds
    and sizes to create depth. The effect covers the entire Streamlit viewport
    including sidebar, header, and all content areas.

    Args:
        intensity: Snow intensity preset ("light", "medium", "heavy")
            - "light": Gentle snowfall with ~50 particles
            - "medium": Moderate snowfall with ~100 particles
            - "heavy": Heavy snowfall with ~200 particles
        speed: Speed multiplier for falling animation (default: 1.0)
            - 0.5 = half speed (slow, gentle)
            - 1.0 = normal speed
            - 2.0 = double speed (fast, blizzard-like)
        color: Hex color code for snowflakes (default: "#FFFFFF" white)
            - Use "#A0D8F1" for light blue tint
            - Use "#E0F7FF" for icy blue
        particle_count: Override automatic particle count from intensity
            - If provided, ignores intensity preset
            - Recommended range: 10-300
        z_index: CSS z-index for layering (default: 999999)
            - Higher values appear on top
            - Default ensures effect appears above all content
        duration: Auto-stop after N seconds (default: None = infinite)
            - Useful for temporary snow bursts
        key: Unique identifier for multiple simultaneous effects
            - Use different keys to run multiple snow effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import snow

        # Simple default snow
        st.title("Winter Dashboard")
        snow()

        # Heavy blue snow falling slowly
        snow(
            intensity="heavy",
            color="#A0D8F1",
            speed=0.7
        )

        # Temporary snow burst on button click
        if st.button("❄️ Make it snow!"):
            snow(
                intensity="heavy",
                duration=5,
                key="snow_burst"
            )

        # Light snow with custom particle count
        snow(
            particle_count=30,
            speed=0.5,
            key="gentle_snow"
        )
        ```

    Performance Notes:
        - Particle counts above 200 may impact performance on slower devices
        - Use "light" intensity for better performance on mobile
        - Effect uses GPU-accelerated CSS transforms for smooth animation
    """
    # Calculate particle count from intensity if not provided
    if particle_count is None:
        intensity_map = {"light": 50, "medium": 100, "heavy": 200}
        particle_count = intensity_map.get(intensity.lower(), 100)

    # Generate unique effect ID
    effect_id = key or "snow-default"

    # Calculate animation duration based on speed
    # Slower speed = longer duration
    animation_duration = 10.0 / speed

    # Generate snowflakes with random positions and delays
    snowflakes_html = ""
    for i in range(particle_count):
        # Random horizontal position
        left = random.randint(0, 100)

        # Random animation delay for staggered effect
        delay = random.uniform(0, animation_duration)

        # Random size for depth effect (smaller = further away)
        size = random.uniform(8, 20)

        # Random animation duration variation
        duration_variation = random.uniform(0.8, 1.2)
        actual_duration = animation_duration * duration_variation

        # Random horizontal drift
        drift = random.randint(-50, 50)

        snowflakes_html += f"""
        <div class="snowflake snowflake-{i}" style="
            left: {left}%;
            font-size: {size}px;
            animation-delay: {delay}s;
            animation-duration: {actual_duration}s;
        ">❄</div>
        """

    # Generate pure CSS (no style tags) with unique scoped names
    styles = f"""
    @keyframes snowfall-{effect_id} {{
        0% {{
            transform: translateY(-10vh) translateX(0) rotate(0deg);
            opacity: 1;
        }}
        100% {{
            transform: translateY(110vh) translateX(20px) rotate(360deg);
            opacity: 0.7;
        }}
    }}
    
    #snow-{effect_id} .snowflake {{
        position: fixed;
        top: -10vh;
        color: {color};
        user-select: none;
        pointer-events: none;
        animation: snowfall-{effect_id} linear infinite;
        will-change: transform, opacity;
        z-index: {z_index};
    }}
    """

    # Combine into clean HTML structure
    html = f"""
<style>
{styles}
</style>

<div class="snow-container" id="snow-{effect_id}" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: {z_index}; overflow: hidden;">
    {snowflakes_html}
</div>
"""

    # Add auto-removal script if duration specified
    if duration:
        html += f"""
<script>
(function() {{
    setTimeout(function() {{
        var element = document.getElementById('snow-{effect_id}');
        if (element) {{
            element.remove();
        }}
    }}, {duration * 1000});
}})();
</script>
"""

    # Inject directly into Streamlit using st.html()
    st.html(html)
