import os
import re
from neo4j import GraphDatabase
from groq import Groq

# =========================================================================
# CREDENCIALES Y CONEXIÓN
# =========================================================================
NEO4J_URI = "neo4j+s://0764d10c.databases.neo4j.io"
NEO4J_USER = "0764d10c"
NEO4J_PASSWORD = "U9K2ZtRxhE3zBR_8LtGniLgxVt_2nr6XKnVT3AikSDY"
GROQ_API_KEY = "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"

# Modelo confirmado en tu cuenta de Groq
MODELO_GROQ = "openai/gpt-oss-120b"

client_groq = Groq(api_key=GROQ_API_KEY)
driver_neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Esquema ontológico para contextualizar la generación de Cypher
ESQUEMA_GRAFO = """
Nodos y Etiquetas:
- Planta (propiedad: nombre)
- Patologia (propiedad: nombre)
- PartePlanta (propiedad: nombre)
- Preparacion (propiedad: nombre)
- FamiliaBotanica (propiedad: nombre)
- NombreTsafiqui (propiedad: nombre)
- NombreCientifico (propiedad: nombre)
- Receta (propiedad: nombre)
- Actor (propiedad: nombre)

Relaciones:
- (:Planta)-[:TRATA_A]->(:Patologia)
- (:Planta)-[:USA_PARTE]->(:PartePlanta)
- (:Planta)-[:PREPARADO_COMO]->(:Preparacion)
- (:Planta)-[:PERTENECE_A_FAMILIA]->(:FamiliaBotanica)
- (:Planta)-[:TIENE_NOMBRE_TSAFIQUI]->(:NombreTsafiqui)
- (:Planta)-[:TIENE_NOMBRE_CIENTIFICO]->(:NombreCientifico)
- (:Planta)-[:ADMINISTRADO_POR]->(:Actor)
- (:Receta)-[:ADMINISTRADO_POR]->(:Actor)
"""

def limpiar_cypher(texto_cypher: str) -> str:
    """Remueve bloques markdown o delimitadores extra del texto generado."""
    query = re.sub(r"```(cypher)?", "", texto_cypher, flags=re.IGNORECASE)
    return query.strip().rstrip(";")

def generar_cypher_con_llm(pregunta_usuario: str) -> str:
    """Traduce la intención en lenguaje natural a una consulta Cypher estricta."""
    prompt_sistema = f"""
Eres un traductor experto de lenguaje natural a consultas Cypher para Neo4j.
Tu única tarea es generar la consulta Cypher para responder a la pregunta del usuario.

Esquema de la base de datos:
{ESQUEMA_GRAFO}

Reglas estrictas:
1. Usa comparaciones insensibles a mayúsculas con toLower() y CONTAINS para textos.
   Ejemplo: WHERE toLower(d.nombre) CONTAINS toLower('fiebre')
2. Devuelve ÚNICAMENTE el código Cypher ejecutable.
3. No agregues explicaciones, comentarios ni bloques markdown ```.
"""
    respuesta = client_groq.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pregunta_usuario}
        ],
        temperature=0.0
    )
    return limpiar_cypher(respuesta.choices[0].message.content)

def ejecutar_cypher(query: str):
    """Ejecuta la consulta en Neo4j AuraDB y devuelve la lista de registros."""
    try:
        with driver_neo4j.session() as session:
            result = session.run(query)
            return [record.data() for record in result]
    except Exception as e:
        print(f"\n[!] Error al ejecutar Cypher: {e}")
        return []

def sintetizar_respuesta(pregunta_usuario: str, datos_grafo: list) -> str:
    """Genera la respuesta final en lenguaje natural a partir de los datos exactos del grafo."""
    prompt_sistema = """
Eres un asistente botánico y antropólogo especializado en la medicina ancestral del pueblo Tsáchila.
Responde de forma clara, profesional y rigurosa usando EXCLUSIVAMENTE los datos del grafo recuperados.
Si la lista de datos está vacía, indica con cortesía que no existe registro de esa dolencia o planta en la base etnobotánica actual.
No inventes datos ni menciones propiedades que no estén en la información proporcionada.
"""
    contenido_usuario = f"""
Pregunta del usuario: {pregunta_usuario}
Datos recuperados de Neo4j:
{datos_grafo}
"""
    respuesta = client_groq.chat.completions.create(
        model=MODELO_GROQ,
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": contenido_usuario}
        ],
        temperature=0.2
    )
    return respuesta.choices[0].message.content

def procesar_consulta(pregunta: str):
    print("\n" + "=" * 70)
    print(f"-> Procesando: {pregunta}")
    
    # 1. Generación de Cypher
    cypher_query = generar_cypher_con_llm(pregunta)
    print(f"\n[1] Cypher generado por el LLM:\n{cypher_query}")
    
    # 2. Búsqueda en Neo4j AuraDB
    datos = ejecutar_cypher(cypher_query)
    print(f"\n[2] Hechos recuperados del Grafo ({len(datos)} registros):")
    if datos:
        for d in datos[:5]:
            print(f"   * {d}")
        if len(datos) > 5:
            print(f"   ... y {len(datos) - 5} registros más.")
    else:
        print("   (Sin coincidencias directas en la base)")
    
    # 3. Síntesis aumentada
    respuesta_final = sintetizar_respuesta(pregunta, datos)
    print(f"\n[3] Respuesta Graph-RAG final:\n{respuesta_final}")
    print("=" * 70 + "\n")

def menu_interactivo():
    preguntas_sugeridas = [
        "¿Qué plantas se usan para tratar las picaduras o mordeduras de serpientes?",
        "¿Cuáles son todas las propiedades, usos y nombres del Achiote?",
        "¿Qué tratamientos o recetas son administrados exclusivamente por el Poné?",
        "¿Qué plantas pertenecen a la familia Piperaceae o Bixaceae?",
        "¿Qué plantas sirven para afecciones respiratorias y qué parte de la planta se utiliza?",
        "¿Qué enfermedades se tratan usando únicamente la corteza de las plantas?"
    ]

    while True:
        print("\n=======================================================")
        print("  SISTEMA GRAPH-RAG: ETNOBOTÁNICA Y MEDICINA TSÁCHILA  ")
        print("=======================================================")
        print("Opciones sugeridas para probar:")
        for idx, p in enumerate(preguntas_sugeridas, 1):
            print(f"  [{idx}] {p}")
        print("  [E] Escribir tu propia pregunta personalizada")
        print("  [S] Salir")
        print("-------------------------------------------------------")
        
        opcion = input("Elige una opción (1-6, E, S): ").strip().upper()
        
        if opcion == "S":
            print("\nCerrando sesión del sistema Graph-RAG. ¡Hasta pronto!")
            break
        elif opcion in ["1", "2", "3", "4", "5", "6"]:
            pregunta_seleccionada = preguntas_sugeridas[int(opcion) - 1]
            procesar_consulta(pregunta_seleccionada)
        elif opcion == "E":
            pregunta_personalizada = input("\nEscribe tu pregunta sobre la medicina Tsáchila: ").strip()
            if pregunta_personalizada:
                procesar_consulta(pregunta_personalizada)
            else:
                print("Pregunta vacía.")
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    try:
        menu_interactivo()
    finally:
        driver_neo4j.close()