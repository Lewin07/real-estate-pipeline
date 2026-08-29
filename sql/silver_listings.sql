CREATE OR REPLACE TABLE real_estate.silver_listings AS
WITH parsed AS (
  SELECT
    JSON_VALUE(raw_json, '$.id')              AS listing_id,
    JSON_VALUE(raw_json, '$.formattedAddress') AS formatted_address,
    JSON_VALUE(raw_json, '$.city')             AS city,
    JSON_VALUE(raw_json, '$.state')            AS state,
    zip_code,
    JSON_VALUE(raw_json, '$.county')           AS county,
    CAST(JSON_VALUE(raw_json, '$.latitude')  AS FLOAT64) AS latitude,
    CAST(JSON_VALUE(raw_json, '$.longitude') AS FLOAT64) AS longitude,
    JSON_VALUE(raw_json, '$.propertyType')     AS property_type,
    CAST(JSON_VALUE(raw_json, '$.bedrooms')      AS INT64)   AS bedrooms,
    CAST(JSON_VALUE(raw_json, '$.bathrooms')     AS FLOAT64) AS bathrooms,
    CAST(JSON_VALUE(raw_json, '$.squareFootage') AS INT64)   AS square_footage,
    CAST(JSON_VALUE(raw_json, '$.lotSize')       AS INT64)   AS lot_size,
    CAST(JSON_VALUE(raw_json, '$.yearBuilt')     AS INT64)   AS year_built,
    JSON_VALUE(raw_json, '$.status')           AS status,
    CAST(JSON_VALUE(raw_json, '$.price') AS FLOAT64) AS price,
    CAST(JSON_VALUE(raw_json, '$.daysOnMarket') AS INT64) AS days_on_market,
    JSON_VALUE(raw_json, '$.listedDate')       AS listed_date,
    JSON_VALUE(raw_json, '$.mlsName')          AS mls_name,
    JSON_VALUE(raw_json, '$.mlsNumber')        AS mls_number,
    JSON_VALUE(raw_json, '$.listingAgent.name')   AS agent_name,
    JSON_VALUE(raw_json, '$.listingOffice.name')  AS office_name,
    captured_at
  FROM real_estate.bronze_listing
)
SELECT *
FROM parsed
-- Deduplica: si por accidente cargaste el mismo bronze dos veces,
-- se queda solo con una fila por (listado, captura).
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY listing_id, captured_at
  ORDER BY captured_at
) = 1;