"""
Motor RAG de la interfaz (solo lectura sobre la base creada en HITO 9).

Hace lo mismo que HITO 9 / 3_recuperador_semantico.py y 4_interfaz_rag.py, pero devuelve además
una "traza" con cada paso interno (vector de la pregunta, candidatos de ChromaDB, filtrado,
prompt enviado al LLM) para poder mostrarlo en la interfaz.
"""
import os
import re
import json
import math
import time
import unicodedata
from functools import lru_cache

RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_DB = os.path.abspath(os.path.join(RAIZ, "..", "HITO 9", "chroma_db_tsachila"))
RUTA_CATALOGO = os.path.join(RAIZ, "catalogo_plantas.json")

MODELO_EMBEDDINGS = "BAAI/bge-m3"
MODELO_LLM = "openai/gpt-oss-120b"
FACTOR_CANDIDATOS = 3  # se piden k*3 candidatos para poder descartar textos repetidos (PDFs duplicados)
MENSAJE_SIN_EVIDENCIA = "Esta información no se encuentra registrada en el corpus documental consultado."

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
6. Si la consulta trata una situación de riesgo para la salud (p. ej., mordedura de serpiente), termina recordando que la información es documental y no sustituye la atención médica profesional.
7. Si el MENSAJE ORIGINAL DEL USUARIO pide un formato o extensión (p. ej. "más resumido", "en una frase", "con viñetas", "explícalo fácil"), aplícalo a la respuesta a la PREGUNTA, manteniendo las citas obligatorias."""

MODELO_REESCRITURA = "llama-3.1-8b-instant"  # rápido; si no está disponible se usa MODELO_LLM
PROMPT_REESCRITURA = """Reescribe la consulta del usuario como UNA pregunta clara, bien escrita y en español, para buscarla en documentos sobre plantas medicinales y cultura del pueblo Tsáchila.
- Corrige la ortografía y las expresiones coloquiales o abreviadas (por ejemplo "toz" es "tos", "q" es "que").
- Si habla en primera persona ("tengo tos, qué puedo tomar"), conviértela en una pregunta general ("¿Qué plantas o remedios se usan para la tos?").
- Mantén los nombres de plantas, lugares y personas tal como aparecen.
- No respondas la pregunta ni agregues datos que no estén en la consulta.
- Recibirás el CONTEXTO (la pregunta anterior de la conversación, si existe) y el MENSAJE NUEVO. Si el mensaje nuevo es un seguimiento que depende del contexto
  ("más resumido", "explícalo mejor", "¿y para los niños?", "cuéntame más"), escribe una pregunta autónoma sobre el MISMO TEMA del contexto.
  El estilo pedido (resumido, corto, con viñetas…) NO forma parte de la pregunta: omítelo.
- Nunca pidas aclaraciones ni expliques lo que haces. Si el mensaje no se puede mejorar, devuélvelo tal cual.
- Devuelve SOLO la pregunta, en una sola línea."""
PATRON_META = re.compile(r"(reescrib|proporcion\w+ (la|una) consulta|no (puedo|tengo)|lo siento|como (un )?(modelo|asistente)|aclaraci)", re.I)

PATRON_CITA = re.compile(r"\[Fuente:\s*(.+?),\s*P[áa]g\.?\s*(\d+)\s*\]")


# -------------------------------------------------------------
# Utilidades de texto y catálogo de plantas
# -------------------------------------------------------------
def normalizar(texto):
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def nombre_legible(fuente):
    """'Achiote_Bixa_orellana_W4252131145.pdf' -> 'Achiote Bixa orellana'."""
    base = re.sub(r"\.pdf$", "", fuente, flags=re.I)
    base = re.sub(r"_W\d+$", "", base)
    return base.replace("_", " ").strip()


@lru_cache(maxsize=1)
def cargar_catalogo():
    with open(RUTA_CATALOGO, encoding="utf-8") as f:
        return json.load(f)


def detectar_plantas(pregunta):
    """Plantas del catálogo mencionadas en la pregunta (por nombre común, científico o género)."""
    q = " " + normalizar(pregunta) + " "
    coincidencias = []
    for planta in cargar_catalogo():
        nombres = {normalizar(planta["comun"])}
        cientifico = normalizar(planta["cientifico"]).replace("…", "").replace("(", " ").replace(")", " ")
        palabras = cientifico.split()
        if len(palabras) >= 2:
            nombres.add(" ".join(palabras[:2]))
        if palabras and len(palabras[0]) > 4:
            nombres.add(palabras[0])
        for n in nombres:
            if n and re.search(rf"(?<![a-z]){re.escape(n)}(?![a-z])", q):
                coincidencias.append((planta, n))
                break
    # Si "palma" y "palma real" aparecen, solo vale la más específica
    return [p for p, n in coincidencias
            if not any(n != m and n in m for _, m in coincidencias)]


# -------------------------------------------------------------
# Carga de recursos (una vez por proceso)
# -------------------------------------------------------------
@lru_cache(maxsize=1)
def cargar_recursos():
    if not RUTA_DB.isascii():
        raise RuntimeError(
            f"La ruta de la base vectorial contiene tildes o caracteres especiales:\n{RUTA_DB}\n"
            "ChromaDB no puede abrir su índice en rutas así (Windows). Mueve el proyecto a una ruta "
            "sin tildes, por ejemplo C:\\Proyecto avance GESTION DE CONOCIMIENTO."
        )
    if not os.path.isdir(RUTA_DB):
        raise FileNotFoundError(f"No existe la base vectorial en: {RUTA_DB}. Ejecuta primero HITO 9 / 2_bge_chroma.py.")

    import chromadb
    from langchain_huggingface import HuggingFaceEmbeddings

    cliente = chromadb.PersistentClient(path=RUTA_DB)
    # Se usa la colección con más vectores (según el script que la creó puede llamarse distinto)
    coleccion = max(cliente.list_collections(), key=lambda c: c.count())
    embeddings = HuggingFaceEmbeddings(
        model_name=MODELO_EMBEDDINGS,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    return coleccion, embeddings


def estadisticas():
    coleccion, _ = cargar_recursos()
    return {"vectores": coleccion.count(), "coleccion": coleccion.name}


# -------------------------------------------------------------
# Reescritura de la pregunta (corrige ortografía y lenguaje coloquiales antes de buscar)
# -------------------------------------------------------------
def reescribir_pregunta(pregunta, api_key, cliente=None, contexto=None):
    """
    Devuelve (pregunta_para_buscar, info). Si algo falla, devuelve la pregunta original,
    de modo que la reescritura nunca impide responder.
      contexto: pregunta anterior de la conversación (para entender seguimientos como "más resumido")
    """
    info = {"modelo": None, "segundos": 0.0, "cambio": False, "error": None, "contexto": contexto}
    if cliente is None:
        from groq import Groq
        cliente = Groq(api_key=api_key)
    mensaje = f"CONTEXTO (pregunta anterior): {contexto or '(ninguno)'}\n\nMENSAJE NUEVO: {pregunta}"
    t0 = time.time()
    for modelo in (MODELO_REESCRITURA, MODELO_LLM):
        try:
            extra = {"reasoning_effort": "low"} if modelo == MODELO_LLM else {}
            r = cliente.chat.completions.create(
                model=modelo,
                messages=[{"role": "system", "content": PROMPT_REESCRITURA},
                          {"role": "user", "content": mensaje}],
                temperature=0, max_completion_tokens=400, **extra)
            texto = " ".join((r.choices[0].message.content or "").split()).strip(' "«»')
            if texto and PATRON_META.search(texto):
                info["error"] = f"descartada (no parece una pregunta): {texto[:80]}"
                continue
            if texto and len(texto) <= 300:
                info.update(modelo=modelo, segundos=time.time() - t0, cambio=texto != pregunta.strip(), error=None)
                return texto, info
            info["error"] = "respuesta vacía o demasiado larga"
        except Exception as e:  # modelo no disponible, sin red, límite de uso…
            info["error"] = str(e)[:160]
    info["segundos"] = time.time() - t0
    return pregunta, info


# -------------------------------------------------------------
# Recuperación
# -------------------------------------------------------------
def _consultar(coleccion, vector, n, fuentes=None):
    consulta = dict(query_embeddings=[vector], n_results=max(1, n),
                    include=["documents", "metadatas", "distances"])
    if fuentes:
        consulta["where"] = {"fuente": {"$in": list(fuentes)}}
    r = coleccion.query(**consulta)
    salida = []
    for doc, meta, dist in zip(r["documents"][0], r["metadatas"][0], r["distances"][0]):
        salida.append({
            "texto": doc,
            "fuente": meta.get("fuente", "desconocido"),
            "pagina": int(meta.get("pagina", 0)),
            "id_chunk": int(meta.get("id_chunk", -1)),
            "distancia": round(float(dist), 4),
            # Vectores normalizados: ||a-b||^2 = 2 - 2cos(a,b)  =>  cos = 1 - distancia/2
            "score": round(1 - float(dist) / 2, 4),
        })
    return salida


def recuperar(pregunta, k=4, plantas_foco=None, solo_foco=False, pregunta_busqueda=None, reescritura=None):
    """
    Devuelve (evidencia, traza).
      plantas_foco     : plantas del catálogo a priorizar (detectadas en la pregunta o elegidas en la barra lateral)
      solo_foco        : si es True, solo se busca dentro de las fichas de esas plantas
      pregunta_busqueda: versión reescrita de la pregunta; si se da, es la que se vectoriza y busca
      reescritura      : info devuelta por reescribir_pregunta (solo para mostrar en la traza)
    """
    coleccion, embeddings = cargar_recursos()
    consulta = pregunta_busqueda or pregunta
    traza = {"pregunta": pregunta, "pregunta_busqueda": consulta, "reescritura": reescritura,
             "k": k, "coleccion": coleccion.name, "total_vectores": coleccion.count(),
             "modelo": MODELO_EMBEDDINGS, "plantas_foco": [p["comun"] for p in (plantas_foco or [])],
             "solo_foco": solo_foco}

    # 1) Vectorizar la pregunta
    t0 = time.time()
    vector = embeddings.embed_query(consulta)
    traza["t_vectorizar"] = time.time() - t0
    traza["dim"] = len(vector)
    traza["norma"] = round(math.sqrt(sum(x * x for x in vector)), 4)
    traza["vector"] = [float(x) for x in vector]

    # 2) Búsqueda en ChromaDB
    t0 = time.time()
    fuentes_foco = sorted({a for p in (plantas_foco or []) for a in p["archivos"]})
    if solo_foco and fuentes_foco:
        candidatos = _consultar(coleccion, vector, k * FACTOR_CANDIDATOS, fuentes_foco)
        for ev in candidatos:
            ev["origen"] = "ficha de la planta"
        candidatos_foco = []
    else:
        candidatos = _consultar(coleccion, vector, k * FACTOR_CANDIDATOS)
        for ev in candidatos:
            ev["origen"] = "búsqueda global"
        # Una búsqueda por planta, intercaladas, para que ninguna se quede sin lugar
        por_planta = [_consultar(coleccion, vector, k * 2, p["archivos"]) for p in (plantas_foco or [])]
        candidatos_foco = []
        for ronda in zip(*por_planta) if por_planta else []:
            candidatos_foco.extend(ronda)
        for ev in candidatos_foco:
            ev["origen"] = "ficha de la planta"
    traza["t_busqueda"] = time.time() - t0
    traza["candidatos_globales"] = candidatos
    traza["candidatos_foco"] = candidatos_foco
    traza["fuentes_foco"] = fuentes_foco

    # 3) Selección: descartar textos repetidos y, si hay planta, reservar la mitad de los lugares a su ficha
    vistos, finales, descartados = set(), [], []

    def agregar(ev):
        clave = " ".join(ev["texto"].split())
        if clave in vistos:
            descartados.append(ev)
            return
        vistos.add(clave)
        finales.append(ev)

    reservados = max(math.ceil(k / 2), len(plantas_foco or [])) if candidatos_foco else 0
    reservados = min(reservados, k)
    for ev in candidatos_foco:
        if len(finales) >= reservados:
            break
        agregar(ev)
    resto = sorted(candidatos + candidatos_foco, key=lambda e: e["score"], reverse=True)
    for ev in resto:
        if len(finales) >= k:
            break
        clave = " ".join(ev["texto"].split())
        if clave not in vistos:
            agregar(ev)
        elif ev not in descartados:
            descartados.append(ev)
    finales.sort(key=lambda e: e["score"], reverse=True)
    traza["descartados_repetidos"] = len(descartados)
    traza["ids_descartados"] = sorted({e["id_chunk"] for e in descartados})
    traza["finales"] = finales
    return finales, traza


# -------------------------------------------------------------
# Redacción con el LLM (Groq)
# -------------------------------------------------------------
def formato_cita(ev):
    return f"[Fuente: {ev['fuente']}, Pág. {ev['pagina']}]"


def construir_contexto(evidencia):
    bloques = []
    for i, ev in enumerate(evidencia, start=1):
        texto = " ".join(ev["texto"].split())
        bloques.append(f"[Fragmento {i}] Cita obligatoria: {formato_cita(ev)}\n{texto}")
    return "\n\n---\n\n".join(bloques)


def construir_mensaje_usuario(pregunta, evidencia, mensaje_original=None):
    texto = f"FRAGMENTOS RECUPERADOS DEL CORPUS:\n\n{construir_contexto(evidencia)}\n\nPREGUNTA: {pregunta}"
    if mensaje_original and mensaje_original.strip() != pregunta.strip():
        texto += f"\n\nMENSAJE ORIGINAL DEL USUARIO: {mensaje_original}"
    return texto


def redactar_respuesta(pregunta, evidencia, api_key, cliente=None, mensaje_original=None):
    if cliente is None:
        from groq import Groq
        cliente = Groq(api_key=api_key)
    respuesta = cliente.chat.completions.create(
        model=MODELO_LLM,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": construir_mensaje_usuario(pregunta, evidencia, mensaje_original)},
        ],
        temperature=0.1,
        max_completion_tokens=4096,  # gpt-oss razona antes de responder; deja margen
    )
    return (respuesta.choices[0].message.content or "").strip()


def auditar_citas(respuesta, evidencia):
    """Compara cada cita de la respuesta con las fuentes realmente recuperadas."""
    validas = {(ev["fuente"].strip(), int(ev["pagina"])) for ev in evidencia}
    citas = [(f.strip(), int(p)) for f, p in PATRON_CITA.findall(respuesta)]
    verificadas = sum(1 for c in citas if c in validas)
    return len(citas), verificadas, validas
