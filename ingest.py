import os
import json
from datetime import datetime, timezone
import time
import logging
from logging.handlers import TimedRotatingFileHandler

file_handler = TimedRotatingFileHandler("ingest.log", when="W0", interval=1,backupCount=8)


import requests
from dotenv import load_dotenv


logging.basicConfig(
    level = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        file_handler,
        logging.StreamHandler() #lo muestra en pantalla.
    ]
)
logger = logging.getLogger(__name__)

#Zip Codes objetivos fijos por semana para poder comparar precios luego.
ZIP_CODES = ["30311","78732","78726"]

#funcion de ingesta de datos
def get_sale_listings(zip_code: str, api_key: str, limit: int = 25, max_retries: int =3) -> dict:
    """Llama a /listings/sale para un zip code y retorna el JSON crudo."""
    url = "https://api.rentcast.io/v1/listings/sale"
    params = {"zipCode": zip_code, "status": "Active", "limit": limit}
    headers = {"X-Api-Key": api_key, "accept": "application/json"}

    for intento in range(1, max_retries +1):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
        except requests.exceptions.RequestException as e:
            #Error de red (sin Internet, timeout, etc.) - Se reintenta
            logger.warning(f"Intento {intento}/{max_retries} - Error de red: {e}.")
            if intento == max_retries:
                raise
            time.sleep(2** intento) #Backoff: 2s, 4s, 8s...
            continue
        if response.status_code == 200:
            return response.json()

        if response.status_code == 429 or response.status_code >= 500:
            # Rate Limit o Error del Servidor - se Reintenta.
            logger.warning(f" Intento {intento}/{max_retries} - fallo con código: {response.status_code}, reintentando...")
            if intento == max_retries:
                raise RuntimeError(f"Error {response.status_code} tras {max_retries} intentos: {response.text}")
            time.sleep(2 ** intento)
            continue

        # Cualquier otro error (401,403,404...) - No se reintenta.
        raise RuntimeError(f"Error al consultar API RentCast {response.status_code} (No se reintenta): {response.text}")
            

def save_bronze(data: dict, zip_code: str) -> str:
    """Guarda el JSON crudo que se obtiene del API en bronze/ con un nombre trazable"""
    capture_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"bronze/{zip_code}_{capture_date}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return filename

def main():
    load_dotenv() #leer archivo .env y cargar sus variables
    api_key = os.getenv("RENTCAST_API_KEY")
    #api_key ="3f8a44ae294a4127835d977e6f7be711"
    #print("DEBUG repr:", repr(api_key))
    #print("DEBUG longitud:", len(api_key) if api_key else None)

    if not api_key:
        raise ValueError("No se encontro RENTCAST_API_KEY. Creaste tu archivo .evn?")

    for zip_code in ZIP_CODES:
        logger.info(f"Consultando listados para {zip_code}....")
        data = get_sale_listings(zip_code, api_key)
        path = save_bronze(data, zip_code)
        logger.info(f"Guardado en {path} ({len(data)} listados)")

if __name__ == "__main__":
    main()

