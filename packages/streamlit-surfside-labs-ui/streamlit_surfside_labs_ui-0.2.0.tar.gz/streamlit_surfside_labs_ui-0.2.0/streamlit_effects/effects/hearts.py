"""
Floating Hearts Effect
======================

Floating hearts animation for Streamlit pages using CSS overlay.
Creates rising heart shapes with optional custom messages covering the entire viewport.
"""

from typing import Optional, List, Union
import streamlit as st
import random


def floating_hearts(
    duration: Optional[int] = None,
    colors: Optional[List[str]] = None,
    speed: float = 1.0,
    heart_count: int = 30,
    message: Optional[Union[str, List[str]]] = None,
    show_message_inside: bool = True,
    z_index: int = 999999,
    key: Optional[str] = None,
) -> None:
    """
    Display floating hearts effect as a full-page overlay with optional custom messages.

    Creates animated CSS hearts that float upward across the screen with optional
    text messages displayed inside or next to the hearts. Perfect for Valentine's Day,
    love-themed content, proposals, or positive feedback.

    Args:
        duration: Effect duration in seconds (default: None = infinite)
        colors: List of hex color codes for hearts (default: shades of red/pink)
        speed: Speed multiplier for floating (default: 1.0)
        heart_count: Number of hearts (default: 30)
        message: Custom text message(s) to display
            - Single string: Same message on all hearts
            - List of strings: Randomly chosen for each heart
            - None: No messages (default)
        show_message_inside: Display message inside hearts (True) or next to them (False)
        z_index: CSS z-index for layering (default: 999999)
        key: Unique identifier for multiple effects

    Returns:
        None (visual effects don't return values)

    Examples:
        ```python
        import streamlit as st
        from streamlit_effects import floating_hearts

        # Simple hearts
        st.title("💝 Happy Valentine's Day!")
        floating_hearts()

        # Hearts with custom message
        floating_hearts(
            message="I Love You",
            colors=["#FF1493", "#FF69B4"],
            heart_count=40
        )

        # Hearts with multiple messages
        floating_hearts(
            message=["Love", "❤️", "XOXO", "Forever", "You & Me"],
            show_message_inside=True,
            speed=0.8
        )

        # Proposal hearts
        if st.button("💍 Pop the Question"):
            floating_hearts(
                message="Will You Marry Me?",
                heart_count=100,
                duration=15,
                key="proposal"
            )
        ```
    """
    # Default heart colors if not provided
    if colors is None:
        colors = [
            "#FF1493",  # Deep Pink
            "#FF69B4",  # Hot Pink
            "#FFB6C1",  # Light Pink
            "#FF0000",  # Red
            "#DC143C",  # Crimson
        ]

    # Convert single message to list for consistency
    messages = []
    if message:
        if isinstance(message, str):
            messages = [message] * heart_count
        else:
            messages = message

    # Generate unique effect ID
    effect_id = key or f"hearts-{random.randint(1000, 9999)}"

    # Calculate animation duration
    animation_duration = 8.0 / speed

    # Generate hearts with CSS shape
    hearts_html = ""
    for i in range(heart_count):
        # Random horizontal position
        left = random.randint(5, 95)

        # Random color
        color = random.choice(colors)

        # Random size
        size = random.randint(30, 60)

        # Random delay
        delay = random.uniform(0, animation_duration)

        # Random duration variation
        duration_var = random.uniform(0.8, 1.2)
        actual_duration = animation_duration * duration_var

        # Random horizontal drift
        drift = random.uniform(-50, 50)

        # Get message for this heart
        heart_message = ""
        if messages:
            heart_message = (
                random.choice(messages)
                if isinstance(messages, list) and len(messages) > 0
                else ""
            )

        # Message display
        message_html = ""
        if heart_message:
            if show_message_inside:
                message_html = (
                    f'<span class="heart-message-inside">{heart_message}</span>'
                )
            else:
                message_html = (
                    f'<span class="heart-message-outside">{heart_message}</span>'
                )

        hearts_html += f"""
        <div class="heart-wrapper" style="
            left: {left}%;
            animation-delay: {delay}s;
            animation-duration: {actual_duration}s;
            --drift: {drift}px;
        ">
            <div class="heart-shape" style="
                width: {size}px;
                height: {size}px;
                background-color: {color};
            ">
                <div class="heart-left"></div>
                <div class="heart-right"></div>
                {message_html}
            </div>
        </div>
        """

    # Generate pure CSS (no style tags) with unique scoped names
    styles = f"""
    @keyframes hearts-float-up-{effect_id} {{
        0% {{
            transform: translateY(110vh) translateX(0) rotate(0deg);
            opacity: 0;
        }}
        10% {{
            opacity: 1;
        }}
        90% {{
            opacity: 1;
        }}
        100% {{
            transform: translateY(-10vh) translateX(var(--drift)) rotate(15deg);
            opacity: 0;
        }}
    }}
    
    #hearts-{effect_id} .heart-wrapper {{
        position: fixed;
        bottom: -10vh;
        pointer-events: none;
        animation: hearts-float-up-{effect_id} ease-in-out infinite;
        will-change: transform, opacity;
        z-index: {z_index};
    }}
    
    #hearts-{effect_id} .heart-shape {{
        position: relative;
        transform: rotate(-45deg);
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    #hearts-{effect_id} .heart-left,
    #hearts-{effect_id} .heart-right {{
        position: absolute;
        width: 100%;
        height: 100%;
        background-color: inherit;
        border-radius: 50%;
    }}
    
    #hearts-{effect_id} .heart-left {{
        left: -50%;
        top: 0;
    }}
    
    #hearts-{effect_id} .heart-right {{
        left: 0;
        top: -50%;
    }}
    
    #hearts-{effect_id} .heart-message-inside {{
        position: absolute;
        transform: rotate(45deg);
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        font-size: 12px;
        white-space: nowrap;
        z-index: 10;
        text-align: center;
        pointer-events: none;
    }}
    
    #hearts-{effect_id} .heart-message-outside {{
        position: absolute;
        left: 120%;
        top: 50%;
        transform: translateY(-50%);
        font-family: 'Arial', sans-serif;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        font-size: 14px;
        white-space: nowrap;
        z-index: 10;
        pointer-events: none;
    }}
    """

    # Combine into clean HTML structure
    html = f"""
<style>
{styles}
</style>

<div class="hearts-container" id="hearts-{effect_id}" style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: {z_index}; overflow: hidden;">
    {hearts_html}
</div>
"""

    # Add auto-removal if duration specified
    if duration:
        html += f"""
<script>
(function() {{
    setTimeout(function() {{
        var element = document.getElementById('hearts-{effect_id}');
        if (element) {{
            element.remove();
        }}
    }}, {duration * 1000});
}})();
</script>
"""

    # Inject directly into Streamlit using st.html()
    st.html(html)
