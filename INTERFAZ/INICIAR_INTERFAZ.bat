@echo off
rem Inicia la interfaz del asistente RAG Tsachila. Doble clic para ejecutar.
cd /d "%~dp0"
echo Iniciando la interfaz... la primera carga tarda ~1 minuto (carga el modelo bge-m3).
echo Se abrira en http://localhost:8501  (cierra esta ventana para detenerla)
python -m streamlit run app.py --server.port 8501 --server.headless false
pause
