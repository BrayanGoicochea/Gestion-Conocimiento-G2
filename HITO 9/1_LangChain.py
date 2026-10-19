import os
import json
import time
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# -------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS
# -------------------------------------------------------------
CARPETA_CORPUS = r"C:\Users\Usuario\Videos\EXTRA\Archivos\corpus_rag_tsachila"
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
ARCHIVO_SALIDA_JSONL = os.path.join(DIRECTORIO_ACTUAL, "chunks_tsachila.jsonl")

def ejecutar_parte1_langchain():
    print("=" * 70)
    print("   HITO 9 - PARTE 1: EXTRACCIÓN Y CHUNKING CON LANGCHAIN")
    print("=" * 70)

    if not os.path.exists(CARPETA_CORPUS):
        print(f"[!] Error: No existe la ruta del corpus: {CARPETA_CORPUS}")
        return

    archivos_pdf = [f for f in os.listdir(CARPETA_CORPUS) if f.lower().endswith(".pdf")]
    total_pdfs = len(archivos_pdf)
    print(f"-> Corpus localizado: {CARPETA_CORPUS}")
    print(f"-> Total de documentos PDF a procesar: {total_pdfs}")

    inicio_tiempo = time.time()
    documentos_langchain = []
    pdfs_con_error = 0

    # ---------------------------------------------------------
    # 1. CARGA MEDIANTE LANGCHAIN (PyPDFLoader)
    # ---------------------------------------------------------
    print("\n[Paso 1/3] Extrayendo páginas y metadatos con LangChain PyPDFLoader...")
    for idx, nombre_pdf in enumerate(archivos_pdf, start=1):
        ruta_pdf = os.path.join(CARPETA_CORPUS, nombre_pdf)
        try:
            loader = PyPDFLoader(ruta_pdf)
            paginas = loader.load()

            for p in paginas:
                # Estandarización estricta de metadatos para la cita obligatoria
                num_pagina = p.metadata.get("page", 0) + 1  # LangChain indexa desde 0
                p.metadata = {
                    "fuente": nombre_pdf,
                    "pagina": num_pagina
                }
                # Solo conservar páginas que contengan texto real
                if p.page_content.strip():
                    documentos_langchain.append(p)

            if idx % 20 == 0 or idx == total_pdfs:
                print(f"   * Procesados {idx}/{total_pdfs} PDFs ({len(documentos_langchain)} páginas válidas acumuladas)...")

        except Exception as e:
            pdfs_con_error += 1
            print(f"   [!] Error cargando {nombre_pdf}: {e}")

    print(f"\n-> Carga LangChain completa: {len(documentos_langchain)} páginas listas.")

    # ---------------------------------------------------------
    # 2. SEGMENTACIÓN CON LANGCHAIN (RecursiveCharacterTextSplitter)
    # ---------------------------------------------------------
    print("\n[Paso 2/3] Segmentando texto en chunks estructurados...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = text_splitter.split_documents(documentos_langchain)
    print(f"-> Total de chunks LangChain generados: {len(chunks)}")

    # ---------------------------------------------------------
    # 3. PERSISTENCIA EN DISCO (.JSONL)
    # ---------------------------------------------------------
    print(f"\n[Paso 3/3] Guardando chunks en archivo persistente...")
    print(f"           Ruta de salida: {ARCHIVO_SALIDA_JSONL}")

    with open(ARCHIVO_SALIDA_JSONL, "w", encoding="utf-8") as f_out:
        for idx, chunk in enumerate(chunks, start=1):
            registro = {
                "id_chunk": idx,
                "fuente": chunk.metadata["fuente"],
                "pagina": chunk.metadata["pagina"],
                "texto": chunk.page_content.strip()
            }
            f_out.write(json.dumps(registro, ensure_ascii=False) + "\n")

    duracion = time.time() - inicio_tiempo
    tamano_mb = os.path.getsize(ARCHIVO_SALIDA_JSONL) / (1024 * 1024)

    print("\n" + "=" * 70)
    print("¡PARTE 1 COMPLETADA EXITOSAMENTE!")
    print(f"Total de fragmentos persistidos: {len(chunks)}")
    print(f"Peso del archivo en disco: {tamano_mb:.2f} MB")
    print(f"Tiempo total: {duracion:.2f} segundos")
    print(f"Archivo listo para la Parte 2: {ARCHIVO_SALIDA_JSONL}")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_parte1_langchain()