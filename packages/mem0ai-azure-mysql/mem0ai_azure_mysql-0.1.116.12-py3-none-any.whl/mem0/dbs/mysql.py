import ssl
import logging
import threading
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from mem0.configs.dbs.mysql import MySQLConfig
from mem0.dbs.base import DBBase

logger = logging.getLogger(__name__)


class MySQLManager(DBBase):
    """MySQL implementation of DBBase for managing memory history using SQLAlchemy."""
    
    def __init__(self, config: Optional[MySQLConfig] = None):
        super().__init__(config)
        if config is None:
            self.config = MySQLConfig()
        else:
            self.config = config
            
        self.engine: Optional[Engine] = None
        self.Session: Optional[sessionmaker] = None
        self._lock = threading.Lock()
        self._connect()
        self._migrate_history_table()
        self._create_history_table()

    def _connect(self) -> None:
        """Establish connection to MySQL database using SQLAlchemy."""
        try:
            # Build connection URL
            connection_url = self._build_connection_url()
            
            # Create engine with connection pooling
            connect_args = {}
            if hasattr(self.config, 'connection_params'):
                # Add valid MySQL connection parameters
                valid_params = {
                    'ssl_ca', 'ssl_cert', 'ssl_key', 'ssl_verify_cert', 'ssl_verify_identity',
                    'connect_timeout', 'charset', 'init_command'
                }
                for key, value in self.config.connection_params.items():
                    if key in valid_params:
                        connect_args[key] = value
            
            if self.config.ssl_enabled:
                connect_args['ssl'] = ssl.create_default_context()
            
            self.engine = create_engine(
                connection_url,
                connect_args=connect_args,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            
            self.Session = sessionmaker(bind=self.engine)
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("Successfully connected to MySQL database using SQLAlchemy")
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to connect to MySQL: {e}")
            raise

    def _build_connection_url(self) -> str:
        """Build SQLAlchemy connection URL for MySQL."""
        # Use PyMySQL as the driver (more reliable than mysqlclient)
        url_parts = ["mysql+pymysql://"]
        
        if self.config.user:
            url_parts.append(self.config.user)
            if self.config.password:
                url_parts.append(f":{self.config.password}")
            url_parts.append("@")
        
        url_parts.append(self.config.host or "localhost")
        
        if self.config.port:
            url_parts.append(f":{self.config.port}")
        
        if self.config.database:
            url_parts.append(f"/{self.config.database}")
        
        return "".join(url_parts)

    def _migrate_history_table(self) -> None:
        """
        If a pre-existing history table had the old schema,
        rename it, create the new schema, copy the intersecting data, then
        drop the old table.
        """
        with self._lock:
            if self.engine is None:
                raise RuntimeError("Database connection is not established")
            try:
                with self.engine.begin() as conn:
                    # Check if history table exists
                    result = conn.execute(text("""
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = DATABASE()
                        AND table_name = 'history'
                    """))
                    
                    count = result.scalar()
                    if count == 0:
                        return  # nothing to migrate
                    
                    # Get current table columns
                    result = conn.execute(text("""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_schema = DATABASE()
                        AND table_name = 'history'
                    """))
                    old_cols = {row[0] for row in result.fetchall()}
                    
                    expected_cols = {
                        "id",
                        "memory_id",
                        "old_memory",
                        "new_memory",
                        "event",
                        "created_at",
                        "updated_at",
                        "is_deleted",
                        "actor_id",
                        "role",
                    }
                    
                    if old_cols == expected_cols:
                        return
                    
                    logger.info("Migrating history table to new schema (no convo columns).")
                    
                    # Clean up any existing history_old table from previous failed migration
                    conn.execute(text("DROP TABLE IF EXISTS history_old"))
                    
                    # Rename the current history table
                    conn.execute(text("ALTER TABLE history RENAME TO history_old"))
                    
                    # Create the new history table with updated schema
                    conn.execute(text("""
                        CREATE TABLE history (
                            id           VARCHAR(36) PRIMARY KEY,
                            memory_id    TEXT,
                            old_memory   TEXT,
                            new_memory   TEXT,
                            event        TEXT,
                            created_at   TIMESTAMP NULL,
                            updated_at   TIMESTAMP NULL,
                            is_deleted   INT,
                            actor_id     TEXT,
                            role         TEXT
                        )
                    """))
                    
                    # Copy data from old table to new table
                    intersecting = list(expected_cols & old_cols)
                    if intersecting:
                        cols_str = ", ".join(f"`{col}`" for col in intersecting)
                        query = f"INSERT INTO history ({cols_str}) SELECT {cols_str} FROM history_old"
                        conn.execute(text(query))
                    
                    # Drop the old table
                    conn.execute(text("DROP TABLE history_old"))
                    
                    logger.info("History table migration completed successfully.")
                    
            except SQLAlchemyError as e:
                logger.error(f"History table migration failed: {e}")
                raise

    def _create_history_table(self) -> None:
        """Create the history table if it doesn't exist."""
        with self._lock:
            if self.engine is None:
                raise RuntimeError("Database connection is not established")
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS history (
                            id           VARCHAR(36) PRIMARY KEY,
                            memory_id    TEXT,
                            old_memory   TEXT,
                            new_memory   TEXT,
                            event        TEXT,
                            created_at   TIMESTAMP NULL,
                            updated_at   TIMESTAMP NULL,
                            is_deleted   INT,
                            actor_id     TEXT,
                            role         TEXT
                        )
                    """))
                    
            except SQLAlchemyError as e:
                logger.error(f"Failed to create history table: {e}")
                raise

    def add_history(
        self,
        memory_id: str,
        old_memory: Optional[str],
        new_memory: Optional[str],
        event: str,
        *,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
        is_deleted: int = 0,
        actor_id: Optional[str] = None,
        role: Optional[str] = None,
    ) -> None:
        """Add a history record to the database.
        
        :param memory_id: The ID of the memory being tracked
        :param old_memory: The previous memory content
        :param new_memory: The new memory content
        :param event: The type of event that occurred
        :param created_at: When the record was created
        :param updated_at: When the record was last updated
        :param is_deleted: Whether the record is deleted (0 or 1)
        :param actor_id: ID of the actor who made the change
        :param role: Role of the actor
        """
        with self._lock:
            if self.engine is None:
                raise RuntimeError("Database connection is not established")
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("""
                        INSERT INTO history (
                            id, memory_id, old_memory, new_memory, event,
                            created_at, updated_at, is_deleted, actor_id, role
                        )
                        VALUES (:id, :memory_id, :old_memory, :new_memory, :event,
                                :created_at, :updated_at, :is_deleted, :actor_id, :role)
                    """), {
                        "id": str(uuid.uuid4()),
                        "memory_id": memory_id,
                        "old_memory": old_memory,
                        "new_memory": new_memory,
                        "event": event,
                        "created_at": created_at,
                        "updated_at": updated_at,
                        "is_deleted": is_deleted,
                        "actor_id": actor_id,
                        "role": role,
                    })
                    
            except SQLAlchemyError as e:
                logger.error(f"Failed to add history record: {e}")
                raise

    def get_history(self, memory_id: str) -> List[Dict[str, Any]]:
        """Retrieve history records for a given memory ID.
        
        :param memory_id: The ID of the memory to get history for
        :return: List of history records as dictionaries
        """
        with self._lock:
            if self.engine is None:
                raise RuntimeError("Database connection is not established")
            
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, memory_id, old_memory, new_memory, event,
                           created_at, updated_at, is_deleted, actor_id, role
                    FROM history
                    WHERE memory_id = :memory_id
                    ORDER BY created_at ASC, updated_at ASC
                """), {"memory_id": memory_id})
                
                rows = result.fetchall()

        return [
            {
                "id": r.id,
                "memory_id": r.memory_id,
                "old_memory": r.old_memory,
                "new_memory": r.new_memory,
                "event": r.event,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
                "is_deleted": bool(r.is_deleted),
                "actor_id": r.actor_id,
                "role": r.role,
            }
            for r in rows
        ]

    def reset(self) -> None:
        """Reset/clear all data in the database."""
        with self._lock:
            if self.engine is None:
                raise RuntimeError("Database connection is not established")
            try:
                with self.engine.begin() as conn:
                    conn.execute(text("DROP TABLE IF EXISTS history"))
                self._create_history_table()
                
            except SQLAlchemyError as e:
                logger.error(f"Failed to reset history table: {e}")
                raise

    def close(self) -> None:
        """Close the database connection and clean up resources."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.Session = None