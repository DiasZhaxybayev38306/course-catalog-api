from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,   # в JSON поля пишутся в camelCase (isElective)
        validate_by_name=True,      # при создании объекта в Python принимаем и snake_case имя
        validate_by_alias=True,     # и camelCase алиас (из JSON запроса)
    )


class Course(CamelModel):
    id: str
    title: str
    description: str
    credits: int
    is_elective: bool = False   # в JSON будет isElective
    likes: int = 0


class EnrollmentIn(CamelModel):
    course_id: str
    student_name: str = Field(min_length=2)


class Enrollment(EnrollmentIn):
    id: int
