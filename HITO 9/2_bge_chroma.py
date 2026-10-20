import os
import json
import shutil
import time
import torch
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# -------------------------------------------------------------
# 1. OPTIMIZACIÓN DE RECURSOS DE CPU
# -------------------------------------------------------------
# Usar todos los hilos del procesador disponibles para operaciones de tensores
num_cores = os.cpu_count() or 4
torch.set_num_threads(num_cores)
os.environ["OMP_NUM_THREADS"] = str(num_cores)
os.environ["MKL_NUM_THREADS"] = str(num_cores)

# Rutas
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_JSONL = os.path.join(DIRECTORIO_ACTUAL, "chunks_tsachila.jsonl")
RUTA_CHROMA_DB = os.path.join(DIRECTORIO_ACTUAL, "chroma_db_tsachila")

def cargar_chunks_desde_disco(ruta_archivo):
    documentos = []
    if not os.path.exists(ruta_archivo):
        print(f"[!] Error: No se encuentra el archivo de chunks: {ruta_archivo}")
        return []

    print(f"-> Cargando fragmentos desde: {ruta_archivo}")
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
    print(f"-> Total cargados: {len(documentos)} chunks.")
    return documentos

def ejecutar_parte2_optimizada():
    print("=" * 70)
    print(f"   HITO 9: INDEXACIÓN ACELERADA EN CPU ({num_cores} HILOS PARALELOS)")
    print("=" * 70)

    inicio = time.time()
    chunks = cargar_chunks_desde_disco(ARCHIVO_JSONL)
    if not chunks:
        return

    # Limpiar base previa para indexar desde cero sin colisiones
    if os.path.exists(RUTA_CHROMA_DB):
        print(f"-> Limpiando directorio previo en: {RUTA_CHROMA_DB}")
        shutil.rmtree(RUTA_CHROMA_DB)

    print("\n[Paso 1/2] Cargando BAAI/bge-m3 desde caché...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 64  # Procesa más fragmentos por ciclo matricial sin saturar RAM
        }
    )

    print(f"\n[Paso 2/2] Generando vectores e indexando en lotes...")
    TAMANO_LOTE = 600  # Reduce la sobrecarga de escritura en disco
    total_chunks = len(chunks)
    vectorstore = None

    for i in range(0, total_chunks, TAMANO_LOTE):
        tiempo_lote = time.time()
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
        segundos_lote = time.time() - tiempo_lote
        print(f"   * Progreso: {procesados}/{total_chunks} ({porcentaje:.1f}%) - Lote en {segundos_lote:.1f}s")

    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print("¡INDEXACIÓN FINALIZADA!")
    print(f"Total vectores calculados: {total_chunks}")
    print(f"Tiempo total: {duracion / 60:.2f} minutos")
    print(f"Directorio local: {RUTA_CHROMA_DB}")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_parte2_optimizada()