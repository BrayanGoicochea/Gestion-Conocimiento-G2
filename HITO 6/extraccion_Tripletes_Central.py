import os
import json

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
ARCHIVO_SALIDA_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")
FUENTE = "Plantas Medicinales y Gastronómicas - Centro Cultural UNI-SHU.pdf"

tripletas_unishu = []

def agregar(sujeto, relacion, objeto):
    if sujeto and relacion and objeto:
        tripletas_unishu.append({
            "sujeto": str(sujeto).strip(),
            "relacion": str(relacion).strip(),
            "objeto": str(objeto).strip(),
            "fuente": FUENTE
        })

# =========================================================================
# 1. TABLA 2: TAXONOMÍA Y NOMBRES EN TSÁFIQUI (59 Especies)
# =========================================================================
taxonomia = [
    ("Achiote", "Mú", "Bixa orellana", "Bixaceae"),
    ("Ajengibre", "Pi'tumbaka", "Alpinia purpurata", "Zingiberaceae"),
    ("Ají de rana", "Burutunka", "Abelmoschus", "Malvaceae"),
    ("Ajo de monte", "Tsa senco", "Mansoa alliacea", "Bignoniaceae"),
    ("Ampo Pole", "Pe Ampo", "Catatola costaricensis", "Icacinaceae"),
    ("Albahaca de monte", "Paban tefun", "Ocimum micranthum", "Lamiaceae"),
    ("Amansadora", "Mipa'kí", "Commelina diffusa", "Commelinaceae"),
    ("Ayahuasca", "Nepi", "Banisteriopsis caapi", "Malpighiaceae"),
    ("Barbasco de rama", "Tsa Kaja'li", "Phyllanthaceae", "Fabaceae"),
    ("Bastón de faraón", "Ishan luli", "Etlingera elatior", "Zingiberaceae"),
    ("Bejuco", "Parishi'li", "Cyclanthaceae", "Cyclanthaceae"),
    ("Betilla", "Elena'shili", "Prestonia mollis", "Apocynaceae"),
    ("Biblia", "Yoshilipa", "Justicia lanthina", "Acanthaceae"),
    ("Chapil", "Pituli", "Geonoma", "Arecaceae"),
    ("Caucho", "Sabe", "Ficus insipida", "Moraceae"),
    ("Caña agria", "Ko'comla", "Gynerium sagittatum", "Poaceae"),
    ("Colin arashili", "Colin'arashili", "Polybotrya alfredii", "Dryopteridaceae"),
    ("Cordoncillo", "Shili'ampo", "Piper sp", "Piperaceae"),
    ("Copal", "Cho chola", "Dacryodes peruviana", "Burseraceae"),
    ("Culantro de poso", "Chiliangua", "Eryngium foetidum", "Apiaceae"),
    ("Guayusa", "Guayosa", "Ilex guayusa", "Aquifoliaceae"),
    ("Helecho", "Hará", "Polybotrya osmundacea", "Dryopteridaceae"),
    ("Hierba de serpiente", "Pini ta'pe", "Triolena pustulata", "Melastomataceae"),
    ("Hiel del sol", "Yo'kantsa", "Asteraceae sp.", "Asteraceae"),
    ("Hierba del trueno", "Kuntata pe", "Floscopa peruviana", "Commelinaceae"),
    ("Hoja de Yuca", "Ku chu", "Manihot esculenta", "Euphorbiaceae"),
    ("Ishentape", "Ishentape", "Palicourea crocea", "Rubiaceae"),
    ("Katsa tape", "Katsa tape", "Solanum schlechtendalianum", "Solanaceae"),
    ("Matico", "Wa'pinku", "Piper secundum", "Piperaceae"),
    ("Malaria", "Chan kui", "Mendoncia sericea", "Mendonciaceae"),
    ("Mocora", "Joro", "Astrocaryum standleyanum", "Arecaceae"),
    ("Ortiga brava", "Tini", "Urtica dioica", "Urticaceae"),
    ("Oton korotape", "Oton korotape", "Ruellia colorata", "Acanthaceae"),
    ("Palma", "Tse'tsero", "Synechanthus warscewiczianus", "Arecaceae"),
    ("Ampo", "Ámpo", "Piper tuberculatum", "Piperaceae"),
    ("Pakigua", "Parashili", "Castilla elastica", "Moraceae"),
    ("Papa chilma", "Tsan pó", "Dioscorea trifida", "Dioscoreaceae"),
    ("Bejuco pescadito", "Watsa senko", "Cucurbitaceae sp.", "Cucurbitaceae"),
    ("Planta de murciélago", "Shu'pantape", "Cleome pilosa", "Capparaceae"),
    ("Palma real", "Ka'ti", "Roystonea regia", "Arecaceae"),
    ("Planta insectívora", "Tso potede", "Nepenthes sp.", "Nepenthaceae"),
    ("Planta zorrilla", "Bo'pitape", "Petiveria alliacea", "Petiveriaceae"),
    ("Pinta", "Pinta", "Clibadium laxum", "Asteraceae"),
    ("Platanillo", "Na luáno", "Heliconia sp.", "Heliconiaceae"),
    ("Bacua'ja bijagua", "Bacua'ja bijagua", "Calathea crotalifera", "Marantaceae"),
    ("Puban kará", "Puban kará", "Siparuna thecaphora", "Siparunaceae"),
    ("Espasmo de arco", "Punta lanza", "Gesneriaceae sp.", "Gesneriaceae"),
    ("San juanillo del monte", "Jelen di ku", "Renealmia thyrsoidea", "Zingiberaceae"),
    ("Simayuca", "Lutum baka", "Manihot pavoniana", "Euphorbiaceae"),
    ("Suashi'li", "Shua shili", "Caesalpinia spinosa", "Fabaceae"),
    ("Tangaré", "Lon kó", "Carapa guianensis", "Meliaceae"),
    ("Uña de gato", "Meshe'tewe'we", "Uncaria guianensis", "Rubiaceae"),
    ("Uña de vaca", "Tsantsa'lo shili", "Cayaponia bonplandii", "Cucurbitaceae"),
    ("Wito", "Ma'li", "Genipa americana", "Rubiaceae"),
    ("Wuarande", "Wuarande", "Siparuna thecaphora", "Siparunaceae"),
    ("Zaragoza", "Zaracoza", "Aristolochia pilosa", "Aristolochiaceae"),
    ("Zarzaparrilla", "Zarzaparrilla", "Smilax officinalis", "Smilacaceae"),
    ("Chiakú Tape", "Chiakú Tape", "Selaginella tomentosa", "Selaginellaceae")
]

for com, tsaf, cien, fam in taxonomia:
    agregar(com, "nombre_tsafiqui", tsaf)
    agregar(com, "nombre_cientifico", cien)
    agregar(com, "pertenece_a_familia", fam)

# =========================================================================
# 2. TABLA 6 & 7: FARMACOPEA, USOS SHAMÁNICOS Y PARTES
# =========================================================================
farmacopea = [
    # Achiote
    ("Achiote", "trata_a", "Inflamación de la vejiga"),
    ("Achiote", "trata_a", "Afecciones del sistema respiratorio"),
    ("Achiote", "trata_a", "Cáncer de piel"),
    ("Achiote", "usa_parte", "Hojas"),
    ("Achiote", "usa_parte", "Semillas"),
    ("Achiote", "preparado_como", "Cataplasma de hojas calientes"),
    ("Achiote", "administrado_por", "Poné"),

    # Ajengibre
    ("Ajengibre", "trata_a", "Alteraciones del sistema nervioso"),
    ("Ajengibre", "trata_a", "Infecciones estomacales"),
    ("Ajengibre", "trata_a", "Inflamación de riñones"),
    ("Ajengibre", "trata_a", "Cataratas"),
    ("Ajengibre", "usa_parte", "Raíz"),
    ("Ajengibre", "usa_parte", "Hojas"),
    ("Ajengibre", "preparado_como", "Infusión"),
    ("Ajengibre", "preparado_como", "Sumo directo para ojos"),

    # Ají de rana
    ("Ají de rana", "trata_a", "Escalofríos"),
    ("Ají de rana", "trata_a", "Fiebre"),
    ("Ají de rana", "trata_a", "Dolor muscular"),
    ("Ají de rana", "trata_a", "Mal aliento"),
    ("Ají de rana", "usa_parte", "Semillas tiernas"),
    ("Ají de rana", "preparado_como", "Cataplasma"),

    # Ajo de monte
    ("Ajo de monte", "trata_a", "Mala vibra"),
    ("Ajo de monte", "usa_parte", "Raíz machacada"),
    ("Ajo de monte", "usa_parte", "Hojas"),
    ("Ajo de monte", "preparado_como", "Baño energético"),

    # Ayahuasca
    ("Ayahuasca", "trata_a", "Intoxicación espiritual"),
    ("Ayahuasca", "trata_a", "Parásitos intestinales"),
    ("Ayahuasca", "usa_parte", "Bejuco"),
    ("Ayahuasca", "usa_parte", "Corteza"),
    ("Ayahuasca", "preparado_como", "Cocción ritual en olla de barro"),
    ("Ayahuasca", "administrado_por", "Poné"),

    # Bastón de faraón
    ("Bastón de faraón", "trata_a", "Estrés"),
    ("Bastón de faraón", "trata_a", "Migraña"),
    ("Bastón de faraón", "trata_a", "Inflamación de ovarios"),
    ("Bastón de faraón", "usa_parte", "Flor"),
    ("Bastón de faraón", "preparado_como", "Extracto macerado"),

    # Bejuco
    ("Bejuco", "trata_a", "Inicio de párkinson"),
    ("Bejuco", "trata_a", "Picadura de insectos"),
    ("Bejuco", "usa_parte", "Corteza"),

    # Biblia
    ("Biblia", "trata_a", "Trastornos de los nervios"),
    ("Biblia", "trata_a", "Diabetes"),
    ("Biblia", "trata_a", "Triglicéridos"),
    ("Biblia", "usa_parte", "Hojas"),
    ("Biblia", "preparado_como", "Infusión"),

    # Caña agria
    ("Caña agria", "trata_a", "Problemas renales"),
    ("Caña agria", "trata_a", "Infección dental"),
    ("Caña agria", "usa_parte", "Tallo"),

    # Hierba de serpiente
    ("Hierba de serpiente", "trata_a", "Picadura de serpiente"),
    ("Hierba de serpiente", "trata_a", "Picadura de insectos"),
    ("Hierba de serpiente", "usa_parte", "Hojas"),
    ("Hierba de serpiente", "preparado_como", "Infusión de hojas maceradas"),

    # Espasmo de arco (Punta lanza)
    ("Espasmo de arco", "trata_a", "Mordedura de serpiente"),
    ("Espasmo de arco", "trata_a", "Hemorragias"),
    ("Espasmo de arco", "trata_a", "Dolor de articulaciones"),
    ("Espasmo de arco", "usa_parte", "Hojas"),
    ("Espasmo de arco", "preparado_como", "Macerado con aguardiente y ruda"),

    # Matico
    ("Matico", "trata_a", "Gastritis"),
    ("Matico", "trata_a", "Infección intestinal"),
    ("Matico", "usa_parte", "Hojas"),
    ("Matico", "preparado_como", "Baños desinflamantes"),

    # Ortiga brava
    ("Ortiga brava", "trata_a", "Inflamación de la vista"),
    ("Ortiga brava", "trata_a", "Diarrea"),
    ("Ortiga brava", "usa_parte", "Hojas"),
    ("Ortiga brava", "usa_parte", "Raíz"),

    # Uña de gato
    ("Uña de gato", "trata_a", "Inflamación de la próstata"),
    ("Uña de gato", "trata_a", "Resfríos"),
    ("Uña de gato", "usa_parte", "Tallo"),
    ("Uña de gato", "preparado_como", "Cocción de tallo"),

    # Zaragoza
    ("Zaragoza", "trata_a", "Mordedura de serpientes"),
    ("Zaragoza", "trata_a", "Picadura de insectos"),
    ("Zaragoza", "usa_parte", "Liana"),
    ("Zaragoza", "preparado_como", "Maceración con licor y espasmo de arco")
]

for s, r, o in farmacopea:
    agregar(s, r, o)

# =========================================================================
# 3. RECETAS CEREMONIALES
# =========================================================================
recetas = [
    ("Don'bada Kapi", "preparado_como", "Té de raíces hervidas con piedras de río"),
    ("Don'bada Kapi", "administrado_por", "Poné"),
    ("Muturu'pi", "trata_a", "Desintoxicación corporal"),
    ("Muturu'pi", "usa_parte", "Hojas de múturu"),
    ("Uru Mala", "preparado_como", "Chicha de yuca fermentada en hoja de bijao"),
    ("Yo'mala", "preparado_como", "Chicha ceremonial con hongo oreja de cerdo y maíz"),
    ("Kanthi Pi", "usa_parte", "Hojas de tabaco"),
    ("Kanthi Pi", "administrado_por", "Poné")
]

for s, r, o in recetas:
    agregar(s, r, o)

# =========================================================================
# CONSOLIDAR CON ARCHIVO EXISTENTE
# =========================================================================
tripletas_existentes = []
if os.path.exists(ARCHIVO_SALIDA_TRIPLETAS):
    try:
        with open(ARCHIVO_SALIDA_TRIPLETAS, "r", encoding="utf-8") as f:
            tripletas_existentes = json.load(f)
    except Exception:
        tripletas_existentes = []

# Unir y deduplicar
claves_vistas = set()
resultado_final = []

for t in tripletas_existentes + tripletas_unishu:
    clave = (t.get("sujeto", "").lower().strip(), 
             t.get("relacion", "").lower().strip(), 
             t.get("objeto", "").lower().strip())
    if clave not in claves_vistas and len(clave[0]) > 0:
        claves_vistas.add(clave)
        resultado_final.append(t)

with open(ARCHIVO_SALIDA_TRIPLETAS, "w", encoding="utf-8") as f:
    json.dump(resultado_final, f, ensure_ascii=False, indent=2)

print("=" * 60)
print(f"ÉXITO: Se estructuró el conocimiento completo de UNI-SHU.")
print(f"- Tripletas propias de UNI-SHU añadidas: {len(tripletas_unishu)}")
print(f"- Total consolidado en 'tripletas_extraidas.json': {len(resultado_final)}")
print("=" * 60)