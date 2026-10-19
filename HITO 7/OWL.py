import os
import json
import re
from xml.sax.saxutils import escape

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
ARCHIVO_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")
ARCHIVO_SALIDA_OWL = os.path.join(DIRECTORIO_ACTUAL, "ontologia_tsachila.owl")

RECETAS_CONOCIDAS = {
    "don'bada kapi", "muturu'pi", "uru mala", "yo'mala", 
    "kanthi pi", "mu queká", "pa copí", "kon konla pi", "pinku daka´pi", "boro mala"
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

def clasificar_relacion_y_objeto(relacion: str, objeto: str):
    rel = relacion.lower().strip()
    obj_clean = normalizar_texto(objeto)
    
    if rel == "trata_a":
        return "trataA", "Patologia"
    elif rel == "usa_parte":
        return "usaParte", "PartePlanta"
    elif rel == "preparado_como":
        return "preparadoComo", "Preparacion"
    elif rel == "pertenece_a_familia":
        return "perteneceAFamilia", "FamiliaBotanica"
    elif rel == "nombre_tsafiqui":
        return "tieneNombreTsafiqui", "NombreTsafiqui"
    elif rel == "nombre_cientifico":
        return "tieneNombreCientifico", "NombreCientifico"
    elif rel == "administrado_por":
        if "baño" in obj_clean.lower() or "infusion" in obj_clean.lower():
            return "preparadoComo", "Preparacion"
        return "administradoPor", "Actor"
    else:
        return sanitizar_id(rel), "Concepto"

def generar_owl():
    if not os.path.exists(ARCHIVO_TRIPLETAS):
        print(f"Error: No se encontró {ARCHIVO_TRIPLETAS}")
        return

    with open(ARCHIVO_TRIPLETAS, "r", encoding="utf-8") as f:
        tripletas = json.load(f)

    base_iri = "http://www.semanticweb.org/ontologia_tsachila#"

    # Conjuntos para recopilar individuos y declaraciones
    clases = {
        "Planta": "Entidad vegetal empleada en la medicina tradicional Tsáchila",
        "Patologia": "Enfermedad, síntoma o dolencia tratada",
        "PartePlanta": "Órgano vegetal utilizado (hojas, corteza, fruto, raíz, etc.)",
        "Preparacion": "Forma galénica o ritual de elaboración del remedio",
        "FamiliaBotanica": "Taxonomía botánica de las especies",
        "NombreTsafiqui": "Denominación vernácula en lengua tsáfiqui",
        "NombreCientifico": "Nomenclatura botánica binomial",
        "Receta": "Fórmula medicinal tradicional compuesta",
        "Actor": "Especialista o practicante tradicional de la salud (p. ej., Poné)"
    }

    propiedades = {
        "trataA": ("Planta", "Patologia"),
        "usaParte": ("Planta", "PartePlanta"),
        "preparadoComo": ("Planta", "Preparacion"),
        "perteneceAFamilia": ("Planta", "FamiliaBotanica"),
        "tieneNombreTsafiqui": ("Planta", "NombreTsafiqui"),
        "tieneNombreCientifico": ("Planta", "NombreCientifico"),
        "administradoPor": ("Planta", "Actor")
    }

    individuos = {}  # id_indiv -> {"label": str, "clase": str}
    relaciones_aserciones = [] # (sujeto_id, prop_name, objeto_id)

    for item in tripletas:
        sujeto = normalizar_texto(item.get("sujeto", ""))
        relacion = normalizar_texto(item.get("relacion", ""))
        objeto = normalizar_texto(item.get("objeto", ""))

        if not sujeto or not relacion or not objeto:
            continue

        id_sujeto = sanitizar_id(sujeto)
        id_objeto = sanitizar_id(objeto)

        clase_sujeto = "Receta" if sujeto.lower() in RECETAS_CONOCIDAS else "Planta"
        prop_owl, clase_objeto = clasificar_relacion_y_objeto(relacion, objeto)

        if id_sujeto not in individuos:
            individuos[id_sujeto] = {"label": sujeto, "clase": clase_sujeto}
        if id_objeto not in individuos:
            individuos[id_objeto] = {"label": objeto, "clase": clase_objeto}

        relaciones_aserciones.append((id_sujeto, prop_owl, id_objeto))

    # Construcción del documento OWL (RDF/XML)
    owl_xml = []
    owl_xml.append('<?xml version="1.0"?>')
    owl_xml.append('<rdf:RDF xmlns="' + base_iri + '"')
    owl_xml.append('     xml:base="' + base_iri + '"')
    owl_xml.append('     xmlns:owl="http://www.w3.org/2002/07/owl#"')
    owl_xml.append('     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"')
    owl_xml.append('     xmlns:xml="http://www.w3.org/XML/1998/namespace"')
    owl_xml.append('     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"')
    owl_xml.append('     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">')
    owl_xml.append('')
    owl_xml.append('    <owl:Ontology rdf:about="http://www.semanticweb.org/ontologia_tsachila">')
    owl_xml.append('        <rdfs:comment xml:lang="es">Ontología formal del Conocimiento Etnobotánico y Medicina Ancestral Tsáchila.</rdfs:comment>')
    owl_xml.append('        <rdfs:label xml:lang="es">Ontología Etnobotánica Tsáchila</rdfs:label>')
    owl_xml.append('    </owl:Ontology>')
    owl_xml.append('')

    # Declaración de Clases
    for cls_name, cls_doc in clases.items():
        owl_xml.append(f'    <owl:Class rdf:about="{base_iri}{cls_name}">')
        owl_xml.append(f'        <rdfs:label xml:lang="es">{escape(cls_name)}</rdfs:label>')
        owl_xml.append(f'        <rdfs:comment xml:lang="es">{escape(cls_doc)}</rdfs:comment>')
        owl_xml.append('    </owl:Class>')

    owl_xml.append('')

    # Declaración de Object Properties
    for prop_name, (domain, range_cls) in propiedades.items():
        owl_xml.append(f'    <owl:ObjectProperty rdf:about="{base_iri}{prop_name}">')
        owl_xml.append(f'        <rdfs:label xml:lang="es">{escape(prop_name)}</rdfs:label>')
        owl_xml.append(f'        <rdfs:domain rdf:resource="{base_iri}{domain}"/>')
        owl_xml.append(f'        <rdfs:range rdf:resource="{base_iri}{range_cls}"/>')
        owl_xml.append('    </owl:ObjectProperty>')

    owl_xml.append('')

    # Declaración de Individuos (Named Individuals)
    for ind_id, ind_info in individuos.items():
        owl_xml.append(f'    <owl:NamedIndividual rdf:about="{base_iri}{ind_id}">')
        owl_xml.append(f'        <rdf:type rdf:resource="{base_iri}{ind_info["clase"]}"/>')
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

    print(f"¡Ontología exportada con éxito!")
    print(f"Archivo generado: {ARCHIVO_SALIDA_OWL}")
    print(f"Total Clases: {len(clases)}")
    print(f"Total Object Properties: {len(propiedades)}")
    print(f"Total Individuos: {len(individuos)}")
    print(f"Total Aserciones de Relaciones: {len(relaciones_aserciones)}")

if __name__ == "__main__":
    generar_owl()