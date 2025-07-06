import streamlit as st
from parser.mhtml_parser import parse_mhtml
import json
import os
from datetime import datetime
import time
import re

st.set_page_config(page_title="GPT Thread Recovery Kit", layout="wide")
st.title("GPT Thread Recovery Kit v1.0")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "match_index" not in st.session_state:
    st.session_state.match_index = 0

if "matched_elements" not in st.session_state:
    st.session_state.matched_elements = []

with st.sidebar:
    st.markdown("### 🔍 Search")
    keyword = st.text_input("Highlight keyword in conversation:", key="search_box")

    uploaded_file = st.file_uploader("Upload your .mhtml ChatGPT export", type="mhtml")
    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded: {uploaded_file.name}")

    st.markdown("### 🗂 Available Conversations")
    files = sorted([f for f in os.listdir(UPLOAD_DIR) if f.endswith(".mhtml")], key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)), reverse=True)
    for f in files:
        if st.button(f, key=f"file_{f}"):
            st.session_state.selected_file = f
            with open(os.path.join(UPLOAD_DIR, f), "rb") as file:
                st.session_state.messages = parse_mhtml(file)

    st.markdown("---")
    st.markdown("**GPT Thread Recovery Kit v1.0**")

def highlight_text(text, keyword, element_id):
    if keyword:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        highlighted = pattern.sub(lambda m: f"<mark style='background-color: yellow'>{m.group(0)}</mark>", text)
        st.session_state.matched_elements.append(element_id)
        return highlighted
    return text

if st.session_state.selected_file:
    try:
        st.success(f"Loaded: {st.session_state.selected_file}")
        st.subheader("Conversation View (Side-by-Side)")

        st.session_state.matched_elements = []

        messages = st.session_state.messages

        # Group messages into pairs (user followed by assistant)
        paired_messages = []
        temp_pair = {}
        for msg in messages:
            if msg["role"] == "user":
                if temp_pair:
                    paired_messages.append(temp_pair)
                    temp_pair = {}
                temp_pair["user"] = msg["content"]
            elif msg["role"] == "assistant":
                temp_pair["assistant"] = msg["content"]
                paired_messages.append(temp_pair)
                temp_pair = {}
        if temp_pair:
            paired_messages.append(temp_pair)

        for i, pair in enumerate(paired_messages):
            col1, col2 = st.columns([1, 1])
            with col1:
                if "user" in pair:
                    st.markdown("**User:**")
                    element_id = f"user_{i}"
                    highlighted_user = highlight_text(pair["user"], keyword, element_id)
                    st.markdown(f"<div id='{element_id}' style='background:#111;padding:10px;border-radius:6px;color:#ccc'>{highlighted_user}</div>", unsafe_allow_html=True)
            with col2:
                if "assistant" in pair:
                    st.markdown("**Assistant:**")
                    element_id = f"assistant_{i}"
                    highlighted_assistant = highlight_text(pair["assistant"], keyword, element_id)
                    st.markdown(f"<div id='{element_id}' style='background:#222;padding:10px;border-radius:6px;color:#eee'>{highlighted_assistant}</div>", unsafe_allow_html=True)

        # JavaScript scroll to current match
        if st.session_state.matched_elements:
            st.markdown(f"""
            <script>
            window.matchElements = {json.dumps(st.session_state.matched_elements)};
            window.matchIndex = {st.session_state.match_index};
            const el = document.getElementById(window.matchElements[window.matchIndex]);
            if (el) el.scrollIntoView({{ behavior: 'smooth' }});
            </script>
            """, unsafe_allow_html=True)

        # Save output JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_filename = f"chat_{timestamp}.json"
        json_path = os.path.join("output", json_filename)
        os.makedirs("output", exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

        with open(json_path, "rb") as f:
            st.download_button("Download JSON", f, file_name=json_filename, mime="application/json")

    except Exception as e:
        st.error(f"Error: {e}")
