from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from ninja import Schema
from ninja.pagination import AsyncPaginationBase
from pydantic import Field


class CustomPagination(AsyncPaginationBase):
    class Input(Schema):
        limit: int = Field(10, gt=0, le=30, description="Number of items per page")
        offset: int = Field(0, ge=0, description="Offset for pagination")

    class Output(Schema):
        items: list  # This will be replaced by the actual model schema list
        count: int = Field(..., description="Total number of items")

    def paginate_queryset(
        self, queryset: QuerySet, pagination: Input, request: HttpRequest, **params: Any
    ) -> Any:
        offset = pagination.offset
        limit = pagination.limit
        return {
            "items": queryset[offset : offset + limit],
            "count": self._items_count(queryset),
        }

    async def apaginate_queryset(
        self, queryset: QuerySet, pagination: Input, request: HttpRequest, **params: Any
    ) -> Any:
        offset = pagination.offset
        limit = pagination.limit
        return {
            "items": queryset[offset : offset + limit],
            "count": await self._aitems_count(queryset),
        }
