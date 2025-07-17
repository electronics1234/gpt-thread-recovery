import streamlit as st
from parser.mhtml_parser import parse_mhtml
from export_utils import export_to_markdown, export_to_pdf
import json
import os
from datetime import datetime
import re

st.set_page_config(page_title="GPT Thread Recovery Kit", layout="wide")
st.title("GPT Thread Recovery Kit v1.0")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    filter_keyword = st.checkbox("Filter results by keyword", value=False)

    uploaded_file = st.file_uploader("Upload your .mhtml ChatGPT export", type="mhtml")
    if uploaded_file:
        file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Uploaded: {uploaded_file.name}")

    st.markdown("### 🗂 Filter by Tag")

    files = sorted([f for f in os.listdir(UPLOAD_DIR) if f.endswith(".mhtml")],
                   key=lambda x: os.path.getmtime(os.path.join(UPLOAD_DIR, x)), reverse=True)

    tag_map = {}
    for f in files:
        json_filename = os.path.splitext(f)[0] + ".json"
        json_path = os.path.join(OUTPUT_DIR, json_filename)
        tags = []

        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as jf:
                    json_data = json.load(jf)
                    tags = json_data.get("tags", [])
            except Exception:
                pass

        tag_map[f] = tags

    all_tags = sorted(set(tag for tags in tag_map.values() for tag in tags))
    selected_tags = st.multiselect("Filter by tag(s):", all_tags)

    st.markdown("### 📂 Available Conversations")

    for f in files:
        tags = tag_map.get(f, [])
        if selected_tags and not any(tag in tags for tag in selected_tags):
            continue

        label = f"{f} ({', '.join(tags)})" if tags else f
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(label, key=f"file_{f}"):
                st.session_state.selected_file = f
                with open(os.path.join(UPLOAD_DIR, f), "rb") as file:
                    st.session_state.messages = parse_mhtml(file)
        with col2:
            delete_clicked = st.button("🗑", key=f"del_{f}", help="Delete file", use_container_width=True)
            if delete_clicked:
                try:
                    os.remove(os.path.join(UPLOAD_DIR, f))
                    base = os.path.splitext(f)[0]
                    for ext in [".json", ".md", ".pdf", ".html"]:
                        out_file = os.path.join(OUTPUT_DIR, base + ext)
                        if os.path.exists(out_file):
                            os.remove(out_file)
                    st.toast(f"Deleted: {f}", icon="🗑️")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Failed to delete {f}: {e}")

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
            if filter_keyword and keyword:
                if not (
                    keyword.lower() in pair.get("user", "").lower()
                    or keyword.lower() in pair.get("assistant", "").lower()
                ):
                    continue

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

        if st.session_state.matched_elements:
            st.markdown(f"""
            <script>
            window.matchElements = {json.dumps(st.session_state.matched_elements)};
            window.matchIndex = {st.session_state.match_index};
            const el = document.getElementById(window.matchElements[window.matchIndex]);
            if (el) el.scrollIntoView({{ behavior: 'smooth' }});
            </script>
            """, unsafe_allow_html=True)

        base_filename = os.path.splitext(st.session_state.selected_file)[0]

        st.markdown("---")
        st.markdown("### 📤 Export Options")

        col_md, col_pdf, col_json = st.columns(3)
        with col_md:
            if st.button("Download Markdown"):
                md_text = export_to_markdown(messages)
                st.download_button("📥 Save Markdown", md_text, file_name=f"{base_filename}.md", mime="text/markdown")

        with col_pdf:
            if st.button("Download PDF"):
                pdf_bytes = export_to_pdf(messages)
                if pdf_bytes:
                    st.download_button("📥 Save PDF", pdf_bytes, file_name=f"{base_filename}.pdf", mime="application/pdf")
                else:
                    st.error("Failed to generate PDF.")

        with col_json:
            if st.button("Download JSON"):
                json_bytes = json.dumps(messages, indent=2, ensure_ascii=False).encode("utf-8")
                st.download_button("📥 Save JSON", json_bytes, file_name=f"{base_filename}.json", mime="application/json")

    except Exception as e:
        st.error(f"Error: {e}")
