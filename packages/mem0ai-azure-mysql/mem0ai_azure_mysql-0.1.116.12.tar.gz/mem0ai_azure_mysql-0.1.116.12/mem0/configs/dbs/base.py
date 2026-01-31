from abc import ABC
from typing import Optional


class BaseDBConfig(ABC):
    """
    Config for Database.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
        ssl_enabled: bool = False,
    ):
        """
        Initializes a configuration class instance for the Database.

        :param host: Database host, defaults to None
        :type host: Optional[str], optional
        :param port: Database port, defaults to None
        :type port: Optional[int], optional
        :param user: Database user, defaults to None
        :type user: Optional[str], optional
        :param password: Database password, defaults to None
        :type password: Optional[str], optional
        :param database: Database name, defaults to None
        :type database: Optional[str], optional
        :param ssl_enabled: Whether to use SSL for the connection, defaults to False
        :type ssl_enabled: bool, optional
        """

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ssl_enabled = ssl_enabled
