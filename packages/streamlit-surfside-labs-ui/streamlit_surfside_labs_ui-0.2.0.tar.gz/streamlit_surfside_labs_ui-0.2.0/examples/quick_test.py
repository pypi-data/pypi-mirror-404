"""
Quick Test of Streamlit Effects
=================================

Simple test to verify effects are working.
"""

import streamlit as st
from streamlit_effects import snow, confetti, get_season

st.title("🧪 Streamlit Effects - Quick Test")

st.write("Toggle the checkboxes below to enable/disable effects:")

col1, col2, col3 = st.columns(3)

with col1:
    enable_snow = st.checkbox("❄️ Enable Snow", value=False)

with col2:
    enable_confetti = st.checkbox("🎉 Enable Confetti", value=False)

with col3:
    season = get_season()
    st.metric("Current Season", season.title())

# Render effects outside conditionals (must be called every rerun to stay visible)
if enable_snow:
    snow(intensity="medium", speed=1.0, key="test_snow")

if enable_confetti:
    confetti(duration=3600, key="test_confetti")  # 1 hour (effectively continuous)

st.divider()

st.markdown("""
### ✅ If you see effects when clicking buttons, the package is working!

**Available Effects:**
- `snow()` - Falling snowflakes
- `confetti()` - Celebration confetti
- `fireworks()` - Fireworks display
- `floating_hearts()` - Rising hearts
- `matrix_rain()` - Matrix digital rain
- `auto_effect()` - Auto-detect seasonal effects
""")
