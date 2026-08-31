{{
  config(materialized='table')
}}

select
    zip_code,
    city,
    state,
    property_type,
    date(captured_at) as captured_date,
    count(*) as listing_count,
    round(avg(price), 2) as avg_price,
    round(avg(price / nullif(square_footage, 0)), 2) as avg_price_per_sqft,
    round(avg(days_on_market), 1) as avg_days_on_market

from {{ ref('stg_listings') }}
group by zip_code, city, state, property_type, captured_date