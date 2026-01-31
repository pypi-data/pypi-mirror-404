"""
Minimal component test
"""

import streamlit as st
from streamlit_effects import snow

st.title("Minimal Test")

st.write("About to call snow()...")

# Call snow with explicit parameters
snow(intensity="medium", speed=1.0, color="#FFFFFF", duration=10, key="test_snow_1")

st.write("Snow called!")
st.write("Check browser console (F12) for any errors.")
