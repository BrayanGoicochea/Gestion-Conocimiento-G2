import os
import glob
import time
import requests
import fitz
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDFS = os.path.join(BASE_DIR, "Archivos", "corpus_rag_tsachila")

HEADERS = {
    "User-Agent": "TsachilaCorpusExpander/2.0 (mailto:investigacion.etnobotanica@unmsm.edu.pe)"
}

CONSULTAS_COMPLEMENTARIAS = [
    # Especies que faltaban con búsquedas ampliadas
    ("Uña de gato", "Uncaria tomentosa medicinal properties"),
    ("Uña de gato", "Uncaria guianensis traditional medicine"),
    ("Wito", "Genipa americana medicinal properties"),
    ("Wito", "Genipa americana food fruit ethnobotany"),
    ("Zarzaparrilla", "Smilax medicinal properties traditional"),
    ("Zaragoza", "Aristolochia medicinal antiophidic snakebite"),
    ("Tangaré", "Carapa guianensis medicinal oil properties"),
    ("Uña de vaca", "Bauhinia forficata medicinal traditional"),
    ("Suashili", "Caesalpinia spinosa medicinal antioxidant"),
    ("Wuarande", "Siparuna medicinal properties traditional"),
    ("Chiakú Tape", "Selaginella medicinal pharmacological"),
    ("Papa chilma", "Dioscorea edible yam ethnobotany food"),
    ("Chicha ancestral", "Chicha traditional beverage fermentation Ecuador"),
    ("Yuca gastronomia", "Manihot esculenta traditional food processing"),
    ("Maiz chicha", "Zea mays traditional ceremonial beverage indigenous"),
    ("Tabaco chamanico", "Nicotiana tabacum traditional shamanic ritual indigenous"),
    ("Plantas antiofidicas", "Medicinal plants snakebite antivenom Ecuador indigenous"),
    ("Plantas antiofidicas", "Antiophidic plants traditional medicine Amazonia"),
    ("Etnobotanica Ecuador", "Etnobotanica plantas medicinales Ecuador comunidades"),
    ("Farmacopea indigena", "Indigenous medicinal plants pharmacopoeia Ecuador"),
    ("Gastronomia Tsachila", "Plantas alimenticias y gastronomia tradicional indigena Ecuador"),
    ("Plantas sagradas", "Shamanic plants ceremonial ethnobotany Ecuador indigenous"),
    ("Plantas purificacion", "Medicinal plants cleansing ritual bath Amazonian indigenous"),
    ("Curanderia y plantas", "Traditional medicine indigenous healers ethnopharmacology Ecuador"),
    ("Bebidas tradicionales", "Traditional fermented beverages indigenous Amazon Andes")
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
                        return False
                except Exception:
                    if os.path.exists(ruta_salida):
                        os.remove(ruta_salida)
                    return False
    except Exception:
        pass
    return False

def buscar_y_descargar(tema_query, ids_vistos, lock, meta_total=220):
    tema, query = tema_query
    total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    if total_actual >= meta_total:
        return 0
        
    url_api = "https://api.openalex.org/works"
    params = {
        "search": query,
        "filter": "has_fulltext:true,is_oa:true",
        "per_page": 10
    }
    descargados = 0
    try:
        resp = requests.get(url_api, params=params, headers=HEADERS, timeout=20)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            for item in results:
                total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
                if total_actual >= meta_total:
                    break
                    
                work_id = item.get("id", "").split("/")[-1]
                with lock:
                    if work_id in ids_vistos:
                        continue
                    ids_vistos.add(work_id)
                    
                titulo = item.get("title") or ""
                oa_url = item.get("open_access", {}).get("oa_url")
                if not oa_url or not oa_url.startswith("http"):
                    continue
                    
                titulo_low = titulo.lower()
                if any(bad in titulo_low for bad in ["bovine", "cattle", "dental", "solar", "photovoltaic", "concrete", "energy loss"]):
                    continue
                    
                nombre_archivo = f"{sanitizar_nombre(tema)}_{work_id}.pdf"
                ruta_salida = os.path.join(CARPETA_PDFS, nombre_archivo)
                
                if os.path.exists(ruta_salida):
                    descargados += 1
                    continue
                    
                if descargar_pdf(oa_url, ruta_salida):
                    descargados += 1
                    print(f" [+] [{tema}] Descargado: {titulo[:55]}... ({work_id})", flush=True)
                    time.sleep(0.1)
    except Exception:
        pass
    return descargados

def completar_hasta_meta(meta_total=220):
    import threading
    print("=" * 70, flush=True)
    print("COMPLETANDO CORPUS HASTA ALCANZAR LA MÉTRICA REGLAMENTARIA (200-500)", flush=True)
    print("=" * 70, flush=True)
    
    ids_vistos = set()
    for f in os.listdir(CARPETA_PDFS):
        parts = f.replace(".pdf", "").split("_")
        if parts:
            ids_vistos.add(parts[-1])
            
    total_inicial = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print(f"Documentos actuales en corpus: {total_inicial}", flush=True)
    print(f"Meta objetivo: {meta_total}", flush=True)
    
    lock = threading.Lock()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = [
            executor.submit(buscar_y_descargar, tq, ids_vistos, lock, meta_total)
            for tq in CONSULTAS_COMPLEMENTARIAS
        ]
        for fut in as_completed(futuros):
            try:
                fut.result()
                total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
                print(f"[*] Progreso global: {total_actual}/{meta_total} PDFs en corpus", flush=True)
                if total_actual >= meta_total:
                    print(f"\n¡META DE {meta_total} DOCUMENTOS ALCANZADA!", flush=True)
                    break
            except Exception:
                pass
                
    total_final = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print("\n" + "=" * 70, flush=True)
    print(f"TOTAL DEFINITIVO EN CORPUS: {total_final} PDFs", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    completar_hasta_meta(meta_total=220)
