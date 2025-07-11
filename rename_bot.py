import streamlit as st
import io
import time
import mimetypes
import re
from pathlib import Path
from PIL import Image
from datetime import datetime
import os

# ======================
# CONFIGURATION & THEME
# ======================
st.set_page_config(
    page_title="Vyron Pro — Rename Bot",
    page_icon="🌀",
    layout="centered",
    initial_sidebar_state="collapsed",
)

downloads_path = Path.home() / "Downloads"

# ======================
# INIT SESSION STATE
# ======================
if "file_bytes" not in st.session_state:
    st.session_state.file_bytes = None
if "renamed_name" not in st.session_state:
    st.session_state.renamed_name = None
if "file_mime" not in st.session_state:
    st.session_state.file_mime = None
if "original_name" not in st.session_state:
    st.session_state.original_name = None
if "history" not in st.session_state:
    st.session_state.history = []

# ======================
# APP HEADER
# ======================
st.markdown(
    """
    <h1 style='text-align: center; color: #005fbb;'>🌀 Vyron Pro — Rename Bot</h1>
    <p style='text-align: center; color: grey;'>Smarter. Cleaner. Better.</p>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("📁 Choose a file to upload", type=None)
save_to_downloads = st.checkbox("Also save a copy to my Downloads folder", value=False)

# ======================
# SMART CLEAN-UP SUGGESTION
# ======================
def smart_clean(filename):
    name, ext = os.path.splitext(filename)
    clean = re.sub(r"(IMG_|VID_|DOC_|Screenshot_)?(\d{8}_\d{6}|\d+)", "", name)
    clean = clean.replace("__", "_").strip("_").strip()
    if not clean:
        clean = "Renamed_File"
    return clean + ext

# ======================
# CASE & FORMATTING
# ======================
def apply_case_format(name, fmt):
    name_no_ext, ext = os.path.splitext(name)
    if fmt == "lowercase":
        name_no_ext = name_no_ext.lower()
    elif fmt == "UPPERCASE":
        name_no_ext = name_no_ext.upper()
    elif fmt == "Title_Case":
        name_no_ext = name_no_ext.title()
    return name_no_ext + ext

def replace_spaces(name, repl):
    return name.replace(" ", repl)

# ======================
# METADATA VIEWER
# ======================
def show_metadata(file_bytes, mime, filename):
    st.subheader("📊 File Metadata")
    size_kb = len(file_bytes) / 1024
    st.write(f"**Name:** {filename}")
    st.write(f"**MIME Type:** {mime}")
    st.write(f"**Size:** {size_kb:.2f} KB")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"**Processed at:** {now}")
    if mime.startswith("image/"):
        try:
            img = Image.open(io.BytesIO(file_bytes))
            st.write(f"**Dimensions:** {img.width}×{img.height}")
        except:
            pass

# ======================
# DUPLICATE CHECK
# ======================
def check_duplicate(name):
    path = downloads_path / name
    counter = 1
    base, ext = os.path.splitext(name)
    while path.exists():
        path = downloads_path / f"{base}({counter}){ext}"
        counter += 1
    return path.name

# ======================
# MAIN LOGIC
# ======================
if uploaded_file:
    file_bytes = uploaded_file.read()
    st.session_state.file_bytes = file_bytes
    st.session_state.file_mime = uploaded_file.type
    st.session_state.original_name = uploaded_file.name

    st.success(f"✅ Uploaded: **{uploaded_file.name}**")

    # Suggest smart clean name
    default_name = smart_clean(uploaded_file.name)

    # IMAGE PREVIEW
    if uploaded_file.type.startswith("image/"):
        st.image(io.BytesIO(file_bytes), caption="Image Preview", use_column_width=True)

    # METADATA
    show_metadata(file_bytes, uploaded_file.type, uploaded_file.name)

    # Name input
    new_name = st.text_input("✍️ Enter new file name:", value=default_name)

    # CASE & FORMAT OPTIONS
    col1, col2 = st.columns(2)
    with col1:
        fmt = st.selectbox("Case Format:", ["None", "lowercase", "UPPERCASE", "Title_Case"])
    with col2:
        space_repl = st.selectbox("Replace Spaces With:", ["(leave)", "_", "-"])

    if new_name and st.button("🚀 Process Rename"):
        with st.spinner("Renaming..."):
            progress = st.progress(0, text="Processing...")
            for i in range(100):
                time.sleep(0.002)
                progress.progress(i + 1, text=f"Processing... {i+1}%")
            progress.empty()

        # Add extension if missing
        if "." not in new_name:
            detected_extension = mimetypes.guess_extension(st.session_state.file_mime) or ''
            if detected_extension:
                new_name += detected_extension
                st.info(f"ℹ️ No extension provided. Added: `{detected_extension}`")
            else:
                st.warning("⚠️ Could not detect file type. Please add an appropriate extension.")

        # Apply formatting
        if fmt != "None":
            new_name = apply_case_format(new_name, fmt)
        if space_repl != "(leave)":
            new_name = replace_spaces(new_name, space_repl)

        # Check for duplicates
        final_name = check_duplicate(new_name)

        st.session_state.renamed_name = final_name

        if save_to_downloads:
            renamed_path = downloads_path / final_name
            with open(renamed_path, "wb") as f:
                f.write(st.session_state.file_bytes)
            st.info(f"✅ Saved a copy to: `{renamed_path}`")

        st.session_state.history.append((
            st.session_state.original_name,
            final_name,
            st.session_state.file_bytes
        ))

        st.success(f"🎉 File renamed to: **{final_name}**")

# ======================
# DOWNLOAD & HISTORY + FOOTER
# ======================
if st.session_state.file_bytes and st.session_state.renamed_name:
    st.markdown("---")
    st.markdown(f"### 📄 Download: `{st.session_state.renamed_name}`")
    st.download_button(
        label=f"📥 Download {st.session_state.renamed_name}",
        data=io.BytesIO(st.session_state.file_bytes),
        file_name=st.session_state.renamed_name,
        mime=st.session_state.file_mime,
    )

if st.session_state.history:
    st.markdown("---")
    st.subheader("🕒 Rename History")
    for idx, (orig, renamed, bytes_) in enumerate(reversed(st.session_state.history[-5:]), 1):
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"{idx}. **{orig} → {renamed}**")
        with col2:
            st.download_button(
                label="Restore",
                data=io.BytesIO(bytes_),
                file_name=renamed,
                mime=mimetypes.guess_type(renamed)[0] or "application/octet-stream",
                key=f"restore_{idx}"
            )

st.markdown(
    """
    <hr>
    <style>
    .footer-icons a {
        margin: 0 15px;
        text-decoration: none;
        color: #005fbb;
        transition: transform 0.2s ease, filter 0.2s ease;
    }
    .footer-icons img {
        width: 36px;
        vertical-align: middle;
        filter: grayscale(50%);
        transition: 0.2s ease;
    }
    .footer-icons a:hover img {
        transform: scale(1.2);
        filter: grayscale(0%);
    }
    </style>

    <p style='text-align: center; color: grey; font-size:small;'>
        Made with ❤️ by Vyron Pro
        <br><br>
        <span class="footer-icons">
            <a href="https://github.com/Krishna2005-yadav" target="_blank">
                <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/github.svg" alt="GitHub" />
            </a>
            <a href="https://twitter.com/YOUR_TWITTER" target="_blank">
                <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/x.svg" alt="Twitter/X" />
            </a>
            <a href="https://linkedin.com/in/YOUR_LINKEDIN" target="_blank">
                <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/linkedin.svg" alt="LinkedIn" />
            </a>
            <a href="https://discord.com/users/YOUR_DISCORD_ID" target="_blank">
                <img src="https://cdn.jsdelivr.net/gh/simple-icons/simple-icons/icons/discord.svg" alt="Discord" />
            </a>
        </span>
    </p>
    """,
    unsafe_allow_html=True
)

#streamlit run rename_bot.py 
