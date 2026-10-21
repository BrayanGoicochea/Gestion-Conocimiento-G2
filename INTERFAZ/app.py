import os
import sys
import html
import time

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motor_rag as motor  # noqa: E402

st.set_page_config(
    page_title="Saberes Tsáchila · Asistente RAG",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

VISTA_CONSULTA = "💬 Consulta"
VISTA_PLANTAS = "🌿 Catálogo de plantas"
VISTA_INTERNO = "🔬 Cómo funciona"

EJEMPLOS = [
    ("🐍 Mordedura de serpiente", "¿Qué plantas o preparaciones se usan para tratar la mordedura de serpiente?"),
    ("🫁 Tos y gripe", "¿Qué remedios tradicionales se emplean para la tos, la gripe y las afecciones respiratorias?"),
    ("🔴 Usos del achiote", "¿Qué usos medicinales y rituales tiene el achiote (Bixa orellana) entre los Tsáchila?"),
    ("🧙 El poné", "¿Quién es el poné y qué papel tiene en la medicina Tsáchila?"),
]

CATEGORIAS = {
    "🩺 Dolencias": [
        ("🐍 Mordedura de serpiente", "¿Qué plantas o preparaciones se usan para tratar la mordedura de serpiente?"),
        ("🫁 Tos y gripe", "¿Qué remedios tradicionales se emplean para la tos, la gripe y las afecciones respiratorias?"),
        ("🤢 Dolor de estómago", "¿Qué plantas medicinales se utilizan para aliviar los dolores estomacales?"),
        ("🤒 Fiebre", "¿Qué plantas se usan para bajar la fiebre?"),
        ("🩹 Heridas e inflamación", "¿Qué plantas se usan para curar heridas o desinflamar?"),
        ("🪱 Parásitos", "¿Qué plantas se emplean contra los parásitos intestinales?"),
    ],
    "🌱 Plantas": [
        ("🔴 Achiote", "¿Qué usos medicinales y rituales tiene el achiote (Bixa orellana) entre los Tsáchila?"),
        ("🍃 Guayusa", "¿Para qué se usa la guayusa (Ilex guayusa)?"),
        ("🌿 Matico", "¿Qué propiedades medicinales tiene el matico (Piper aduncum)?"),
        ("🧪 Ayahuasca", "¿Cómo se emplea la ayahuasca (Banisteriopsis caapi) en la tradición Tsáchila?"),
        ("🌾 Ortiga brava", "¿Para qué se usa la ortiga brava (Urera baccifera)?"),
        ("🪔 Copal", "¿Qué usos tiene el copal (Dacryodes peruviana)?"),
    ],
    "🏺 Cultura y saber": [
        ("🧙 El poné", "¿Quién es el poné y qué papel tiene en la medicina Tsáchila?"),
        ("🎉 Fiesta Kasama", "¿Qué es la fiesta Kasama y qué importancia cultural tiene?"),
        ("📚 Transmisión del saber", "¿Cómo se transmite el conocimiento de las plantas medicinales entre generaciones?"),
        ("♨️ Baños de vapor", "¿Qué plantas se usan en baños de vapor y para qué sirven?"),
        ("🎨 Pintura ritual", "¿Qué significado tienen el achiote y la pintura corporal en la cultura Tsáchila?"),
        ("⚠️ Pérdida del conocimiento", "¿Qué amenazas existen para la pérdida del conocimiento botánico indígena?"),
    ],
}

# -------------------------------------------------------------
# ESTILOS
# -------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea { font-family: 'Inter', system-ui, sans-serif; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem; padding-bottom: 6rem; max-width: 1180px; }

/* ---------- Cabecera ---------- */
.hero {
    position: relative; overflow: hidden;
    background: radial-gradient(1200px 400px at 90% -20%, rgba(250,204,21,.28), transparent 60%),
                linear-gradient(135deg, #063b2e 0%, #047857 55%, #10b981 100%);
    color: #fff; padding: 2rem 2.2rem; border-radius: 24px; margin-bottom: 1.3rem;
    box-shadow: 0 18px 40px rgba(6, 78, 59, .28);
}
.hero::after { content: "🌿"; position: absolute; right: 1.6rem; bottom: -1.2rem; font-size: 8rem; opacity: .13; transform: rotate(-12deg); }
.hero.compact { padding: 1rem 1.5rem; border-radius: 18px; box-shadow: 0 8px 22px rgba(6, 78, 59, .18); }
.hero.compact::after { display: none; }
.hero.compact h1 { font-size: 1.5rem; margin: 0; }
.hero.compact p { font-size: .9rem; margin-top: .15rem; }
.chip { display: inline-block; background: #f8fffb; border: 1px solid #d1fae5; color: #064e3b; border-radius: 999px;
    padding: .25rem .8rem; font-size: .82rem; margin: 0 .4rem .4rem 0; }
.chip b { font-weight: 700; }
.hero-badge { display: inline-block; background: rgba(255,255,255,.16); border: 1px solid rgba(255,255,255,.35);
    padding: .22rem .8rem; border-radius: 999px; font-size: .76rem; letter-spacing: .06em; font-weight: 600; }
.hero h1 { color: #fff; font-size: 2.25rem; font-weight: 800; letter-spacing: -.02em; margin: .65rem 0 .45rem; line-height: 1.15; }
.hero p { color: #d1fae5; margin: 0; font-size: 1.04rem; max-width: 46rem; }
.stats { display: flex; gap: .8rem; flex-wrap: wrap; margin-top: 1.25rem; }
.stat { background: rgba(255,255,255,.13); border: 1px solid rgba(255,255,255,.25); border-radius: 14px; padding: .55rem 1rem; backdrop-filter: blur(4px); }
.stat b { display: block; font-size: 1.3rem; font-weight: 800; }
.stat span { font-size: .75rem; color: #d1fae5; }

.titulo-seccion { color: #065f46; font-weight: 700; font-size: 1.05rem; margin: 1.1rem 0 .5rem; }
.sub { color: #6b7280; font-size: .88rem; margin-bottom: .6rem; }

/* ---------- Botones (sugerencias) ---------- */
div.stButton > button {
    border-radius: 14px; border: 1px solid #a7f3d0; background: #fff; color: #065f46; font-weight: 600;
    padding: .65rem .9rem; transition: all .18s ease; box-shadow: 0 1px 2px rgba(6,78,59,.06); width: 100%;
    white-space: normal; height: auto; min-height: 3rem; line-height: 1.25;
}
div.stButton > button:hover { background: #059669; color: #fff; border-color: #059669; transform: translateY(-2px); box-shadow: 0 8px 18px rgba(5,150,105,.28); }

/* ---------- Chat ---------- */
[data-testid="stChatMessage"] { background: #fff; border: 1px solid #e5efe9; border-radius: 20px; padding: 1rem 1.2rem; box-shadow: 0 4px 14px rgba(6,78,59,.06); margin-bottom: .9rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: #ecfdf5; border-color: #a7f3d0; }
[data-testid="stChatInput"] { border-radius: 18px; }

/* ---------- Citas ---------- */
.cita { padding: .05rem .4rem; border-radius: 7px; font-size: .8rem; font-weight: 600; white-space: normal; }
.cita-ok { background: #d1fae5; color: #065f46; border: 1px solid #6ee7b7; }
.cita-ko { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

/* ---------- Fuentes ---------- */
.fuentes-titulo { font-weight: 700; color: #065f46; margin: 1rem 0 .5rem; font-size: .95rem; }
.fuentes { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: .6rem; }
.src { display: flex; gap: .7rem; align-items: flex-start; background: #f8fffb; border: 1px solid #d1fae5; border-radius: 14px; padding: .65rem .8rem; }
.src-ico { font-size: 1.4rem; line-height: 1; }
.src-t { font-weight: 600; color: #064e3b; font-size: .86rem; line-height: 1.25; word-break: break-word; }
.src-m { color: #6b7280; font-size: .76rem; margin-top: .2rem; }
.badge { display: inline-block; padding: .02rem .5rem; border-radius: 999px; font-size: .7rem; font-weight: 700; }
.badge-ok { background: #d1fae5; color: #065f46; }
.badge-no { background: #f3f4f6; color: #6b7280; }
.badge-foco { background: #fef3c7; color: #92400e; }

.frag { background: #fff; border: 1px solid #d1fae5; border-left: 4px solid #059669; border-radius: 12px; padding: .8rem 1rem; margin-bottom: .7rem; }
.frag-head { display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .5rem; }
.tag { background: #ecfdf5; color: #065f46; border: 1px solid #a7f3d0; border-radius: 999px; padding: .08rem .6rem; font-size: .74rem; font-weight: 600; }
.tag-pdf { background: #064e3b; color: #fff; border-color: #064e3b; word-break: break-all; }
.frag-text { color: #1f2937; font-size: .88rem; line-height: 1.55; }

/* ---------- Pasos "cómo funciona" ---------- */
.paso { background: #fff; border: 1px solid #d1fae5; border-radius: 18px; padding: 1.1rem 1.2rem; height: 100%; box-shadow: 0 4px 14px rgba(6,78,59,.05); }
.paso .n { display: inline-flex; width: 2rem; height: 2rem; align-items: center; justify-content: center; border-radius: 50%; background: #059669; color: #fff; font-weight: 800; margin-bottom: .5rem; }
.paso h4 { margin: 0 0 .3rem; color: #064e3b; font-size: 1rem; }
.paso p { margin: 0; color: #4b5563; font-size: .88rem; line-height: 1.5; }

/* ---------- Vista interna: gráfico del vector y tabla de candidatos ---------- */
.vector-grafico { display: flex; gap: 2px; height: 130px; background: #f8fffb; border: 1px solid #d1fae5; border-radius: 12px; padding: 6px; margin-bottom: 1rem;
    background-image: linear-gradient(#a7f3d0, #a7f3d0); background-size: calc(100% - 12px) 1px; background-position: 6px 50%; background-repeat: no-repeat; }
.vb { position: relative; flex: 1; }
.vb span { position: absolute; left: 12%; right: 12%; border-radius: 2px; }
.vb span.pos { bottom: 50%; background: #059669; }
.vb span.neg { top: 50%; background: #f59e0b; }
.tabla-wrap { overflow-x: auto; border: 1px solid #d1fae5; border-radius: 12px; margin-bottom: 1rem; }
.tabla { width: 100%; border-collapse: collapse; font-size: .8rem; }
.tabla th { background: #ecfdf5; color: #065f46; text-align: left; padding: .45rem .6rem; white-space: nowrap; }
.tabla td { padding: .4rem .6rem; border-top: 1px solid #ecfdf5; color: #374151; }
.tabla tr.fila-ok td { background: #f0fdf4; font-weight: 600; color: #064e3b; }

.planta-sci { color: #6b7280; font-style: italic; font-size: .85rem; margin-bottom: .3rem; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #ecfdf5 0%, #f6faf8 100%); border-right: 1px solid #d1fae5; }
.aviso { background: #fffbeb; border: 1px solid #fde68a; color: #92400e; border-radius: 14px; padding: .75rem 1rem; font-size: .9rem; margin-bottom: .6rem; }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# RECURSOS
# -------------------------------------------------------------
@st.cache_resource(show_spinner="Cargando el modelo BAAI/bge-m3 y la base vectorial (la primera vez tarda ~1 minuto)...")
def iniciar_motor():
    motor.cargar_recursos()
    return motor.estadisticas()


@st.cache_data(show_spinner=False)
def contar_documentos():
    coleccion, _ = motor.cargar_recursos()
    metas = coleccion.get(include=["metadatas"])["metadatas"]
    return len({m["fuente"] for m in metas})


def obtener_api_key():
    clave = os.environ.get("GROQ_API_KEY", "")
    if not clave:
        try:
            clave = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            clave = ""
    return clave


# -------------------------------------------------------------
# ESTADO
# -------------------------------------------------------------
ss = st.session_state
ss.setdefault("historial", [])
ss.setdefault("vista", VISTA_CONSULTA)
ss.setdefault("categoria", list(CATEGORIAS)[0])
ss.setdefault("foco_sel", "— Ninguna —")


def preguntar(texto, foco=None):
    ss.pregunta_pendiente = texto
    ss.vista = VISTA_CONSULTA
    if foco:
        ss.foco_sel = foco


def limpiar():
    ss.historial = []


# -------------------------------------------------------------
# CARGA DEL MOTOR
# -------------------------------------------------------------
try:
    stats = iniciar_motor()
    n_docs = contar_documentos()
except Exception as e:
    st.error(f"No se pudo iniciar el motor RAG:\n\n{e}")
    st.stop()

catalogo = motor.cargar_catalogo()
nombres_plantas = [p["comun"] for p in catalogo]

# -------------------------------------------------------------
# BARRA LATERAL
# -------------------------------------------------------------
with st.sidebar:
    st.radio("Navegación", [VISTA_CONSULTA, VISTA_PLANTAS, VISTA_INTERNO], key="vista", label_visibility="collapsed")
    st.divider()

    st.button("🗑️ Nueva conversación", on_click=limpiar, width="stretch")

    api_key = obtener_api_key()
    if not api_key:
        api_key = st.text_input("🔑 Groq API Key", type="password",
                                help="Pégala aquí o guárdala en Windows para no repetirlo (ver INSTRUCCIONES.md).")

    with st.expander("⚙️ Opciones avanzadas"):
        k = st.slider("Fragmentos a recuperar", 1, 10, 4, help="Cuántos fragmentos se entregan al LLM como evidencia.")
        st.selectbox("Enfocar en una planta", ["— Ninguna —"] + nombres_plantas, key="foco_sel",
                     help="Si mencionas una planta en la pregunta, se detecta sola.")
        solo_foco = st.checkbox("Buscar solo en sus fichas", value=False, disabled=ss.foco_sel == "— Ninguna —")
        reescribir = st.checkbox("Corregir la pregunta antes de buscar", value=True,
                                 help="Groq reescribe tu pregunta en español claro (corrige faltas y lenguaje coloquial) antes de buscar. Requiere la clave de Groq.")
    st.caption("🔑 Clave de Groq lista" if api_key else "Sin clave de Groq: solo se muestra la evidencia.")
    st.caption("La información es documental y no sustituye la atención médica profesional.")


# -------------------------------------------------------------
# COMPONENTES
# -------------------------------------------------------------
def cabecera(compacta=False):
    st.markdown("""
    <div class="hero compact">
        <h1>🌿 Saberes Tsáchila</h1>
        <p>Medicina ancestral · cada respuesta cita su fuente y página</p>
    </div>""", unsafe_allow_html=True)


def resaltar_citas(respuesta, validas):
    texto = html.escape(respuesta, quote=False)

    def reemplazo(m):
        fuente = html.unescape(m.group(1)).strip()
        ok = (fuente, int(m.group(2))) in validas
        clase = "cita-ok" if ok else "cita-ko"
        titulo = "Cita verificada contra la evidencia recuperada" if ok else "Cita NO encontrada en la evidencia recuperada"
        return f'<span class="cita {clase}" title="{titulo}">{m.group(0).replace("_", "&#95;")}</span>'

    return motor.PATRON_CITA.sub(reemplazo, texto)


def tarjetas_fuentes(msg):
    citadas = {(f.strip(), int(p)) for f, p in motor.PATRON_CITA.findall(msg["content"])}
    vistas, chips = set(), []
    for ev in msg["evidencia"]:
        clave = (ev["fuente"], ev["pagina"])
        if clave in vistas:
            continue
        vistas.add(clave)
        marca = " ✓" if clave in citadas else ""
        chips.append(f'<span class="chip">📄 {html.escape(motor.nombre_legible(ev["fuente"]))} · <b>pág. {ev["pagina"]}</b>{marca}</span>')
    return '<div class="fuentes-titulo">Fuentes</div>' + "".join(chips)


def tarjeta_fragmento(i, ev):
    texto = html.escape(" ".join(ev["texto"].split()))
    return f"""
    <div class="frag"><div class="frag-head">
        <span class="tag">Fragmento {i}</span><span class="tag tag-pdf">📄 {html.escape(ev['fuente'])}</span>
        <span class="tag">Pág. {ev['pagina']}</span><span class="tag">Similitud {ev['score']:.3f}</span>
        <span class="tag">Chunk #{ev['id_chunk']}</span></div>
        <div class="frag-text">{texto}</div></div>"""


def texto_consola(msg):
    t = msg["traza"]
    v = t["vector"]
    L = [f'pregunta> {t["pregunta"]}', ""]
    r = t.get("reescritura")
    if r:
        L += ["[0/5] REESCRITURA DE LA PREGUNTA (corrige ortografía y lenguaje coloquial)",
              f'      modelo       : {r["modelo"] or "—"}  ({r["segundos"]:.1f} s)',
              f'      contexto     : {r.get("contexto") or "(sin pregunta anterior)"}',
              f'      original     : {t["pregunta"]}',
              f'      para buscar  : {t["pregunta_busqueda"]}' + ("" if r["cambio"] else "   (sin cambios)")]
        if not r["modelo"]:
            L.append(f'      no disponible ({r.get("error")}) → se usó la pregunta original')
        L.append("")
    L += ["[1/5] VECTORIZACIÓN DE LA PREGUNTA",
          f'      modelo       : {t["modelo"]} (CPU)',
          f'      dimensiones  : {t["dim"]}      norma L2: {t["norma"]}  (vector normalizado)',
          f'      vector[0:8]  : [{", ".join(f"{x:+.4f}" for x in v[:8])}, ...]',
          f'      tiempo       : {t["t_vectorizar"] * 1000:.0f} ms', ""]
    L += ["[2/5] BÚSQUEDA VECTORIAL EN CHROMADB",
          f'      colección    : {t["coleccion"]}  ({t["total_vectores"]:,} vectores)',
          f'      candidatos   : {len(t["candidatos_globales"])} globales'
          + (f' + {len(t["candidatos_foco"])} de fichas de planta' if t["candidatos_foco"] else ""),
          f'      tiempo       : {t["t_busqueda"] * 1000:.0f} ms',
          "      (similitud = coseno = 1 - distancia²/2, porque los vectores están normalizados)"]
    if t["plantas_foco"]:
        L.append(f'      plantas foco : {", ".join(t["plantas_foco"])}' + ("  [solo sus fichas]" if t["solo_foco"] else ""))
    L.append("")
    L += [f'[3/5] SELECCIÓN DE LOS {t["k"]} MEJORES FRAGMENTOS',
          f'      textos repetidos descartados (PDFs duplicados): {t["descartados_repetidos"]}']
    for i, ev in enumerate(t["finales"], start=1):
        L.append(f'      #{i}  sim={ev["score"]:.3f}  dist={ev["distancia"]:.3f}  chunk={ev["id_chunk"]}  '
                 f'[Fuente: {ev["fuente"]}, Pág. {ev["pagina"]}]')
    L.append("")
    if msg.get("sin_llm"):
        L += ["[4/5] PROMPT → no se envió (no hay API key de Groq)", "[5/5] RESPUESTA → no generada"]
    else:
        L += [f'[4/5] PROMPT ENVIADO AL LLM  ({motor.MODELO_LLM}, temperatura 0.1)',
              f'      {len(t["finales"])} fragmentos + reglas obligatorias de citación',
              f'[5/5] RESPUESTA REDACTADA EN {msg["t_llm"]:.1f} s',
              f'      citas en la respuesta: {msg["total_citas"]}   verificadas contra la evidencia: {msg["verificadas"]}']
    return "\n".join(L)


def mostrar_proceso(msg, idx):
    t = msg["traza"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Vectorizar", f"{t['t_vectorizar'] * 1000:.0f} ms")
    c2.metric("Buscar en ChromaDB", f"{t['t_busqueda'] * 1000:.0f} ms")
    c3.metric("Redactar (Groq)", f"{msg['t_llm']:.1f} s" if not msg.get("sin_llm") else "—")
    c4.metric("Citas verificadas", f"{msg['verificadas']}/{msg['total_citas']}" if not msg.get("sin_llm") else "—")

    st.markdown("**🖥️ Consola del proceso**")
    st.code(texto_consola(msg), language="text")

    st.markdown("**① La pregunta convertida en un vector** — primeras 64 de 1024 dimensiones "
                "(cada barra es un número; arriba positivo, abajo negativo)")
    valores = t["vector"][:64]
    tope = max(abs(x) for x in valores) or 1.0
    barras = "".join(
        f'<div class="vb"><span class="{"pos" if x >= 0 else "neg"}" style="height:{abs(x) / tope * 50:.1f}%"></span></div>'
        for x in valores)
    st.markdown(f'<div class="vector-grafico">{barras}</div>', unsafe_allow_html=True)

    st.markdown("**② Candidatos que devolvió ChromaDB** (ordenados por cercanía)")
    ids_finales = {e["id_chunk"] for e in t["finales"]}
    ids_repetidos = set(t["ids_descartados"])
    filas = []
    for ev in sorted(t["candidatos_globales"] + t["candidatos_foco"], key=lambda e: e["score"], reverse=True):
        elegido = ev["id_chunk"] in ids_finales
        estado = "✅ elegido" if elegido else ("♻️ texto repetido" if ev["id_chunk"] in ids_repetidos else "· fuera del top-k")
        filas.append(f'<tr class="{"fila-ok" if elegido else ""}"><td>{estado}</td><td>{ev["score"]:.3f}</td>'
                     f'<td>{ev["distancia"]:.3f}</td><td>{html.escape(motor.nombre_legible(ev["fuente"]))}</td>'
                     f'<td>{ev["pagina"]}</td><td>{ev["id_chunk"]}</td><td>{ev["origen"]}</td></tr>')
    st.markdown('<div class="tabla-wrap"><table class="tabla"><thead><tr><th>Estado</th><th>Similitud</th><th>Distancia</th>'
                '<th>Documento</th><th>Pág.</th><th>Chunk</th><th>Origen</th></tr></thead><tbody>'
                + "".join(filas) + "</tbody></table></div>", unsafe_allow_html=True)

    if not msg.get("sin_llm"):
        st.markdown("**③ Mensaje que recibió el LLM**")
        with st.expander("Instrucciones del sistema (reglas de citación)"):
            st.code(motor.PROMPT_SISTEMA, language="text")
        st.code(motor.construir_mensaje_usuario(t["pregunta_busqueda"], t["finales"], t["pregunta"]), language="text")


def mostrar_respuesta(msg, idx):
    if msg.get("error"):
        st.error(f"No se pudo redactar la respuesta con Groq: {msg['error']}")
    if msg.get("sin_llm"):
        st.markdown('<div class="aviso">🔑 Sin clave de Groq no se redacta la respuesta; abajo están las fuentes que encontré.</div>',
                    unsafe_allow_html=True)
    elif msg["content"]:
        st.markdown(resaltar_citas(msg["content"], msg["validas"]), unsafe_allow_html=True)
    rees = msg["traza"].get("reescritura")
    if rees and rees["cambio"]:
        st.caption(f'🔎 Entendí tu pregunta como: «{msg["traza"]["pregunta_busqueda"]}»')
    if msg["evidencia"]:
        st.markdown(tarjetas_fuentes(msg), unsafe_allow_html=True)
    else:
        st.info("No se recuperó ningún fragmento para esta consulta.")
    with st.expander("🔎 Ver detalle y consola"):
        pestana_texto, pestana_consola = st.tabs(["📖 Fragmentos", "🖥️ Consola del proceso"])
        with pestana_texto:
            for i, ev in enumerate(msg["evidencia"], start=1):
                st.markdown(tarjeta_fragmento(i, ev), unsafe_allow_html=True)
        with pestana_consola:
            mostrar_proceso(msg, idx)


def procesar(pregunta, k, solo_foco, api_key, reescribir):
    with st.chat_message("assistant", avatar="🌿"):
        with st.spinner("Buscando en el corpus y redactando la respuesta…"):
            consulta, info_reescritura = pregunta, None
            if api_key and reescribir:
                previas = [m["content"] for m in ss.historial[:-1] if m["role"] == "user"]
                consulta, info_reescritura = motor.reescribir_pregunta(pregunta, api_key, contexto=previas[-1] if previas else None)
            plantas = motor.detectar_plantas(f"{pregunta} {consulta}")
            if ss.foco_sel != "— Ninguna —":
                elegida = next(p for p in catalogo if p["comun"] == ss.foco_sel)
                if elegida["comun"] not in [p["comun"] for p in plantas]:
                    plantas.append(elegida)
            evidencia, traza = motor.recuperar(pregunta, k=k, plantas_foco=plantas, solo_foco=solo_foco and bool(plantas),
                                               pregunta_busqueda=consulta, reescritura=info_reescritura)

            msg = {"role": "assistant", "content": "", "evidencia": evidencia, "traza": traza, "validas": set(),
                   "total_citas": 0, "verificadas": 0, "t_llm": 0.0, "sin_llm": False, "error": None}
            if not api_key:
                msg["sin_llm"] = True
            elif not evidencia:
                msg["content"] = motor.MENSAJE_SIN_EVIDENCIA
            else:
                try:
                    t0 = time.time()
                    msg["content"] = motor.redactar_respuesta(consulta, evidencia, api_key, mensaje_original=pregunta) or motor.MENSAJE_SIN_EVIDENCIA
                    msg["t_llm"] = time.time() - t0
                except Exception as e:  # clave inválida, sin red, límite de uso…
                    msg["error"] = str(e)
                    msg["sin_llm"] = True
            if msg["content"]:
                msg["total_citas"], msg["verificadas"], msg["validas"] = motor.auditar_citas(msg["content"], evidencia)
    ss.historial.append(msg)
    st.rerun()


# -------------------------------------------------------------
# VISTA: CONSULTA
# -------------------------------------------------------------
def vista_consulta():
    entrada = st.chat_input("Escribe tu pregunta sobre medicina ancestral Tsáchila…")
    pregunta = entrada or ss.pop("pregunta_pendiente", None)
    if pregunta:
        ss.historial.append({"role": "user", "content": pregunta})

    cabecera(compacta=bool(ss.historial))

    if not ss.historial:
        st.markdown('<div class="titulo-seccion">¿Qué quieres saber?</div>'
                    '<div class="sub">Escribe tu pregunta abajo o prueba con una de estas:</div>', unsafe_allow_html=True)
        cols = st.columns(len(EJEMPLOS))
        for col, (etiqueta, texto) in zip(cols, EJEMPLOS):
            col.button(etiqueta, key=f"ej_{etiqueta}", on_click=preguntar, args=(texto,), help=texto, width="stretch")

    for i, msg in enumerate(ss.historial):
        if msg["role"] == "user":
            with st.chat_message("user", avatar="🧑"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🌿"):
                mostrar_respuesta(msg, i)

    if ss.historial and ss.historial[-1]["role"] == "user":
        procesar(ss.historial[-1]["content"], k, solo_foco, api_key, reescribir)



# -------------------------------------------------------------
# VISTA: CATÁLOGO DE PLANTAS
# -------------------------------------------------------------
def vista_plantas():
    cabecera(compacta=True)
    st.markdown('<div class="titulo-seccion">🌿 Catálogo de plantas del corpus</div>'
                '<div class="sub">Plantas con ficha propia en el corpus. Pulsa una para preguntar sobre ella: la búsqueda se enfoca en sus fichas.</div>',
                unsafe_allow_html=True)
    filtro = st.text_input("Buscar planta", placeholder="Ej.: achiote, Piper, guayusa…", label_visibility="collapsed")
    q = motor.normalizar(filtro)
    visibles = [p for p in catalogo if q in motor.normalizar(p["comun"] + " " + p["cientifico"])]
    st.caption(f"{len(visibles)} de {len(catalogo)} plantas")
    for fila in range(0, len(visibles), 3):
        cols = st.columns(3)
        for col, p in zip(cols, visibles[fila:fila + 3]):
            with col.container(border=True):
                st.markdown(f"#### 🌱 {p['comun']}")
                st.markdown(f'<div class="planta-sci">{html.escape(p["cientifico"])}</div>', unsafe_allow_html=True)
                st.caption(f"📄 {len(p['archivos'])} ficha(s) en el corpus")
                cient = p["cientifico"].replace("…", "")
                st.button("Preguntar sobre esta planta", key=f"pl_{p['comun']}", on_click=preguntar,
                          args=(f"¿Para qué se usa {p['comun']} ({cient}) en la medicina y la cultura Tsáchila?", p["comun"]),
                          width="stretch")


# -------------------------------------------------------------
# VISTA: CÓMO FUNCIONA
# -------------------------------------------------------------
def vista_interno():
    cabecera(compacta=True)
    st.markdown('<div class="titulo-seccion">🔬 ¿Cómo funciona por dentro?</div>'
                '<div class="sub">RAG (Retrieval-Augmented Generation): el modelo no responde de memoria, '
                'primero busca evidencia en el corpus y solo redacta con ella.</div>', unsafe_allow_html=True)
    pasos = [
        ("1", "Preparación del corpus", f"{n_docs} documentos PDF se leen con LangChain y se cortan en <b>{stats['vectores']:,} fragmentos</b> de ~700 caracteres (HITO 9 · script 1)."),
        ("2", "Vectorización", "Cada fragmento se convierte en un vector de <b>1024 números</b> con <b>BAAI/bge-m3</b>. Textos con significado parecido quedan cerca (script 2)."),
        ("3", "Pregunta → vector", "Tu pregunta se convierte en un vector con el mismo modelo y se buscan los fragmentos más cercanos en <b>ChromaDB</b> (script 3)."),
        ("4", "Redacción con citas", "Los mejores fragmentos se envían a <b>Groq</b> con reglas estrictas: responder solo con ellos y citar <i>[Fuente, Pág.]</i> (script 4)."),
        ("5", "Verificación", "Cada cita de la respuesta se compara con los fragmentos recuperados: <span class='cita cita-ok'>verde</span> si existe, <span class='cita cita-ko'>roja</span> si no."),
    ]
    cols = st.columns(5)
    for col, (n, titulo, texto) in zip(cols, pasos):
        col.markdown(f'<div class="paso"><div class="n">{n}</div><h4>{titulo}</h4><p>{texto}</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="titulo-seccion">🖥️ Mira el proceso real de cada pregunta</div>', unsafe_allow_html=True)
    st.info("En la vista **💬 Consulta**, debajo de cada respuesta, abre **«Ver cómo lo resolvió el sistema por dentro»**: "
            "verás la consola con el vector de la pregunta, los candidatos de ChromaDB con su similitud, "
            "los fragmentos elegidos y el prompt exacto que recibió el LLM.")
    st.markdown("**Fórmula de similitud:** los vectores están normalizados, por eso la distancia que entrega ChromaDB cumple "
                "`distancia² = 2 − 2·coseno` y la similitud se calcula como `1 − distancia²/2` (1 = idéntico).")


{VISTA_CONSULTA: vista_consulta, VISTA_PLANTAS: vista_plantas, VISTA_INTERNO: vista_interno}[ss.vista]()
