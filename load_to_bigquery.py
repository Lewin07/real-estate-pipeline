import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from google.cloud import bigquery

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("load.log"),logging.StreamHandler()],

)
logger = logging.getLogger(__name__)

PROJECT_ID = "real-estate-pipeline-507020"
DATASET = "real_estate"
TABLE = "bronze_listing"

SCHEMA = [
    bigquery.SchemaField("zip_code", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("captured_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("raw_json", "STRING", mode="REQUIRED"),
]

def rows_from_bronze_file(path: Path) -> list[dict]:
    """Lee un archivo bronze/{zip}_{fecha}.json y arma una fila por listado."""
    zip_code, fecha_str = path.stem.split("_")  # "30311_2026-08-29" -> "30311", "2026-08-29"
    captured_at = datetime.strptime(fecha_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()

    with open(path, encoding="utf-8") as f:
        listings = json.load(f)

    return [
        {
            "zip_code": zip_code,
            "captured_at": captured_at,
            "raw_json": json.dumps(listing),
        }
        for listing in listings
    ]


def get_already_loaded(client: bigquery.Client, table_id: str) -> set[tuple[str, str]]:
    """Devuelve el conjunto de (zip_code, captured_at) que ya están en BigQuery."""
    query = f"SELECT DISTINCT zip_code, captured_at FROM `{table_id}`"
    try:
        rows = client.query(query).result()
    except Exception:
        # La tabla no existe todavía (primera corrida) - nada cargado aún.
        return set()

    return {(row.zip_code, row.captured_at.isoformat()) for row in rows}


def main():
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    try:
        client.get_table(table_id)
    except Exception:
        logger.info(f"Tabla {table_id} no existe, creándola...")
        client.create_table(bigquery.Table(table_id, schema=SCHEMA))

    already_loaded = get_already_loaded(client, table_id)
    logger.info(f"{len(already_loaded)} combinaciones (zip, fecha) ya existen en BigQuery")

    bronze_dir = Path("bronze")
    loaded_dir = bronze_dir / "loaded"
    loaded_dir.mkdir(exist_ok=True)

    all_files = sorted(bronze_dir.glob("*.json"))

    if not all_files:
        logger.warning("No hay archivos en bronze/. ¿Falta correr ingest.py?")
        return

    all_rows = []
    files_to_move = []

    for path in all_files:
        zip_code, fecha_str = path.stem.split("_")
        captured_at = datetime.strptime(fecha_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()

        if (zip_code, captured_at) in already_loaded:
            logger.info(f"{path.name}: ya estaba cargado en BigQuery, se omite")
            files_to_move.append(path)  # igual lo movemos, para mantener bronze/ limpio
            continue

        rows = rows_from_bronze_file(path)
        all_rows.extend(rows)
        files_to_move.append(path)
        logger.info(f"{path.name}: {len(rows)} listados preparados para cargar")

    if not all_rows:
        logger.info("Nada nuevo que cargar - todo ya estaba en BigQuery")
    else:
        job_config = bigquery.LoadJobConfig(schema=SCHEMA, write_disposition="WRITE_APPEND")
        load_job = client.load_table_from_json(all_rows, table_id, job_config=job_config)
        load_job.result()
        logger.info(f"Cargadas {len(all_rows)} filas nuevas en {table_id}")

    for path in files_to_move:
        path.rename(loaded_dir / path.name)

if __name__ == "__main__":
    main()