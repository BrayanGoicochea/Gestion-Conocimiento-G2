import os
import json
import shutil
import time
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# -------------------------------------------------------------
# RUTAS DE ENTRADA Y SALIDA LOCAL
# -------------------------------------------------------------
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSONL = os.path.join(DIRECTORIO_ACTUAL, "chunks_tsachila.jsonl")
RUTA_CHROMA_DB = os.path.join(DIRECTORIO_ACTUAL, "chroma_db_tsachila")

def cargar_chunks_desde_disco(ruta_archivo):
    """Lee el archivo JSONL de la Parte 1 y reconstruye los Documents de LangChain."""
    documentos = []
    if not os.path.exists(ruta_archivo):
        print(f"[!] Error: No se encuentra el archivo de chunks: {ruta_archivo}")
        return []

    print(f"-> Leyendo fragmentos desde: {ruta_archivo}")
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                item = json.loads(linea)
                doc = Document(
                    page_content=item["texto"],
                    metadata={
                        "fuente": item["fuente"],
                        "pagina": item["pagina"],
                        "id_chunk": item["id_chunk"]
                    }
                )
                documentos.append(doc)

    print(f"-> Total de fragmentos cargados: {len(documentos)}")
    return documentos

def ejecutar_parte2_indexacion():
    print("=" * 70)
    print("   HITO 9 - PARTE 2: EMBEDDINGS (BGE-M3) + INDEXACIÓN EN CHROMADB")
    print("=" * 70)

    # 1. Cargar fragmentos persistidos
    inicio = time.time()
    chunks = cargar_chunks_desde_disco(ARCHIVO_JSONL)
    if not chunks:
        print("[!] Proceso abortado: no hay fragmentos para indexar.")
        return

    # 2. Inicializar BAAI/bge-m3 con LangChain
    print("\n[Paso 1/2] Cargando modelo BAAI/bge-m3...")
    print("           (Si es la primera vez, descargará los pesos a la caché local)")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )

    # Limpiar carpeta anterior si existe para evitar duplicación
    if os.path.exists(RUTA_CHROMA_DB):
        print(f"-> Limpiando base vectorial previa en: {RUTA_CHROMA_DB}")
        shutil.rmtree(RUTA_CHROMA_DB)

    # 3. Indexar en ChromaDB por lotes
    print(f"\n[Paso 2/2] Generando vectores y guardando en ChromaDB...")
    print(f"           Directorio local: {RUTA_CHROMA_DB}")

    TAMANO_LOTE = 300
    total_chunks = len(chunks)
    vectorstore = None

    for i in range(0, total_chunks, TAMANO_LOTE):
        lote = chunks[i : i + TAMANO_LOTE]

        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=lote,
                embedding=embeddings,
                persist_directory=RUTA_CHROMA_DB
            )
        else:
            vectorstore.add_documents(documents=lote)

        procesados = min(i + TAMANO_LOTE, total_chunks)
        porcentaje = (procesados / total_chunks) * 100
        print(f"   * Progreso: {procesados}/{total_chunks} fragmentos indexados ({porcentaje:.1f}%)")

    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print("¡PARTE 2 COMPLETADA EXITOSAMENTE!")
    print(f"Total de fragmentos indexados: {total_chunks}")
    print(f"Tiempo total transcurrido: {duracion / 60:.2f} minutos")
    print(f"Base de datos vectorial persistida en: {RUTA_CHROMA_DB}")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_parte2_indexacion()