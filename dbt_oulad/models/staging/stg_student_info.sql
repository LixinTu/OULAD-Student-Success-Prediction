select
    cast(id_student as bigint) as id_student,
    cast(code_module as varchar(16)) as code_module,
    cast(studied_credits as double precision) as studied_credits,
    cast(age_band_num as integer) as age_band_num,
    cast(imd_band_num as integer) as imd_band_num,
    cast(disability_flag as integer) as disability_flag,
    cast(pass_probability_base as double precision) as pass_probability_base
from {{ source('raw', 'student_info') }}
