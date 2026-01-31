"""
Matrix Rain Effect
==================

Matrix-style digital rain animation for Streamlit pages using CSS overlay.
Creates falling streams of characters covering the entire viewport.
"""

from typing import Optional
import streamlit as st
import random


def matrix_rain(
    duration: Optional[int] = None,
    color: str = "#00FF00",
    font_size: int = 16,
    speed: float = 1.0,
    density: str = "medium",
    z_index: int = 999999,
    key: Optional[str] = None,
) -> None:
    """
    Display Matrix-style digital rain effect as a full-page overlay.

    Creates falling streams of characters similar to "The Matrix" movie,
    perfect for tech-themed content or cyberpunk aesthetics.

    Args:
        duration: Effect duration in seconds (default: None = infinite)
        color: Hex color code for text (default: "#00FF00" matrix green)
        font_size: Font size in pixels (default: 16)
        speed: Speed multiplier for falling (default: 1.0)
        density: Column density preset
            - "light": Sparse columns (75)
            - "medium": Moderate columns (150)
            - "heavy": Dense columns (240)
        z_index: CSS z-index for layering (default: 999999)
        key: Unique identifier for multiple effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import matrix_rain

        # Classic green Matrix effect
        st.title("🖥️ Welcome to The Matrix")
        matrix_rain()

        # Custom colored dense rain
        matrix_rain(
            color="#00FFFF",
            density="heavy",
            speed=1.5,
            font_size=14
        )

        # Temporary effect on button
        if st.button("Enter The Matrix"):
            matrix_rain(duration=10, key="matrix_burst")
        ```
    """
    # Map density to column count (tripled for better coverage)
    density_map = {"light": 75, "medium": 150, "heavy": 240}
    column_count = density_map.get(density.lower(), 150)

    # Generate unique effect ID
    effect_id = key or f"matrix-{random.randint(1000, 9999)}"

    # Matrix characters (English letters, numbers, symbols)
    matrix_chars = (
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:',.<>?/~`\""
    )

    # Calculate animation duration (slower for better effect)
    animation_duration = 30.0 / speed

    # Generate columns
    columns_html = ""
    for i in range(column_count):
        # Calculate horizontal position
        left = (i / column_count) * 100 + random.uniform(-1, 1)

        # Generate character sequence (90 chars - long columns)
        chars = "".join(random.choice(matrix_chars) for _ in range(90))

        # Random delay and starting position for staggered effect
        delay = random.uniform(0, animation_duration)

        # Random starting Y position (some start already on screen)
        start_y = random.uniform(-200, 0)  # -200% to 0% (some visible, some above)

        # Random duration variation
        duration_var = random.uniform(0.8, 1.2)
        actual_duration = animation_duration * duration_var

        # Create column HTML with trailing effect
        columns_html += f"""
        <div class="matrix-column" style="
            left: {left}%;
            top: {start_y}%;
            font-size: {font_size}px;
            animation-delay: {delay}s;
            animation-duration: {actual_duration}s;
        ">
        """

        # Add characters with trailing opacity
        for char_idx, char in enumerate(chars):
            # Leading characters are brighter
            opacity = 1.0 - (char_idx * 0.03)
            opacity = max(0.15, min(1.0, opacity))

            columns_html += (
                f'<div class="matrix-char" style="opacity: {opacity:.2f};">{char}</div>'
            )

        columns_html += "</div>"

    # Generate pure CSS (no style tags) with unique scoped names
    styles = f"""
    @keyframes matrix-fall-{effect_id} {{
        0% {{
            transform: translateY(0);
            opacity: 0;
        }}
        3% {{
            opacity: 1;
        }}
        100% {{
            transform: translateY(calc(100vh + 200%));
            opacity: 1;
        }}
    }}
    
    #matrix-{effect_id} .matrix-column {{
        position: fixed;
        color: {color};
        font-family: 'Courier New', monospace;
        font-weight: bold;
        pointer-events: none;
        animation: matrix-fall-{effect_id} linear infinite;
        will-change: transform;
        z-index: {z_index};
        white-space: nowrap;
        line-height: 1.2;
    }}
    
    #matrix-{effect_id} .matrix-char {{
        display: block;
    }}
    
    #matrix-{effect_id} .matrix-char:first-child {{
        text-shadow: 0 0 10px {color}, 0 0 20px {color};
    }}
    """

    # Combine into clean HTML structure
    html = f"""
<style>
{styles}
</style>

<div class="matrix-container" id="matrix-{effect_id}" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: {z_index}; overflow: hidden;">
    {columns_html}
</div>
"""

    # Add auto-removal if duration specified
    if duration:
        html += f"""
<script>
(function() {{
    setTimeout(function() {{
        var element = document.getElementById('matrix-{effect_id}');
        if (element) {{
            element.remove();
        }}
    }}, {duration * 1000});
}})();
</script>
"""

    # Inject directly into Streamlit using st.html()
    st.html(html)
