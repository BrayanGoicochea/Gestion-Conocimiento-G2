import os
import json
from neo4j import GraphDatabase

# =========================================================================
# CREDENCIALES DE CONEXIÓN A NEO4J AURADB
# =========================================================================
NEO4J_URI = "neo4j+s://0764d10c.databases.neo4j.io"
NEO4J_USER = "0764d10c"
NEO4J_PASSWORD = "U9K2ZtRxhE3zBR_8LtGniLgxVt_2nr6XKnVT3AikSDY"

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)
ARCHIVO_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")

RECETAS_CONOCIDAS = {
    "don'bada kapi", "muturu'pi", "uru mala", "yo'mala", 
    "kanthi pi", "mu queká", "pa copí", "kon konla pi", "pinku daka´pi", "boro mala"
}

def normalizar_texto(texto: str) -> str:
    if not texto:
        return ""
    return " ".join(texto.strip().split())

def determinar_etiqueta_sujeto(sujeto: str) -> str:
    s_clean = normalizar_texto(sujeto).lower()
    if s_clean in RECETAS_CONOCIDAS:
        return "Receta"
    return "Planta"

def determinar_etiqueta_objeto(relacion: str, objeto: str) -> tuple[str, str]:
    rel = relacion.lower().strip()
    obj_clean = normalizar_texto(objeto)
    
    if rel == "trata_a":
        return "TRATA_A", "Patologia"
    elif rel == "usa_parte":
        return "USA_PARTE", "PartePlanta"
    elif rel == "preparado_como":
        return "PREPARADO_COMO", "Preparacion"
    elif rel == "pertenece_a_familia":
        return "PERTENECE_A_FAMILIA", "FamiliaBotanica"
    elif rel == "nombre_tsafiqui":
        return "TIENE_NOMBRE_TSAFIQUI", "NombreTsafiqui"
    elif rel == "nombre_cientifico":
        return "TIENE_NOMBRE_CIENTIFICO", "NombreCientifico"
    elif rel == "administrado_por":
        if "baño" in obj_clean.lower() or "infusion" in obj_clean.lower():
            return "PREPARADO_COMO", "Preparacion"
        return "ADMINISTRADO_POR", "Actor"
    else:
        tipo_rel = rel.upper().replace(" ", "_")
        return tipo_rel, "Concepto"

def cargar_grafo():
    if not os.path.exists(ARCHIVO_TRIPLETAS):
        print(f"Error: No se encontró el archivo en {ARCHIVO_TRIPLETAS}")
        return

    print("Leyendo tripletas extraídas...")
    with open(ARCHIVO_TRIPLETAS, "r", encoding="utf-8") as f:
        tripletas = json.load(f)

    print(f"Total de tripletas a procesar: {len(tripletas)}")
    print("Conectando con Neo4j AuraDB...")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        print("Creando restricciones de unicidad...")
        labels = [
            "Planta", "Patologia", "PartePlanta", "Preparacion", 
            "FamiliaBotanica", "NombreTsafiqui", "NombreCientifico", "Receta", "Actor"
        ]
        for lbl in labels:
            session.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{lbl}) REQUIRE n.nombre IS UNIQUE")

        print("Insertando nodos y relaciones en el grafo...")
        contador = 0
        for item in tripletas:
            sujeto = normalizar_texto(item.get("sujeto", ""))
            relacion = normalizar_texto(item.get("relacion", ""))
            objeto = normalizar_texto(item.get("objeto", ""))
            fuente = normalizar_texto(item.get("fuente", ""))

            if not sujeto or not relacion or not objeto:
                continue

            label_sujeto = determinar_etiqueta_sujeto(sujeto)
            tipo_rel, label_objeto = determinar_etiqueta_objeto(relacion, objeto)

            query = f"""
            MERGE (s:{label_sujeto} {{nombre: $sujeto}})
            MERGE (o:{label_objeto} {{nombre: $objeto}})
            MERGE (s)-[r:{tipo_rel}]->(o)
            ON CREATE SET r.fuente = $fuente
            """

            session.run(query, sujeto=sujeto, objeto=objeto, fuente=fuente)
            contador += 1
            if contador % 50 == 0:
                print(f"   -> {contador}/{len(tripletas)} tripletas procesadas...")

    driver.close()
    print("=" * 60)
    print(f"¡ÉXITO TOTAL! Se registraron {contador} relaciones en Neo4j AuraDB.")
    print("=" * 60)

if __name__ == "__main__":
    cargar_grafo()