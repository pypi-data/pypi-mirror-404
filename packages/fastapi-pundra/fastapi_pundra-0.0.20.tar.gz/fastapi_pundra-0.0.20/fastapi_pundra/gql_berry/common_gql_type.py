import strawberry
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

@strawberry.type(description="Generic list type with pagination")
class PaginatedList(Generic[T]):
    data: List[T]
    pagination: strawberry.scalars.JSON
    additional_data: Optional[strawberry.scalars.JSON] = None