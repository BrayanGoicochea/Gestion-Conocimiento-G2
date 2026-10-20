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

CONSULTAS_ZENODO = [
    ("Uncaria tomentosa", "Uncaria tomentosa medicinal"),
    ("Uncaria tomentosa", "Uncaria tomentosa traditional medicine"),
    ("Genipa americana", "Genipa americana medicinal"),
    ("Genipa americana", "Genipa americana food traditional"),
    ("Smilax", "Smilax medicinal properties"),
    ("Aristolochia", "Aristolochia medicinal antiophidic"),
    ("Carapa guianensis", "Carapa guianensis medicinal properties"),
    ("Bauhinia", "Bauhinia medicinal properties"),
    ("Caesalpinia spinosa", "Caesalpinia spinosa medicinal tara"),
    ("Siparuna thecaphora", "Siparuna medicinal ethnobotany"),
    ("Selaginella", "Selaginella medicinal pharmacological"),
    ("Dioscorea trifida", "Dioscorea trifida yam food edible"),
    ("Ilex guayusa", "Ilex guayusa ethnobotany tea traditional"),
    ("Banisteriopsis caapi", "Banisteriopsis caapi ayahuasca indigenous"),
    ("Mansoa alliacea", "Mansoa alliacea ajo de monte medicinal"),
    ("Petiveria alliacea", "Petiveria alliacea medicinal properties"),
    ("Piper aduncum", "Piper aduncum matico medicinal"),
    ("Eryngium foetidum", "Eryngium foetidum culantro culinaria medicinal"),
    ("Bixa orellana", "Bixa orellana achiote medicinal food"),
    ("Manihot esculenta", "Manihot esculenta chicha tradicional yuca"),
    ("Zea mays", "Chicha tradicional maiz fermentacion Ecuador"),
    ("Plantas Antiofidicas", "Plantas medicinales mordedura de serpiente antiofidica"),
    ("Etnobotanica Ecuador", "Etnobotanica plantas medicinales indigenas Ecuador"),
    ("Chamanismo Indigena", "Chamanismo medicina tradicional Tsachila Ecuador"),
    ("Gastronomia Tradicional", "Plantas alimenticias y cocina tradicional indigena Ecuador"),
    ("Plantas Medicinales Shuar", "Plantas medicinales Amazonia Ecuador curacion"),
    ("Fitoterapia Andina", "Plantas medicinales tradicion ancestral Ecuador"),
    ("Rituales de Sanacion", "Medicina tradicional plantas curanderos Ecuador"),
    ("Farmacopea Tradicional", "Farmacopea tradicional plantas medicinales indigenas"),
    ("Ficus insipida", "Ficus insipida medicinal latex traditional"),
    ("Ocimum micranthum", "Ocimum micranthum essential oil medicinal"),
    ("Alpinia purpurata", "Alpinia purpurata medicinal pharmacological"),
    ("Dacryodes peruviana", "Dacryodes peruviana copal resin traditional"),
    ("Urera baccifera", "Urera baccifera ortiga medicinal antiinflammatory"),
    ("Astrocaryum standleyanum", "Astrocaryum mocora traditional fruit palm")
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

def recolectar_desde_zenodo(meta_total=220):
    print("=" * 70, flush=True)
    print("RECOLECCIÓN DESDE REPOSITORIO ZENODO (OPEN SCIENCE)", flush=True)
    print("=" * 70, flush=True)
    
    total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print(f"Documentos actuales en corpus: {total_actual}", flush=True)
    print(f"Meta a alcanzar: {meta_total}", flush=True)
    
    ids_vistos = set()
    for f in os.listdir(CARPETA_PDFS):
        base = os.path.splitext(f)[0]
        ids_vistos.add(base.split("_")[-1])
        
    for etiqueta, query in CONSULTAS_ZENODO:
        total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
        if total_actual >= meta_total:
            print(f"\n¡META DE {meta_total} DOCUMENTOS ALCANZADA ({total_actual} PDFs)! Deteniendo descargas.", flush=True)
            break
            
        print(f"\n--> Consultando Zenodo para: '{etiqueta}'...", flush=True)
        try:
            url_api = "https://zenodo.org/api/records"
            params = {
                "q": f"{query} resource_type.type:publication",
                "size": 10
            }
            resp = requests.get(url_api, params=params, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue
                
            hits = resp.json().get("hits", {}).get("hits", [])
            descargas_consulta = 0
            
            for h in hits:
                if total_actual >= meta_total or descargas_consulta >= 3:
                    break
                    
                rec_id = str(h.get("id", ""))
                if rec_id in ids_vistos:
                    continue
                    
                title = h.get("metadata", {}).get("title", "")
                files = h.get("files", [])
                
                pdf_link = None
                for f in files:
                    if f.get("key", "").lower().endswith(".pdf"):
                        pdf_link = f.get("links", {}).get("self")
                        break
                        
                if not pdf_link:
                    continue
                    
                nombre_archivo = f"{sanitizar_nombre(etiqueta)}_{rec_id}.pdf"
                ruta_salida = os.path.join(CARPETA_PDFS, nombre_archivo)
                
                if os.path.exists(ruta_salida):
                    ids_vistos.add(rec_id)
                    continue
                    
                if descargar_pdf(pdf_link, ruta_salida):
                    ids_vistos.add(rec_id)
                    descargas_consulta += 1
                    total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
                    print(f" [+] [{etiqueta}] Descargado: {title[:55]}... ({total_actual}/{meta_total})", flush=True)
                    time.sleep(0.2)
                    
        except Exception as e:
            print(f" [!] Error en consulta Zenodo '{query}': {e}", flush=True)
            
    total_final = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print("\n" + "=" * 70, flush=True)
    print(f"PROCESO FINALIZADO:")
    print(f" - Total definitivo de documentos en corpus: {total_final} PDFs", flush=True)
    print(f" - Cumplimiento del mínimo obligatorio (200 a 500 docs): {'CUMPLE' if total_final >= 200 else 'EN PROGRESO'}", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    recolectar_desde_zenodo(meta_total=220)
