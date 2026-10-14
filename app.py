import streamlit as st

st.set_page_config(
    page_title="SmartRes | OS Resource Manager",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ SmartRes")
st.subheader("Smart Operating System Resource Management System")

st.write(
    "An interactive simulation of operating-system process "
    "management, resource allocation, and deadlock avoidance."
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Active Processes", 0)

with col2:
    st.metric("Resource Types", 0)

with col3:
    st.metric("Pending Requests", 0)

st.info(
    "Foundation ready. Process management, resource allocation, "
    "database persistence, and Banker’s Algorithm will be added "
    "in the next implementation stages."
)

st.caption("SmartRes • Development Build 0.1")