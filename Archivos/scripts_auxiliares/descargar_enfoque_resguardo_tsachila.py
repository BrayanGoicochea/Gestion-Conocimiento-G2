import os
import requests
import fitz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDFS = os.path.join(BASE_DIR, "Archivos", "corpus_rag_tsachila")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 5 Documentos estratégicos con máxima pertinencia al objetivo:
# 1. Medicina tradicional en la nacionalidad Tsáchila (Zenodo 11094465)
# 2. Resguardo y transmisión de conocimiento de plantas medicinales (PLOS 10.1371/journal.pone.0239345)
# 3. Pérdida y preservación de conocimiento botánico tradicional indígena (PLOS 10.1371/journal.pone.0151693)
# 4. Cocina tradicional viviente y farmacia natural comunitaria (Zenodo 6636693)
# 5. Evaluación y rescate del conocimiento ancestral sobre plantas medicinales (Zenodo 15200768)

ENLACES_TARGET = [
    {
        "nombre": "Medicina_Tradicional_Nacionalidad_Tsachila_Z11094465.pdf",
        "url": "https://zenodo.org/api/records/11094465/files/Medicina%20tradicional%20y%20COVID-19%2C%20influencia%20en%20la%20recuperaci%C3%B3n%20y%20satisfacci%C3%B3n%20de%20la%20nacionalidad%20Ts%C3%A1chila.pdf/content"
    },
    {
        "nombre": "Transmision_Social_Conocimiento_Plantas_Medicinales_pone0239345.pdf",
        "url": "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0239345&type=printable"
    },
    {
        "nombre": "Preservacion_Perdida_Conocimiento_Botanico_Indigena_pone0151693.pdf",
        "url": "https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0151693&type=printable"
    },
    {
        "nombre": "Cocina_Viviente_Farmacia_Plantas_Alimenticias_Z6636693.pdf",
        "url": "https://zenodo.org/api/records/6636693/files/ED44.pdf/content"
    },
    {
        "nombre": "Evaluacion_Resguardo_Conocimiento_Ancestral_Plantas_Z15200768.pdf",
        "url": "https://zenodo.org/api/records/15200768/files/56.%20plantasmedicinales.pdf/content"
    }
]

def descargar_pdf(url: str, ruta_salida: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, stream=True)
        if r.status_code == 200:
            chunk_iter = r.iter_content(chunk_size=8192)
            first_chunk = next(chunk_iter, None)
            if first_chunk and b"%PDF" in first_chunk[:1024]:
                with open(ruta_salida, "wb") as f:
                    f.write(first_chunk)
                    for chunk in chunk_iter:
                        f.write(chunk)
                try:
                    doc = fitz.open(ruta_salida)
                    pags = len(doc)
                    doc.close()
                    if pags >= 1:
                        return True
                    else:
                        os.remove(ruta_salida)
                except Exception:
                    if os.path.exists(ruta_salida):
                        os.remove(ruta_salida)
    except Exception:
        pass
    return False

def ejecutar_elevacion():
    print("=" * 70, flush=True)
    print("ELEVACIÓN DE CORPUS A 205 DOCUMENTOS CON MÁXIMO FOCO EN EL TEMA", flush=True)
    print("=" * 70, flush=True)
    
    total_inicial = len([f for f in os.listdir(CARPETA_PDFS) if f.lower().endswith('.pdf')])
    print(f"Total PDFs iniciales: {total_inicial}", flush=True)
    
    nuevos = 0
    for item in ENLACES_TARGET:
        nombre = item["nombre"]
        url = item["url"]
        ruta = os.path.join(CARPETA_PDFS, nombre)
        
        if os.path.exists(ruta):
            print(f" [*] Ya existe: {nombre}", flush=True)
            continue
            
        print(f" [+] Descargando: {nombre}...", flush=True)
        if descargar_pdf(url, ruta):
            nuevos += 1
            print(f"     -> Descargado con éxito ({nombre})", flush=True)
        else:
            print(f"     -> Error descargando ({nombre})", flush=True)
            
    total_final = len([f for f in os.listdir(CARPETA_PDFS) if f.lower().endswith('.pdf')])
    print("\n" + "=" * 70, flush=True)
    print(f"RESULTADO: Se agregaron {nuevos} documentos focales.", flush=True)
    print(f"TOTAL DEFINITIVO EN CORPUS: {total_final} PDFs", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    ejecutar_elevacion()
