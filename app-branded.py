from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import streamlit as st
import tempfile
import os
from pathlib import Path
import mimetypes
import glob

# Para obtener contexto de URL externa
import requests
from bs4 import BeautifulSoup

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
        "Enter your super-ultra secret password (v26/06/2025 12:52h)",
        type="password"
    )
    if pw == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

client = OpenAI()

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Convert Branded Video into Text")
st.title("📝 Branded Video > Text AI Converter for SMN")

# --- CARGA DE PROMPTS EXTERNOS ---
# Carga todos los prompts desde .txt
PROMPT_DIR = Path("prompts")

def load_prompt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# Sitios
sites = {f.stem: load_prompt(f) for f in (PROMPT_DIR / "sites").glob("*.txt")}
# Editores
editors = {f.stem: load_prompt(f) for f in (PROMPT_DIR / "editors").glob("*.txt")}
# Categorías
categories = {f.stem: load_prompt(f) for f in (PROMPT_DIR / "category").glob("*.txt")}
# Idiomas
languages = {f.stem: load_prompt(f) for f in (PROMPT_DIR / "languages").glob("*.txt")}

# --- SELECCIÓN DE TIPO DE SUBIDA ---
upload_type = st.radio(
    "¿Qué quieres subir?",
    ["Video", "Imagen"],
    horizontal=True
)
video_file = None
image_file = None

# Flags para metadata
en_smn_video = True
visual_analysis = False
frame_interval = 1

# --- CARGA DE ARCHIVOS TEMPORALES ---
if upload_type == "Video":
    video_file = st.file_uploader(
        "Sube tu video (.mp4, .mov, .avi, .mp3, .wav, .ogg, .webm):",
        type=["mp4", "mov", "avi", "mpeg", "mp3", "wav", "ogg", "webm"]
    )
    if video_file:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(video_file.read())
        tmp_path = tmp.name
        tmp.close()
    smn_choice = st.radio(
        "¿Es un video de SMN?",
        ["Sí", "No"],
        horizontal=True,
        key="smn_choice"
    )
    en_smn_video = (smn_choice == "Sí")
    if have_cv2 and video_file:
        visual_analysis = st.checkbox(
            "Marcar si NO tiene voz."
        )
        if visual_analysis:
            frame_interval = st.slider(
                "Extraer un frame cada N segundos", 1, 10, 1
            )
elif upload_type == "Imagen":
    image_file = st.file_uploader(
        "Sube una imagen (.jpg, .jpeg, .png):",
        type=["jpg", "jpeg", "png"]
    )
    if image_file:
        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(image_file.read())
        tmp_path = tmp.name
        tmp.close()
        # Aquí podrías añadir análisis de visión

# --- METADATOS PARA VIDEO NO SMN ---
if upload_type == "Video" and video_file and not en_smn_video:
    network = st.selectbox(
        "Red social:",
        ["YouTube", "TikTok", "Instagram", "Facebook", "Twitter", "Otra"]
    )
    username = st.text_input("Cuenta (ej: @usuario):")
    original_url = st.text_input("URL del video:")
    extra_video_prompt = st.text_area(
        "Instrucciones extra (opcional):",
        height=80
    )

# --- CONFIGURACIÓN DEL ARTÍCULO ---
# Campo adicional: URL de contexto
context_url = st.text_input("URL de contexto (opcional):")

editor = st.selectbox("Editor:", ["Seleccionar...", *editors.keys()])
site = st.selectbox("Sitio publicación:", ["Seleccionar...", *sites.keys()])
category_key = st.selectbox("Categoría:", ["Seleccionar...", *categories.keys()])
language_key = st.selectbox("Idioma salida:", ["Seleccionar...", *languages.keys()])
extra_prompt = ""
if site != "Seleccionar...":
    extra_prompt = st.text_area("Instrucciones editor (opcional):", height=80)

# --- GENERAR ARTÍCULO ---
if st.button("Crear artículo"):
    try:
        # Contexto adicional desde URL
        context_content = ""
        if context_url:
            try:
                r = requests.get(context_url)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, 'html.parser')
                # Tomar párrafos relevantes
                paragraphs = soup.find_all('p')
                context_content = '\n'.join(p.get_text() for p in paragraphs[:10])
            except Exception as e:
                st.warning(f"Error al extraer contexto: {e}")

        # Transcripción / Análisis visual
        transcription = ""
        visual_context = ""
        if upload_type == "Video" and video_file:
            # Análisis visual
            if visual_analysis and have_cv2:
                with st.spinner("Analizando frames..."):
                    cap = cv2.VideoCapture(tmp_path)
                    fps = cap.get(cv2.CAP_PROP_FPS) or 25
                    cnt = 0
                    success, frame = cap.read()
                    while success:
                        if cnt % int(fps * frame_interval) == 0:
                            _, buf = cv2.imencode('.jpg', frame)
                            b64 = base64.b64encode(buf).decode()
                            resp_fr = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role":"user","content":[
                                        {"type":"text","text":"Describe lo visual."},
                                        {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}
                                    ]}
                                ], max_tokens=150)
                            visual_context += resp_fr.choices[0].message.content + "\n"
                        success, frame = cap.read()
                        cnt += 1
                    cap.release()
            # Transcripción audio
            with st.spinner("Transcribiendo audio..."):
                with open(tmp_path, 'rb') as f:
                    tr = client.audio.transcriptions.create(
                        model='whisper-1', file=f, response_format='json')
                transcription = tr.text
            st.text_area("Transcripción:", transcription, height=200)
            if visual_context:
                st.text_area("Contexto visual:", visual_context, height=200)
        elif upload_type == "Imagen" and image_file:
            transcription = st.session_state.get('image_description', '')
            st.text_area("Descripción imagen:", transcription, height=200)
        else:
            st.error("Primero sube un video o imagen válida.")
            st.stop()

        # Construir prompt final
        prompt = ''
        if site in sites:
            prompt += sites[site]
        if editor in editors:
            prompt += f"\nEditor:\n{editors[editor]}"
        if context_content:
            prompt += f"\nContexto extra desde {context_url}:\n{context_content}"
        prompt += f"\nTranscripción:\n{transcription}"
        if upload_type == "Video" and not en_smn_video:
            prompt += f"\nInstrucciones video no SMN:\n{extra_video_prompt}\nRed: {network}\nCuenta: {username}\nURL original: {original_url}"
        if visual_context:
            prompt += f"\nContexto visual:\n{visual_context}"
        if category_key in categories:
            prompt += f"\nCategoría:\n{categories[category_key]}"
        if language_key in languages:
            prompt += f"\nIdioma:\n{languages[language_key]}"
        if extra_prompt:
            prompt += f"\nInstrucciones editor:\n{extra_prompt}"

        # Fallback modelos
        models = ["gpt-4o", "gpt-4", "gpt-3.5-turbo-16k", "gpt-3.5-turbo"]
        resp = None
        for m in models:
            try:
                with st.spinner(f"Generando con {m}..."):
                    resp = client.chat.completions.create(
                        model=m,
                        messages=[
                            {"role":"system","content":"Eres un redactor profesional."},
                            {"role":"user","content":prompt}
                        ],
                        temperature=0.7
                    )
                break
            except Exception:
                continue
        if not resp:
            st.error("Fallaron todos los modelos.")
            st.stop()

        article = resp.choices[0].message.content
        st.subheader("Artículo generado")
        st.markdown(article)

    except Exception as e:
        st.error(f"Error: {e}")
    finally:
        # Limpieza
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
