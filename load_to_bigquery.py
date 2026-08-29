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

def rows_from_bronze_file(path: Path)-> list[dict]:
    """"Lee un archivo bronze/{zip}_{fecha}.json y arma una fila por listado."""
    zip_code = path.stem.split("_")[0] #"30311_2026-08-29" -> "30311"
    captured_at = datetime.now(timezone.utc).isoformat() #2026-08-29T12:34:56.789012+00:00

    with open(path, encoding ="utf-8") as f:
        listings = json.load(f)

    return [
        {
            "zip_code" : zip_code,
            "captured_at" : captured_at,
            "raw_json" : json.dumps(listing)
        }
        for listing in listings
    ]

def main():
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

    # Crea la tabal si no existe aun (si es primera corrida)
    try:
        client.get_table(table_id)
    except Exception:
        logger.info(f"Tabla {table_id} no existe, procedo a crearla...")
        client.create_table(bigquery.Table(table_id, schema=SCHEMA))

    all_rows = []
    for path in sorted(Path("bronze").glob("*.json")):
        rows = rows_from_bronze_file(path)
        all_rows.extend(rows)
        logger.info(f"{path.name}: {len(rows)} listados preparados")

    if not all_rows:
        logger.warning("No se encontraron archivos en bronze/. Corriste ya ingest.py?")
        return

    # EN la version SANDBOX no se puede hacer streaming insert, asi que se comenta la carga a BigQuery. En produccion se puede descomentar.

    # errors = client.insert_rows_json(table_id, all_rows)
    # if errors:
    #     raise RuntimeError(f"Errores al insertar en BigQuery: {errors}")

    # logger.info(f"Cargadas {len(all_rows)} filas en {table_id}")

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        write_disposition= "WRITE_APPEND",
    )

    load_job = client.load_table_from_json(all_rows, table_id, job_config=job_config)
    load_job.result() # Espera a que el job termine, y lanza un error si algo sale mal.

    logger.info(f"Cargadas {len(all_rows)} filas en {table_id}")

if __name__ == "__main__":
    main()