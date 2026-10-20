"""
=============================================================================
HITO 9: MÓDULO RAG CON CITAS DE FUENTES (LANGCHAIN + CHROMADB + BGE-M3 + GROQ)
Asignatura: Gestión del Conocimiento (2011003) - UNMSM
Proyecto: Enterprise Brain - Etnobotánica y Gastronomía Tsáchila
=============================================================================
Este script implementa el Módulo RAG con Citas exigido en el Hito 9:
  1. Carga la base vectorial ChromaDB indexada con el modelo BAAI/bge-m3.
  2. Recupera los k fragmentos semánticamente más relevantes con sus metadatos
     (nombre de archivo fuente y número de página).
  3. Envía el contexto al LLM exigiendo en el prompt la citación formal:
     "[Fuente: <archivo.pdf>, Pág. <N>]" en cada afirmación factual.
  4. Permite consultas interactivas por consola o pruebas automatizadas de competencia.
=============================================================================
"""

import os
import sys
import json
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from groq import Groq

# ---------------------------------------------------------------------------
# CONFIGURACIÓN Y RUTAS
# ---------------------------------------------------------------------------
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
RUTA_CHROMA_DB = os.path.join(DIRECTORIO_ACTUAL, "chroma_db_tsachila")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
MODELO_LLM = "qwen/qwen3.8-27b"

client_groq = Groq(api_key=GROQ_API_KEY)

# ===========================================================================
# 1. CARGA DEL RETRIEVER VECTORIAL (BGE-M3 + CHROMADB)
# ===========================================================================
def inicializar_sistema_rag():
    if not os.path.exists(RUTA_CHROMA_DB):
        raise FileNotFoundError(
            f"No se encontró la base vectorial en: {RUTA_CHROMA_DB}. "
            "Asegúrate de ejecutar primero '1_LangChain.py' y '2_bge_chroma.py'."
        )

    print("-> Inicializando embeddings BAAI/bge-m3...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    print("-> Conectando con ChromaDB persistente...")
    vectorstore = Chroma(
        persist_directory=RUTA_CHROMA_DB,
        embedding_function=embeddings
    )
    return vectorstore

# ===========================================================================
# 2. PROMPT DE SÍNTESIS CON EXIGENCIA ESTRICTA DE CITAS
# ===========================================================================
PROMPT_SISTEMA_RAG = """
Eres un asistente botánico, antropólogo e investigador académico especializado en el conocimiento tradicional, medicinal y gastronómico del pueblo originario Tsáchila (Ecuador).

Tu función primordial es responder a las consultas de los usuarios con absoluto rigor científico y documental, UTILIZANDO EXCLUSIVAMENTE los fragmentos provistos en el CONTEXTO RECUPERADO.

REGLAS DE ORO PARA LAS CITAS (OBLIGATORIO SEGÚN LA GUÍA DEL CURSO):
1. Cada hecho, afirmación botánica, preparación medicinal, dosis o receta gastronómica DEBE citar obligatoriamente su fuente y página exacta utilizando el formato:
   [Fuente: <nombre_documento>, Pág. <número>]
2. Si un fragmento apoya la afirmación, coloca la cita inmediatamente al final de la oración.
3. Si el contexto recuperado no contiene la información para responder con certeza, declara honestamente: "No se encuentra evidencia documentada en el corpus actual sobre esta consulta específica." No inventes información.
4. Al final de tu respuesta, añade una sección titulada '### Referencias Documentales Consultadas' enumerando las fuentes citadas.
"""

def responder_con_rag_y_citas(vectorstore, pregunta: str, top_k: int = 4) -> dict:
    # 1. Recuperar chunks relevantes
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
    documentos = retriever.invoke(pregunta)

    # 2. Formatear el contexto con metadatos explícitos
    contexto_formateado = []
    fuentes_vistas = []

    for idx, doc in enumerate(documentos, start=1):
        fuente = doc.metadata.get("fuente", "Documento_Desconocido")
        pagina = doc.metadata.get("pagina", "S/P")
        texto_chunk = doc.page_content.strip()

        fuentes_vistas.append({"fuente": fuente, "pagina": pagina})
        bloque = f"--- FRAGMENTO {idx} [Documento: {fuente} | Página: {pagina}] ---\n{texto_chunk}\n"
        contexto_formateado.append(bloque)

    contexto_total = "\n".join(contexto_formateado)

    # 3. Llamada al LLM con Groq
    prompt_usuario = f"""
CONTEXTO RECUPERADO DE LA BASE DE DATOS DOCUMENTAL:
{contexto_total}

PREGUNTA DEL INVESTIGADOR:
{pregunta}

Por favor, elabora tu respuesta siguiendo las reglas de citación estricta [Fuente: ..., Pág. ...].
"""

    response = client_groq.chat.completions.create(
        model=MODELO_LLM,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA_RAG},
            {"role": "user", "content": prompt_usuario}
        ],
        temperature=0.1,
        max_tokens=900
    )

    respuesta_texto = response.choices[0].message.content

    return {
        "pregunta": pregunta,
        "respuesta": respuesta_texto,
        "fuentes": fuentes_vistas,
        "contextos": contexto_formateado
    }

# ===========================================================================
# 3. INTERFAZ DE DEMOSTRACIÓN INTERACTIVA Y EVALUACIÓN
# ===========================================================================
def menu_rag_interactivo():
    print("=" * 75)
    print("   SISTEMA RAG CON CITAS: ETNOBOTÁNICA Y GASTRONOMÍA TSÁCHILA   ")
    print("   HITO 9 - MÓDULO RAG (LangChain + ChromaDB + BGE-M3 + Groq)   ")
    print("=" * 75)

    vectorstore = inicializar_sistema_rag()

    preguntas_competencia = [
        "¿Qué plantas y preparaciones utiliza la comunidad Tsáchila para tratar mordeduras de serpientes y en qué documentos se registra?",
        "¿Cuáles son los usos medicinales y el valor cultural del Achiote (Mú) según el Centro Cultural UNI-SHU?",
        "¿Cómo se prepara tradicionalmente la Chicha de Yuca (Uru Mala) y en qué rituales o festividades se consume?",
        "¿Qué propiedades terapéuticas tiene la Uña de Gato (Uncaria tomentosa) y qué partes de la planta se emplean?",
        "¿Qué rol cumple el Poné (Chamán) en la administración de remedios ancestrales y plantas maestras como el Nepi (Ayahuasca)?"
    ]

    while True:
        print("\nOpciones de Consulta:")
        for idx, p in enumerate(preguntas_competencia, start=1):
            print(f" [{idx}] {p}")
        print(" [P] Escribir una pregunta personalizada")
        print(" [S] Salir")
        print("-" * 75)

        opcion = input("Selecciona una opción: ").strip().upper()

        if opcion == "S":
            print("\nFinalizando módulo RAG con citas. ¡Hasta luego!")
            break
        elif opcion in ["1", "2", "3", "4", "5"]:
            pregunta_sel = preguntas_competencia[int(opcion) - 1]
            print(f"\n[?] Consultando: {pregunta_sel}")
            res = responder_con_rag_y_citas(vectorstore, pregunta_sel)
            print("\n" + "=" * 75)
            print("RESPUESTA GENERADA CON CITAS:")
            print("=" * 75)
            print(res["respuesta"])
            print("=" * 75)
        elif opcion == "P":
            pregunta_user = input("\nIngresa tu pregunta sobre medicina o gastronomía Tsáchila: ").strip()
            if pregunta_user:
                res = responder_con_rag_y_citas(vectorstore, pregunta_user)
                print("\n" + "=" * 75)
                print("RESPUESTA GENERADA CON CITAS:")
                print("=" * 75)
                print(res["respuesta"])
                print("=" * 75)
        else:
            print("Opción inválida. Intente de nuevo.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Modo línea de comando directo
        query = " ".join(sys.argv[1:])
        vs = inicializar_sistema_rag()
        salida = responder_con_rag_y_citas(vs, query)
        print(salida["respuesta"])
    else:
        menu_rag_interactivo()
