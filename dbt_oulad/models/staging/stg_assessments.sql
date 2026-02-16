select
    cast(id_assessment as bigint) as id_assessment,
    cast(date as integer) as assessment_date,
    cast(weight as double precision) as weight
from {{ source('raw', 'assessments') }}
