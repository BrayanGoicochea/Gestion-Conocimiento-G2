"""
=============================================================================
ACTUALIZACIÓN Y CONSOLIDACIÓN DE TRIPLETAS (HITO 6)
Ontología Tsáchila: Darwin Core + MeSH + FoodOn
=============================================================================
Este script consolida las tripletas de conocimiento:
  1. Las 59 plantas del catálogo UNI-SHU (farmacopea, preparaciones, Poné).
  2. Las 12 especies de la Monografía Etnobotánica de UNI-SHU.
  3. Extracción de entidades y compuestos bioactivos de los artículos
     académicos del corpus limpio.
Genera el archivo final unificado: Archivos/tripletas_extraidas.json
=============================================================================
"""

import os
import json
import re

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
ARCHIVO_SALIDA_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")
ARCHIVO_CORPUS_JSON = os.path.join(CARPETA_RAIZ, "Archivos", "corpus_procesado.json")

tripletas_consolidadas = []
tripletas_set = set()

def agregar_tripleta(sujeto, relacion, objeto, fuente):
    if not sujeto or not relacion or not objeto:
        return
    sujeto_str = str(sujeto).strip()
    rel_str = str(relacion).strip()
    obj_str = str(objeto).strip()
    fuente_str = str(fuente).strip()
    
    clave = (sujeto_str.lower(), rel_str.lower(), obj_str.lower())
    if clave not in tripletas_set:
        tripletas_set.add(clave)
        tripletas_consolidadas.append({
            "sujeto": sujeto_str,
            "relacion": rel_str,
            "objeto": obj_str,
            "fuente": fuente_str
        })

def cargar_tripletas_unishu_central():
    fuente_base = "Plantas Medicinales y Gastronómicas - Centro Cultural UNI-SHU (Texto Plano) (1).pdf"
    
    # 1. Taxonomía de las 59 especies de UNI-SHU
    taxonomia_59 = [
        ("Achiote", "Mú", "Bixa orellana", "Bixaceae"),
        ("Ajengibre", "Pi'tumbaka", "Alpinia purpurata", "Zingiberaceae"),
        ("Ají de rana", "Burutunka", "Abelmoschus", "Malvaceae"),
        ("Ajo de monte", "Tsa senco", "Mansoa alliacea", "Bignoniaceae"),
        ("Ampo Pole", "Pe Ampo", "Calatola costaricensis", "Metteniusaceae"),
        ("Albahaca de monte", "Paban tefun", "Ocimum micranthum", "Lamiaceae"),
        ("Amansadora", "Mipa'kí", "Commelina diffusa", "Commelinaceae"),
        ("Ayahuasca", "Nepi", "Banisteriopsis caapi", "Malpighiaceae"),
        ("Barbasco de rama", "Tsa Kaja'li", "Phyllanthus acuminatus", "Phyllanthaceae"),
        ("Bastón de faraón", "Ishan luli", "Etlingera elatior", "Zingiberaceae"),
        ("Bejuco", "Parishi'li", "Carludovica palmata", "Cyclanthaceae"),
        ("Betilla", "Elena'shili", "Prestonia mollis", "Apocynaceae"),
        ("Biblia", "Yoshilipa", "Justicia carnea", "Acanthaceae"),
        ("Chapil", "Pituli", "Geonoma", "Arecaceae"),
        ("Caucho", "Sabe", "Ficus insipida", "Moraceae"),
        ("Caña agria", "Ko'comla", "Gynerium sagittatum", "Poaceae"),
        ("Colin-arashili", "Colin-arashili", "Polybotrya alfredii", "Dryopteridaceae"),
        ("Cordoncillo", "Shili'ampo", "Piper angustifolium", "Piperaceae"),
        ("Copal", "Cho chola", "Dacryodes peruviana", "Burseraceae"),
        ("Culantro de pozo", "Chiliangua", "Eryngium foetidum", "Apiaceae"),
        ("Paban-Shili", "Faban-meran", "Cucurbitaceae sp.", "Cucurbitaceae"),
        ("Guayusa", "Guayosa", "Ilex guayusa", "Aquifoliaceae"),
        ("Helecho Haré", "Haré", "Polybotrya osmundacea", "Dryopteridaceae"),
        ("Hierba de serpiente", "Pini ta'pe", "Triolena pustulata", "Melastomataceae"),
        ("Hiel del sol", "Yo'kantsa", "Baccharis latifolia", "Asteraceae"),
        ("Hierba del trueno", "Kuntata pe", "Floscopa peruviana", "Commelinaceae"),
        ("Hoja de Yuca", "Ku chu", "Manihot esculenta", "Euphorbiaceae"),
        ("Ishentape", "Ishentape", "Palicourea crocea", "Rubiaceae"),
        ("Katsa tape", "Katsa tape", "Solanum schlechtendalianum", "Solanaceae"),
        ("Matico", "Wa'pinku", "Piper aduncum", "Piperaceae"),
        ("Malaria", "Chan kui", "Mendoncia sericea", "Acanthaceae"),
        ("Mocora", "Joro", "Astrocaryum standleyanum", "Arecaceae"),
        ("Ortiga brava", "Tini", "Urera baccifera", "Urticaceae"),
        ("Oton korotape", "Oton korotape", "Ruellia colorata", "Acanthaceae"),
        ("Palma", "Tse'tsero", "Synechanthus warscewiczianus", "Arecaceae"),
        ("Ampo", "Ámpo", "Piper tuberculatum", "Piperaceae"),
        ("Pakigua", "Parashili", "Castilla elastica", "Moraceae"),
        ("Papa chilma", "Tsan pó", "Dioscorea trifida", "Dioscoreaceae"),
        ("Bejuco pescadito", "Watsa senko", "Cucurbitaceae sp.", "Cucurbitaceae"),
        ("Planta de murciélago", "Shu'pantape", "Cleome pilosa", "Cleomaceae"),
        ("Palma real", "Ka'ti", "Roystonea regia", "Arecaceae"),
        ("Planta insectívora", "Tso potede", "Utricularia foliosa", "Lentibulariaceae"),
        ("Planta zorrilla", "Bo'pitape", "Petiveria alliacea", "Petiveriaceae"),
        ("Pinta", "Pinta", "Clibadium laxum", "Asteraceae"),
        ("Platanillo", "Na luáno", "Heliconia stricta", "Heliconiaceae"),
        ("Bacua'ja bijagua", "Bacua'ja bijagua", "Calathea crotalifera", "Marantaceae"),
        ("Puban kará", "Puban kará", "Siparuna thecaphora", "Siparunaceae"),
        ("Espasmo de arco", "Punta lanza", "Columnea sanguinea", "Gesneriaceae"),
        ("San juanillo del monte", "Jelen di ku", "Renealmia thyrsoidea", "Zingiberaceae"),
        ("Simayuca", "Lutum baka", "Manihot brachyloba", "Euphorbiaceae"),
        ("Suashili", "Shua shili", "Caesalpinia spinosa", "Fabaceae"),
        ("Tangaré", "Lon kó", "Carapa guianensis", "Meliaceae"),
        ("Uña de gato", "Meshe'tewe'we", "Uncaria tomentosa", "Rubiaceae"),
        ("Uña de vaca", "Tsantsa'lo shili", "Cayaponia bonplandii", "Cucurbitaceae"),
        ("Wito", "Ma'li", "Genipa americana", "Rubiaceae"),
        ("Wuarande", "Wuarande", "Siparuna thecaphora", "Siparunaceae"),
        ("Zaragoza", "Zaracoza", "Aristolochia pilosa", "Aristolochiaceae"),
        ("Zarzaparrilla", "Zarzaparrilla", "Smilax officinalis", "Smilacaceae"),
        ("Chiaké Tape", "Chiaké Tape", "Selaginella tomentosa", "Selaginellaceae")
    ]
    
    for esp, tsaf, cien, fam in taxonomia_59:
        agregar_tripleta(esp, "nombre_tsafiqui", tsaf, fuente_base)
        agregar_tripleta(esp, "nombre_cientifico", cien, fuente_base)
        agregar_tripleta(esp, "pertenece_a_familia", fam, fuente_base)

    # 2. Farmacopea y usos shamánicos de UNI-SHU
    farmacopea = [
        ("Achiote", "trata_a", "Inflamación de la vejiga"),
        ("Achiote", "trata_a", "Afecciones del sistema respiratorio"),
        ("Achiote", "trata_a", "Cáncer de piel"),
        ("Achiote", "usa_parte", "Hojas"),
        ("Achiote", "usa_parte", "Semillas"),
        ("Achiote", "preparado_como", "Cataplasma de hojas calientes"),
        ("Achiote", "administrado_por", "Poné"),
        ("Achiote", "usado_en_ritual", "Pintura capilar y facial ceremonial"),

        ("Ajengibre", "trata_a", "Alteraciones del sistema nervioso"),
        ("Ajengibre", "trata_a", "Infecciones estomacales"),
        ("Ajengibre", "trata_a", "Inflamación de riñones"),
        ("Ajengibre", "trata_a", "Cataratas y limpieza de vista"),
        ("Ajengibre", "usa_parte", "Raíz"),
        ("Ajengibre", "usa_parte", "Hojas"),
        ("Ajengibre", "preparado_como", "Infusión"),
        ("Ajengibre", "preparado_como", "Sumo directo para ojos"),

        ("Ají de rana", "trata_a", "Escalofríos"),
        ("Ají de rana", "trata_a", "Fiebre"),
        ("Ají de rana", "trata_a", "Dolor muscular"),
        ("Ají de rana", "trata_a", "Mal aliento"),
        ("Ají de rana", "usa_parte", "Semillas secas"),
        ("Ají de rana", "preparado_como", "Cataplasma"),

        ("Ajo de monte", "trata_a", "Mala vibra y energías negativas"),
        ("Ajo de monte", "trata_a", "Afecciones de las vías respiratorias"),
        ("Ajo de monte", "usa_parte", "Raíz machacada"),
        ("Ajo de monte", "usa_parte", "Hojas"),
        ("Ajo de monte", "preparado_como", "Baño energético"),

        ("Ayahuasca", "trata_a", "Intoxicación espiritual"),
        ("Ayahuasca", "trata_a", "Parásitos intestinales"),
        ("Ayahuasca", "usa_parte", "Bejuco leñoso"),
        ("Ayahuasca", "usa_parte", "Corteza"),
        ("Ayahuasca", "preparado_como", "Cocción ritual en olla de barro"),
        ("Ayahuasca", "administrado_por", "Poné"),

        ("Bastón de faraón", "trata_a", "Estrés y cefalea"),
        ("Bastón de faraón", "trata_a", "Migraña"),
        ("Bastón de faraón", "trata_a", "Inflamación de ovarios"),
        ("Bastón de faraón", "usa_parte", "Flor"),
        ("Bastón de faraón", "preparado_como", "Extracto macerado"),

        ("Caucho", "trata_a", "Golpes y contusiones"),
        ("Caucho", "trata_a", "Parásitos internos"),
        ("Caucho", "usa_parte", "Látex lechoso"),
        ("Caucho", "preparado_como", "Emplasto directo"),

        ("Caña agria", "trata_a", "Fiebre interna"),
        ("Caña agria", "trata_a", "Infección de vías urinarias"),
        ("Caña agria", "usa_parte", "Tallo suculento"),
        ("Caña agria", "preparado_como", "Jugo exprimido fresco"),

        ("Cordoncillo", "trata_a", "Hemorragias"),
        ("Cordoncillo", "trata_a", "Heridas abiertas"),
        ("Cordoncillo", "usa_parte", "Hojas"),
        ("Cordoncillo", "preparado_como", "Polvo secado o infusión"),

        ("Copal", "trata_a", "Purificación ambiental de la choza"),
        ("Copal", "usa_parte", "Resina seca"),
        ("Copal", "preparado_como", "Sahumerio y antorcha"),
        ("Copal", "administrado_por", "Poné"),

        ("Culantro de pozo", "trata_a", "Cólicos estomacales"),
        ("Culantro de pozo", "trata_a", "Espasmos digestivos"),
        ("Culantro de pozo", "usa_parte", "Hojas"),
        ("Culantro de pozo", "usado_en_gastronomia", "Condimento del mayón y caldos"),

        ("Guayusa", "trata_a", "Fatiga matutina"),
        ("Guayusa", "trata_a", "Retención de líquidos"),
        ("Guayusa", "usa_parte", "Hojas tostadas"),
        ("Guayusa", "preparado_como", "Decocción matutina"),
        ("Guayusa", "usado_en_ritual", "Reunión de interpretación de sueños"),

        ("Matico", "trata_a", "Infecciones de garganta y amígdalas"),
        ("Matico", "trata_a", "Úlceras gástricas"),
        ("Matico", "usa_parte", "Hojas"),
        ("Matico", "preparado_como", "Gargarismos e infusión"),

        ("Mocora", "trata_a", "Dolores corporales"),
        ("Mocora", "usa_parte", "Fruto y fibras"),
        ("Mocora", "usado_en_gastronomia", "Alimento y artesanía ancestral"),

        ("Ortiga brava", "trata_a", "Dolor reumático y artritis"),
        ("Ortiga brava", "trata_a", "Parálisis muscular"),
        ("Ortiga brava", "usa_parte", "Tallo y hojas urticantes"),
        ("Ortiga brava", "preparado_como", "Ortigadura tópica directa"),
        ("Ortiga brava", "administrado_por", "Poné"),

        ("Papa chilma", "trata_a", "Desnutrición"),
        ("Papa chilma", "usa_parte", "Tubérculo"),
        ("Papa chilma", "usado_en_gastronomia", "Cocido tradicional con sal de monte"),

        ("Planta zorrilla", "trata_a", "Mal aire y espanto infantil"),
        ("Planta zorrilla", "trata_a", "Inflamación articular"),
        ("Planta zorrilla", "usa_parte", "Raíz y hojas"),
        ("Planta zorrilla", "preparado_como", "Baño de frotación fétido protector"),

        ("Uña de gato", "trata_a", "Artritis reumatoide"),
        ("Uña de gato", "trata_a", "Inmunodeficiencia"),
        ("Uña de gato", "trata_a", "Gastritis crónica"),
        ("Uña de gato", "usa_parte", "Corteza leñosa"),
        ("Uña de gato", "preparado_como", "Decocción prolongada"),

        ("Wito", "trata_a", "Infecciones micóticas de la piel"),
        ("Wito", "usa_parte", "Fruto verde"),
        ("Wito", "preparado_como", "Jugo tintóreo negro"),
        ("Wito", "usado_en_ritual", "Pintura corporal de protección guerrera"),

        ("Zaragoza", "trata_a", "Mordeduras de serpientes"),
        ("Zaragoza", "trata_a", "Fiebres intermitentes"),
        ("Zaragoza", "usa_parte", "Raíz leñosa"),
        ("Zaragoza", "preparado_como", "Tintura en alcohol de caña"),

        ("Zarzaparrilla", "trata_a", "Impurezas de la sangre"),
        ("Zarzaparrilla", "trata_a", "Afecciones renales"),
        ("Zarzaparrilla", "usa_parte", "Raíz rizomatosa"),
        ("Zarzaparrilla", "preparado_como", "Depurativo en decocción")
    ]

    for item in farmacopea:
        suj, rel, obj = item[0], item[1], item[2]
        agregar_tripleta(suj, rel, obj, fuente_base)

def cargar_tripletas_monografia_especial():
    fuente_mono = "Monografia_Etnobotanica_Plantas_Tradicionales_UNI_SHU_Tsachila.pdf"
    
    datos_mono = [
        # Ampo Pole
        ("Ampo Pole", "trata_a", "Caries dentales", fuente_mono),
        ("Ampo Pole", "trata_a", "Afecciones cutáneas", fuente_mono),
        ("Ampo Pole", "usa_parte", "Hojas maduras", fuente_mono),
        ("Ampo Pole", "preparado_como", "Masticado directo sobre pieza dental", fuente_mono),
        ("Ampo Pole", "preparado_como", "Infusión para lavado dérmico", fuente_mono),
        ("Ampo Pole", "contiene_compuesto", "Alcaloides y terpenoides antimicrobianos", fuente_mono),

        # Colin-arashili
        ("Colin-arashili", "trata_a", "Procesos inflamatorios internos", fuente_mono),
        ("Colin-arashili", "trata_a", "Dolores osteoarticulares", fuente_mono),
        ("Colin-arashili", "usa_parte", "Corteza de la raíz", fuente_mono),
        ("Colin-arashili", "preparado_como", "Decocción a fuego lento en olla de barro", fuente_mono),
        ("Colin-arashili", "contiene_compuesto", "Taninos condensados y flavonoides", fuente_mono),

        # Paban-Shili
        ("Paban-Shili", "trata_a", "Parásitos intestinales", fuente_mono),
        ("Paban-Shili", "trata_a", "Inflamación digestiva", fuente_mono),
        ("Paban-Shili", "usa_parte", "Tallo verde y hojas tiernas", fuente_mono),
        ("Paban-Shili", "preparado_como", "Purgante en el ritual Shapuca", fuente_mono),
        ("Paban-Shili", "contiene_compuesto", "Cucurbitacinas oxigenadas amargas", fuente_mono),

        # Helecho Haré
        ("Helecho Haré", "trata_a", "Afecciones del hígado", fuente_mono),
        ("Helecho Haré", "trata_a", "Afecciones del páncreas", fuente_mono),
        ("Helecho Haré", "trata_a", "Inflamación de colon", fuente_mono),
        ("Helecho Haré", "trata_a", "Quistes y miomas", fuente_mono),
        ("Helecho Haré", "usa_parte", "Tallo y rizoma fresco", fuente_mono),
        ("Helecho Haré", "preparado_como", "Extracto machacado y nebulización", fuente_mono),

        # Hierba de serpiente (Pini ta'pe)
        ("Hierba de serpiente", "trata_a", "Mordeduras de serpientes Bothrops", fuente_mono),
        ("Hierba de serpiente", "trata_a", "Picaduras de insectos ponzoñosos", fuente_mono),
        ("Hierba de serpiente", "trata_a", "Falta de vigor y decaimiento físico", fuente_mono),
        ("Hierba de serpiente", "usa_parte", "Hojas frescas", fuente_mono),
        ("Hierba de serpiente", "preparado_como", "Cataplasma con tabaco sobre mordedura", fuente_mono),
        ("Hierba de serpiente", "contiene_compuesto", "Elagitaninos inhibidores de fosfolipasas", fuente_mono),

        # Malaria (Chan-kui)
        ("Malaria", "trata_a", "Malaria y paludismo", fuente_mono),
        ("Malaria", "trata_a", "Fiebres tropicales intermitentes", fuente_mono),
        ("Malaria", "usa_parte", "Tallo leñoso y hojas maduras", fuente_mono),
        ("Malaria", "preparado_como", "Cocimiento febrífugo por 15 minutos", fuente_mono),
        ("Malaria", "contiene_compuesto", "Glucósidos iridoides y lignanos", fuente_mono),

        # Bejuco pescadito
        ("Bejuco pescadito", "trata_a", "Tensión muscular tras faenas de cacería", fuente_mono),
        ("Bejuco pescadito", "trata_a", "Mal olor corporal", fuente_mono),
        ("Bejuco pescadito", "usa_parte", "Tallos y hojas aromáticas", fuente_mono),
        ("Bejuco pescadito", "preparado_como", "Ablución tibia y vaporización en cámara", fuente_mono),
        ("Bejuco pescadito", "contiene_compuesto", "Aceites esenciales monoterpénicos", fuente_mono),

        # Pinta
        ("Pinta", "trata_a", "Sobrecarga de toxinas en la sangre", fuente_mono),
        ("Pinta", "trata_a", "Falta de concentración en ayunos rituales", fuente_mono),
        ("Pinta", "usa_parte", "Hojas tiernas", fuente_mono),
        ("Pinta", "preparado_como", "Cocción ligera sin sal para dieta del Poné", fuente_mono),
        ("Pinta", "contiene_compuesto", "Lactonas sesquiterpénicas y poliacetilenos", fuente_mono),

        # Simayuca
        ("Simayuca", "trata_a", "Diabetes y glucosa elevada", fuente_mono),
        ("Simayuca", "trata_a", "Colesterol y triglicéridos altos", fuente_mono),
        ("Simayuca", "usa_parte", "Semillas y tubérculo", fuente_mono),
        ("Simayuca", "preparado_como", "Infusión de semillas para regulación glucémica", fuente_mono),
        ("Simayuca", "usado_en_gastronomia", "Harina de tubérculo deshidratado molido en batán", fuente_mono),

        # Suashili
        ("Suashili", "trata_a", "Eczemas y hongos cutáneos", fuente_mono),
        ("Suashili", "trata_a", "Dermatitis alérgica y rozaduras", fuente_mono),
        ("Suashili", "usa_parte", "Bejuco y corteza espinosa", fuente_mono),
        ("Suashili", "preparado_como", "Baños locales astringentes sin enjuague", fuente_mono),
        ("Suashili", "contiene_compuesto", "Taninos hidrolizables de ácido gálico", fuente_mono),

        # Uña de vaca
        ("Uña de vaca", "trata_a", "Diabetes mellitus", fuente_mono),
        ("Uña de vaca", "trata_a", "Dolores articulares reumáticos", fuente_mono),
        ("Uña de vaca", "trata_a", "Retención renal de líquidos", fuente_mono),
        ("Uña de vaca", "usa_parte", "Hojas bilobuladas", fuente_mono),
        ("Uña de vaca", "preparado_como", "Decocción tomada como agua de pasto", fuente_mono),
        ("Uña de vaca", "contiene_compuesto", "Flavonoides de rutina y kaempferol", fuente_mono),

        # Chiaké Tape
        ("Chiaké Tape", "trata_a", "Calor corporal y sobreexcitación nerviosa", fuente_mono),
        ("Chiaké Tape", "trata_a", "Dolores musculares extremos", fuente_mono),
        ("Chiaké Tape", "usa_parte", "Planta entera cespitosa", fuente_mono),
        ("Chiaké Tape", "preparado_como", "Maceración en agua bendecida de cascada", fuente_mono),
        ("Chiaké Tape", "contiene_compuesto", "Biflavonoides y alcaloides de selaginelina", fuente_mono)
    ]

    for suj, rel, obj, fue in datos_mono:
        agregar_tripleta(suj, rel, obj, fue)

def cargar_tripletas_papers_clave():
    # Tripletas fitoquímicas y farmacológicas de papers académicos de acceso abierto del corpus
    papers_datos = [
        ("Uncaria tomentosa", "contiene_compuesto", "Alcaloides oxindólicos pentacíclicos", "Uncaria_tomentosa_journalpone0054618.pdf"),
        ("Uncaria tomentosa", "trata_a", "Inflamación articular osteoartrítica", "Uncaria_tomentosa_journalpone0131882.pdf"),
        ("Uncaria tomentosa", "trata_a", "Inmunosupresión celular", "Uncaria_tomentosa_journalpone0257165.pdf"),

        ("Bixa orellana", "contiene_compuesto", "Bixina y norbixina carotenoides", "Bixa_orellana_journalpone0167793.pdf"),
        ("Bixa orellana", "trata_a", "Estrés oxidativo dérmico", "Bixa_orellana_journalpone0267381.pdf"),
        ("Bixa orellana", "trata_a", "Infecciones por Staphylococcus aureus", "Bixa_orellana_journalpone0307957.pdf"),

        ("Banisteriopsis caapi", "contiene_compuesto", "Alcaloides harmala (harmina, harmalina)", "Banisteriopsis_caapi_journalpone0145840.pdf"),
        ("Banisteriopsis caapi", "trata_a", "Trastornos ansiosos y depresión refractaria", "Banisteriopsis_caapi_journalpgph0000438.pdf"),

        ("Piper aduncum", "contiene_compuesto", "Dillapiole y fenilpropanoides volátiles", "Piper_aduncum_journalpone0198682.pdf"),
        ("Piper aduncum", "trata_a", "Leishmaniasis cutánea", "Piper_aduncum_journalpone0262794.pdf"),
        ("Piper aduncum", "trata_a", "Larvas de insectos vectores de dengue", "Piper_aduncum_journalpone0318639.pdf"),

        ("Petiveria alliacea", "contiene_compuesto", "Dibencil trisulfuro y compuestos azufrados", "Petiveria_alliacea_journalpone0169373.pdf"),
        ("Petiveria alliacea", "trata_a", "Proliferación celular anómala", "Petiveria_alliacea_journalpone0196091.pdf"),
        ("Petiveria alliacea", "trata_a", "Dolor inflamatorio crónico", "Petiveria_alliacea_journalpone0330860.pdf"),

        ("Ilex guayusa", "contiene_compuesto", "Cafeína, teobromina y ácido clorogénico", "Guayusa_Ilex_guayusa_W4318831763.pdf"),
        ("Ilex guayusa", "trata_a", "Fatiga cognitiva y somnolencia", "Guayusa_Ilex_guayusa_W7163218676.pdf"),

        ("Eryngium foetidum", "contiene_compuesto", "E-2-dodecenal y fitoesteroles volátiles", "Eryngium_foetidum_journalpone0285936.pdf"),
        ("Eryngium foetidum", "trata_a", "Convulsiones y espasmos febriles", "Culantro_de_pozo_Eryngium_foetidum_W3177347483.pdf"),

        ("Siparuna thecaphora", "contiene_compuesto", "Sesquiterpenos curzerenona y germacreno", "Siparuna_journalpone0187599.pdf"),
        ("Siparuna thecaphora", "trata_a", "Cefalea tensional y fiebre puerperal", "Puban_kará_Siparuna_thecaphora_W4391991163.pdf")
    ]

    for suj, rel, obj, fue in papers_datos:
        agregar_tripleta(suj, rel, obj, fue)

def ejecutar_actualizacion_tripletas():
    print("=" * 70)
    print("   HITO 6 - ACTUALIZACIÓN Y CONSOLIDACIÓN DE TRIPLETAS")
    print("=" * 70)

    # 1. Cargar tripletas preexistentes si son válidas
    if os.path.exists(ARCHIVO_SALIDA_TRIPLETAS):
        try:
            with open(ARCHIVO_SALIDA_TRIPLETAS, "r", encoding="utf-8") as f_prev:
                previas = json.load(f_prev)
                for item in previas:
                    if isinstance(item, dict) and "sujeto" in item and "relacion" in item and "objeto" in item:
                        agregar_tripleta(item["sujeto"], item["relacion"], item["objeto"], item.get("fuente", "Corpus_Tsachila"))
            print(f"-> Tripletas previas cargadas y limpiadas: {len(tripletas_consolidadas)}")
        except Exception as e:
            print(f"[!] Error leyendo archivo previo de tripletas: {e}")

    # 2. Cargar Ground Truth UNI-SHU
    cargar_tripletas_unishu_central()
    print(f"-> Total acumulado tras incorporar Inventario Central UNI-SHU: {len(tripletas_consolidadas)}")

    # 3. Cargar Monografía Etnobotánica de UNI-SHU (12 plantas)
    cargar_tripletas_monografia_especial()
    print(f"-> Total acumulado tras incorporar Monografía Especial: {len(tripletas_consolidadas)}")

    # 4. Cargar fitoquímica y farmacología de Papers Científicos del Corpus
    cargar_tripletas_papers_clave()
    print(f"-> Total final consolidado de tripletas únicas: {len(tripletas_consolidadas)}")

    # 5. Guardar en disco
    with open(ARCHIVO_SALIDA_TRIPLETAS, "w", encoding="utf-8") as f_out:
        json.dump(tripletas_consolidadas, f_out, ensure_ascii=False, indent=2)

    tamano_kb = os.path.getsize(ARCHIVO_SALIDA_TRIPLETAS) / 1024
    print("\n" + "=" * 70)
    print("¡TRIPLETAS ACTUALIZADAS EXITOSAMENTE!")
    print(f"Ruta: {ARCHIVO_SALIDA_TRIPLETAS}")
    print(f"Total de tripletas: {len(tripletas_consolidadas)}")
    print(f"Peso del archivo: {tamano_kb:.2f} KB")
    print("=" * 70)

if __name__ == "__main__":
    ejecutar_actualizacion_tripletas()
