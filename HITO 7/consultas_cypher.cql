// ============================================================================
// HITO 7: CONSULTAS DE VALIDACIÓN Y COMPETENCIA EN CYPHER (NEO4J)
// Caso de Estudio: Conocimiento Etnobotánico y Gastronómico Tsáchila
// ============================================================================

// 1. Verificación de Restricciones e Índices
SHOW CONSTRAINTS;

// 2. Conteo de Nodos por Etiqueta (Métricas del Grafo)
MATCH (n)
RETURN labels(n)[0] AS Categoria, count(n) AS TotalNodos
ORDER BY TotalNodos DESC;

// 3. Conteo de Relaciones por Tipo
MATCH ()-[r]->()
RETURN type(r) AS Relacion, count(r) AS TotalRelaciones
ORDER BY TotalRelaciones DESC;

// ----------------------------------------------------------------------------
// PREGUNTAS DE COMPETENCIA Y CONSULTAS DE MÚLTIPLES SALTOS
// ----------------------------------------------------------------------------

// Consulta 1: ¿Qué plantas se utilizan para curar mordeduras o picaduras de serpientes, 
// qué parte de la planta se usa y cómo se preparan?
MATCH (p:Planta)-[:TRATA_A]->(d:Patologia)
WHERE toLower(d.nombre) CONTAINS "serpiente"
OPTIONAL MATCH (p)-[:USA_PARTE]->(parte:PartePlanta)
OPTIONAL MATCH (p)-[:PREPARADO_COMO]->(prep:Preparacion)
OPTIONAL MATCH (p)-[:TIENE_NOMBRE_TSAFIQUI]->(tsaf:NombreTsafiqui)
RETURN p.nombre AS Planta, tsaf.nombre AS NombreTsafiqui, d.nombre AS Dolencia, 
       collect(DISTINCT parte.nombre) AS PartesUsadas, 
       collect(DISTINCT prep.nombre) AS Preparaciones;

// Consulta 2: ¿Cuáles son las plantas de la familia Piperaceae o Bixaceae, qué dolencias tratan y cuál es su nombre científico?
MATCH (p:Planta)-[:PERTENECE_A_FAMILIA]->(f:FamiliaBotanica)
WHERE toLower(f.nombre) IN ["piperaceae", "bixaceae"]
OPTIONAL MATCH (p)-[:TIENE_NOMBRE_CIENTIFICO]->(c:NombreCientifico)
OPTIONAL MATCH (p)-[:TRATA_A]->(d:Patologia)
RETURN p.nombre AS Planta, f.nombre AS Familia, c.nombre AS NombreCientifico, 
       collect(DISTINCT d.nombre) AS Tratamientos;

// Consulta 3: Tratamientos ceremoniales y recetas administradas exclusivamente por el Poné (Chamán)
MATCH (s)-[:ADMINISTRADO_POR]->(a:Actor)
WHERE toLower(a.nombre) CONTAINS "poné" OR toLower(a.nombre) CONTAINS "pone"
OPTIONAL MATCH (s)-[:PREPARADO_COMO]->(prep)
OPTIONAL MATCH (s)-[:TRATA_A]->(d:Patologia)
RETURN labels(s)[0] AS Tipo, s.nombre AS Remedio_O_Planta, 
       collect(DISTINCT d.nombre) AS Cura, 
       collect(DISTINCT prep.nombre) AS MetodoElaboracion;

// Consulta 4: Consulta de 3 saltos - Relación Especie -> Familia -> Síntoma -> Preparación
MATCH (p:Planta)-[:PERTENECE_A_FAMILIA]->(f:FamiliaBotanica),
      (p)-[:TRATA_A]->(d:Patologia),
      (p)-[:PREPARADO_COMO]->(prep:Preparacion)
RETURN f.nombre AS Familia, p.nombre AS Planta, d.nombre AS Sintoma, prep.nombre AS FormaUso
LIMIT 25;

// Consulta 5: Plantas con uso dual (Gastronomía y Medicina)
MATCH (p:Planta)-[:USA_PARTE]->(parte:PartePlanta)
OPTIONAL MATCH (p)-[:TRATA_A]->(med:Patologia)
OPTIONAL MATCH (p)-[:INGREDIENTE_DE_PLATO]->(plato:PlatoGastronomico)
WHERE plato IS NOT NULL OR toLower(p.nombre) IN ["achiote", "culantro de pozo", "guayusa", "hoja de yuca"]
RETURN p.nombre AS Planta, collect(DISTINCT med.nombre) AS UsoMedicinal, 
       collect(DISTINCT plato.nombre) AS UsoGastronomico;

// Consulta 6: Auditoría de Trazabilidad: Obtener la fuente bibliográfica documentada de cada relación
MATCH (p:Planta)-[r]->(o)
WHERE r.fuente IS NOT NULL
RETURN p.nombre AS Origen, type(r) AS Relacion, o.nombre AS Destino, r.fuente AS Fuente
LIMIT 20;
