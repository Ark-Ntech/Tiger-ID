"""Database optimization utilities"""

from sqlalchemy import event, create_engine, Engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import QueuePool
from typing import Optional
import os
import time

from backend.utils.logging import get_logger

logger = get_logger(__name__)


def optimize_connection_pool(engine: Engine, pool_size: int = 20, max_overflow: int = 40):
    """
    Optimize database connection pool settings
    
    Args:
        engine: SQLAlchemy engine
        pool_size: Number of connections to maintain
        max_overflow: Maximum overflow connections
    """
    # Update pool settings
    if hasattr(engine.pool, 'size'):
        engine.pool.size = pool_size
    if hasattr(engine.pool, 'max_overflow'):
        engine.pool.max_overflow = max_overflow
    
    logger.info(f"Connection pool optimized: size={pool_size}, max_overflow={max_overflow}")


def add_query_optimization_hooks(engine: Engine):
    """
    Add query optimization hooks to SQLAlchemy engine
    
    Args:
        engine: SQLAlchemy engine
    """
    @event.listens_for(engine, "before_cursor_execute")
    def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log slow queries"""
        context._query_start_time = time.time()
    
    @event.listens_for(engine, "after_cursor_execute")
    def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        """Log slow queries"""
        if hasattr(context, '_query_start_time'):
            total = time.time() - context._query_start_time
            if total > 1.0:  # Log queries slower than 1 second
                logger.warning(f"Slow query detected: {total:.2f}s - {statement[:100]}")
    
    logger.info("Query optimization hooks added")


def optimize_query(session: Session, query, use_indexes: bool = True):
    """
    Optimize a SQLAlchemy query
    
    Args:
        session: Database session
        query: SQLAlchemy query
        use_indexes: Whether to use indexes
    
    Returns:
        Optimized query
    """
    # Add query hints for index usage
    if use_indexes:
        # PostgreSQL-specific optimizations
        # Note: This is a placeholder - actual optimization depends on schema
        pass
    
    return query

