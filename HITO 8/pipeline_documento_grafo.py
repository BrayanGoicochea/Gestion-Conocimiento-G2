"""
=============================================================================
HITO 8: FLUJO COMPLETO: DOCUMENTO -> GRAFO DE CONOCIMIENTO (PIPELINE ETL)
Asignatura: Gestión del Conocimiento (2011003) - UNMSM
Proyecto: Enterprise Brain - Etnobotánica y Gastronomía Tsáchila
=============================================================================
Este script implementa el flujo automatizado end-to-end:
  [Documento PDF/TXT] 
         │
         ▼  (1. Ingesta y Limpieza con PyMuPDF)
    [Texto Limpio]
         │
         ▼  (2. Extracción de Entidades y Relaciones con LLM / Ontología)
   [Tripletas Validadas]
         │
         ▼  (3. Carga Automatizada en Base de Datos de Grafos)
  [Neo4j AuraDB Poblado]
=============================================================================
"""

import os
import sys
import re
import json
import time
import fitz  # PyMuPDF
from neo4j import GraphDatabase
from groq import Groq

# ---------------------------------------------------------------------------
# CONFIGURACIÓN DE RUTAS Y CREDENCIALES
# ---------------------------------------------------------------------------
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
CARPETA_CORPUS = os.path.join(CARPETA_RAIZ, "Archivos", "corpus_rag_tsachila")
ARCHIVO_TRIPLETAS_GLOBAL = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")

# Credenciales de Servicios
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")
NEO4J_URI = os.environ.get("NEO4J_URI", "neo4j+s://0764d10c.databases.neo4j.io")
NEO4J_USER = os.environ.get("NEO4J_USER", "0764d10c")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "U9K2ZtRxhE3zBR_8LtGniLgxVt_2nr6XKnVT3AikSDY")

client_groq = Groq(api_key=GROQ_API_KEY)
MODELO_LLM = "qwen/qwen3.8-27b"

RECETAS_MEDICINALES = {
    "don'bada kapi", "muturu'pi", "kanthi pi", "mu queká", "pa copí", "boro mala"
}
PLATOS_GASTRONOMICOS = {
    "uru mala", "yo'mala", "chicha de yuca", "chicha de maiz", "caldo de bagre tsachila", "ayampaco"
}

# ===========================================================================
# PASO 1: INGESTA Y PARSING DEL DOCUMENTO (PyMuPDF)
# ===========================================================================
def extraer_y_limpiar_texto(ruta_archivo: str, max_paginas: int = 20) -> tuple[str, str]:
    """Extrae texto de PDF o TXT y aplica limpieza profunda."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No existe el archivo: {ruta_archivo}")

    nombre_fuente = os.path.basename(ruta_archivo)
    extension = os.path.splitext(nombre_fuente)[1].lower()
    texto_crudo = ""

    if extension == ".pdf":
        doc = fitz.open(ruta_archivo)
        total_pags = min(len(doc), max_paginas)
        paginas_texto = [doc[i].get_text("text") for i in range(total_pags)]
        doc.close()
        texto_crudo = "\n".join(paginas_texto)
    else:
        with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
            texto_crudo = f.read()

    # Normalización de texto
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto_crudo)
    texto = re.sub(r"\n\s*\n+", "\n\n", texto)
    lineas = [" ".join(p.split()) for p in texto.split("\n\n") if p.strip()]
    texto_limpio = "\n\n".join(lineas)
    texto_limpio = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", texto_limpio)

    return texto_limpio.strip(), nombre_fuente

# ===========================================================================
# PASO 2: EXTRACCIÓN DE TRIPLETAS CONTEXTUALIZADAS EN LA ONTOLOGÍA (LLM)
# ===========================================================================
PROMPT_EXTRACCION = """
Eres un especialista en extracción ontológica para grafos de conocimiento sobre etnobotánica y gastronomía Tsáchila.
Analiza el fragmento y extrae tripletas normalizadas de hechos científicos y tradicionales.

Relaciones admitidas estrictamente:
- "trata_a": (Planta|Receta) -> (Patologia / Dolencia)
- "usa_parte": (Planta) -> (PartePlanta: Hojas, Raíz, Semilla, Corteza, etc.)
- "preparado_como": (Planta|Receta) -> (Preparacion: Infusión, Cataplasma, Baño purificador, etc.)
- "pertenece_a_familia": (Planta) -> (FamiliaBotanica)
- "tiene_nombre_tsafiqui": (Planta) -> (NombreTsafiqui)
- "tiene_nombre_cientifico": (Planta) -> (NombreCientifico)
- "administrado_por": (Planta|Receta) -> (Actor: Poné, Chamán, Curandera)
- "ingrediente_de_plato": (Planta) -> (PlatoGastronomico: Chicha, Caldo, Ayampaco, etc.)

Devuelve un JSON estrictamente con la estructura:
{{"tripletas": [{{"sujeto": "...", "relacion": "...", "objeto": "..."}}]}}
Si no hay hechos botánicos o terapéuticos directos, devuelve {{"tripletas": []}}.

Fragmento:
\"\"\"{fragmento}\"\"\"
"""

def extraer_tripletas_bloque(texto_bloque: str, nombre_fuente: str) -> list[dict]:
    try:
        response = client_groq.chat.completions.create(
            model=MODELO_LLM,
            messages=[{"role": "user", "content": PROMPT_EXTRACCION.format(fragmento=texto_bloque)}],
            temperature=0.1,
            max_tokens=600,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        tripletas = data.get("tripletas", []) if isinstance(data, dict) else []
        resultado = []
        for t in tripletas:
            if isinstance(t, dict) and "sujeto" in t and "relacion" in t and "objeto" in t:
                t["fuente"] = nombre_fuente
                resultado.append(t)
        return resultado
    except Exception as e:
        return []

# ===========================================================================
# PASO 3: NORMALIZACIÓN ONTOLÓGICA Y MAPEO DE ETIQUETAS
# ===========================================================================
def mapear_etiquetas_ontologicas(sujeto: str, relacion: str, objeto: str) -> tuple[str, str, str]:
    s_clean = sujeto.strip()
    s_low = s_clean.lower()
    o_clean = objeto.strip()
    o_low = o_clean.lower()
    r_clean = relacion.strip().lower()

    # Etiqueta Sujeto
    if s_low in RECETAS_MEDICINALES:
        lbl_sujeto = "RecetaMedicinal"
    elif s_low in PLATOS_GASTRONOMICOS:
        lbl_sujeto = "PlatoGastronomico"
    else:
        lbl_sujeto = "Planta"

    # Etiqueta Relación y Objeto
    if r_clean == "trata_a":
        return lbl_sujeto, "TRATA_A", "Patologia"
    elif r_clean == "usa_parte":
        return lbl_sujeto, "USA_PARTE", "PartePlanta"
    elif r_clean == "preparado_como":
        if any(g in o_low for g in ["chicha", "caldo", "alimento", "plato"]):
            return lbl_sujeto, "PREPARADO_COMO", "PlatoGastronomico"
        return lbl_sujeto, "PREPARADO_COMO", "Preparacion"
    elif r_clean == "pertenece_a_familia":
        return lbl_sujeto, "PERTENECE_A_FAMILIA", "FamiliaBotanica"
    elif r_clean == "tiene_nombre_tsafiqui":
        return lbl_sujeto, "TIENE_NOMBRE_TSAFIQUI", "NombreTsafiqui"
    elif r_clean == "tiene_nombre_cientifico":
        return lbl_sujeto, "TIENE_NOMBRE_CIENTIFICO", "NombreCientifico"
    elif r_clean == "administrado_por":
        return lbl_sujeto, "ADMINISTRADO_POR", "Actor"
    elif r_clean in ["ingrediente_de_plato", "ingrediente_de"]:
        return lbl_sujeto, "INGREDIENTE_DE_PLATO", "PlatoGastronomico"
    else:
        return lbl_sujeto, r_clean.upper().replace(" ", "_"), "Concepto"

# ===========================================================================
# PASO 4: CARGA AUTOMATIZADA EN NEO4J AURADB
# ===========================================================================
def ingestar_tripletas_neo4j(tripletas: list[dict]) -> int:
    if not tripletas:
        return 0

    print(f"\n[Neo4j] Conectando a AuraDB para ingestar {len(tripletas)} tripletas...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    cargadas = 0

    with driver.session() as session:
        # Asegurar restricciones
        labels = [
            "Planta", "Patologia", "PartePlanta", "Preparacion", 
            "FamiliaBotanica", "NombreTsafiqui", "NombreCientifico", 
            "RecetaMedicinal", "PlatoGastronomico", "Actor"
        ]
        for lbl in labels:
            session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{lbl}) REQUIRE n.nombre IS UNIQUE")

        for item in tripletas:
            sujeto = item["sujeto"].strip()
            relacion = item["relacion"].strip()
            objeto = item["objeto"].strip()
            fuente = item.get("fuente", "Desconocida")

            if not sujeto or not relacion or not objeto:
                continue

            lbl_sujeto, tipo_rel, lbl_objeto = mapear_etiquetas_ontologicas(sujeto, relacion, objeto)

            query = f"""
            MERGE (s:{lbl_sujeto} {{nombre: $sujeto}})
            MERGE (o:{lbl_objeto} {{nombre: $objeto}})
            MERGE (s)-[r:{tipo_rel}]->(o)
            ON CREATE SET r.fuente = $fuente, r.creado_en = timestamp()
            """
            session.run(query, sujeto=sujeto, objeto=objeto, fuente=fuente)
            cargadas += 1

    driver.close()
    return cargadas

# ===========================================================================
# PIPELINE INTEGRAL: FLUJO COMPLETO DOCUMENTO -> GRAFO
# ===========================================================================
def ejecutar_pipeline_documento_a_grafo(ruta_documento: str):
    print("=" * 75)
    print("  EJECUTANDO PIPELINE COMPLETO: DOCUMENTO -> GRAFO DE CONOCIMIENTO  ")
    print("=" * 75)
    print(f"-> Documento entrante: {ruta_documento}")
    
    inicio = time.time()

    # 1. Parsing y Limpieza
    print("\n[Paso 1/4] Extrayendo y limpiando texto del documento...")
    texto_limpio, nombre_fuente = extraer_y_limpiar_texto(ruta_documento)
    print(f"           Texto extraído: {len(texto_limpio)} caracteres.")

    # 2. Extracción PLN con LLM
    print("\n[Paso 2/4] Extrayendo entidades y relaciones semánticas con LLM...")
    # Segmentar en ventanas de 2500 caracteres
    bloques = [texto_limpio[i:i+2500] for i in range(0, min(len(texto_limpio), 10000), 2500)]
    tripletas_extraidas = []
    
    for idx, bloque in enumerate(bloques, 1):
        # Filtro de pertinencia
        if any(k in bloque.lower() for k in ["planta", "medicinal", "tsáchila", "propiedad", "hoja", "raíz", "cura", "uso"]):
            print(f"           Analizando bloque {idx}/{len(bloques)}...")
            t_bloque = extraer_tripletas_bloque(bloque, nombre_fuente)
            tripletas_extraidas.extend(t_bloque)
            time.sleep(1.0)

    # Deduplicar
    claves = set()
    tripletas_unicas = []
    for t in tripletas_extraidas:
        k = (t["sujeto"].lower(), t["relacion"].lower(), t["objeto"].lower())
        if k not in claves:
            claves.add(k)
            tripletas_unicas.append(t)

    print(f"           Tripletas únicas extraídas: {len(tripletas_unicas)}")
    for t in tripletas_unicas[:5]:
        print(f"            * ({t['sujeto']}) -[:{t['relacion']}]-> ({t['objeto']})")
    if len(tripletas_unicas) > 5:
        print(f"            ... y {len(tripletas_unicas) - 5} tripletas adicionales.")

    # 3. Persistencia local de trazabilidad
    print("\n[Paso 3/4] Actualizando archivo de tripletas consolidadas...")
    tripletas_disco = []
    if os.path.exists(ARCHIVO_TRIPLETAS_GLOBAL):
        try:
            with open(ARCHIVO_TRIPLETAS_GLOBAL, "r", encoding="utf-8") as f:
                tripletas_disco = json.load(f)
        except Exception:
            tripletas_disco = []
            
    # Unir
    for t in tripletas_unicas:
        k = (t["sujeto"].lower(), t["relacion"].lower(), t["objeto"].lower())
        if not any((d["sujeto"].lower(), d["relacion"].lower(), d["objeto"].lower()) == k for d in tripletas_disco):
            tripletas_disco.append(t)
            
    with open(ARCHIVO_TRIPLETAS_GLOBAL, "w", encoding="utf-8") as f:
        json.dump(tripletas_disco, f, ensure_ascii=False, indent=2)

    # 4. Ingesta Directa al Grafo Neo4j
    print("\n[Paso 4/4] Ingestando tripletas en Neo4j AuraDB...")
    total_ingestadas = ingestar_tripletas_neo4j(tripletas_unicas)

    duracion = time.time() - inicio
    print("\n" + "=" * 75)
    print("¡PIPELINE DOCUMENTO -> GRAFO COMPLETADO EXITOSAMENTE!")
    print(f" - Documento procesado: {nombre_fuente}")
    print(f" - Relaciones incorporadas en el Grafo: {total_ingestadas}")
    print(f" - Duración total del flujo: {duracion:.2f} segundos")
    print("=" * 75)

if __name__ == "__main__":
    # Si se pasa un argumento por línea de comandos, procesa ese documento
    if len(sys.argv) > 1:
        doc_path = sys.argv[1]
    else:
        # Documento representativo de prueba: libro oficial UNI-SHU
        doc_path = os.path.join(CARPETA_RAIZ, "Plantas Medicinales y Gastronómicas - Centro Cultural UNI-SHU (Texto Plano) (1).pdf")
        if not os.path.exists(doc_path):
            doc_path = os.path.join(CARPETA_CORPUS, os.listdir(CARPETA_CORPUS)[0])
            
    ejecutar_pipeline_documento_a_grafo(doc_path)
