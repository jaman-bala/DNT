# Базовый паггинация
from ninja import Schema
from ninja.pagination import PaginationBase
from pydantic import Field


class CustomPagination(PaginationBase):
    class Input(Schema):
        limit: int = Field(10, gt=0, le=30, description="Number of items per page")
        offset: int = Field(0, ge=0, description="Offset for pagination")

    class Output(Schema):
        items: list  # This will be replaced by the actual model schema list
        count: int = Field(..., description="Total number of items")

    def paginate_queryset(self, queryset, pagination: Input, **kwargs):
        offset = pagination.offset
        limit = pagination.limit
        return {
            "items": queryset[offset : offset + limit],
            "count": queryset.count(),
        }
