"""
Full-Page CSS Overlay Test
============================

Test script to verify effects cover entire viewport including sidebar and header.
"""

import streamlit as st
from streamlit_effects import snow, confetti, floating_hearts, fireworks, matrix_rain

st.set_page_config(page_title="🎨 Full-Page Effects Test", layout="wide")

# Sidebar content (effects should overlay this)
with st.sidebar:
    st.header("🎯 Sidebar Content")
    st.write("Effects should cover this sidebar!")
    st.metric("Test Metric", "100%")
    st.button("Sidebar Button")

# Main content
st.title("🎨 Full-Page CSS Overlay Effects Test")
st.markdown("""
### Testing Full-Viewport Coverage

The effects below should cover:
- ✅ This main content area
- ✅ The sidebar (left panel)
- ✅ The header/toolbar (top)
- ✅ Everything on screen!

Click buttons to test each effect:
""")

# Effect controls
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    if st.button("❄️ Snow", use_container_width=True):
        st.session_state.show_snow = True

with col2:
    if st.button("🎉 Confetti", use_container_width=True):
        confetti(
            duration=5, key=f"confetti-{st.session_state.get('confetti_count', 0)}"
        )
        st.session_state.confetti_count = st.session_state.get("confetti_count", 0) + 1

with col3:
    if st.button("❤️ Hearts", use_container_width=True):
        st.session_state.show_hearts = True

with col4:
    if st.button("🎆 Fireworks", use_container_width=True):
        fireworks(
            duration=8, key=f"fireworks-{st.session_state.get('fireworks_count', 0)}"
        )
        st.session_state.fireworks_count = (
            st.session_state.get("fireworks_count", 0) + 1
        )

with col5:
    if st.button("🖥️ Matrix", use_container_width=True):
        st.session_state.show_matrix = True

st.divider()

# Continuous effects (toggleable)
if st.session_state.get("show_snow", False):
    snow(intensity="medium", speed=1.0, duration=None)
    if st.button("🛑 Stop Snow"):
        st.session_state.show_snow = False
        st.rerun()

if st.session_state.get("show_hearts", False):
    floating_hearts(heart_count=30, speed=1.0, duration=None)
    if st.button("🛑 Stop Hearts"):
        st.session_state.show_hearts = False
        st.rerun()

if st.session_state.get("show_matrix", False):
    matrix_rain(density="medium", speed=1.0, duration=None)
    if st.button("🛑 Stop Matrix"):
        st.session_state.show_matrix = False
        st.rerun()

# Test content
st.header("📊 Sample Dashboard Content")
col_a, col_b, col_c = st.columns(3)

with col_a:
    st.metric("Revenue", "$1.2M", "+15%")
    st.progress(0.75)

with col_b:
    st.metric("Users", "10,234", "+8%")
    st.progress(0.60)

with col_c:
    st.metric("Conversion", "3.4%", "+2.1%")
    st.progress(0.85)

st.info(
    "🎯 **Verification**: Do you see effects covering the ENTIRE screen including sidebar and header?"
)

st.markdown("""
### Expected Behavior:
- Snow/Hearts/Matrix should continue until stopped
- Confetti/Fireworks should auto-remove after duration
- All effects should be non-interactive (don't block buttons)
- Effects should cover sidebar, header, and all content
""")
