import os
import json
import time
from openai import OpenAI

GROQ_API_KEY = "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"

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1"
)

DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CARPETA_RAIZ = os.path.dirname(DIRECTORIO_ACTUAL)

ARCHIVO_CORPUS_JSON = os.path.join(CARPETA_RAIZ, "Archivos", "corpus_procesado.json")
ARCHIVO_SALIDA_TRIPLETAS = os.path.join(CARPETA_RAIZ, "Archivos", "tripletas_extraidas.json")

KEYWORDS_MEDICINALES = [
    "planta", "medicinal", "remedio", "enfermedad", "síntoma", "patología",
    "poné", "curación", "infusión", "hojas", "raíz", "corteza", "tsáchila",
    "tsafiki", "chaman", "dolor", "fiebre", "picadura", "baño", "limpia"
]

def contiene_informacion_relevante(texto: str) -> bool:
    texto_min = texto.lower()
    coincidencias = sum(1 for kw in KEYWORDS_MEDICINALES if kw in texto_min)
    return coincidencias >= 2

def extraer_tripletas_con_llm(fragmento_texto: str, nombre_fuente: str) -> list:
    prompt = f"""
Eres un especialista en extracción de conocimiento para construir una Ontología y Grafo sobre Medicina Ancestral Tsáchila.

Analiza el texto y extrae relaciones sobre plantas, dolencias, preparaciones y partes botánicas.

Reglas estrictas:
1. Normaliza las relaciones a: "trata_a", "usa_parte", "preparado_como", "administrado_por", "pertenece_a_familia".
2. Si no hay información relevante, devuelve el campo "tripletas" como lista vacía: {{"tripletas": []}}.
3. Devuelve SIEMPRE un JSON con la clave raíz "tripletas":
{{"tripletas": [{{"sujeto": "...", "relacion": "...", "objeto": "..."}}]}}

Texto a analizar:
\"\"\"{fragmento_texto}\"\"\"
"""

    for intento in range(3):
        try:
            response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            contenido = response.choices[0].message.content.strip()
            data = json.loads(contenido)
            
            # Obtener la lista ya sea bajo "tripletas" o la primera lista del dict
            lista_tripletas = data.get("tripletas", []) if isinstance(data, dict) else data
            if isinstance(lista_tripletas, dict):
                lista_tripletas = list(lista_tripletas.values())

            if isinstance(lista_tripletas, list):
                resultado = []
                for item in lista_tripletas:
                    if isinstance(item, dict) and "sujeto" in item and "relacion" in item and "objeto" in item:
                        item["fuente"] = nombre_fuente
                        resultado.append(item)
                return resultado
            return []

        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                # Si supera el rate limit por minuto, espera 10 segundos y reintenta
                time.sleep(10)
            else:
                print(f"    [!] Error en {nombre_fuente[:30]}: {e}")
                return []
    return []

def procesar_extraccion():
    if not os.path.exists(ARCHIVO_CORPUS_JSON):
        print(f"Error: No se encontró '{ARCHIVO_CORPUS_JSON}'.")
        return

    print("Cargando corpus procesado...")
    with open(ARCHIVO_CORPUS_JSON, "r", encoding="utf-8") as f:
        documentos = json.load(f)

    print(f"Total de documentos cargados: {len(documentos)}")

    # Priorizar UNI-SHU al inicio
    documentos.sort(
        key=lambda d: 0 if "uni-shu" in d.get("nombre_archivo", "").lower() else 1
    )

    todas_las_tripletas = []
    tripletas_vistas = set()
    docs_con_tripletas = 0

    for idx, doc in enumerate(documentos, start=1):
        nombre_archivo = doc.get("nombre_archivo", f"doc_{idx}")
        texto = doc.get("texto", "")

        if not contiene_informacion_relevante(texto):
            continue

        print(f"[{idx}/{len(documentos)}] Analizando: {nombre_archivo[:45]}...")

        # Bloques de 2500 caracteres para no saturar tokens
        bloques = [texto[i:i + 2500] for i in range(0, min(len(texto), 15000), 2500)]
        tripletas_doc = []

        for bloque in bloques:
            if contiene_informacion_relevante(bloque):
                tripletas = extraer_tripletas_con_llm(bloque, nombre_archivo)
                for t in tripletas:
                    clave = (str(t.get("sujeto", "")).lower().strip(), 
                             str(t.get("relacion", "")).lower().strip(), 
                             str(t.get("objeto", "")).lower().strip())
                    if clave not in tripletas_vistas and len(clave[0]) > 1:
                        tripletas_vistas.add(clave)
                        tripletas_doc.append(t)
                        todas_las_tripletas.append(t)
                time.sleep(2.5)  # Pausa para respetar el límite de 1000 tokens/minuto

        if tripletas_doc:
            docs_con_tripletas += 1
            print(f"    -> {len(tripletas_doc)} nuevas tripletas añadidas (Total acumulado: {len(todas_las_tripletas)})")

    with open(ARCHIVO_SALIDA_TRIPLETAS, "w", encoding="utf-8") as f_out:
        json.dump(todas_las_tripletas, f_out, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("RESUMEN DE EXTRACCIÓN:")
    print(f"- Total de tripletas únicas: {len(todas_las_tripletas)}")
    print(f"- Documentos procesados con éxito: {docs_con_tripletas}")
    print(f"- Guardado en: {ARCHIVO_SALIDA_TRIPLETAS}")
    print("=" * 50)

if __name__ == "__main__":
    procesar_extraccion()