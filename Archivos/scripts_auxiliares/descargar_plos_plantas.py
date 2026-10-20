import os
import glob
import time
import requests
import fitz

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDFS = os.path.join(BASE_DIR, "Archivos", "corpus_rag_tsachila")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Consultas específicas por especie y etnobotánica/gastronomía tradicional ecuatoriana
CONSULTAS_PLOS = [
    ("Uncaria tomentosa", "Uncaria tomentosa medicinal"),
    ("Uncaria tomentosa", "Uncaria tomentosa ethnobotany"),
    ("Banisteriopsis caapi", "Banisteriopsis caapi ayahuasca indigenous"),
    ("Ilex guayusa", "Ilex guayusa ethnobotany traditional tea"),
    ("Bixa orellana", "Bixa orellana medicinal annatto food"),
    ("Piper aduncum", "Piper aduncum medicinal essential oil"),
    ("Eryngium foetidum", "Eryngium foetidum medicinal culinary"),
    ("Genipa americana", "Genipa americana medicinal traditional"),
    ("Petiveria alliacea", "Petiveria alliacea medicinal pharmacological"),
    ("Mansoa alliacea", "Mansoa alliacea medicinal ethnobotany"),
    ("Ficus insipida", "Ficus insipida medicinal latex traditional"),
    ("Aristolochia", "Aristolochia snakebite antiophidic medicinal"),
    ("Smilax", "Smilax medicinal properties traditional"),
    ("Siparuna", "Siparuna medicinal traditional Amazonia"),
    ("Bauhinia", "Bauhinia medicinal properties traditional"),
    ("Caesalpinia spinosa", "Caesalpinia spinosa tara medicinal properties"),
    ("Carapa guianensis", "Carapa guianensis medicinal andiroba"),
    ("Manihot esculenta", "Manihot esculenta traditional fermentation cassava chicha"),
    ("Zea mays", "Zea mays traditional fermentation beverage chicha"),
    ("Dioscorea trifida", "Dioscorea edible tubers traditional food indigenous"),
    ("Etnobotanica Ecuador", "medicinal plants Ecuador traditional ethnobotany"),
    ("Medicina Tradicional Ecuador", "indigenous traditional medicine Ecuador healers"),
    ("Plantas Antiofidicas Ecuador", "snakebite medicinal plants Ecuador indigenous treatment"),
    ("Bebidas Fermentadas Indigenas", "traditional fermented beverages Amazon indigenous plants"),
    ("Plantas Alimenticias Indigenas", "traditional food plants indigenous Amazonia Andes"),
    ("Farmacopea Amazonica", "Amazonian ethnobotany indigenous pharmacopoeia plants"),
    ("Plantas Sagradas Chamanismo", "shamanism indigenous ritual plants Ecuador traditional"),
    ("Curanderia y Plantas", "herbal medicine traditional practices indigenous South America")
]

def sanitizar_nombre(texto: str) -> str:
    return "".join(c for c in texto if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")

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

def recolectar_desde_plos(meta_total=215):
    print("=" * 70, flush=True)
    print("RECOLECCIÓN CIENTÍFICA DESDE PLOS (PUBLIC LIBRARY OF SCIENCE)", flush=True)
    print("=" * 70, flush=True)
    
    total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print(f"Documentos actuales en corpus: {total_actual}", flush=True)
    print(f"Meta objetivo: {meta_total} PDFs", flush=True)
    
    ids_vistos = set()
    for f in os.listdir(CARPETA_PDFS):
        base = os.path.splitext(f)[0]
        ids_vistos.add(base.split("_")[-1])
        
    for etiqueta, query in CONSULTAS_PLOS:
        total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
        if total_actual >= meta_total:
            print(f"\n¡META DE {meta_total} DOCUMENTOS ALCANZADA ({total_actual} PDFs)! Deteniendo descargas.", flush=True)
            break
            
        print(f"\n--> Consultando PLOS para: '{etiqueta}' (Query: {query})...", flush=True)
        try:
            url_api = "https://api.plos.org/search"
            params = {
                "q": query,
                "wt": "json",
                "rows": 6,
                "fl": "id,title_display"
            }
            resp = requests.get(url_api, params=params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
                
            docs = resp.json().get("response", {}).get("docs", [])
            descargas_consulta = 0
            
            for d in docs:
                if total_actual >= meta_total or descargas_consulta >= 3:
                    break
                    
                doi = d.get("id", "")
                work_id = doi.split("/")[-1]
                if work_id in ids_vistos:
                    continue
                    
                title = d.get("title_display", "")
                pdf_url = f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable"
                
                nombre_archivo = f"{sanitizar_nombre(etiqueta)}_{sanitizar_nombre(work_id)}.pdf"
                ruta_salida = os.path.join(CARPETA_PDFS, nombre_archivo)
                
                if os.path.exists(ruta_salida):
                    ids_vistos.add(work_id)
                    continue
                    
                if descargar_pdf(pdf_url, ruta_salida):
                    ids_vistos.add(work_id)
                    descargas_consulta += 1
                    total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
                    print(f" [+] [{etiqueta}] Descargado: {title[:55]}... ({total_actual}/{meta_total})", flush=True)
                    time.sleep(0.3)
                    
        except Exception as e:
            print(f" [!] Error en consulta PLOS '{query}': {e}", flush=True)
            
    total_final = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print("\n" + "=" * 70, flush=True)
    print(f"PROCESO FINALIZADO:")
    print(f" - Total definitivo de documentos en corpus: {total_final} PDFs", flush=True)
    print(f" - Cumplimiento del mínimo obligatorio (200 a 500 docs): {'CUMPLE' if total_final >= 200 else 'EN PROGRESO'}", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    recolectar_desde_plos(meta_total=215)
