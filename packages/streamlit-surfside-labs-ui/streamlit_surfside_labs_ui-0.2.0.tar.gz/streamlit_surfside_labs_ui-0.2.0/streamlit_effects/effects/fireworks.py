"""
Fireworks Effect
================

Fireworks explosion animation for Streamlit pages using CSS overlay.
Creates bursting firework effects covering the entire viewport.
"""

from typing import Optional, List
import streamlit as st
import random
import math


def fireworks(
    duration: int = 10,
    intensity: str = "medium",
    colors: Optional[List[str]] = None,
    z_index: int = 999999,
    key: Optional[str] = None,
) -> None:
    """
    Display fireworks explosion effect as a full-page overlay.

    Creates animated firework bursts that explode and fade across the screen,
    perfect for celebrations and special announcements.

    Args:
        duration: Effect duration in seconds (default: 10)
        intensity: Fireworks intensity preset
            - "light": Few fireworks, 3-4 bursts
            - "medium": Moderate fireworks, 6-8 bursts
            - "heavy": Many fireworks, 10-12 bursts
        colors: List of hex color codes for fireworks (default: vibrant colors)
        z_index: CSS z-index for layering (default: 999999)
        key: Unique identifier for multiple effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import fireworks

        # Simple fireworks display
        if st.button("🎆 Fireworks!"):
            fireworks()

        # Heavy fireworks for grand celebration
        if st.button("🎇 Grand Finale!"):
            fireworks(
                intensity="heavy",
                duration=15,
                colors=["#FFD700", "#FF4500", "#00CED1"]
            )
        ```
    """
    # Default vibrant colors if not provided
    if colors is None:
        colors = [
            "#FF0000",  # Red
            "#FFD700",  # Gold
            "#00FF00",  # Green
            "#0000FF",  # Blue
            "#FF00FF",  # Magenta
            "#00CED1",  # Turquoise
            "#FF4500",  # Orange Red
        ]

    # Map intensity to burst count
    intensity_map = {"light": 4, "medium": 8, "heavy": 12}
    burst_count = intensity_map.get(intensity.lower(), 8)

    # Generate unique effect ID
    effect_id = key or f"fireworks-{random.randint(1000, 9999)}"

    # Generate firework bursts with particles
    bursts_html = ""
    animations_css = ""
    explosion_duration = 0.7  # How long the explosion animation takes

    for burst_idx in range(burst_count):
        # Random position
        x = random.randint(20, 80)
        y = random.randint(20, 60)

        # Random color
        color = random.choice(colors)

        # Random delay for staggered bursts
        burst_delay = random.uniform(0, duration * 0.7)

        # Total animation duration = delay until explosion + explosion duration
        total_duration = burst_delay + explosion_duration

        # Calculate percentage at which explosion should start
        delay_percent = (
            (burst_delay / total_duration) * 100 if total_duration > 0 else 0
        )
        explosion_start_percent = delay_percent
        explosion_mid_percent = delay_percent + 3  # Quick appearance

        # Create unique animation name for this burst
        burst_anim_name = f"firework-burst-{effect_id}-{burst_idx}"

        # Generate keyframe animation for this specific burst
        animations_css += f"""
    @keyframes {burst_anim_name} {{
        0% {{
            opacity: 0;
            transform: translate(0, 0) scale(0);
        }}
        {explosion_start_percent:.1f}% {{
            opacity: 0;
            transform: translate(0, 0) scale(0);
        }}
        {explosion_mid_percent:.1f}% {{
            opacity: 1;
            transform: translate(0, 0) scale(1);
        }}
        100% {{
            opacity: 0;
            transform: translate(var(--offset-x), var(--offset-y)) scale(0.2);
        }}
    }}
    """

        # Create particles radiating outward (30 particles per burst for fuller effect)
        particles_per_burst = 30
        for p in range(particles_per_burst):
            # Calculate angle for this particle (evenly distributed in circle)
            angle_deg = (360 / particles_per_burst) * p
            angle_rad = angle_deg * 3.14159 / 180

            # Calculate x and y offset using actual trig
            distance = random.randint(100, 180)
            offset_x = math.cos(angle_rad) * distance
            offset_y = math.sin(angle_rad) * distance

            # Particle size
            particle_size = random.randint(4, 8)

            bursts_html += f"""
        <div class="firework-particle burst-{burst_idx}" style="
            left: {x}%;
            top: {y}%;
            width: {particle_size}px;
            height: {particle_size}px;
            background-color: {color};
            box-shadow: 0 0 8px {color};
            animation: {burst_anim_name} {total_duration}s ease-out forwards;
            --offset-x: {offset_x}px;
            --offset-y: {offset_y}px;
        "></div>
        """

    # Generate pure CSS (no style tags) with unique scoped names
    # The per-burst animations are already generated in animations_css above
    styles = f"""
    {animations_css}
    
    #fireworks-{effect_id} .firework-particle {{
        position: fixed;
        border-radius: 50%;
        pointer-events: none;
        z-index: {z_index};
    }}
    """

    # Combine into clean HTML structure
    html = f"""
<style>
{styles}
</style>

<div class="fireworks-container" id="fireworks-{effect_id}" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: {z_index}; overflow: hidden;">
    {bursts_html}
</div>
"""

    # Add auto-removal
    if duration:
        html += f"""
<script>
(function() {{
    setTimeout(function() {{
        var element = document.getElementById('fireworks-{effect_id}');
        if (element) {{
            element.remove();
        }}
    }}, {duration * 1000});
}})();
</script>
"""

    # Inject directly into Streamlit using st.html()
    st.html(html)
