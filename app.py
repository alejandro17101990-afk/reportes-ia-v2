import streamlit as st
from docx import Document
import speech_recognition as sr
from openai import OpenAI
from streamlit_quill import st_quill

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Radiology AI Workspace", layout="wide", initial_sidebar_state="expanded")

# 2. INYECCIÓN DE CSS (DISEÑO PREMIUM)
st.markdown("""
    <style>
    .stApp { background-color: #08080c; color: #e2e8f0; font-family: 'Inter', sans-serif; }
    [data-testid="stSidebar"] { background-color: #0d0d12; border-right: 1px solid #1f1f2e; }
    .stButton>button { background-color: #1d4ed8 !important; color: white !important; border-radius: 8px !important; border: none !important; padding: 0.5rem 1rem !important; font-weight: 600 !important; transition: all 0.2s ease; width: 100%; }
    .stButton>button:hover { background-color: #2563eb !important; box-shadow: 0 0 15px rgba(37, 99, 235, 0.4); }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] { background-color: #12121a; border: 1px solid #232336; border-radius: 12px; padding: 20px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stTextArea textarea { background-color: #0f0f14 !important; color: #f8fafc !important; border: 1px solid #2a2a3f !important; border-radius: 8px !important; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 600 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. FUNCIONES AUXILIARES
def leer_word(file):
    doc = Document(file)
    return '\n'.join([para.text for para in doc.paragraphs])

def transcribir_audio(audio_file):
    r = sr.Recognizer()
    with sr.AudioFile(audio_file) as source:
        audio_data = r.record(source)
        try:
            return r.recognize_google(audio_data, language="es-MX")
        except sr.UnknownValueError:
            return "[No se detectó voz clara]"
        except Exception as e:
            return f"[Error: {e}]"

if 'reporte_generado' not in st.session_state:
    st.session_state.reporte_generado = ""

# 4. BARRA LATERAL
with st.sidebar:
    st.title("🌌 Plataforma IA")
    try:
        api_key = st.secrets["deepseek_key"]
        st.success("DeepSeek: Conectado 🟢")
    except Exception:
        api_key = st.text_input("DeepSeek API Key", type="password")
    
    st.divider()
    st.caption("PLANTILLAS Y CONTEXTO")
    archivo_plantilla = st.file_uploader("Cargar Plantilla (.docx, .txt)", type=["docx", "txt"])
    
    plantilla_contenido = ""
    if archivo_plantilla:
        if archivo_plantilla.name.endswith(".docx"):
            plantilla_contenido = leer_word(archivo_plantilla)
        else:
            plantilla_contenido = archivo_plantilla.read().decode("utf-8")
        st.success("Plantilla activa ✅")

# 5. ESPACIO DE TRABAJO
if api_key:
    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

    st.title("Configurar Reporte")
    col_input, col_output = st.columns([1.1, 1.3], gap="large")

    with col_input:
        st.subheader("Entrada de Datos")
        mod_col, sub_col = st.columns(2)
        with mod_col:
            modalidad = st.selectbox("Modalidad", ["Tomografía", "Resonancia", "Rayos X", "Ultrasonido", "Fluoroscopia"])
        with sub_col:
            estilo = st.selectbox("Estilo", ["Conciso", "Académico", "Institucional"])
        
        st.write("🎙️ **Voz a texto**")
        audio_file = st.audio_input("Grabar hallazgos")
        st.write("📝 **Notas adicionales**")
        notas_texto = st.text_area("Define el contexto...", height=120)

        if st.button("Procesar y Generar Reporte"):
            with st.spinner("Procesando con DeepSeek AI..."):
                texto_dictado = ""
                if audio_file:
                    texto_dictado = transcribir_audio(audio_file)
                    st.info(f"**Voz detectada:** {texto_dictado}")

                hallazgos = f"Notas: {notas_texto}\nDictado: {texto_dictado}"
                
                if not notas_texto and not texto_dictado:
                    st.warning("Por favor, ingresa notas o dicta hallazgos.")
                else:
                    prompt = f"""
                    Eres un Médico Radiólogo experto. Genera un informe estructurado de {modalidad} en estilo {estilo}.
                    PLANTILLA INSTITUCIONAL: {plantilla_contenido if plantilla_contenido else "Usa estructura estándar médica."}
                    HALLAZGOS: {hallazgos}
                    Usa formato HTML básico para resaltar texto (<b> para negritas). Devuelve solo el reporte clínico.
                    """
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "system", "content": prompt}, {"role": "user", "content": "Genera el reporte."}],
                        temperature=0.2
                    )
                    st.session_state.reporte_generado = response.choices[0].message.content

    with col_output:
        st.subheader("</> Redacción del Reporte")
        contenido_editado = st_quill(value=st.session_state.reporte_generado, html=True, key="editor_quill")
else:
    st.info("👈 Ingresa tu API Key de DeepSeek para desbloquear el espacio de trabajo.")
