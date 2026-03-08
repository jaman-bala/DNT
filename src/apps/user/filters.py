# Фильтр для пользователей
from ninja import Field, FilterSchema


class UserFilterSchema(FilterSchema):
    search: str | None = Field(
        None,
        q=[
            "phone__icontains",
            "first_name__icontains",
            "email__icontains",
        ],
        description="Search by phone, first name, or email",
    )
