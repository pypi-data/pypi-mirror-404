"""
Streamlit Effects Gallery
==========================

Interactive demonstration of all available effects in streamlit-effects.
Browse and customize each effect with live previews.

NOTE: Uses session state to persist effects across reruns.
"""

import streamlit as st
import time
from datetime import date

# Import effects
import sys

sys.path.insert(0, "..")  # Allow importing from parent directory during development
from streamlit_effects import (
    snow,
    confetti,
    fireworks,
    floating_hearts,
    matrix_rain,
    auto_effect,
    get_holiday_name,
    get_season,
)

# Page configuration
st.set_page_config(
    page_title="Streamlit Effects Gallery",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state for active effects
if "active_effects" not in st.session_state:
    st.session_state.active_effects = {}

# Title
st.title("✨ Streamlit Effects Gallery")
st.markdown(
    "Interactive demonstration of animated background effects for Streamlit apps"
)

# Sidebar - Effect Selection
st.sidebar.title("🎨 Effect Gallery")
st.sidebar.markdown("Select an effect to preview:")

effect_choice = st.sidebar.radio(
    "Choose Effect:",
    [
        "❄️ Snow",
        "🎉 Confetti",
        "🎆 Fireworks",
        "💕 Floating Hearts",
        "🟢 Matrix Rain",
        "🎯 Auto-Detect (Seasonal)",
    ],
    index=0,
)

st.sidebar.divider()

# Show active effects status in sidebar
if st.session_state.active_effects:
    st.sidebar.success(f"✨ {len(st.session_state.active_effects)} effect(s) active")
    if st.sidebar.button("🛑 Stop All Effects"):
        st.session_state.active_effects = {}
        st.rerun()
else:
    st.sidebar.info("No active effects")

st.sidebar.divider()

# Effect-specific controls based on selection
if effect_choice == "❄️ Snow":
    st.header("❄️ Snow Effect")
    st.markdown("Falling snowflakes with configurable intensity, speed, and color.")

    col1, col2 = st.columns(2)

    with col1:
        intensity = st.selectbox(
            "Intensity:",
            ["light", "medium", "heavy", "blizzard"],
            index=1,
        )

        speed = st.slider(
            "Speed:",
            min_value=0.1,
            max_value=3.0,
            value=1.0,
            step=0.1,
        )

    with col2:
        color = st.color_picker(
            "Snowflake Color:",
            value="#FFFFFF",
        )

        duration = st.number_input(
            "Duration (seconds, 0 = infinite):",
            min_value=0,
            max_value=60,
            value=0,
        )

    st.divider()

    if st.button("🌨️ Apply Snow Effect", type="primary", use_container_width=True):
        effect_id = f"snow_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "snow",
            "params": {
                "intensity": intensity,
                "speed": speed,
                "color": color,
                "duration": duration if duration > 0 else None,
            },
            "started_at": time.time(),
            "duration": duration if duration > 0 else None,
        }
        st.success(f"Snow effect applied! Intensity: {intensity}, Speed: {speed}x")

elif effect_choice == "🎉 Confetti":
    st.header("🎉 Confetti Effect")
    st.markdown("Celebration confetti burst with customizable colors and spread.")

    col1, col2 = st.columns(2)

    with col1:
        duration = st.slider(
            "Duration (seconds):",
            min_value=1,
            max_value=15,
            value=5,
        )

        particle_count = st.slider(
            "Particle Count:",
            min_value=50,
            max_value=300,
            value=150,
        )

        spread = st.slider(
            "Spread Angle (degrees):",
            min_value=45,
            max_value=360,
            value=360,
        )

    with col2:
        origin_x = st.slider(
            "Horizontal Origin:",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            help="0.0 = left, 0.5 = center, 1.0 = right",
        )

        origin_y = st.slider(
            "Vertical Origin:",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            help="0.0 = top, 0.5 = middle, 1.0 = bottom",
        )

        velocity = st.slider(
            "Launch Velocity:",
            min_value=10.0,
            max_value=100.0,
            value=50.0,
        )

    st.divider()

    if st.button("🎊 Launch Confetti", type="primary", use_container_width=True):
        effect_id = f"confetti_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "confetti",
            "params": {
                "duration": duration,
                "particle_count": particle_count,
                "spread": spread,
                "origin_x": origin_x,
                "origin_y": origin_y,
                "velocity": velocity,
            },
            "started_at": time.time(),
            "duration": duration,
        }
        st.success(
            f"Confetti launched! {particle_count} particles for {duration} seconds"
        )

elif effect_choice == "🎆 Fireworks":
    st.header("🎆 Fireworks Effect")
    st.markdown("Spectacular fireworks display perfect for celebrations.")

    col1, col2 = st.columns(2)

    with col1:
        duration = st.slider(
            "Duration (seconds):",
            min_value=3,
            max_value=20,
            value=8,
        )

        intensity = st.selectbox(
            "Intensity:",
            ["light", "medium", "heavy"],
            index=1,
        )

    with col2:
        launch_count = st.slider(
            "Simultaneous Launches:",
            min_value=1,
            max_value=8,
            value=3,
        )

        color_preset = st.selectbox(
            "Color Scheme:",
            ["Patriotic (Red/White/Blue)", "Rainbow", "Gold & Silver", "Custom"],
            index=0,
        )

    # Set colors based on preset
    if color_preset == "Patriotic (Red/White/Blue)":
        colors = ["#FF0000", "#FFFFFF", "#0000FF", "#FFD700"]
    elif color_preset == "Rainbow":
        colors = [
            "#FF0000",
            "#FF7F00",
            "#FFFF00",
            "#00FF00",
            "#0000FF",
            "#4B0082",
            "#9400D3",
        ]
    elif color_preset == "Gold & Silver":
        colors = ["#FFD700", "#C0C0C0", "#FFFFFF", "#FFA500"]
    else:
        colors = None  # Will use default

    st.divider()

    if st.button("🚀 Launch Fireworks", type="primary", use_container_width=True):
        effect_id = f"fireworks_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "fireworks",
            "params": {
                "duration": duration,
                "intensity": intensity,
                "launch_count": launch_count,
                "colors": colors,
            },
            "started_at": time.time(),
            "duration": duration,
        }
        st.success(f"Fireworks launched! {intensity} intensity for {duration} seconds")

elif effect_choice == "💕 Floating Hearts":
    st.header("💕 Floating Hearts Effect")
    st.markdown("Romantic floating hearts perfect for Valentine's Day or appreciation.")

    col1, col2 = st.columns(2)

    with col1:
        intensity = st.selectbox(
            "Intensity:",
            ["light", "medium", "heavy"],
            index=1,
        )

        speed = st.slider(
            "Float Speed:",
            min_value=0.1,
            max_value=2.0,
            value=1.0,
            step=0.1,
        )

    with col2:
        color_scheme = st.selectbox(
            "Color Scheme:",
            ["Classic Pink/Red", "Pastel", "Hot Pink", "Rainbow Hearts"],
            index=0,
        )

        duration = st.number_input(
            "Duration (seconds, 0 = infinite):",
            min_value=0,
            max_value=60,
            value=0,
        )

    # Set colors based on scheme
    if color_scheme == "Classic Pink/Red":
        colors = ["#FF1493", "#FF69B4", "#FF0000", "#FFC0CB", "#DC143C"]
    elif color_scheme == "Pastel":
        colors = ["#FFB6C1", "#FFC0CB", "#FFE4E1", "#FFF0F5"]
    elif color_scheme == "Hot Pink":
        colors = ["#FF1493", "#FF69B4", "#FF00FF"]
    else:  # Rainbow Hearts
        colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#FF00FF"]

    st.divider()

    if st.button("💖 Float Hearts", type="primary", use_container_width=True):
        effect_id = f"hearts_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "hearts",
            "params": {
                "intensity": intensity,
                "speed": speed,
                "colors": colors,
                "duration": duration if duration > 0 else None,
            },
            "started_at": time.time(),
            "duration": duration if duration > 0 else None,
        }
        st.success(f"Hearts are floating! Intensity: {intensity}, Speed: {speed}x")

elif effect_choice == "🟢 Matrix Rain":
    st.header("🟢 Matrix Rain Effect")
    st.markdown("Classic Matrix-style digital rain effect.")

    col1, col2 = st.columns(2)

    with col1:
        intensity = st.selectbox(
            "Intensity:",
            ["light", "medium", "heavy"],
            index=1,
        )

        speed = st.slider(
            "Fall Speed:",
            min_value=0.1,
            max_value=3.0,
            value=1.0,
            step=0.1,
        )

    with col2:
        color = st.color_picker(
            "Code Color:", value="#00FF00", help="Classic Matrix green: #00FF00"
        )

        font_size = st.slider(
            "Font Size:",
            min_value=10,
            max_value=24,
            value=16,
        )

        duration = st.number_input(
            "Duration (seconds, 0 = infinite):",
            min_value=0,
            max_value=60,
            value=0,
        )

    st.divider()

    if st.button("🕶️ Enter The Matrix", type="primary", use_container_width=True):
        effect_id = f"matrix_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "matrix",
            "params": {
                "intensity": intensity,
                "speed": speed,
                "color": color,
                "font_size": font_size,
                "duration": duration if duration > 0 else None,
            },
            "started_at": time.time(),
            "duration": duration if duration > 0 else None,
        }
        st.success(f"Welcome to The Matrix! Intensity: {intensity}")

elif effect_choice == "🎯 Auto-Detect (Seasonal)":
    st.header("🎯 Auto-Detect Seasonal Effects")
    st.markdown("Automatically applies appropriate effects based on the current date.")

    # Show current date info
    today = date.today()
    holiday = get_holiday_name(today)
    season = get_season(today)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Today's Date", today.strftime("%B %d, %Y"))

    with col2:
        st.metric("Season", season.title())

    with col3:
        if holiday:
            st.metric("Holiday", holiday)
        else:
            st.metric("Holiday", "None")

    st.divider()

    st.markdown("### 🗓️ Effect Calendar")
    st.markdown("""
    **Holidays Detected:**
    - 🎆 **New Year's Day (Jan 1)**: Fireworks
    - 💕 **Valentine's Day (Feb 14)**: Floating Hearts  
    - 🎆 **Independence Day (Jul 4)**: Fireworks
    - 🎄 **Christmas Season (Dec 20-26)**: Snow
    - 🎆 **New Year's Eve (Dec 31)**: Fireworks
    
    **Seasonal Effects:**
    - ❄️ **Winter (Dec-Feb)**: Snow
    - 🌸 **Spring (Mar-May)**: Coming soon...
    - 🦋 **Summer (Jun-Aug)**: Coming soon...
    - 🍂 **Fall (Sep-Nov)**: Coming soon...
    """)

    st.divider()

    intensity = st.selectbox(
        "Effect Intensity:",
        ["light", "medium", "heavy"],
        index=1,
    )

    if st.button(
        "🎨 Apply Auto-Detected Effect", type="primary", use_container_width=True
    ):
        effect_id = f"auto_{time.time()}"
        st.session_state.active_effects[effect_id] = {
            "type": "auto",
            "params": {
                "intensity": intensity,
            },
            "started_at": time.time(),
            "duration": None,  # Auto effects run indefinitely
        }

        effect_name = "seasonal effect"
        if holiday:
            st.success(f"✨ Auto-detected effect applied for: **{holiday}**")
        else:
            st.success(f"✨ Auto-detected effect applied for: **{season.title()}**")

# ============================================================================
# EFFECT RENDERING SECTION
# ============================================================================
# This section runs on EVERY rerun and renders all active effects.
# Effects must be called every rerun to remain visible in the UI.

current_time = time.time()

# Clean up expired effects and render active ones
for effect_id in list(st.session_state.active_effects.keys()):
    effect = st.session_state.active_effects[effect_id]

    # Check if effect has expired
    if effect["duration"] is not None:
        elapsed = current_time - effect["started_at"]
        if elapsed > effect["duration"]:
            del st.session_state.active_effects[effect_id]
            continue

    # Render effect based on type
    effect_type = effect["type"]
    params = effect["params"]

    if effect_type == "snow":
        snow(**params, key=effect_id)
    elif effect_type == "confetti":
        confetti(**params, key=effect_id)
    elif effect_type == "fireworks":
        fireworks(**params, key=effect_id)
    elif effect_type == "hearts":
        floating_hearts(**params, key=effect_id)
    elif effect_type == "matrix":
        matrix_rain(**params, key=effect_id)
    elif effect_type == "auto":
        auto_effect(**params)

# Footer
st.divider()
st.markdown("---")
st.markdown(
    """
<div style='text-align: center; color: #666;'>
    <p>Built with ❤️ using <a href='https://streamlit.io' target='_blank'>Streamlit</a></p>
    <p>📦 <code>streamlit-effects</code> v0.1.0</p>
</div>
""",
    unsafe_allow_html=True,
)
