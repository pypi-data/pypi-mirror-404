"""
Confetti Effect
===============

Celebration confetti animation for Streamlit pages using CSS overlay.
Creates an explosion of colorful confetti pieces covering the entire viewport.
"""

from typing import Optional, List
import streamlit as st
import random


def confetti(
    duration: int = 5,
    particle_count: int = 150,
    colors: Optional[List[str]] = None,
    velocity: float = 50.0,
    z_index: int = 999999,
    key: Optional[str] = None,
) -> None:
    """
    Display confetti celebration effect as a full-page overlay.

    Creates a shower of colorful confetti pieces that rain down from above
    the screen, perfect for celebrating achievements, completions, or positive events.
    Effect covers the entire Streamlit viewport including sidebar and header.

    Args:
        duration: Effect duration in seconds (default: 5)
            - Confetti will fall and then auto-remove
            - Minimum recommended: 3 seconds
        particle_count: Number of confetti pieces (default: 150)
            - 50-100: Light celebration
            - 150-200: Medium celebration
            - 200+: Intense celebration
        colors: List of hex color codes for confetti (default: rainbow)
            - Default: ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#FFA500"]
            - Custom example: ["#FF1493", "#00CED1", "#FFD700"]
        velocity: Fall speed multiplier (default: 50.0)
            - 25: Slow, gentle fall (peaceful)
            - 50: Normal speed (default)
            - 75: Fast fall (exciting)
        z_index: CSS z-index for layering (default: 999999)
        key: Unique identifier for multiple effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import confetti

        # Simple celebration on button click
        if st.button("🎉 Celebrate!"):
            confetti()

        # More intense celebration with faster fall
        if st.button("✅ Success!"):
            confetti(
                particle_count=200,
                velocity=75,
                duration=8,
                key="success_confetti"
            )

        # Custom colored confetti shower
        if st.button("🎊 Party!"):
            confetti(
                duration=10,
                particle_count=300,
                colors=["#FF1493", "#00CED1", "#FFD700", "#FF69B4"],
                key="party_confetti"
            )
        ```

    Performance Notes:
        - Particle counts above 300 may impact performance on slower devices
        - Uses CSS transforms for GPU-accelerated animation
        - Staggered start timing creates smooth continuous rain effect
    """
    # Default rainbow colors if not provided
    if colors is None:
        colors = [
            "#FF0000",  # Red
            "#00FF00",  # Green
            "#0000FF",  # Blue
            "#FFFF00",  # Yellow
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FFA500",  # Orange
        ]

    # Generate unique effect ID
    effect_id = key or f"confetti-{random.randint(1000, 9999)}"

    # Generate confetti pieces falling from above like rain
    confetti_html = ""
    for i in range(particle_count):
        # Random color from palette
        color = random.choice(colors)

        # Random starting X position (dispersed across screen width)
        start_x = random.uniform(5, 95)  # 5-95% to avoid edges

        # Random horizontal drift (wind effect as it falls)
        horizontal_drift = random.uniform(-150, 150)  # px

        # Random rotation properties
        rotation_speed = random.randint(2, 8)

        # Random size (width and height)
        size = random.randint(8, 15)
        width = size
        height = random.randint(int(size * 0.5), size)

        # Fall duration with velocity applied
        base_fall_time = 3.0  # Base seconds to fall
        fall_duration = base_fall_time * (50.0 / velocity)  # Adjust by velocity
        fall_duration *= random.uniform(0.8, 1.2)  # Add variation

        # Random start delay for staggered effect
        start_delay = random.uniform(0, 1.0)  # 0-1 second stagger

        confetti_html += f"""
        <div class="confetti-piece confetti-{i}" style="
            left: {start_x}%;
            top: -10vh;
            width: {width}px;
            height: {height}px;
            background-color: {color};
            animation-duration: {fall_duration}s;
            animation-delay: {start_delay}s;
            --horizontal-drift: {horizontal_drift}px;
            --rotation: {rotation_speed * 360}deg;
        "></div>
        """

    # Generate pure CSS (no style tags) with unique scoped names
    styles = f"""
    @keyframes confetti-fall-{effect_id} {{
        0% {{
            transform: translate(0, 0) rotate(0deg);
            opacity: 1;
        }}
        100% {{
            transform: translate(var(--horizontal-drift), 110vh) rotate(var(--rotation));
            opacity: 1;
        }}
    }}
    
    #confetti-{effect_id} .confetti-piece {{
        position: fixed;
        pointer-events: none;
        animation: confetti-fall-{effect_id} ease-in forwards;
        will-change: transform;
        z-index: {z_index};
    }}
    """

    # Combine into clean HTML structure
    html = f"""
<style>
{styles}
</style>

<div class="confetti-container" id="confetti-{effect_id}" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: {z_index}; overflow: hidden;">
    {confetti_html}
</div>
"""

    # Add auto-removal script
    if duration:
        html += f"""
<script>
(function() {{
    setTimeout(function() {{
        var element = document.getElementById('confetti-{effect_id}');
        if (element) {{
            element.remove();
        }}
    }}, {duration * 1000});
}})();
</script>
"""

    # Inject directly into Streamlit using st.html()
    st.html(html)
