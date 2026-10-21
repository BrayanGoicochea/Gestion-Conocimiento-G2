import os
import json
import shutil
import sys
import time
import numpy as np
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
# Vectores ya calculados, un archivo .npy por lote (permite reanudar tras una interrupción)
RUTA_LOTES = os.path.join(DIRECTORIO_ACTUAL, "vectores_lotes")

TAMANO_LOTE = 600
TAMANO_ESCRITURA_CHROMA = 2000

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

def ruta_lote(i):
    return os.path.join(RUTA_LOTES, f"lote_{i:06d}.npy")

def ejecutar_parte2_optimizada():
    print("=" * 70)
    print(f"   HITO 9: INDEXACIÓN ACELERADA EN CPU ({num_cores} HILOS PARALELOS)")
    print("=" * 70)

    inicio = time.time()
    chunks = cargar_chunks_desde_disco(ARCHIVO_JSONL)
    if not chunks:
        return
    total_chunks = len(chunks)

    # Con --reiniciar se descarta todo lo calculado; sin él se reanuda
    if "--reiniciar" in sys.argv:
        for ruta in (RUTA_LOTES, RUTA_CHROMA_DB):
            if os.path.exists(ruta):
                print(f"-> Limpiando: {ruta}")
                shutil.rmtree(ruta)
    os.makedirs(RUTA_LOTES, exist_ok=True)

    print("\n[Paso 1/3] Cargando BAAI/bge-m3 desde caché...")
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": 64  # Procesa más fragmentos por ciclo matricial sin saturar RAM
        }
    )

    print(f"\n[Paso 2/3] Calculando vectores por lotes (se guardan en disco uno a uno)...")
    for i in range(0, total_chunks, TAMANO_LOTE):
        destino = ruta_lote(i)
        if os.path.exists(destino):
            continue  # ya calculado en una corrida anterior

        tiempo_lote = time.time()
        lote = chunks[i : i + TAMANO_LOTE]
        vectores = np.array(
            embeddings.embed_documents([c.page_content for c in lote]), dtype=np.float32
        )
        # Escritura atómica: un corte a mitad de escritura no deja un lote corrupto
        np.save(destino + ".tmp.npy", vectores)
        os.replace(destino + ".tmp.npy", destino)

        procesados = min(i + TAMANO_LOTE, total_chunks)
        porcentaje = (procesados / total_chunks) * 100
        print(f"   * Progreso: {procesados}/{total_chunks} ({porcentaje:.1f}%) - Lote en {time.time() - tiempo_lote:.1f}s")

    print(f"\n[Paso 3/3] Construyendo la base Chroma con los vectores calculados...")
    if os.path.exists(RUTA_CHROMA_DB):
        shutil.rmtree(RUTA_CHROMA_DB)
    vectorstore = Chroma(embedding_function=embeddings, persist_directory=RUTA_CHROMA_DB)
    todos = np.concatenate([np.load(ruta_lote(i)) for i in range(0, total_chunks, TAMANO_LOTE)])
    assert len(todos) == total_chunks, f"Vectores ({len(todos)}) != chunks ({total_chunks})"

    for i in range(0, total_chunks, TAMANO_ESCRITURA_CHROMA):
        parte = chunks[i : i + TAMANO_ESCRITURA_CHROMA]
        vectorstore._collection.add(
            ids=[f"chunk_{c.metadata['id_chunk']}" for c in parte],
            embeddings=todos[i : i + TAMANO_ESCRITURA_CHROMA].tolist(),
            documents=[c.page_content for c in parte],
            metadatas=[c.metadata for c in parte],
        )

    duracion = time.time() - inicio
    print("\n" + "=" * 70)
    print("¡INDEXACIÓN FINALIZADA!")
    print(f"Total vectores en Chroma: {vectorstore._collection.count()}")
    print(f"Tiempo total de esta corrida: {duracion / 60:.2f} minutos")
    print(f"Directorio local: {RUTA_CHROMA_DB}")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_parte2_optimizada()
