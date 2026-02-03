import os
from typing import cast

import requests
import streamlit as st


API_URL = os.getenv("TRANSLATION_API_URL", "http://localhost:8000")
APP_URL = os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501")

st.set_page_config(page_title="Translator", page_icon="🌍")
st.title("Translator")

print(f"Streamlit UI available at: {APP_URL}")

with st.form("translate"):
    text = st.text_area("Text", height=120)
    col1, col2 = st.columns(2)
    with col1:
        source_lang = st.selectbox("Source language", ["en"])
    with col2:
        target_lang = st.selectbox("Target language", ["fr"])
    submitted = st.form_submit_button("Translate")

if submitted:
    if not text.strip():
        st.warning("Please enter some text.")
    else:
        payload = {
            "text": text,
            "source_lang": source_lang,
            "target_lang": target_lang,
        }
        try:
            response = requests.post(f"{API_URL}/translate", json=payload, timeout=30)
            if response.ok:
                data = response.json()
                st.success("Translation")
                st.write(data["translation"])
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except requests.RequestException as exc:
            st.error(f"Request failed: {exc}")
