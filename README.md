# Pipeline de Datos de Bienes Raíces

Pipeline de datos end-to-end que ingesta listados de propiedades en venta desde la API de [RentCast](https://developers.rentcast.io), los transforma con dbt en BigQuery, y corre automáticamente cada semana — pensado como pieza de portafolio para servicios de analítica de mercado inmobiliario.

## Arquitectura

\```
RentCast API
    │
    ▼
ingest.py  ──────────►  bronze/{zip}_{fecha}.json          (capa bronze local)
    │
    ▼
load_to_bigquery.py  ─►  BigQuery: real_estate.bronze_listing   (capa bronze en la nube)
    │
    ▼
dbt (stg_listings)  ──►  BigQuery: real_estate.stg_listings      (capa silver)
    │
    ▼
dbt (gold_price_by_property_type) ► BigQuery: real_estate.gold_price_by_property_type
    │
    ▼
Dashboard (Looker Studio)
\```

Todo el flujo corre automáticamente cada lunes vía **GitHub Actions**, sin intervención manual. Si algo falla, se crea un GitHub Issue automáticamente con el link a los logs.

## Componentes

| Capa | Herramienta | Qué hace |
|---|---|---|
| Ingesta | Python (`ingest.py`) | Llama a RentCast, guarda JSON crudo, con retries y logging |
| Carga | Python (`load_to_bigquery.py`) | Sube el JSON crudo a BigQuery como capa bronze |
| Transformación | dbt | Limpia/tipa (`stg_listings`) y agrega métricas (`gold_price_by_property_type`), con tests |
| Orquestación | GitHub Actions | Corre todo el pipeline semanalmente, con alertas automáticas |
| Autenticación | Workload Identity Federation | GitHub Actions se autentica a Google Cloud sin ninguna key JSON |

## Requisitos

- Python 3.12+
- Docker Desktop (opcional, para correr la ingesta en contenedor)
- Cuenta de Google Cloud con BigQuery (tier Sandbox, sin tarjeta necesaria)
- Una API key de RentCast (tier gratis: 50 llamadas/mes)

## Configuración

1. Clona el repo y entra a la carpeta.
2. Copia `.env.example` a `.env` y agrega tu API key real (sin comillas, sin espacios).
3. Autentica con Google Cloud localmente: `gcloud auth application-default login`
4. Configura tu conexión dbt (`profiles.yml`) apuntando a tu propio proyecto de BigQuery.

## Cómo correrlo localmente

\```bash
# Ingesta + carga a BigQuery
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 ingest.py
python3 load_to_bigquery.py

# Transformación con dbt
cd real_estate_dbt
dbt build
\```

### Con Docker (solo la ingesta)

\```bash
docker build -t real-estate-pipeline .
docker run --env-file .env \
  -v "$(pwd)/bronze:/app/bronze" \
  -v "$(pwd)/ingest.log:/app/ingest.log" \
  real-estate-pipeline
\```

## Orquestación automática

El pipeline corre solo, todos los lunes a las 9am UTC, vía [GitHub Actions](.github/workflows/weekly_pipeline.yml) — o manualmente desde la pestaña "Actions" del repo. La autenticación a Google Cloud usa Workload Identity Federation, sin ninguna key almacenada como secreto. Si el pipeline falla, se abre automáticamente un GitHub Issue con el link a los logs.

## Correr los tests

\```bash
pytest                          # tests de Python (ingesta)
cd real_estate_dbt && dbt build  # tests de datos (dbt)
\```

## Zip codes objetivo

Definidos en `ZIP_CODES` dentro de `ingest.py`, fijos entre corridas para poder comparar precios en el tiempo:
- `30311` — Atlanta, GA
- `78732` — Austin, TX
- `78726` — Austin, TX

## Notas de diseño

- Ningún secreto (API key, credenciales de GCP) vive en el código ni en la imagen Docker — se inyectan en tiempo de ejecución.
- BigQuery corre en tier Sandbox: no permite *streaming inserts*, por eso la carga usa un *load job* por lotes.
- Errores 4xx (excepto 429) no se reintentan; 429 y 5xx sí, con backoff exponencial.
- La capa silver (`stg_listings`) deduplica con `ROW_NUMBER()`/`QUALIFY` por `(listing_id, captured_at)`.
- `propertyType: "Land"` no trae `bedrooms`/`bathrooms`/`squareFootage`/`yearBuilt` — se maneja como nulo explícito, no como error, y los tests de dbt lo reflejan (sin `not_null` forzado en esos campos).

## Roadmap

- [x] Ingesta con manejo de errores, retries y logging
- [x] Tests unitarios (pytest)
- [x] Dockerizado
- [x] Carga a warehouse (BigQuery)
- [x] Modelos dbt (staging → gold) con tests
- [x] Orquestación automática semanal (GitHub Actions + Workload Identity Federation)
- [x] Alertas automáticas en caso de falla
- [ ] Dashboard (Looker Studio)
- [ ] Tabla de historial de precios por listado (despivot de `history`)