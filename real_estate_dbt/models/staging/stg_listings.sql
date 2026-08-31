{{
  config(materialized='view')
}}

with parsed as (

    select
        json_value(raw_json, '$.id')               as listing_id,
        json_value(raw_json, '$.formattedAddress')  as formatted_address,
        json_value(raw_json, '$.city')              as city,
        json_value(raw_json, '$.state')             as state,
        zip_code,
        json_value(raw_json, '$.county')            as county,
        cast(json_value(raw_json, '$.latitude')  as float64) as latitude,
        cast(json_value(raw_json, '$.longitude') as float64) as longitude,
        json_value(raw_json, '$.propertyType')      as property_type,
        cast(json_value(raw_json, '$.bedrooms')      as int64)   as bedrooms,
        cast(json_value(raw_json, '$.bathrooms')     as float64) as bathrooms,
        cast(json_value(raw_json, '$.squareFootage') as int64)   as square_footage,
        cast(json_value(raw_json, '$.lotSize')       as int64)   as lot_size,
        cast(json_value(raw_json, '$.yearBuilt')     as int64)   as year_built,
        json_value(raw_json, '$.status')            as status,
        cast(json_value(raw_json, '$.price') as float64) as price,
        cast(json_value(raw_json, '$.daysOnMarket') as int64) as days_on_market,
        json_value(raw_json, '$.listedDate')        as listed_date,
        json_value(raw_json, '$.mlsName')           as mls_name,
        json_value(raw_json, '$.mlsNumber')         as mls_number,
        json_value(raw_json, '$.listingAgent.name')  as agent_name,
        json_value(raw_json, '$.listingOffice.name') as office_name,
        captured_at

    from {{ source('real_estate', 'bronze_listing') }}

)

select *
from parsed
qualify row_number() over (
    partition by listing_id, captured_at
    order by captured_at
) = 1