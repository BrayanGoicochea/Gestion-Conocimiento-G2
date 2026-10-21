import os
import sys
import time
from functools import lru_cache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# -------------------------------------------------------------
# CONFIGURACIÓN (debe coincidir con la Parte 2)
# -------------------------------------------------------------
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
RUTA_CHROMA_DB = os.path.join(DIRECTORIO_ACTUAL, "chroma_db_tsachila")
NOMBRE_COLECCION = "corpus_tsachila"  # Nombre por defecto que usa Chroma.from_documents en la Parte 2
MODELO_EMBEDDINGS = "BAAI/bge-m3"

# Se piden más candidatos de los necesarios porque el corpus contiene PDFs
# duplicados: así, tras descartar textos repetidos, siguen quedando k fragmentos.
FACTOR_CANDIDATOS = 3


@lru_cache(maxsize=1)
def obtener_vectorstore():
    """Carga BAAI/bge-m3 y abre la base ChromaDB persistida (una sola vez por proceso)."""
    if not os.path.isdir(RUTA_CHROMA_DB):
        raise FileNotFoundError(
            f"No existe la base vectorial en: {RUTA_CHROMA_DB}. Ejecuta primero la Parte 2."
        )

    embeddings = HuggingFaceEmbeddings(
        model_name=MODELO_EMBEDDINGS,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}  # Igual que en la indexación
    )
    return Chroma(
        collection_name=NOMBRE_COLECCION,
        embedding_function=embeddings,
        persist_directory=RUTA_CHROMA_DB
    )


def recuperar_evidencia(query: str, k: int = 4) -> list[dict]:
    """
    Devuelve los k fragmentos más cercanos semánticamente a la consulta.

    Cada elemento: {"texto", "fuente", "pagina", "id_chunk", "score", "distancia"}
      - distancia: distancia L2 al cuadrado que devuelve ChromaDB (menor = más cercano).
      - score: similitud coseno equivalente (1 = idéntico). Como los vectores están
        normalizados, ||a - b||^2 = 2 - 2*cos(a, b)  =>  cos = 1 - distancia / 2.
    """
    query = (query or "").strip()
    if not query or k < 1:
        return []

    vectorstore = obtener_vectorstore()
    candidatos = vectorstore.similarity_search_with_score(query, k=k * FACTOR_CANDIDATOS)

    evidencia = []
    textos_vistos = set()
    for doc, distancia in candidatos:
        clave = " ".join(doc.page_content.split())
        if clave in textos_vistos:
            continue
        textos_vistos.add(clave)

        evidencia.append({
            "texto": doc.page_content,
            "fuente": doc.metadata.get("fuente", "desconocido"),
            "pagina": int(doc.metadata.get("pagina", 0)),
            "id_chunk": int(doc.metadata.get("id_chunk", -1)),
            "score": round(1 - float(distancia) / 2, 4),
            "distancia": round(float(distancia), 4)
        })
        if len(evidencia) == k:
            break

    return evidencia


def imprimir_evidencia(query, evidencia, segundos):
    print("\n" + "-" * 70)
    print(f"Consulta: {query}")
    print(f"Fragmentos recuperados: {len(evidencia)} en {segundos * 1000:.0f} ms")
    print("-" * 70)
    for i, ev in enumerate(evidencia, start=1):
        texto = " ".join(ev["texto"].split())
        print(f"\n[Fragmento {i}] similitud={ev['score']:.3f} | id_chunk={ev['id_chunk']}")
        print(f"   Cita: [Fuente: {ev['fuente']}, Pág. {ev['pagina']}]")
        print(f"   Texto: {texto[:300]}{'...' if len(texto) > 300 else ''}")


def ejecutar_parte3_prueba():
    print("=" * 70)
    print("   HITO 9 - PARTE 3: RECUPERADOR SEMÁNTICO (BGE-M3 + CHROMADB)")
    print("=" * 70)

    print("-> Cargando BAAI/bge-m3 y conectando con ChromaDB...")
    inicio = time.time()
    try:
        vectorstore = obtener_vectorstore()
    except FileNotFoundError as e:
        print(f"[!] {e}")
        return
    print(f"-> Listo en {time.time() - inicio:.1f}s | Vectores en la colección: {vectorstore._collection.count()}")

    # Consulta por argumento:  python 3_recuperador_semantico.py "mi pregunta"
    if len(sys.argv) > 1:
        consulta = " ".join(sys.argv[1:])
        t = time.time()
        evidencia = recuperar_evidencia(consulta)
        imprimir_evidencia(consulta, evidencia, time.time() - t)
        return

    # Modo interactivo
    print("\nEscribe una pregunta (Enter vacío o 'salir' para terminar).")
    print("Ejemplo: ¿Qué planta sirve para la mordedura de serpiente?")
    while True:
        try:
            consulta = input("\nPregunta> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not consulta or consulta.lower() in ("salir", "exit", "q"):
            break
        t = time.time()
        evidencia = recuperar_evidencia(consulta)
        imprimir_evidencia(consulta, evidencia, time.time() - t)

    print("\nFin de la prueba del recuperador.")


if __name__ == "__main__":
    ejecutar_parte3_prueba()
