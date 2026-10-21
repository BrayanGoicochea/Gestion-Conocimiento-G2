# Interfaz · Saberes Tsáchila (RAG)

Chatbot sobre medicina ancestral Tsáchila. Usa la base vectorial creada en `HITO 9/chroma_db_tsachila`
(solo lectura; no modifica nada de los HITO).

## Cómo ejecutarla

**Opción 1 (la fácil):** doble clic en `INICIAR_INTERFAZ.bat`.

**Opción 2 (terminal):**

```powershell
cd "C:\Proyecto avance GESTION DE CONOCIMIENTO\INTERFAZ"
python -m streamlit run app.py
```

Se abre en <http://localhost:8501>. La primera carga tarda ~1 minuto (carga el modelo `BAAI/bge-m3`).
Para detenerla: `Ctrl + C` en la terminal o cerrar la ventana.

Requisitos: `pip install -r "..\HITO 9\requirements.txt"` (ya instalados en este equipo).

> **Importante:** el proyecto debe estar en una ruta **sin tildes** (como `C:\Proyecto avance GESTION DE CONOCIMIENTO`).
> En Windows, ChromaDB no puede abrir su índice si la ruta contiene caracteres como `Ó`.

## Cómo guardar tu API key de Groq (para no pegarla cada vez)

**Opción A · Variable de entorno de Windows (recomendada).** Una sola vez, en PowerShell:

```powershell
setx GROQ_API_KEY "pega_aqui_tu_clave"
```

Cierra y vuelve a abrir la terminal (o el `.bat`) y la interfaz mostrará *"API key de Groq detectada"*.
Para comprobar: `echo $env:GROQ_API_KEY` en una terminal nueva.

**Opción B · Archivo local del proyecto.** Crea `INTERFAZ\.streamlit\secrets.toml` con:

```toml
GROQ_API_KEY = "pega_aqui_tu_clave"
```

Ese archivo está en `.gitignore`, así que no se sube a GitHub.

**Nunca** pegues la clave dentro de `app.py`, ni la subas al repositorio. Si se filtra, revócala en la consola de Groq y genera otra.

## Qué incluye

- **💬 Consulta:** chat con respuesta redactada, citas verificadas (verde/rojo) y tarjetas con la fuente y página de cada dato.
- **Preguntas sugeridas** por tema (dolencias, plantas, cultura) y **catálogo de 42 plantas**.
- **🖥️ Consola RAG** bajo cada respuesta: vector de la pregunta, candidatos de ChromaDB con similitud, fragmentos elegidos y prompt enviado al LLM.
- **Detección de plantas:** si mencionas una planta del catálogo, se priorizan sus fichas.
- **🔬 Cómo funciona:** explicación del pipeline para exponer.
