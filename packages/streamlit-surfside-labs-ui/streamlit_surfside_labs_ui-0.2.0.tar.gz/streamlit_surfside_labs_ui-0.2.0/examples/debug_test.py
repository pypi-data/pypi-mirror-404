"""
Debug test - check if component loads at all
"""

import streamlit as st
import sys

sys.path.insert(0, "..")

st.title("Component Debug Test")

# Check if component can be imported
try:
    from streamlit_effects.utils.component_registry import (
        _component_func,
        render_effect,
    )

    st.success("✅ Component imported successfully")

    # Check build path
    import os

    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    build_dir = os.path.join(parent_dir, "streamlit_effects", "frontend", "build")
    st.write(f"Build dir: {build_dir}")
    st.write(f"Build dir exists: {os.path.exists(build_dir)}")

    if os.path.exists(build_dir):
        files = os.listdir(build_dir)
        st.write(f"Files in build: {files}")

        index_path = os.path.join(build_dir, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                content = f.read()
                st.code(content, language="html")

except Exception as e:
    st.error(f"❌ Error importing component: {e}")
    import traceback

    st.code(traceback.format_exc())

st.divider()

# Try to render component
st.write("Attempting to render snow effect...")
try:
    from streamlit_effects import snow

    result = snow(intensity="medium", duration=5, key="debug_snow")
    st.write(f"Component returned: {result}")
    st.success("✅ Component called (check if iframe appears above)")
except Exception as e:
    st.error(f"❌ Error calling component: {e}")
    import traceback

    st.code(traceback.format_exc())
