import os
import glob
import time
import requests
import fitz  # PyMuPDF
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_PDFS = os.path.join(BASE_DIR, "Archivos", "corpus_rag_tsachila")
CARPETA_TXT = os.path.join(BASE_DIR, "Archivos", "corpus_limpio_txt")
CARPETA_BACKUP_RUIDO = os.path.join(BASE_DIR, "Archivos", "descarte_ruido")

os.makedirs(CARPETA_PDFS, exist_ok=True)
os.makedirs(CARPETA_TXT, exist_ok=True)
os.makedirs(CARPETA_BACKUP_RUIDO, exist_ok=True)

# ---------------------------------------------------------------------------
# 1. DOCUMENTOS HISTÓRICOS Y ETNOGRÁFICOS TSÁCHILA QUE DEBEN CONSERVARSE
# ---------------------------------------------------------------------------
DOCUMENTOS_CORE_CONSERVAR = [
    "ETNOBOTÁNICA_TSÁCHILA_PICHINCHA-ECUADOR_W7217728698",
    "ETNOTURISMO_Y_PROPIEDADES_FITOQUÍMICAS_DE_LAS_W7219438246",
    "Plantas Medicinales y Gastronómicas - Centro Cultural UNI-SHU",
    "Plantas Medicinales y Gastronómicas - Centro Cultural UNI-SHU (Texto Plano) (1)",
    "Objetos_rituales_e_identidad_W1836145780",
    "Chamanismo_liderazgo_y_poder_indígena_el_caso_W2067877726",
    "LA_ETNOBOTÁNICA_EN_EL_ECUADOR_W7218107037",
    "Identité_cosmologie_et_chamanisme_des_Tsachil_W7219268622",
    "La_fiesta_Kasama_y_la_lucha_por_la_pervivenci_W3110170264",
    "Brujería_curandería_y_chamanismo__la_dimensió_W7125461361",
    "Cultura_viva_y_resistencia_mediante_el_turism_W7163817757",
    "The_Current_Status_of_Ethnobiology_in_Ecuador_W2894434204",
    "En_el_cruce_de_caminos_Identidad_cosmovisión_W4238033680",
    "Al_sur_del_lejano_Oeste_marginalidad_ambivale_W2927798297",
    "Pensando_el_cambio_cosmo-ecológico_en_las_soc_W4416912623",
    "Análisis_de_la_educación_intercultural_biling_W3003183717"
]

def depurar_ruido_existente():
    print("=" * 70)
    print("FASE 1: DEPURACIÓN DEL 90% DE RUIDO EN EL CORPUS")
    print("=" * 70)
    
    archivos_pdf = glob.glob(os.path.join(CARPETA_PDFS, "*.pdf"))
    print(f"Total PDFs actuales en '{CARPETA_PDFS}': {len(archivos_pdf)}")
    
    conservados = 0
    descartados = 0
    
    for ruta_pdf in archivos_pdf:
        nombre_base = os.path.splitext(os.path.basename(ruta_pdf))[0]
        # Verificar si está en la lista de documentos core
        es_core = any(core.lower() in nombre_base.lower() for core in DOCUMENTOS_CORE_CONSERVAR)
        
        if not es_core:
            # Mover el PDF a la carpeta de descarte
            destino_pdf = os.path.join(CARPETA_BACKUP_RUIDO, os.path.basename(ruta_pdf))
            try:
                os.replace(ruta_pdf, destino_pdf)
                descartados += 1
            except Exception as e:
                print(f"Error moviendo {nombre_base}: {e}")
            
            # Eliminar el .txt correspondiente si existe
            ruta_txt = os.path.join(CARPETA_TXT, f"{nombre_base}.txt")
            if os.path.exists(ruta_txt):
                try:
                    os.remove(ruta_txt)
                except Exception:
                    pass
        else:
            conservados += 1
            print(f" [CONSERVADO CORE] {nombre_base[:60]}")

    print(f"\nResumen Depuración:")
    print(f" - Documentos relevantes conservados: {conservados}")
    print(f" - Documentos de ruido descartados (movidos a '{CARPETA_BACKUP_RUIDO}'): {descartados}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# 2. CATÁLOGO COMPLETO DE PLANTAS Y ESPECIES (UNI-SHU TSÁCHILA)
# ---------------------------------------------------------------------------
CATALOGO_PLANTAS = [
    {"comun": "Achiote", "tsafiqui": "Mú", "cientifico": "Bixa orellana", "familia": "Bixaceae", "tipo": "medicinal_gastronomico"},
    {"comun": "Ajengibre", "tsafiqui": "Pi'tumbaka", "cientifico": "Alpinia purpurata", "familia": "Zingiberaceae", "tipo": "medicinal"},
    {"comun": "Ají de rana", "tsafiqui": "Burutunka", "cientifico": "Abelmoschus esculentus", "familia": "Malvaceae", "tipo": "medicinal_gastronomico"},
    {"comun": "Ajo de monte", "tsafiqui": "Tsa senco", "cientifico": "Mansoa alliacea", "familia": "Bignoniaceae", "tipo": "medicinal"},
    {"comun": "Ampo Pole", "tsafiqui": "Pe Ampo", "cientifico": "Catatola costaricensis", "familia": "Icacinaceae", "tipo": "medicinal"},
    {"comun": "Albahaca de monte", "tsafiqui": "Paban tefun", "cientifico": "Ocimum micranthum", "familia": "Lamiaceae", "tipo": "medicinal_gastronomico"},
    {"comun": "Amansadora", "tsafiqui": "Mipa'kí", "cientifico": "Commelina diffusa", "familia": "Commelinaceae", "tipo": "medicinal"},
    {"comun": "Ayahuasca", "tsafiqui": "Nepi", "cientifico": "Banisteriopsis caapi", "familia": "Malpighiaceae", "tipo": "ritual_medicinal"},
    {"comun": "Barbasco de rama", "tsafiqui": "Tsa Kaja'li", "cientifico": "Phyllanthus acuminatus", "familia": "Phyllanthaceae", "tipo": "ritual_medicinal"},
    {"comun": "Bastón de faraón", "tsafiqui": "Ishan luli", "cientifico": "Etlingera elatior", "familia": "Zingiberaceae", "tipo": "medicinal_gastronomico"},
    {"comun": "Bejuco", "tsafiqui": "Parishi'li", "cientifico": "Cyclanthaceae Carludovica", "familia": "Cyclanthaceae", "tipo": "medicinal_artesanal"},
    {"comun": "Betilla", "tsafiqui": "Elena'shili", "cientifico": "Prestonia mollis", "familia": "Apocynaceae", "tipo": "medicinal"},
    {"comun": "Biblia", "tsafiqui": "Yoshilipa", "cientifico": "Justicia carnea", "familia": "Acanthaceae", "tipo": "medicinal"},
    {"comun": "Chapil", "tsafiqui": "Pituli", "cientifico": "Geonoma macrostachys", "familia": "Arecaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Caucho", "tsafiqui": "Sabe", "cientifico": "Ficus insipida", "familia": "Moraceae", "tipo": "medicinal"},
    {"comun": "Caña agria", "tsafiqui": "Ko'comla", "cientifico": "Gynerium sagittatum", "familia": "Poaceae", "tipo": "medicinal"},
    {"comun": "Colin arashili", "tsafiqui": "Colin'arashili", "cientifico": "Polybotrya alfredii", "familia": "Dryopteridaceae", "tipo": "medicinal"},
    {"comun": "Cordoncillo", "tsafiqui": "Shili'ampo", "cientifico": "Piper angustifolium", "familia": "Piperaceae", "tipo": "medicinal"},
    {"comun": "Copal", "tsafiqui": "Cho chola", "cientifico": "Dacryodes peruviana", "familia": "Burseraceae", "tipo": "ritual_medicinal"},
    {"comun": "Culantro de pozo", "tsafiqui": "Chiliangua", "cientifico": "Eryngium foetidum", "familia": "Apiaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Guayusa", "tsafiqui": "Guayosa", "cientifico": "Ilex guayusa", "familia": "Aquifoliaceae", "tipo": "medicinal_gastronomico"},
    {"comun": "Helecho", "tsafiqui": "Hará", "cientifico": "Polybotrya osmundacea", "familia": "Dryopteridaceae", "tipo": "medicinal"},
    {"comun": "Hierba de serpiente", "tsafiqui": "Pini ta'pe", "cientifico": "Triolena pustulata", "familia": "Melastomataceae", "tipo": "antiofidico_medicinal"},
    {"comun": "Hiel del sol", "tsafiqui": "Yo'kantsa", "cientifico": "Baccharis latifolia", "familia": "Asteraceae", "tipo": "medicinal"},
    {"comun": "Hierba del trueno", "tsafiqui": "Kuntata pe", "cientifico": "Floscopa peruviana", "familia": "Commelinaceae", "tipo": "medicinal"},
    {"comun": "Hoja de Yuca", "tsafiqui": "Ku chu", "cientifico": "Manihot esculenta", "familia": "Euphorbiaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Ishentape", "tsafiqui": "Ishentape", "cientifico": "Palicourea crocea", "familia": "Rubiaceae", "tipo": "medicinal"},
    {"comun": "Katsa tape", "tsafiqui": "Katsa tape", "cientifico": "Solanum schlechtendalianum", "familia": "Solanaceae", "tipo": "medicinal"},
    {"comun": "Matico", "tsafiqui": "Wa'pinku", "cientifico": "Piper aduncum", "familia": "Piperaceae", "tipo": "medicinal"},
    {"comun": "Malaria", "tsafiqui": "Chan kui", "cientifico": "Mendoncia sericea", "familia": "Mendonciaceae", "tipo": "medicinal"},
    {"comun": "Mocora", "tsafiqui": "Joro", "cientifico": "Astrocaryum standleyanum", "familia": "Arecaceae", "tipo": "gastronomico_artesanal"},
    {"comun": "Ortiga brava", "tsafiqui": "Tini", "cientifico": "Urera baccifera", "familia": "Urticaceae", "tipo": "medicinal_purificacion"},
    {"comun": "Oton korotape", "tsafiqui": "Oton korotape", "cientifico": "Ruellia colorata", "familia": "Acanthaceae", "tipo": "medicinal"},
    {"comun": "Palma", "tsafiqui": "Tse'tsero", "cientifico": "Synechanthus warscewiczianus", "familia": "Arecaceae", "tipo": "medicinal"},
    {"comun": "Ampo", "tsafiqui": "Ámpo", "cientifico": "Piper tuberculatum", "familia": "Piperaceae", "tipo": "medicinal"},
    {"comun": "Pakigua", "tsafiqui": "Parashili", "cientifico": "Castilla elastica", "familia": "Moraceae", "tipo": "medicinal"},
    {"comun": "Papa chilma", "tsafiqui": "Tsan pó", "cientifico": "Dioscorea trifida", "familia": "Dioscoreaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Bejuco pescadito", "tsafiqui": "Watsa senko", "cientifico": "Gurania spinulosa", "familia": "Cucurbitaceae", "tipo": "medicinal"},
    {"comun": "Planta de murciélago", "tsafiqui": "Shu'pantape", "cientifico": "Cleome pilosa", "familia": "Capparaceae", "tipo": "medicinal"},
    {"comun": "Palma real", "tsafiqui": "Ka'ti", "cientifico": "Roystonea regia", "familia": "Arecaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Planta insectívora", "tsafiqui": "Tso potede", "cientifico": "Utricularia foliosa", "familia": "Lentibulariaceae", "tipo": "ritual_medicinal"},
    {"comun": "Planta zorrilla", "tsafiqui": "Bo'pitape", "cientifico": "Petiveria alliacea", "familia": "Petiveriaceae", "tipo": "medicinal_limpia"},
    {"comun": "Pinta", "tsafiqui": "Pinta", "cientifico": "Clibadium laxum", "familia": "Asteraceae", "tipo": "medicinal"},
    {"comun": "Platanillo", "tsafiqui": "Na luáno", "cientifico": "Heliconia stricta", "familia": "Heliconiaceae", "tipo": "gastronomico_medicinal"},
    {"comun": "Bacua'ja bijagua", "tsafiqui": "Bacua'ja bijagua", "cientifico": "Calathea crotalifera", "familia": "Marantaceae", "tipo": "gastronomico_envoltura"},
    {"comun": "Puban kará", "tsafiqui": "Puban kará", "cientifico": "Siparuna thecaphora", "familia": "Siparunaceae", "tipo": "medicinal_chamanico"},
    {"comun": "Espasmo de arco", "tsafiqui": "Punta lanza", "cientifico": "Columnea sanguinea", "familia": "Gesneriaceae", "tipo": "antiofidico_medicinal"},
    {"comun": "San juanillo del monte", "tsafiqui": "Jelen di ku", "cientifico": "Renealmia thyrsoidea", "familia": "Zingiberaceae", "tipo": "medicinal"},
    {"comun": "Simayuca", "tsafiqui": "Lutum baka", "familia": "Euphorbiaceae", "cientifico": "Manihot brachyloba", "tipo": "medicinal_gastronomico"},
    {"comun": "Suashi'li", "tsafiqui": "Shua shili", "cientifico": "Caesalpinia spinosa", "familia": "Fabaceae", "tipo": "medicinal"},
    {"comun": "Tangaré", "tsafiqui": "Lon kó", "cientifico": "Carapa guianensis", "familia": "Meliaceae", "tipo": "medicinal_cosmetico"},
    {"comun": "Uña de gato", "tsafiqui": "Meshe'tewe'we", "cientifico": "Uncaria tomentosa", "familia": "Rubiaceae", "tipo": "medicinal"},
    {"comun": "Uña de vaca", "tsafiqui": "Tsantsa'lo shili", "cientifico": "Bauhinia variegata", "familia": "Fabaceae", "tipo": "medicinal"},
    {"comun": "Wito", "tsafiqui": "Ma'li", "cientifico": "Genipa americana", "familia": "Rubiaceae", "tipo": "corporal_gastronomico"},
    {"comun": "Wuarande", "tsafiqui": "Wuarande", "cientifico": "Siparuna eggersii", "familia": "Siparunaceae", "tipo": "medicinal"},
    {"comun": "Zaragoza", "tsafiqui": "Zaracoza", "cientifico": "Aristolochia pilosa", "familia": "Aristolochiaceae", "tipo": "antiofidico_medicinal"},
    {"comun": "Zarzaparrilla", "tsafiqui": "Zarzaparrilla", "cientifico": "Smilax officinalis", "familia": "Smilacaceae", "tipo": "medicinal"},
    {"comun": "Chiakú Tape", "tsafiqui": "Chiakú Tape", "cientifico": "Selaginella tomentosa", "familia": "Selaginellaceae", "tipo": "medicinal"},
    # Adicionales gastronómicos y ceremoniales Tsáchila indispensables
    {"comun": "Chicha de Yuca", "tsafiqui": "Uru Mala", "cientifico": "Manihot esculenta chicha", "familia": "Euphorbiaceae", "tipo": "gastronomico_ceremonial"},
    {"comun": "Chicha de Maiz", "tsafiqui": "Yo'mala", "cientifico": "Zea mays chicha tradicional", "familia": "Poaceae", "tipo": "gastronomico_ceremonial"},
    {"comun": "Tabaco Ritual", "tsafiqui": "Kanthi Pi", "cientifico": "Nicotiana tabacum chamanismo", "familia": "Solanaceae", "tipo": "ritual_chamanico"},
    {"comun": "Muturu", "tsafiqui": "Muturu'pi", "cientifico": "Grias peruviana", "familia": "Lecythidaceae", "tipo": "medicinal_desintoxicante"}
]

HEADERS = {
    "User-Agent": "TsachilaEthnobotanicalBrain/2.0 (mailto:investigacion.tsachila@unmsm.edu.pe)"
}

def sanitizar_nombre(texto: str) -> str:
    return "".join(c for c in texto if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")

def descargar_pdf(url: str, ruta_salida: str) -> bool:
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, stream=True)
        if r.status_code == 200:
            content_type = r.headers.get("content-type", "").lower()
            # Descargar primeros bytes para verificar firma PDF
            chunk_iter = r.iter_content(chunk_size=8192)
            first_chunk = next(chunk_iter, None)
            if first_chunk and b"%PDF" in first_chunk[:1024]:
                with open(ruta_salida, "wb") as f:
                    f.write(first_chunk)
                    for chunk in chunk_iter:
                        f.write(chunk)
                # Validar que PyMuPDF pueda abrirlo y tenga texto
                try:
                    doc = fitz.open(ruta_salida)
                    num_paginas = len(doc)
                    doc.close()
                    if num_paginas >= 1:
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

def buscar_y_descargar_para_planta(planta: dict, ids_descargados: set, max_por_planta: int = 4):
    comun = planta["comun"]
    cientifico = planta["cientifico"]
    tipo = planta["tipo"]
    
    # 2 consultas diferenciadas: medicinal y etnobotanica/gastronomica
    consultas = [
        f"{cientifico} medicinal properties",
        f"{cientifico} ethnobotany traditional use {comun}"
    ]
    if "gastronomico" in tipo:
        consultas.append(f"{cientifico} edible food culinary {comun}")
    
    descargas_exitosas = 0
    
    for query in consultas:
        if descargas_exitosas >= max_por_planta:
            break
            
        url_api = "https://api.openalex.org/works"
        params = {
            "search": query,
            "filter": "has_fulltext:true,is_oa:true",
            "per_page": 8
        }
        
        try:
            resp = requests.get(url_api, params=params, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                continue
            resultados = resp.json().get("results", [])
            
            for item in resultados:
                if descargas_exitosas >= max_por_planta:
                    break
                    
                work_id = item.get("id", "").split("/")[-1]
                if work_id in ids_descargados:
                    continue
                    
                titulo = item.get("title") or ""
                oa_url = item.get("open_access", {}).get("oa_url")
                if not oa_url or not oa_url.startswith("http"):
                    continue
                
                # Descartar ruido evidente
                titulo_low = titulo.lower()
                if any(bad in titulo_low for bad in ["bovine", "cattle", "dental", "solar", "concrete", "photovoltaic", "energy loss", "pedagog", "covid"]):
                    continue
                
                nombre_archivo = f"{sanitizar_nombre(comun)}_{sanitizar_nombre(cientifico[:25])}_{work_id}.pdf"
                ruta_salida = os.path.join(CARPETA_PDFS, nombre_archivo)
                
                if os.path.exists(ruta_salida):
                    ids_descargados.add(work_id)
                    descargas_exitosas += 1
                    continue
                    
                if descargar_pdf(oa_url, ruta_salida):
                    ids_descargados.add(work_id)
                    descargas_exitosas += 1
                    print(f" [+] [{comun}] Descargado: {titulo[:60]}... ({work_id})")
                
                time.sleep(0.3)
        except Exception as e:
            # Continuar con la siguiente consulta
            pass
            
    return descargas_exitosas

def procesar_una_planta(planta, ids_descargados, lock, max_por_planta=3):
    comun = planta["comun"]
    cientifico = planta["cientifico"]
    tipo = planta["tipo"]
    
    consultas = [
        f"{cientifico} medicinal properties",
        f"{cientifico} ethnobotany traditional use {comun}"
    ]
    if "gastronomico" in tipo:
        consultas.append(f"{cientifico} edible food culinary {comun}")
    
    descargas_exitosas = 0
    
    for query in consultas:
        if descargas_exitosas >= max_por_planta:
            break
            
        url_api = "https://api.openalex.org/works"
        params = {
            "search": query,
            "filter": "has_fulltext:true,is_oa:true",
            "per_page": 8
        }
        
        try:
            resp = requests.get(url_api, params=params, headers=HEADERS, timeout=20)
            if resp.status_code != 200:
                continue
            resultados = resp.json().get("results", [])
            
            for item in resultados:
                if descargas_exitosas >= max_por_planta:
                    break
                    
                work_id = item.get("id", "").split("/")[-1]
                
                with lock:
                    if work_id in ids_descargados:
                        continue
                    ids_descargados.add(work_id)
                    
                titulo = item.get("title") or ""
                oa_url = item.get("open_access", {}).get("oa_url")
                if not oa_url or not oa_url.startswith("http"):
                    continue
                
                titulo_low = titulo.lower()
                if any(bad in titulo_low for bad in ["bovine", "cattle", "dental", "solar", "concrete", "photovoltaic", "energy loss", "pedagog", "covid"]):
                    continue
                
                nombre_archivo = f"{sanitizar_nombre(comun)}_{sanitizar_nombre(cientifico[:25])}_{work_id}.pdf"
                ruta_salida = os.path.join(CARPETA_PDFS, nombre_archivo)
                
                if os.path.exists(ruta_salida):
                    descargas_exitosas += 1
                    continue
                    
                if descargar_pdf(oa_url, ruta_salida):
                    descargas_exitosas += 1
                    print(f" [+] [{comun}] Descargado: {titulo[:55]}... ({work_id})", flush=True)
                
                time.sleep(0.1)
        except Exception:
            pass
            
    return descargas_exitosas

def ejecutar_recoleccion_corpus(meta_total_docs=220):
    import threading
    print("=" * 70, flush=True)
    print("FASE 2: RECOLECCIÓN MULTIHILO (ZOOM POR CADA PLANTA)", flush=True)
    print("=" * 70, flush=True)
    print(f"Total especies en catálogo Tsáchila: {len(CATALOGO_PLANTAS)}", flush=True)
    print(f"Meta objetivo de documentos válidos en corpus: {meta_total_docs}", flush=True)
    
    ids_descargados = set()
    for f in os.listdir(CARPETA_PDFS):
        parts = f.replace(".pdf", "").split("_")
        if parts:
            ids_descargados.add(parts[-1])
            
    total_inicial = len(glob.glob(os.path.join(CARPETA_PDFS, '*.pdf')))
    print(f"Documentos preexistentes válidos en carpeta: {total_inicial}", flush=True)
    
    lock = threading.Lock()
    total_descargas = 0
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {
            executor.submit(procesar_una_planta, planta, ids_descargados, lock, 3): planta
            for planta in CATALOGO_PLANTAS
        }
        for fut in as_completed(futuros):
            p = futuros[fut]
            try:
                exitos = fut.result()
                total_descargas += exitos
                total_actual = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
                print(f"[*] Progreso: {total_actual}/{meta_total_docs} documentos en corpus (Completado: {p['comun']})", flush=True)
                if total_actual >= meta_total_docs:
                    print(f"\n¡Meta de documentos alcanzada ({total_actual})! Deteniendo nuevas solicitudes.", flush=True)
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
            except Exception as e:
                pass
        
    total_final = len(glob.glob(os.path.join(CARPETA_PDFS, "*.pdf")))
    print("\n" + "=" * 70, flush=True)
    print("RECOLECCIÓN COMPLETADA CON ÉXITO:", flush=True)
    print(f" - Nuevos PDFs botánicos/etnobotánicos descargados: {total_descargas}", flush=True)
    print(f" - Total acumulado de documentos en corpus: {total_final}", flush=True)
    print(f" - Carpeta destino: {CARPETA_PDFS}", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    depurar_ruido_existente()
    ejecutar_recoleccion_corpus(meta_total_docs=220)
