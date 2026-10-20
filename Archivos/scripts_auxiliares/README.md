# Scripts Auxiliares de Recolección y Procesamiento del Corpus

Este directorio reúne los scripts desarrollados para la construcción, depuración, descarga y enriquecimiento del corpus documental del proyecto:

1. **`depurar_y_descargar_corpus.py`**:
   - Analiza el catálogo de 59 especies de la Reserva UNI-SHU.
   - Conecta a la API de OpenAlex con multihilo (`ThreadPoolExecutor`).
   - Descarga artículos científicos abiertos por nombre botánico binomial.
   - Filtra y elimina el 90% de documentos no pertinentes del corpus original.

2. **`descargar_plos_plantas.py`**:
   - Conecta a la API pública de PLOS (`https://api.plos.org/search`).
   - Descarga artículos de alta calidad en PDF directamente desde el DOI de PLOS ONE.
   - Garantiza cobertura para especies etnobotánicas clave como *Uncaria tomentosa*, *Bixa orellana*, *Ilex guayusa*, *Petiveria alliacea*, etc.

3. **`descargar_zenodo_plantas.py`**:
   - Módulo auxiliar para búsqueda de tratados y compendios etnobotánicos en Zenodo.

4. **`descargar_enfoque_resguardo_tsachila.py`**:
   - Descarga artículos específicos sobre preservación y pérdida de conocimiento ecológico tradicional en pueblos indígenas.

5. **`generar_monografia_plantas_especiales.py`**:
   - Genera el PDF canónico `Monografia_Etnobotanica_Plantas_Tradicionales_UNI_SHU_Tsachila.pdf` utilizando ReportLab.
   - Contiene las fichas técnicas detalladas de las 12 especies endémicas y de uso tradicional de UNI-SHU que no contaban con papers monográficos aislados en bases internacionales.

6. **`completar_corpus_hasta_220.py`**:
   - Script de control de volumen para asegurar el cumplimiento del rango métrico reglamentario (200 - 500 documentos).

7. **`Extra.py`**:
   - Script base de referencia inicial para scraping y consulta a APIs académicas.
