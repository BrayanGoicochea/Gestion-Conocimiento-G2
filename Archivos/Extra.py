import os
import time
import requests

def descargar_corpus_rag(max_docs=250, output_dir="corpus_rag_tsachila"):
    os.makedirs(output_dir, exist_ok=True)
    base_url = "https://api.openalex.org/works"
    
    # 1. Búsquedas priorizadas: primero Tsáchila y luego etnobotánica/medicina indígena relevante
    queries = [
        "tsachila",
        "tsa'chila",
        "tsafiki medicina",
        "colorados chamanismo ecuador",
        "etnobotanica plantas medicinales ecuador",
        "medicina indigena ecuador plantas",
        "shamanism ecuador ethnobotany"
    ]
    
    headers = {
        "User-Agent": "RAG-AcademicCorpus/1.0 (mailto:estudiante@universidad.edu)"
    }
    
    descargados = 0
    ids_vistos = set()
    
    print(f"Iniciando recolección estricta de hasta {max_docs} documentos...")

    for query in queries:
        if descargados >= max_docs:
            break
            
        print(f"\n--- Consultando grupo temático: '{query}' ---")
        page = 1
        
        while descargados < max_docs:
            params = {
                "search": query,
                "filter": "has_fulltext:true,is_oa:true",
                "per_page": 40,
                "page": page
            }
            
            try:
                resp = requests.get(base_url, params=params, headers=headers, timeout=20)
                if resp.status_code != 200:
                    break
                    
                results = resp.json().get("results", [])
                if not results:
                    break  # Pasa a la siguiente query
                    
                for work in results:
                    if descargados >= max_docs:
                        break
                        
                    work_id = work.get("id", "").split("/")[-1]
                    if work_id in ids_vistos:
                        continue
                    ids_vistos.add(work_id)
                    
                    titulo = work.get("title") or ""
                    titulo_lower = titulo.lower()
                    
                    # Filtro de descarte de temas irrelevantes (leyes, medicina convencional ajena)
                    palabras_prohibidas = ["innocence", "penal", "childbirth", "tuberculosis", "covid", "tribunal", "abogado"]
                    if any(p in titulo_lower for p in palabras_prohibidas):
                        continue
                        
                    pdf_url = work.get("open_access", {}).get("oa_url")
                    if not pdf_url:
                        continue
                        
                    # Descarga
                    try:
                        clean_title = "".join(c for c in titulo if c.isalnum() or c in (" ", "_", "-"))[:45].strip().replace(" ", "_")
                        pdf_resp = requests.get(pdf_url, headers=headers, timeout=20, stream=True)
                        content_type = pdf_resp.headers.get("content-type", "").lower()
                        
                        if pdf_resp.status_code == 200 and "application/pdf" in content_type:
                            file_path = os.path.join(output_dir, f"{clean_title}_{work_id}.pdf")
                            with open(file_path, "wb") as f:
                                for chunk in pdf_resp.iter_content(chunk_size=8192):
                                    f.write(chunk)
                                    
                            descargados += 1
                            print(f"[{descargados}/{max_docs}] Descargado: {clean_title}.pdf")
                    except Exception:
                        continue
                        
                    time.sleep(0.4)
                    
                page += 1
                
            except Exception as e:
                print(f"Error en consulta: {e}")
                break

    print(f"\nFinalizado: {descargados} PDFs descargados con éxito en '{output_dir}'.")

if __name__ == "__main__":
    descargar_corpus_rag(max_docs=200) 