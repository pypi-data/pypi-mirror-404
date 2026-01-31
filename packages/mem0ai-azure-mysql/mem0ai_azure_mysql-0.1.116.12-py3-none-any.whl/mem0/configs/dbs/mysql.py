from typing import Optional

from mem0.configs.dbs.base import BaseDBConfig


class MySQLConfig(BaseDBConfig):
    """Configuration for MySQL database."""
    
    def __init__(
        self,
        host: Optional[str] = "localhost",
        port: Optional[int] = 3306,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        ssl_enabled: bool = False,
        **kwargs
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ssl_enabled = ssl_enabled
        self.connection_params = kwargs