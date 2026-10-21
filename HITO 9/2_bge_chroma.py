import os
import json
import shutil
import time
import torch
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# -------------------------------------------------------------
# 1. MAXIMIZAR RENDIMIENTO EN CPU MULTI-CORE (32 GB RAM)
# -------------------------------------------------------------
num_cores = os.cpu_count() or 8
torch.set_num_threads(num_cores)
torch.set_num_interop_threads(2)
os.environ["OMP_NUM_THREADS"] = str(num_cores)
os.environ["MKL_NUM_THREADS"] = str(num_cores)

# Rutas del entorno local
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSONL = os.path.join(DIRECTORIO_ACTUAL, "chunks_tsachila.jsonl")
RUTA_CHROMA_DB = os.path.join(DIRECTORIO_ACTUAL, "chroma_db_tsachila")


### Convierte cada línea de texto del JSON en un objeto Document de LangChain. 
# Dentro del diccionario metadata, guarda "id_chunk" 
# (que es el ID numérico: 1, 2, 3... 18338) junto a la fuente y la página.

def cargar_chunks_desde_disco(ruta_archivo):
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
    print(f"-> Total cargados: {len(documentos)} chunks en memoria RAM.")
    return documentos

def ejecutar_parte2_alta_potencia():
    print("=" * 70)
    print(f"   HITO 9: INDEXACIÓN ACELERADA (32GB RAM - {num_cores} CORES)")
    print("=" * 70)

    inicio = time.time()
    chunks = cargar_chunks_desde_disco(ARCHIVO_JSONL)
    if not chunks:
        return

    # Limpiar base previa para indexar desde cero
    if os.path.exists(RUTA_CHROMA_DB):
        print(f"-> Limpiando directorio previo en: {RUTA_CHROMA_DB}")
        shutil.rmtree(RUTA_CHROMA_DB)

    print("\n[Paso 1/2] Inicializando BAAI/bge-m3 optimizado...")
    
    # Se eliminó 'show_progress_bar' para evitar duplicidad de argumento
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 128
        }
    )

    print(f"\n[Paso 2/2] Indexando en ChromaDB con lotes extendidos...")
    TAMANO_LOTE = 1200
    total_chunks = len(chunks)
    
    # Inicialización de la colección persistente en disco
    vectorstore = Chroma(
        collection_name="corpus_tsachila",
        embedding_function=embeddings,
        persist_directory=RUTA_CHROMA_DB
    )

    for i in range(0, total_chunks, TAMANO_LOTE):
        tiempo_lote = time.time()
        lote = chunks[i : i + TAMANO_LOTE]

        vectorstore.add_documents(documents=lote) # acaespecificamente se hace el embedding

        procesados = min(i + TAMANO_LOTE, total_chunks)
        porcentaje = (procesados / total_chunks) * 100
        segundos_lote = time.time() - tiempo_lote
        print(f"   * Progreso: {procesados}/{total_chunks} ({porcentaje:.1f}%) | Lote en {segundos_lote:.1f}s")

    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print("¡INDEXACIÓN COMPLETADA EXITOSAMENTE!")
    print(f"Total vectores generados: {total_chunks}")
    print(f"Tiempo total: {duracion / 60:.2f} minutos")
    print(f"Ubicación de ChromaDB: {RUTA_CHROMA_DB}")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_parte2_alta_potencia()