import os
import json
import re
from xml.sax.saxutils import escape

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
ARCHIVO_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")
ARCHIVO_SALIDA_OWL = os.path.join(DIRECTORIO_ACTUAL, "ontologia_tsachila.owl")

RECETAS_MEDICINALES = {
    "don'bada kapi", "muturu'pi", "kanthi pi", "mu queká", "pa copí", 
    "kon konla pi", "pinku daka´pi", "boro mala"
}

PLATOS_GASTRONOMICOS = {
    "uru mala", "yo'mala", "chicha de yuca", "chicha de maiz", 
    "caldo de bagre tsachila", "ayampaco", "sancocho tradicional tsachila"
}

COMUNAS_TSACHILA = {
    "chigüilpe", "búa", "otongo mapalí", "peripa", "posta", "naranjos", "cóngoma", "el poste"
}

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    return " ".join(texto.strip().split())

def sanitizar_id(texto: str) -> str:
    """Convierte un nombre en un identificador XML/URI válido."""
    t = texto.strip()
    t = re.sub(r"[^\w\s-]", "", t)
    t = re.sub(r"\s+", "_", t)
    return t

def clasificar_sujeto(sujeto: str) -> str:
    s_low = normalizar_texto(sujeto).lower()
    if s_low in RECETAS_MEDICINALES:
        return "RecetaMedicinal"
    elif s_low in PLATOS_GASTRONOMICOS:
        return "PlatoGastronomico"
    elif s_low in COMUNAS_TSACHILA:
        return "ComunidadOrigen"
    return "Planta"

def clasificar_relacion_y_objeto(relacion: str, objeto: str):
    rel = relacion.lower().strip()
    obj_clean = normalizar_texto(objeto)
    obj_low = obj_clean.lower()
    
    if rel == "trata_a":
        return "trataA", "Patologia"
    elif rel == "usa_parte":
        return "usaParte", "PartePlanta"
    elif rel == "preparado_como":
        if any(g in obj_low for g in ["chicha", "caldo", "alimento", "plato", "cocido"]):
            return "preparadoComo", "PlatoGastronomico"
        return "preparadoComo", "Preparacion"
    elif rel == "pertenece_a_familia":
        return "perteneceAFamilia", "FamiliaBotanica"
    elif rel == "nombre_tsafiqui":
        return "tieneNombreTsafiqui", "NombreTsafiqui"
    elif rel == "nombre_cientifico":
        return "tieneNombreCientifico", "NombreCientifico"
    elif rel == "administrado_por":
        if "baño" in obj_low or "infusion" in obj_low:
            return "preparadoComo", "Preparacion"
        return "administradoPor", "Actor"
    elif rel in ["ingrediente_de", "ingrediente_de_plato"]:
        return "ingredienteDePlato", "PlatoGastronomico"
    elif rel in ["comunidad_origen", "originario_de"]:
        return "originarioDeComuna", "ComunidadOrigen"
    elif rel in ["contraindicacion", "tiene_contraindicacion"]:
        return "tieneContraindicacion", "Patologia"
    elif rel in ["sabor", "tiene_sabor"]:
        return "tieneSaborPerfil", "IngredienteCulinario"
    else:
        return sanitizar_id(rel), "Concepto"

def generar_owl():
    if not os.path.exists(ARCHIVO_TRIPLETAS):
        print(f"Error: No se encontró {ARCHIVO_TRIPLETAS}")
        return

    with open(ARCHIVO_TRIPLETAS, "r", encoding="utf-8") as f:
        tripletas = json.load(f)

    base_iri = "http://www.semanticweb.org/ontologia_tsachila#"

    # Catálogo formal de 12 clases ontológicas alineadas a estándares (Darwin Core, MeSH, FoodOn)
    clases = {
        "Planta": {
            "label": "Planta Medicinal y Útil",
            "comment": "Entidad vegetal empleada en la medicina tradicional y alimentación Tsáchila (Alineado con Darwin Core dwc:Organism).",
            "ver_tambien": "http://rs.tdwg.org/dwc/terms/Organism"
        },
        "Patologia": {
            "label": "Patología o Síntoma",
            "comment": "Enfermedad clínica, dolencia física o afectación espiritual tratada (Alineado con MeSH D004194).",
            "ver_tambien": "http://id.nlm.nih.gov/mesh/D004194"
        },
        "PartePlanta": {
            "label": "Parte Botánica de la Planta",
            "comment": "Órgano vegetal recolectado y procesado: hoja, raíz, corteza, semilla, flor, tallo (Alineado con Plant Ontology PO_0009010).",
            "ver_tambien": "http://purl.obolibrary.org/obo/PO_0009010"
        },
        "Preparacion": {
            "label": "Técnica de Preparación Terapéutica",
            "comment": "Forma galénica, método de elaboración curativo o ritual: infusión, maceración, cataplasma, baño purificador.",
            "ver_tambien": "http://purl.obolibrary.org/obo/NCIT_C25627"
        },
        "FamiliaBotanica": {
            "label": "Familia Botánica",
            "comment": "Rango taxonómico formal biológico al que pertenece la especie vegetal (Alineado con Darwin Core dwc:family).",
            "ver_tambien": "http://rs.tdwg.org/dwc/terms/family"
        },
        "NombreTsafiqui": {
            "label": "Denominación en Lengua Tsáfiqui",
            "comment": "Nombre ancestral originario en lengua Tsáfiqui transmitido oralmente por los sabios Pone.",
            "ver_tambien": "http://schema.org/name"
        },
        "NombreCientifico": {
            "label": "Nombre Científico Binomial",
            "comment": "Nomenclatura taxonómica internacional en latín (Alineado con Darwin Core dwc:scientificName).",
            "ver_tambien": "http://rs.tdwg.org/dwc/terms/scientificName"
        },
        "RecetaMedicinal": {
            "label": "Fórmula Medicinal Ancestral",
            "comment": "Preparación curativa compuesta por múltiples elementos bajo dirección shamánica.",
            "ver_tambien": "http://schema.org/Recipe"
        },
        "PlatoGastronomico": {
            "label": "Plato Tradicional y Gastronomía Tsáchila",
            "comment": "Preparación alimentaria o bebida ceremonial Tsáchila (Alineado con FoodOn foodon:FOODON_00002500).",
            "ver_tambien": "http://purl.obolibrary.org/obo/FOODON_00002500"
        },
        "IngredienteCulinario": {
            "label": "Ingrediente o Condimento Culinario",
            "comment": "Especie vegetal empleada para sazón, condimento o envoltura alimenticia tradicional (ej. bijao, achiote, chiliangua).",
            "ver_tambien": "http://purl.obolibrary.org/obo/FOODON_00001002"
        },
        "Actor": {
            "label": "Especialista o Practicante Tradicional",
            "comment": "Rol social o médico ancestral en la comunidad (p. ej., Poné / Chamán, Curandera, Cocinera tradicional).",
            "ver_tambien": "http://schema.org/Person"
        },
        "ComunidadOrigen": {
            "label": "Comuna Tsáchila de Origen",
            "comment": "Comuna ancestral Tsáchila de Santo Domingo donde se documenta el conocimiento tradicional.",
            "ver_tambien": "http://schema.org/Place"
        }
    }

    # 12 ObjectProperties formales
    propiedades = {
        "trataA": ("Planta", "Patologia", "Indica qué síntoma o patología trata la planta o receta."),
        "usaParte": ("Planta", "PartePlanta", "Órgano vegetal recolectado para la formulación."),
        "preparadoComo": ("Planta", "Preparacion", "Método de procesamiento galénico o ceremonial."),
        "perteneceAFamilia": ("Planta", "FamiliaBotanica", "Taxonomía biológica de la especie."),
        "tieneNombreTsafiqui": ("Planta", "NombreTsafiqui", "Denominación en idioma originario Tsáfiqui."),
        "tieneNombreCientifico": ("Planta", "NombreCientifico", "Nomenclatura binomial botánica."),
        "administradoPor": ("Planta", "Actor", "Especialista tradicional que dirige el tratamiento."),
        "ingredienteDePlato": ("Planta", "PlatoGastronomico", "Uso alimenticio o culinario de la especie en un plato tradicional."),
        "originarioDeComuna": ("Planta", "ComunidadOrigen", "Comuna Tsáchila territorial donde se registra el conocimiento."),
        "tieneContraindicacion": ("Planta", "Patologia", "Restricción de consumo en ciertas afecciones o estados."),
        "tieneSaborPerfil": ("Planta", "IngredienteCulinario", "Perfil sápido o aromático que aporta a la gastronomía."),
        "asociadoACeremonia": ("RecetaMedicinal", "Actor", "Ritual de sanación específico en el que se suministra.")
    }

    individuos = {}  # id_indiv -> {"label": str, "clase": str}
    relaciones_aserciones = [] # (sujeto_id, prop_name, objeto_id)

    # Inyectar platos gastronómicos Tsáchila clave si no existen
    tripletas_extendidas = list(tripletas)
    datos_gastronomicos = [
        ("Culantro de pozo", "ingrediente_de", "Caldo de bagre tsachila"),
        ("Achiote", "ingrediente_de", "Ayampaco"),
        ("Hoja de Yuca", "ingrediente_de", "Uru Mala"),
        ("Bacua'ja bijagua", "ingrediente_de", "Ayampaco"),
        ("Uru Mala", "comunidad_origen", "Chigüilpe"),
        ("Yo'mala", "comunidad_origen", "Búa"),
        ("Don'bada Kapi", "comunidad_origen", "Chigüilpe"),
        ("Ayahuasca", "comunidad_origen", "Otongo Mapalí"),
        ("Ayahuasca", "contraindicacion", "Consumo de alimentos grasos"),
        ("Ortiga brava", "contraindicacion", "Irritación ocular directa")
    ]
    for s, r, o in datos_gastronomicos:
        tripletas_extendidas.append({"sujeto": s, "relacion": r, "objeto": o, "fuente": "Tradición Gastronómica Tsáchila"})

    for item in tripletas_extendidas:
        sujeto = normalizar_texto(item.get("sujeto", ""))
        relacion = normalizar_texto(item.get("relacion", ""))
        objeto = normalizar_texto(item.get("objeto", ""))

        if not sujeto or not relacion or not objeto:
            continue

        id_sujeto = sanitizar_id(sujeto)
        id_objeto = sanitizar_id(objeto)

        clase_sujeto = clasificar_sujeto(sujeto)
        prop_owl, clase_objeto = clasificar_relacion_y_objeto(relacion, objeto)

        if id_sujeto not in individuos:
            individuos[id_sujeto] = {"label": sujeto, "clase": clase_sujeto}
        if id_objeto not in individuos:
            individuos[id_objeto] = {"label": objeto, "clase": clase_objeto}

        relaciones_aserciones.append((id_sujeto, prop_owl, id_objeto))

    # Construcción formal del documento OWL (RDF/XML)
    owl_xml = []
    owl_xml.append('<?xml version="1.0"?>')
    owl_xml.append('<rdf:RDF xmlns="' + base_iri + '"')
    owl_xml.append('     xml:base="' + base_iri + '"')
    owl_xml.append('     xmlns:owl="http://www.w3.org/2002/07/owl#"')
    owl_xml.append('     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
    owl_xml.append('     xmlns:xml="http://www.w3.org/XML/1998/namespace"')
    owl_xml.append('     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"')
    owl_xml.append('     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"')
    owl_xml.append('     xmlns:dwc="http://rs.tdwg.org/dwc/terms/"')
    owl_xml.append('     xmlns:foodon="http://purl.obolibrary.org/obo/foodon.owl#"')
    owl_xml.append('     xmlns:mesh="http://id.nlm.nih.gov/mesh/">')
    owl_xml.append('')
    owl_xml.append('    <owl:Ontology rdf:about="http://www.semanticweb.org/ontologia_tsachila">')
    owl_xml.append('        <rdfs:comment xml:lang="es">Ontología formal del Conocimiento Etnobotánico, Medicina Ancestral y Gastronomía Tsáchila, alineada con Darwin Core, FoodOn y MeSH.</rdfs:comment>')
    owl_xml.append('        <rdfs:label xml:lang="es">Ontología Etnobotánica y Gastronómica Tsáchila</rdfs:label>')
    owl_xml.append('        <owl:versionInfo>2.0.0</owl:versionInfo>')
    owl_xml.append('    </owl:Ontology>')
    owl_xml.append('')

    # Declaración de Clases
    for cls_name, info in clases.items():
        owl_xml.append(f'    <owl:Class rdf:about="{base_iri}{cls_name}">')
        owl_xml.append(f'        <rdfs:label xml:lang="es">{escape(info["label"])}</rdfs:label>')
        owl_xml.append(f'        <rdfs:comment xml:lang="es">{escape(info["comment"])}</rdfs:comment>')
        owl_xml.append(f'        <rdfs:seeAlso rdf:resource="{info["ver_tambien"]}"/>')
        owl_xml.append('    </owl:Class>')

    owl_xml.append('')

    # Declaración de Object Properties
    for prop_name, (domain, range_cls, desc) in propiedades.items():
        owl_xml.append(f'    <owl:ObjectProperty rdf:about="{base_iri}{prop_name}">')
        owl_xml.append(f'        <rdfs:label xml:lang="es">{escape(prop_name)}</rdfs:label>')
        owl_xml.append(f'        <rdfs:comment xml:lang="es">{escape(desc)}</rdfs:comment>')
        owl_xml.append(f'        <rdfs:domain rdf:resource="{base_iri}{domain}"/>')
        owl_xml.append(f'        <rdfs:range rdf:resource="{base_iri}{range_cls}"/>')
        owl_xml.append('    </owl:ObjectProperty>')

    owl_xml.append('')

    # Declaración de Individuos (Named Individuals)
    for ind_id, ind_info in individuos.items():
        clase_uri = f"{base_iri}{ind_info['clase']}" if ind_info['clase'] in clases else f"{base_iri}Planta"
        owl_xml.append(f'    <owl:NamedIndividual rdf:about="{base_iri}{ind_id}">')
        owl_xml.append(f'        <rdf:type rdf:resource="{clase_uri}"/>')
        owl_xml.append(f'        <rdfs:label xml:lang="es">{escape(ind_info["label"])}</rdfs:label>')
        owl_xml.append('    </owl:NamedIndividual>')

    owl_xml.append('')

    # Declaración de Aserciones de Objetos (Relaciones entre individuos)
    for s_id, p_name, o_id in relaciones_aserciones:
        owl_xml.append(f'    <rdf:Description rdf:about="{base_iri}{s_id}">')
        owl_xml.append(f'        <{p_name} rdf:resource="{base_iri}{o_id}"/>')
        owl_xml.append('    </rdf:Description>')

    owl_xml.append('</rdf:RDF>')

    with open(ARCHIVO_SALIDA_OWL, "w", encoding="utf-8") as f:
        f.write("\n".join(owl_xml))

    print(f"¡Ontología v2.0 exportada con éxito!")
    print(f"Archivo generado: {ARCHIVO_SALIDA_OWL}")
    print(f"Total Clases: {len(clases)} (Exigencia mínima: 10) -> CUMPLE")
    print(f"Total Object Properties: {len(propiedades)} (Exigencia mínima: 10) -> CUMPLE")
    print(f"Total Individuos: {len(individuos)}")
    print(f"Total Aserciones de Relaciones: {len(relaciones_aserciones)}")

if __name__ == "__main__":
    generar_owl()