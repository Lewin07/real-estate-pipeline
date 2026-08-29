# Pipeline de Datos de Bienes Raíces

Pipeline de ingesta que consulta listados de propiedades en venta desde la API de [RentCast](https://developers.rentcast.io) y los guarda como capa bronze, como base para un pipeline de analítica de mercado inmobiliario (warehouse + dbt + dashboard, en construcción).

## Arquitectura

\```
RentCast API  -->  ingest.py  -->  bronze/{zip}_{fecha}.json
\```

- **Bronze:** JSON crudo tal como lo devuelve la API, sin transformar, un archivo por zip code por corrida.
- Próximas capas (silver/gold) y warehouse: en desarrollo.

## Requisitos

- Python 3.12+
- Docker Desktop (opcional, para correr en contenedor)
- Una API key de RentCast (tier gratis: 50 llamadas/mes) — [regístrate aquí](https://developers.rentcast.io)

## Configuración

1. Clona el repo y entra a la carpeta.
2. Copia `.env.example` a `.env` y agrega tu API key real:
   \```
   cp .env.example .env
   \```
3. Edita `.env` y reemplaza el valor de `RENTCAST_API_KEY` (sin comillas, sin espacios alrededor del `=`).

## Cómo correrlo

### Opción A — directo con Python

\```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ingest.py
\```

### Opción B — con Docker

\```bash
docker build -t real-estate-pipeline .
docker run --env-file .env \
  -v "$(pwd)/bronze:/app/bronze" \
  -v "$(pwd)/ingest.log:/app/ingest.log" \
  real-estate-pipeline
\```

Los volúmenes (`-v`) conectan las carpetas `bronze/` y el archivo `ingest.log` del contenedor con tu máquina, para que los datos y el registro de ejecución persistan fuera del contenedor.

## Correr los tests

\```bash
pytest
\```

## Zip codes objetivo

Definidos en `ZIP_CODES` dentro de `ingest.py`. Se mantienen fijos entre corridas para poder comparar precios en el tiempo:
- `30311` — Atlanta, GA
- `78732` — Austin, TX
- `78726` — Austin, TX

## Notas de diseño

- La API key nunca se incluye en la imagen Docker ni en el repositorio — se inyecta vía `.env` / `--env-file` al momento de correr, no de construir.
- Manejo de errores: errores 4xx (excepto 429) no se reintentan por diseño, ya que reintentar no resuelve un problema de permisos o autenticación. Errores 429 y 5xx sí se reintentan con backoff exponencial.
- `propertyType: "Land"` no trae `bedrooms`/`bathrooms`/`squareFootage`/`yearBuilt` — se maneja como nulo explícito, no como error.

## Roadmap

- [x] Ingesta con manejo de errores, retries y logging
- [x] Tests unitarios
- [x] Dockerizado
- [ ] Carga a warehouse (BigQuery) — capa bronze/silver
- [ ] Modelos dbt (silver → gold)
- [ ] Orquestación automática (GitHub Actions, semanal)
- [ ] Dashboard (Looker Studio)