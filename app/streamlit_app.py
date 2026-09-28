import streamlit as st

from app.triage.workflow import triage_incident

st.set_page_config(page_title="Team AI Incident Triage", layout="wide")
st.title("Team AI Incident Triage")

sample = "The orders import failed after the vendor file arrived with a new column."
incident_text = st.text_area("Incident report", value=sample, height=180)

if st.button("Triage incident", type="primary"):
    result = triage_incident(incident_text)
    st.subheader("Result")
    st.json(result.model_dump())
