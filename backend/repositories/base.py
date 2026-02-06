"""Base repository with generic CRUD operations, pagination, and filtering."""

from typing import TypeVar, Generic, Optional, List, Dict, Any, Type
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, or_, and_
from sqlalchemy.sql import func

from backend.database.models import Base

T = TypeVar("T", bound=Base)


class PaginatedResult(Generic[T]):
    """Container for paginated query results."""

    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "data": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
        }


class FilterCriteria:
    """Container for filter criteria."""

    def __init__(
        self,
        field: str,
        operator: str,  # eq, ne, gt, gte, lt, lte, like, ilike, in, not_in, is_null
        value: Any
    ):
        self.field = field
        self.operator = operator
        self.value = value


class BaseRepository(Generic[T]):
    """Base repository with generic CRUD operations.

    Provides a consistent interface for database operations across all entities.
    """

    def __init__(self, db: Session, model_class: Type[T]):
        """Initialize repository.

        Args:
            db: SQLAlchemy database session
            model_class: SQLAlchemy model class this repository manages
        """
        self.db = db
        self.model_class = model_class

    def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by primary key ID.

        Args:
            id: UUID of the entity

        Returns:
            Entity if found, None otherwise
        """
        pk_column = self._get_primary_key_column()
        # Convert UUID to string for SQLite String(36) column comparison
        id_value = str(id) if isinstance(id, UUID) else id
        return self.db.query(self.model_class).filter(pk_column == id_value).first()

    def get_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """Get all entities with optional limit and offset.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of entities
        """
        return self.db.query(self.model_class).limit(limit).offset(offset).all()

    def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        filters: Optional[List[FilterCriteria]] = None
    ) -> PaginatedResult[T]:
        """Get paginated results with optional sorting and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_by: Column name to sort by
            sort_order: 'asc' or 'desc'
            filters: List of filter criteria

        Returns:
            PaginatedResult with items and pagination metadata
        """
        query = self.db.query(self.model_class)

        # Apply filters
        if filters:
            query = self._apply_filters(query, filters)

        # Get total count
        total = query.count()

        # Apply sorting
        if sort_by and hasattr(self.model_class, sort_by):
            column = getattr(self.model_class, sort_by)
            query = query.order_by(desc(column) if sort_order == "desc" else asc(column))

        # Apply pagination
        offset = (page - 1) * page_size
        items = query.limit(page_size).offset(offset).all()

        return PaginatedResult(
            items=items,
            total=total,
            page=page,
            page_size=page_size
        )

    def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with generated ID
        """
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def create_many(self, entities: List[T]) -> List[T]:
        """Create multiple entities in a single transaction.

        Args:
            entities: List of entities to create

        Returns:
            List of created entities
        """
        self.db.add_all(entities)
        self.db.commit()
        for entity in entities:
            self.db.refresh(entity)
        return entities

    def update(self, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity: Entity with updated values

        Returns:
            Updated entity
        """
        self.db.commit()
        self.db.refresh(entity)
        return entity

    def delete(self, entity: T) -> bool:
        """Delete an entity.

        Args:
            entity: Entity to delete

        Returns:
            True if deleted successfully
        """
        self.db.delete(entity)
        self.db.commit()
        return True

    def delete_by_id(self, id: UUID) -> bool:
        """Delete an entity by ID.

        Args:
            id: UUID of entity to delete

        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_id(id)
        if entity:
            return self.delete(entity)
        return False

    def exists(self, id: UUID) -> bool:
        """Check if an entity exists by ID.

        Args:
            id: UUID to check

        Returns:
            True if exists, False otherwise
        """
        pk_column = self._get_primary_key_column()
        # Convert UUID to string for SQLite String(36) column comparison
        id_value = str(id) if isinstance(id, UUID) else id
        return self.db.query(
            self.db.query(self.model_class).filter(pk_column == id_value).exists()
        ).scalar()

    def count(self, filters: Optional[List[FilterCriteria]] = None) -> int:
        """Count entities with optional filtering.

        Args:
            filters: Optional list of filter criteria

        Returns:
            Count of matching entities
        """
        query = self.db.query(func.count()).select_from(self.model_class)
        if filters:
            query = self._apply_filters(query, filters)
        return query.scalar()

    def find_by(self, **kwargs) -> List[T]:
        """Find entities by field values.

        Args:
            **kwargs: Field=value pairs to filter by

        Returns:
            List of matching entities
        """
        from enum import Enum

        query = self.db.query(self.model_class)
        for field, value in kwargs.items():
            if hasattr(self.model_class, field):
                # Convert Enum values to their string values for SQLite compatibility
                if isinstance(value, Enum):
                    value = value.value
                query = query.filter(getattr(self.model_class, field) == value)
        return query.all()

    def find_one_by(self, **kwargs) -> Optional[T]:
        """Find single entity by field values.

        Args:
            **kwargs: Field=value pairs to filter by

        Returns:
            First matching entity or None
        """
        from enum import Enum

        query = self.db.query(self.model_class)
        for field, value in kwargs.items():
            if hasattr(self.model_class, field):
                # Convert Enum values to their string values for SQLite compatibility
                if isinstance(value, Enum):
                    value = value.value
                query = query.filter(getattr(self.model_class, field) == value)
        return query.first()

    def _get_primary_key_column(self):
        """Get the primary key column for this model."""
        mapper = self.model_class.__mapper__
        pk_columns = mapper.primary_key
        if pk_columns:
            return pk_columns[0]
        raise ValueError(f"No primary key found for {self.model_class.__name__}")

    def _apply_filters(self, query, filters: List[FilterCriteria]):
        """Apply filter criteria to a query.

        Args:
            query: SQLAlchemy query
            filters: List of filter criteria

        Returns:
            Query with filters applied
        """
        from enum import Enum

        for criteria in filters:
            if not hasattr(self.model_class, criteria.field):
                continue

            column = getattr(self.model_class, criteria.field)

            # Convert Enum values to their string values for SQLite compatibility
            value = criteria.value
            if isinstance(value, Enum):
                value = value.value

            if criteria.operator == "eq":
                query = query.filter(column == value)
            elif criteria.operator == "ne":
                query = query.filter(column != value)
            elif criteria.operator == "gt":
                query = query.filter(column > value)
            elif criteria.operator == "gte":
                query = query.filter(column >= value)
            elif criteria.operator == "lt":
                query = query.filter(column < value)
            elif criteria.operator == "lte":
                query = query.filter(column <= value)
            elif criteria.operator == "like":
                query = query.filter(column.like(f"%{value}%"))
            elif criteria.operator == "ilike":
                query = query.filter(column.ilike(f"%{value}%"))
            elif criteria.operator == "in":
                # Convert list of enums to their values
                if value and isinstance(value, list) and len(value) > 0 and isinstance(value[0], Enum):
                    value = [v.value for v in value]
                query = query.filter(column.in_(value))
            elif criteria.operator == "not_in":
                # Convert list of enums to their values
                if value and isinstance(value, list) and len(value) > 0 and isinstance(value[0], Enum):
                    value = [v.value for v in value]
                query = query.filter(~column.in_(value))
            elif criteria.operator == "is_null":
                if value:
                    query = query.filter(column.is_(None))
                else:
                    query = query.filter(column.isnot(None))

        return query
