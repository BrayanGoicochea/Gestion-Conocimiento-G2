import os
import re
import html
import time
import importlib.util
import streamlit as st
from groq import Groq

# -------------------------------------------------------------
# CONFIGURACIÓN GENERAL
# -------------------------------------------------------------
st.set_page_config(
    page_title="RAG Tsáchila · Medicina Ancestral",
    page_icon="🌿",
    layout="wide"
)

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_RECUPERADOR = os.path.join(DIRECTORIO_ACTUAL, "3_recuperador_semantico.py")
MODELO_LLM = "openai/gpt-oss-120b"
MENSAJE_SIN_EVIDENCIA = "Esta información no se encuentra registrada en el corpus documental consultado."

PREGUNTAS_SUGERIDAS = [
    ("🐍 Mordedura de serpiente", "¿Qué plantas o preparaciones se usan para tratar la mordedura de serpiente?"),
    ("🫁 Afecciones respiratorias", "¿Qué remedios tradicionales se emplean para las afecciones respiratorias como la tos o la gripe?"),
    ("🌱 Dolores estomacales", "¿Qué plantas medicinales se utilizan para aliviar los dolores estomacales?"),
    ("🔴 Usos del achiote", "¿Qué usos medicinales y rituales tiene el achiote (Bixa orellana) entre los Tsáchila?"),
]

PROMPT_SISTEMA = f"""Eres un Redactor Académico especializado en etnobotánica y en la medicina ancestral del pueblo Tsáchila (Santo Domingo de los Tsáchilas, Ecuador).

REGLAS OBLIGATORIAS:
1. Responde ÚNICAMENTE con la información contenida en los FRAGMENTOS proporcionados. No uses conocimiento externo ni supongas datos.
2. Cada afirmación, planta, preparación, dosis o dolencia que menciones DEBE ir seguida inmediatamente de su cita con el formato exacto:
   [Fuente: archivo.pdf, Pág. X]
   Copia la cita tal como aparece en la cabecera del fragmento del que proviene la información. Usa una cita por corchete; si una idea proviene de dos fragmentos, escribe dos citas seguidas.
3. Nunca inventes nombres de archivos, números de página, plantas ni preparaciones.
4. Si los fragmentos no contienen la respuesta, responde exactamente: "{MENSAJE_SIN_EVIDENCIA}"
   Si solo la contienen en parte, responde lo que esté respaldado y declara explícitamente qué parte no se encuentra registrada en el corpus.
5. Redacta en español, con tono académico y claro. Usa párrafos breves o viñetas.
6. Si la consulta trata una situación de riesgo para la salud (p. ej., mordedura de serpiente), termina recordando que la información es documental y no sustituye la atención médica profesional."""

# Captura citas del tipo [Fuente: archivo.pdf, Pág. 12]
PATRON_CITA = re.compile(r"\[Fuente:\s*(.+?),\s*P[áa]g\.?\s*(\d+)\s*\]")


# -------------------------------------------------------------
# ESTILOS (temática botánica / esmeralda)
# -------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.hero {
    background: linear-gradient(135deg, #064e3b 0%, #047857 55%, #10b981 100%);
    color: #ffffff; padding: 1.8rem 2rem; border-radius: 18px;
    margin-bottom: 1.2rem; box-shadow: 0 10px 30px rgba(6, 78, 59, 0.25);
}
.hero h1 { color: #ffffff; font-size: 1.85rem; font-weight: 700; margin: 0.5rem 0 0.4rem; line-height: 1.25; }
.hero p { color: #d1fae5; margin: 0; font-size: 1rem; }
.hero-badge {
    display: inline-block; background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.35); padding: 0.2rem 0.75rem;
    border-radius: 999px; font-size: 0.78rem; letter-spacing: 0.03em;
}
.seccion { color: #065f46; font-weight: 600; font-size: 0.9rem; margin: 0.4rem 0 0.3rem; }

.frag {
    background: #ffffff; border: 1px solid #d1fae5; border-left: 4px solid #059669;
    border-radius: 12px; padding: 0.9rem 1rem; margin-bottom: 0.8rem;
}
.frag-head { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.55rem; }
.tag {
    background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0;
    border-radius: 999px; padding: 0.1rem 0.6rem; font-size: 0.76rem; font-weight: 600;
}
.tag-pdf { background: #064e3b; color: #ffffff; border-color: #064e3b; word-break: break-all; }
.frag-text { color: #1f2937; font-size: 0.9rem; line-height: 1.55; }

.cita { padding: 0.05rem 0.4rem; border-radius: 6px; font-size: 0.82rem; font-weight: 600; white-space: normal; }
.cita-ok { background: #d1fae5; color: #065f46; }
.cita-ko { background: #fee2e2; color: #991b1b; }

section[data-testid="stSidebar"] { background: #ecfdf5; }
div.stButton > button {
    border-radius: 999px; border: 1px solid #6ee7b7; background: #ffffff; color: #065f46; font-weight: 500;
}
div.stButton > button:hover { background: #059669; color: #ffffff; border-color: #059669; }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# RECURSOS (se cargan una sola vez por sesión del servidor)
# -------------------------------------------------------------
@st.cache_resource(show_spinner="Cargando BAAI/bge-m3 y la base vectorial ChromaDB...")
def cargar_recuperador():
    # El nombre del archivo empieza por un dígito, así que no admite "import" normal
    spec = importlib.util.spec_from_file_location("recuperador_semantico", RUTA_RECUPERADOR)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    modulo.obtener_vectorstore()  # Precarga del modelo y de la colección
    return modulo.recuperar_evidencia


def obtener_api_key():
    clave = os.environ.get("GROQ_API_KEY", "")
    if not clave:
        try:
            clave = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            clave = ""
    return clave


# -------------------------------------------------------------
# REDACTOR ACADÉMICO (Groq)
# -------------------------------------------------------------
def formato_cita(ev):
    return f"[Fuente: {ev['fuente']}, Pág. {ev['pagina']}]"


def construir_contexto(evidencia):
    bloques = []
    for i, ev in enumerate(evidencia, start=1):
        texto = " ".join(ev["texto"].split())
        bloques.append(f"[Fragmento {i}] Cita obligatoria: {formato_cita(ev)}\n{texto}")
    return "\n\n---\n\n".join(bloques)


def redactar_respuesta(pregunta, evidencia, api_key):
    cliente = Groq(api_key=api_key)
    mensaje_usuario = (
        f"FRAGMENTOS RECUPERADOS DEL CORPUS:\n\n{construir_contexto(evidencia)}\n\n"
        f"PREGUNTA DEL USUARIO: {pregunta}"
    )
    respuesta = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": mensaje_usuario}
        ],
        temperature=0.1,
        max_completion_tokens=4096  # gpt-oss razona antes de responder; deja margen
    )
    return (respuesta.choices[0].message.content or "").strip()


def auditar_citas(respuesta, evidencia):
    """Compara cada cita de la respuesta con las fuentes realmente recuperadas."""
    validas = {(ev["fuente"].strip(), int(ev["pagina"])) for ev in evidencia}
    citas = [(f.strip(), int(p)) for f, p in PATRON_CITA.findall(respuesta)]
    verificadas = sum(1 for c in citas if c in validas)
    return len(citas), verificadas, validas


def resaltar_citas(respuesta, validas):
    """Escapa el HTML de la respuesta y pinta cada cita en verde (verificada) o rojo (no verificada)."""
    texto = html.escape(respuesta, quote=False)

    def reemplazo(m):
        fuente_original = html.unescape(m.group(1)).strip()
        ok = (fuente_original, int(m.group(2))) in validas
        clase = "cita-ok" if ok else "cita-ko"
        titulo = "Cita verificada contra la evidencia recuperada" if ok else "Cita NO encontrada en la evidencia recuperada"
        contenido = m.group(0).replace("_", "&#95;")  # Evita que Markdown convierta "_" en cursiva
        return f'<span class="cita {clase}" title="{titulo}">{contenido}</span>'

    return PATRON_CITA.sub(reemplazo, texto)


# -------------------------------------------------------------
# COMPONENTES VISUALES
# -------------------------------------------------------------
def tarjeta_fragmento(i, ev):
    texto = html.escape(" ".join(ev["texto"].split()))
    return f"""
    <div class="frag">
        <div class="frag-head">
            <span class="tag">Fragmento {i}</span>
            <span class="tag tag-pdf">📄 {html.escape(ev['fuente'])}</span>
            <span class="tag">Pág. {ev['pagina']}</span>
            <span class="tag">Similitud {ev['score']:.3f}</span>
            <span class="tag">Chunk #{ev['id_chunk']}</span>
        </div>
        <div class="frag-text">{texto}</div>
    </div>
    """


def mostrar_respuesta(msg):
    st.markdown(resaltar_citas(msg["content"], msg["validas"]), unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Citas verificadas", f"{msg['verificadas']}/{msg['total_citas']}")
    col2.metric("Recuperación", f"{msg['t_recuperacion'] * 1000:.0f} ms")
    col3.metric("Redacción (Groq)", f"{msg['t_llm']:.1f} s")

    with st.expander(f"📚 Fuentes y Fragmentos Recuperados (Evidencia Documental) · {len(msg['evidencia'])}"):
        if not msg["evidencia"]:
            st.info("No se recuperó ningún fragmento para esta consulta.")
        for i, ev in enumerate(msg["evidencia"], start=1):
            st.markdown(tarjeta_fragmento(i, ev), unsafe_allow_html=True)


def elegir_sugerencia(pregunta):
    st.session_state.pregunta_sugerida = pregunta


# -------------------------------------------------------------
# ESTADO DE LA SESIÓN
# -------------------------------------------------------------
if "historial" not in st.session_state:
    st.session_state.historial = []


# -------------------------------------------------------------
# BARRA LATERAL
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🌿 Panel de control")

    api_key = obtener_api_key()
    if api_key:
        st.success("GROQ_API_KEY detectada")
    else:
        api_key = st.text_input("Groq API Key", type="password", help="O define la variable de entorno GROQ_API_KEY")

    k = st.slider("Fragmentos a recuperar (k)", min_value=1, max_value=10, value=4,
                  help="Número de fragmentos que se entregan al LLM como evidencia")

    if st.button("🗑️ Limpiar historial"):
        st.session_state.historial = []
        st.rerun()

    st.divider()
    st.markdown(f"""
**Arquitectura**
- Embeddings: `BAAI/bge-m3` (CPU)
- Vector DB: `ChromaDB` local
- LLM: `{MODELO_LLM}` (Groq)

**Leyenda de citas**
<span class="cita cita-ok">verificada</span> &nbsp; <span class="cita cita-ko">no verificada</span>
""", unsafe_allow_html=True)
    st.caption("La información es documental y no sustituye la atención médica profesional.")


# -------------------------------------------------------------
# CABECERA Y SUGERENCIAS
# -------------------------------------------------------------
st.markdown("""
<div class="hero">
    <span class="hero-badge">HITO 9 · RAG CON CITAS</span>
    <h1>Sistema RAG Tsáchila - Medicina Ancestral con Citas Verificables</h1>
    <p>Respuestas generadas exclusivamente a partir del corpus documental, con fuente y página en cada afirmación.</p>
</div>
""", unsafe_allow_html=True)

try:
    recuperar_evidencia = cargar_recuperador()
except Exception as e:
    st.error(f"No se pudo cargar el recuperador semántico: {e}")
    st.stop()

st.markdown('<div class="seccion">Preguntas sugeridas</div>', unsafe_allow_html=True)
columnas = st.columns(len(PREGUNTAS_SUGERIDAS))
for col, (etiqueta, pregunta) in zip(columnas, PREGUNTAS_SUGERIDAS):
    col.button(etiqueta, key=f"sug_{etiqueta}", on_click=elegir_sugerencia, args=(pregunta,))


# -------------------------------------------------------------
# HISTORIAL
# -------------------------------------------------------------
for msg in st.session_state.historial:
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🌿"):
        if msg["role"] == "user":
            st.markdown(msg["content"])
        else:
            mostrar_respuesta(msg)


# -------------------------------------------------------------
# NUEVA CONSULTA
# -------------------------------------------------------------
pregunta_chat = st.chat_input("Escribe tu pregunta sobre medicina ancestral Tsáchila...")
pregunta = pregunta_chat or st.session_state.pop("pregunta_sugerida", None)

if pregunta:
    st.session_state.historial.append({"role": "user", "content": pregunta})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(pregunta)

    with st.chat_message("assistant", avatar="🌿"):
        if not api_key:
            st.warning("Ingresa tu Groq API Key en la barra lateral para generar la respuesta.")
            st.session_state.historial.pop()
            st.stop()

        with st.spinner("Buscando evidencia en el corpus..."):
            t0 = time.time()
            evidencia = recuperar_evidencia(pregunta, k=k)
            t_recuperacion = time.time() - t0

        t_llm = 0.0
        if not evidencia:
            respuesta = MENSAJE_SIN_EVIDENCIA
        else:
            with st.spinner("Redactando respuesta con citas..."):
                try:
                    t0 = time.time()
                    respuesta = redactar_respuesta(pregunta, evidencia, api_key) or MENSAJE_SIN_EVIDENCIA
                    t_llm = time.time() - t0
                except Exception as e:
                    st.error(f"Error al consultar Groq: {e}")
                    st.session_state.historial.pop()
                    st.stop()

        total_citas, verificadas, validas = auditar_citas(respuesta, evidencia)
        msg = {
            "role": "assistant",
            "content": respuesta,
            "evidencia": evidencia,
            "validas": validas,
            "total_citas": total_citas,
            "verificadas": verificadas,
            "t_recuperacion": t_recuperacion,
            "t_llm": t_llm
        }
        st.session_state.historial.append(msg)
        mostrar_respuesta(msg)
