"""
Apache Doris 数据库连接模块

通过 MySQL 协议连接到 Apache Doris

依赖安装:
-----------
pip install mysql-connector-python

或使用 conda/micromamba:
conda install mysql-connector-python
micromamba install mysql-connector-python
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any


class DorisConnection:
    """Doris 数据库连接类"""

    def __init__(
        self,
        host: str = "192.168.73.11",
        port: int = 9030,
        user: str = "leadingtek",
        password: str = "Aa123456",
        database: Optional[str] = None,
        charset: str = "utf8mb4"
    ):
        """
        初始化 Doris 连接参数

        Args:
            host: Doris FE 服务器地址
            port: Doris FE 查询端口，默认 9030
            user: 用户名
            password: 密码
            database: 数据库名称（可选）
            charset: 字符集，默认 utf8mb4
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection: Optional[mysql.connector.MySQLConnection] = None

    def connect(self) -> bool:
        """
        建立数据库连接

        Returns:
            bool: 连接成功返回 True，失败返回 False
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset=self.charset,
                autocommit=True
            )
            print(f"成功连接到 Doris: {self.host}:{self.port} (charset: {self.charset})")
            return True
        except Error as e:
            print(f"连接 Doris 失败: {e}")
            return False

    def disconnect(self):
        """关闭数据库连接"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("Doris 连接已关闭")

    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        执行查询语句

        Args:
            query: SQL 查询语句

        Returns:
            List[Dict]: 查询结果列表
        """
        if not self.connection or not self.connection.is_connected():
            print("未连接到数据库，请先调用 connect() 方法")
            return []

        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"执行查询失败: {e}")
            return []

    def execute_update(self, query: str) -> bool:
        """
        执行更新/插入/删除语句

        Args:
            query: SQL 语句

        Returns:
            bool: 执行成功返回 True，失败返回 False
        """
        if not self.connection or not self.connection.is_connected():
            print("未连接到数据库，请先调用 connect() 方法")
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            cursor.close()
            return True
        except Error as e:
            print(f"执行语句失败: {e}")
            return False

    def test_connection(self) -> bool:
        """
        测试数据库连接

        Returns:
            bool: 连接正常返回 True，否则返回 False
        """
        if not self.connection or not self.connection.is_connected():
            return False

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            return result[0] == 1
        except Error as e:
            print(f"连接测试失败: {e}")
            return False


def create_doris_connection(
    host: str = "192.168.73.11",
    port: int = 9030,
    user: str = "leadingtek",
    password: str = "Aa123456",
    database: Optional[str] = None,
    charset: str = "utf8mb4"
) -> DorisConnection:
    """
    创建并返回 Doris 连接的便捷函数

    Args:
        host: Doris FE 服务器地址
        port: Doris FE 查询端口
        user: 用户名
        password: 密码
        database: 数据库名称（可选）
        charset: 字符集，默认 utf8mb4

    Returns:
        DorisConnection: Doris 连接对象
    """
    doris = DorisConnection(host, port, user, password, database, charset)
    if doris.connect():
        return doris
    else:
        raise ConnectionError("无法连接到 Doris 数据库")


# 使用示例
if __name__ == "__main__":
    # 创建连接
    doris = create_doris_connection()

    # 测试连接
    if doris.test_connection():
        print("连接测试成功！")

        # 查询示例：显示所有数据库
        print("\n=== 所有数据库 ===")
        databases = doris.execute_query("SHOW DATABASES")
        for db in databases:
            print(f"- {db['Database']}")

        # 查询示例：显示当前数据库的表
        print("\n=== 所有表 ===")
        tables = doris.execute_query("SHOW TABLES")
        for table in tables:
            print(f"- {table}")

    # 关闭连接
    doris.disconnect()
