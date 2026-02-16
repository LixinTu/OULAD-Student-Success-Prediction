select
    cast(id_student as bigint) as id_student,
    cast(id_assessment as bigint) as id_assessment,
    cast(date_submitted as integer) as date_submitted,
    cast(score as double precision) as score,
    cast(is_banked as integer) as is_banked,
    cast(coalesce(submitted, '1') as integer) as submitted
from {{ source('raw', 'student_assessment') }}
