
-- Use the `ref` function to select from other models

select id
from {{ ref('my_first_dbt_model') }}
union all
select 1 as id
