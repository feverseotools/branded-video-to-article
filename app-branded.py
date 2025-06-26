from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
import streamlit as st
import tempfile
import os
from pathlib import Path
import mimetypes
import glob

# Check for OpenCV availability
try:
    import cv2
    have_cv2 = True
except ModuleNotFoundError:
    have_cv2 = False
    cv2 = None

import base64

# --- AUTENTICACIÓN SIMPLE ---
PASSWORD = "SECRETMEDIA"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    pw = st.text_input(
        "Enter your super-ultra secret password (v26/06/2025 11:28h)",
        type="password"
    )
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Convert Video into Text")
st.title("📝 Video > Text AI Converter for SMN")

# --- CARGA DE PROMPTS EXTERNOS ---
def load_prompt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

sites = {
    "Valencia Secreta": load_prompt("prompts/sites/valencia_secreta.txt"),
    "Barcelona Secreta": load_prompt("prompts/sites/barcelona_secreta.txt"),
    "Madrid Secreto": load_prompt("prompts/sites/madrid_secreto.txt"),
    "New York City": load_prompt("prompts/sites/nyc_secret.txt"),
    "EXPERIMENTAL JAKUB": load_prompt("prompts/sites/experimental.txt")
}

editors = {
    "Álvaro Llagunes": load_prompt("prompts/editors/alvaro_llagunes.txt"),
    "Bianca Bahamondes": load_prompt("prompts/editors/bianca_bahamondes.txt"),
    "Jorge López Torrecilla": load_prompt("prompts/editors/jorge_lopez.txt"),
    "Alberto del Castillo": load_prompt("prompts/editors/alberto_del_castillo.txt")
}

categories = {
    "Gastronomy (restaurants, bars, street food)": load_prompt("prompts/category/food.txt"),
    "Sports for Secret Media": load_prompt("prompts/category/sports-smn.txt"),
    "NYC Book Club - Community": load_prompt("prompts/category/nyc-book-club.txt"),
    "Housing situation in big cities": load_prompt("prompts/category/problemas-vivienda.txt"),
    "Generic (use with caution)": load_prompt("prompts/category/generic.txt")
}

languages = {
    "English for US": load_prompt("prompts/languages/en-us.txt"),
    "Español para España": load_prompt("prompts/languages/es-sp.txt")
}

# --- SELECCIÓN DE TIPO DE SUBIDA ---
upload_type = st.radio(
    "What do you want to upload?",
    ["Video", "Image"],
    horizontal=True
)
video_file = None
image_file = None

# Flags for metadata
is_smn_video = True
visual_analysis = False
frame_interval = 1

# --- FILE UPLOADER & OPTIONS ---
if upload_type == "Video":
    video_file = st.file_uploader(
        "Upload your video (.mp4, .mov, .avi, .mp3, .wav, .ogg, .webm):",
        type=["mp4", "mov", "avi", "mpeg", "mp3", "wav", "ogg", "webm"]
    )
    is_smn = st.radio(
        "Is this an SMN-owned video?",
        ["Yes", "No"],
        horizontal=True,
        key="is_smn"
    )
    is_smn_video = (is_smn == "Yes")
    if video_file:
        if have_cv2:
            visual_analysis = st.checkbox(
                "If this video DOESN'T include voice over, mark this box; if it does, leave it unchecked.",
                key="visual_analysis"
            )
            if visual_analysis:
                frame_interval = st.slider(
                    "(Don't modify this unless you know what you're doing) Extract one frame every N seconds",
                    1,
                    10,
                    1,
                    key="frame_interval"
                )
        else:
            st.warning(
                "Frame analysis disabled: install 'opencv-python-headless' to enable this feature."
            )
elif upload_type == "Image":
    image_file = st.file_uploader(
        "Upload an image (.jpg, .jpeg, .png):",
        type=["jpg", "jpeg", "png"]
    )

# --- PROCESAMIENTO DE VÍDEO ---
if upload_type == "Video" and video_file:
    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=Path(video_file.name).suffix
    ) as tmp:
        tmp.write(video_file.read())
        tmp_path = tmp.name
    mime_type, _ = mimetypes.guess_type(tmp_path)
    if not mime_type or not (
        mime_type.startswith("video") or mime_type.startswith("audio")
    ):
        st.error("❌ Invalid file format for Whisper.")
        os.remove(tmp_path)
        st.stop()

# --- PROCESAMIENTO DE IMAGEN ---
elif upload_type == "Image" and image_file:
    if "image_description" not in st.session_state:
        image_bytes = image_file.read()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        with st.spinner("🧠 Analyzing image with GPT-4o..."):
            resp = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": \
                            "Describe this image in detail. " \
                            "Focus on visual details, place, objects, text if any."
                        },
                        {"type": "image_url", "image_url": {"url":
                            f"data:image/jpeg;base64,{b64}"}}]
                    }
                ],
                max_tokens=800
            )
        st.session_state.image_description = resp.choices[0].message.content
        st.success("✅ Image description generated")
elif upload_type == "Image":
    st.info("📸 Please upload an image to continue.")

# --- PREVIEW IMAGEN ---
if "image_description" in st.session_state:
    st.text_area(
        "🖼 Description of the image:",
        st.session_state.image_description,
        height=200,
        key="image_desc_preview"
    )

# --- METADATOS PARA VÍDEO NO SMN ---
if upload_type == "Video" and not is_smn_video and video_file:
    network = st.selectbox(
        "Social network:",
        ["YouTube", "TikTok", "Instagram", "Facebook", "Twitter", "Other"],
        key="video_network"
    )
    username = st.text_input(
        "Account (example: @user123):",
        key="video_username"
    )
    original_url = st.text_input(
        "URL of the video:",
        key="video_url"
    )
    tmp_extra_video = st.text_area(
        "(Optional) Extra instructions for this non-SMN video \
        (use as much context as you want):",
        height=100,
        key="extra_video_prompt"
    )

# --- CONFIGURACIÓN DEL ARTÍCULO ---
editor = st.selectbox(
    "Editor:",
    ["Select...", *editors.keys()]
)
site = st.selectbox(
    "Publish site:",
    ["Select...", *sites.keys()]
)
category_key = st.selectbox(
    "Content category:",
    ["Select...", *categories.keys()]
)
language_key = st.selectbox(
    "Output language:",
    ["Select...", *languages.keys()]
)
extra_prompt = ""
if site != "Select...":
    extra_prompt = st.text_area(
        "Additional editor instructions (optional):"
    )

# --- GENERAR ARTÍCULO ---
if st.button("✍️ Create article"):
    try:
        # Transcripción y análisis visual
        transcription = ""
        visual_context = ""
        if upload_type == "Video":
            if visual_analysis and have_cv2:
                with st.spinner(
                    "🖼 Analyzing video frames (this may take some time)..."
                ):
                    cap = cv2.VideoCapture(tmp_path)
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    frame_count = 0
                    success, frame = cap.read()
                    while success:
                        if frame_count % int(fps * frame_interval) == 0:
                            _, buffer = cv2.imencode('.jpg', frame)
                            b64_frame = \
                                base64.b64encode(buffer).decode("utf-8")
                            resp = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "user", "content": [
                                        {"type": "text", "text":
                                            "Describe visual elements in this frame."
                                        },
                                        {"type": "image_url", "image_url": {
                                            "url":
                                            f"data:image/jpeg;base64,{b64_frame}"}}
                                    ]}
                                ],
                                max_tokens=150
                            )
                            visual_context += (
                                resp.choices[0].message.content + "\n"
                            )
                        success, frame = cap.read()
                        frame_count += 1
                    cap.release()
            with st.spinner("⏳ Transcribing audio with Whisper..."):
                with open(tmp_path, "rb") as audio_f:
                    tr = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_f,
                        response_format="json"
                    )
                transcription = tr.text
            st.success("✅ Transcription completed")
            st.text_area(
                "Transcribed text:",
                transcription,
                height=200,
                key="video_text"
            )
            if visual_analysis and have_cv2:
                st.text_area(
                    "Visual context:",
                    visual_context,
                    height=200,
                    key="visual_context"
                )
        elif upload_type == "Image" and "image_description" in st.session_state:
            transcription = st.session_state.image_description
            st.text_area(
                "Image description:",
                transcription,
                height=200,
                key="image_text_area"
            )
        else:
            st.error(
                "❌ Upload a valid video or wait for image description."
            )
            st.stop()
        # Construir prompt
        full_prompt = sites[site]
        if editor != "Select...":
            full_prompt += f"\n\nEditor context:\n{editors[editor]}"
        full_prompt += f"\n\nTranscription for article:\n{transcription}"
        if upload_type == "Video" and not is_smn_video:
            full_prompt += (
                f"\n\nNon-SMN video instructions:\n{tmp_extra_video}"
            )
            full_prompt += (
                f"\nSource network: {network}" +
                f"\nOriginal account: {username}" +
                f"\nOriginal URL: {original_url}"
            )
        if upload_type == "Video" and visual_analysis and have_cv2:
            full_prompt += (
                f"\n\nExtracted visual context:\n{visual_context}"
            )
        if category_key != "Select...":
            full_prompt += (
                f"\n\nCategory context:\n{categories[category_key]}"
            )
        if language_key != "Select...":
            full_prompt += (
                f"\n\nLanguage for article:\n{languages[language_key]}"
            )
        if extra_prompt:
            full_prompt += (
                f"\n\nAdditional editor instructions:\n{extra_prompt}"
            )
        # 3. Generar artículo con múltiples modelos de fallback
        models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo-16k", "gpt-3.5-turbo", "gpt-3.5"]
        resp = None
        last_error = None
        for model_name in models:
            try:
                with st.spinner(f"🧠 Generating article using {model_name}..."):
                    resp = client.chat.completions.create(
                        model=model_name,
                        messages=[
                            {"role": "system", "content": "Eres un redactor profesional especializado en contenido local."},
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=0.7
                    )
                st.info(f"✅ Generated with {model_name}")
                break
            except Exception as e:
                # Reintentar con siguiente modelo si error de modelo no encontrado o acceso
                err_code = getattr(e, 'code', None)
                if err_code == 'model_not_found' or ('does not have access' in str(e)):
                    last_error = e
                    continue
                else:
                    raise
        if resp is None:
            st.error(f"❌ Todos los modelos fallaron. Último error: {last_error}")
            st.stop()
        article = resp.choices[0].message.content
        # Mostrar artículo
        st.info(f"📝 Words: {len(article.split())}")
        st.success("✅ Article ready")
        st.subheader("🔎 Article:")
        st.markdown(article, unsafe_allow_html=True)
        # Titulares Discover, HTML/MD preview y descarga...
    except Exception as e:
        st.error(f"❌ Error: {e}")
    finally:
        if (
            upload_type == "Video"
            and 'tmp_path' in locals()
            and os.path.exists(tmp_path)
        ):
            os.remove(tmp_path)
