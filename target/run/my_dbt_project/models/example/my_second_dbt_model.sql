create or replace view `workspace`.`default`.`my_second_dbt_model`
  
  
  
  as
    -- Use the `ref` function to select from other models

select id
from `workspace`.`default`.`my_first_dbt_model`
union all
select 1 as id
