import os
import re
import json
import fitz  # PyMuPDF


def limpiar_texto(texto: str) -> str:
    """Limpia saltos de línea rotos, guiones de separación y caracteres raros."""
    if not texto:
        return ""

    # 1. Unir palabras separadas por guión al final de una línea (ej: "etno-\nbotánica" -> "etnobotánica")
    texto = re.sub(r"(\w+)-\n(\w+)", r"\1\2", texto)

    # 2. Reducir múltiples saltos de línea consecutivos
    texto = re.sub(r"\n\s*\n+", "\n\n", texto)

    # 3. Unir líneas rotas dentro de un mismo párrafo respetando espacios
    lineas = texto.split("\n\n")
    parrafos_limpios = []
    for parrafo in lineas:
        p_unido = " ".join(parrafo.split())
        if p_unido:
            parrafos_limpios.append(p_unido)

    texto_final = "\n\n".join(parrafos_limpios)

    # 4. Eliminar caracteres de control invisibles o corruptos
    texto_final = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", texto_final)

    return texto_final.strip()


def parsear_y_limpiar_corpus(
    carpeta_entrada=r"C:\Users\Usuario\Videos\EXTRA\corpus_rag_tsachila",
    carpeta_salida_txt=r"C:\Users\Usuario\Videos\EXTRA\corpus_limpio_txt",
    archivo_json_salida=r"C:\Users\Usuario\Videos\EXTRA\corpus_procesado.json",
    max_paginas_por_doc=None,
):
    """
    Lee todos los PDFs de la carpeta, los limpia y genera tanto los archivos
    individuales .txt como el archivo consolidado corpus_procesado.json.
    """
    if not os.path.exists(carpeta_entrada):
        print(f"Error: La carpeta '{carpeta_entrada}' no existe.")
        return

    os.makedirs(carpeta_salida_txt, exist_ok=True)

    archivos_pdf = [
        f for f in os.listdir(carpeta_entrada) if f.lower().endswith(".pdf")
    ]
    print(
        f"Se encontraron {len(archivos_pdf)} archivos PDF en '{carpeta_entrada}'."
    )

    corpus_procesado = []
    total_archivos = len(archivos_pdf)

    for i, archivo in enumerate(archivos_pdf, start=1):
        ruta_pdf = os.path.join(carpeta_entrada, archivo)
        nombre_base = os.path.splitext(archivo)[0]

        try:
            doc = fitz.open(ruta_pdf)
            total_pags = len(doc)
            limite_pags = (
                min(total_pags, max_paginas_por_doc)
                if max_paginas_por_doc
                else total_pags
            )

            texto_acumulado = []

            for num_pag in range(limite_pags):
                pagina = doc[num_pag]
                texto_pag = pagina.get_text("text")
                texto_acumulado.append(texto_pag)

            doc.close()

            # Unir y aplicar la limpieza profunda
            texto_bruto = "\n".join(texto_acumulado)
            texto_limpio = limpiar_texto(texto_bruto)

            if len(texto_limpio) > 50:
                # 1. Guardar archivo individual en formato .txt
                ruta_txt = os.path.join(
                    carpeta_salida_txt, f"{nombre_base}.txt"
                )
                with open(ruta_txt, "w", encoding="utf-8") as f_txt:
                    f_txt.write(texto_limpio)

                # 2. Agregar al archivo consolidado JSON
                item_doc = {
                    "id_documento": i,
                    "nombre_archivo": archivo,
                    "total_paginas_leidas": limite_pags,
                    "caracteres": len(texto_limpio),
                    "texto": texto_limpio,
                }
                corpus_procesado.append(item_doc)

                print(
                    f"[{i}/{total_archivos}] OK: {archivo[:45]}... ({len(texto_limpio)} caracteres)"
                )
            else:
                print(
                    f"[{i}/{total_archivos}] AVISO: {archivo[:45]}... (Sin texto extraíble o muy corto)"
                )

        except Exception as e:
            print(f"[{i}/{total_archivos}] ERROR en {archivo}: {e}")

    # Guardar archivo consolidado para el repositorio
    with open(archivo_json_salida, "w", encoding="utf-8") as f_json:
        json.dump(corpus_procesado, f_json, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("RESUMEN DE EXTRACCIÓN Y LIMPIEZA:")
    print(f"- Total de PDFs procesados con éxito: {len(corpus_procesado)}")
    print(f"- Archivos de texto individuales guardados en: '{carpeta_salida_txt}'")
    print(f"- Archivo consolidado JSON listo: '{archivo_json_salida}'")[cite: 7]
    print("=" * 50)


if __name__ == "__main__":
    parsear_y_limpiar_corpus()