import os
import time
from typing import cast

import requests
import streamlit as st


API_URL = os.getenv("TRANSLATION_API_URL", "http://localhost:8000")
APP_URL = os.getenv("STREAMLIT_PUBLIC_URL", "http://localhost:8501")


def check_api_ready() -> bool:
    try:
        response = requests.get(f"{API_URL}/ready", timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False


def fetch_supported_pairs():
    cached = st.session_state.get("supported_pairs")
    if cached is not None:
        return cached
    try:
        response = requests.get(f"{API_URL}/supported-languages", timeout=5)
        if response.ok:
            pairs = response.json().get("pairs", [])
            st.session_state["supported_pairs"] = pairs
            return pairs
    except requests.RequestException:
        pass
    return []


def build_language_options(pairs):
    sources = sorted({p["source_lang"] for p in pairs})
    targets_by_source = {}
    for pair in pairs:
        targets_by_source.setdefault(pair["source_lang"], set()).add(pair["target_lang"])
    targets_by_source = {k: sorted(v) for k, v in targets_by_source.items()}
    return sources, targets_by_source


def wait_for_api_ready(max_wait_seconds: int = 30, interval_seconds: int = 2) -> bool:
    deadline = time.time() + max_wait_seconds
    while time.time() < deadline:
        if check_api_ready():
            return True
        time.sleep(interval_seconds)
    return False


def stop_if_not_ready() -> None:
    st.error("Translation API is not ready. Please try again in a moment.")
    st.stop()


def get_cached_api_ready(ttl_seconds: int = 30) -> bool:
    now = time.time()
    cached = st.session_state.get("api_ready")
    checked_at = st.session_state.get("api_ready_checked_at", 0.0)
    if cached is not None and (now - checked_at) < ttl_seconds:
        return bool(cached)
    ready = check_api_ready()
    st.session_state["api_ready"] = ready
    st.session_state["api_ready_checked_at"] = now
    return ready


def set_api_not_ready() -> None:
    st.session_state["api_ready"] = False
    st.session_state["api_ready_checked_at"] = time.time()

def main() -> None:
    st.set_page_config(page_title="Translator", page_icon="🌍")
    st.title("Translator")

    print(f"Streamlit UI available at: {APP_URL}")

    with st.spinner("Waiting for translation API..."):
        api_ready = wait_for_api_ready()
        st.session_state["api_ready"] = api_ready
        st.session_state["api_ready_checked_at"] = time.time()

    if not api_ready:
        stop_if_not_ready()

    pairs = fetch_supported_pairs()
    if not pairs:
        st.error("No supported language pairs available from the API.")
        st.stop()

    source_options, targets_by_source = build_language_options(pairs)

    with st.form("translate"):
        text = st.text_area("Text", height=120)
        col1, col2 = st.columns(2)
        with col1:
            source_lang = cast(str, st.selectbox("Source language", source_options))
        with col2:
            targets = targets_by_source.get(source_lang, [])
            target_lang = cast(str, st.selectbox("Target language", targets))
        submitted = st.form_submit_button("Translate")

    if submitted:
        if not text.strip():
            st.warning("Please enter some text.")
        else:
            if not get_cached_api_ready():
                stop_if_not_ready()
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
                    set_api_not_ready()
                    st.error(f"Error {response.status_code}: {response.text}")
            except requests.RequestException as exc:
                set_api_not_ready()
                st.error(f"Request failed: {exc}")


if __name__ == "__main__":
    main()
