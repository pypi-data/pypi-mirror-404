from typing import Any
from dataclasses import dataclass
from typing import Generic, TypeVar
from contextlib import contextmanager
from sqlalchemy import Delete, Update
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.selectable import Select


def datasource(datasource_name: str, transactional: bool = False):
    """
    多功能数据源装饰器，既可用于类也可用于方法
    :param datasource_name: 数据源名称
    :param transactional: 是否开启事务
    """

class Page(object):
    def __init__(self, page_num: int, page_size: int):
        """
        :param page_num: 页码
        :param page_size: 每页数量
        """

@dataclass
class DataSource:
    db_type: str
    host: str = None
    port: int = None
    user: str = None
    password: str = None
    database: str = None
    sqlite_path: str = None


class DBConfig:

    def __init__(self, primary: str=None, mapper_xml_path: str=None, raw_sql: bool=False, **kwargs) -> None:
        """
        :param primary: 主库名称
        :param mapper_xml_path: xml文件夹路径
        :param raw_sql: 是否打印原始sql语句
        示例:
        {
            "primary": "default",
            "raw_sql": False,
            "mapper_xml_path": "./xml_dir",
            "default": {
                "db_type": "sqlite",
                "sqlite_path": "default.db",
            }
            "mysql_ds": {
                "db_type": "mysql",
                "host": "127.0.0.1",
                "port": 3306,
                "user": "root",
                "password": "123456",
                "database": "test"
            }
        }
        """

class EasyOrmConfig(object):

    def __init__(self, db_config: DBConfig):
        """
        :param db_config: DBConfig   数据库配置
        """

    @classmethod
    def add_datasource_config(cls, datasource_name: str, datasource_config: DataSource):
        """
        :param datasource_name: str   数据源名称
        :param datasource_config: DataSource   数据源配置
        """

    @classmethod
    def remove_datasource(cls, datasource_name: str):
        """
        :param datasource_name: str   数据源名称
        """

def select_one(sql: str):
    """
    装饰器用于 查询单条数据
    :param sql: str
    """

def select_list(sql: str):
    """
    装饰器用于 查询多条数据
    :param sql: str
    """

def select_page(sql: str):
    """
    装饰器用于 查询分页数据
    :param sql: str
    """

def insert(sql: str):
    """
    装饰器用于 插入数据
    :param sql: str
    :return:
    """

def insert_list(sql: str):
    """
    装饰器用于 批量插入数据
    :param sql: str
    :return:
    """

def delete(sql: str):
    """
    装饰器用于 删除数据
    :param sql: str
    :return:
    """

def update(sql: str):
    """
    装饰器用于 更新数据
    :param sql: str
    :return:
    """

@contextmanager
def db_session(datasource_name:str=None):
    """
    指定数据源获取session, 当不指定时使用默认数据源, 执行sqlalchemy 语法
    :param datasource_name: str
    :return: session
    """


T = TypeVar('T', bound=DeclarativeBase)

class BaseMapper(Generic[T]):
    """
    可继承例如:
    class TestMapper(BaseMapper[TestModel]):

    也可不指定泛型继承
    class TestModel(BaseMapper):
    """

    @property
    def session(self):
        """
        获取当前数据库session
        """

    @classmethod
    @contextmanager
    def db_session(cls, datasource_name:str=None):
        """
        指定数据源获取session, 当不指定时使用默认数据源, 执行sqlalchemy 语法
        :param datasource_name: str
        :return: session
        """

    @classmethod
    def switch_datasource(cls, datasource_name: str):
        """
        切换到指定数据源执行sql
        :param datasource_name:
        :return:
        """

    def add(self, data: Any):
        """
        sqlalchemy orm添加数据
        :param data: Any
        """

    def add_all(self, data: list):
        """
        sqlalchemy orm批量添加数据
        :param data: list
        """

    def save_batch(self, data: list):
        """
        sqlalchemy orm2.0 批量添加数据
        :param data: list
        """


    def insert(self, data: Any):
        """
        sqlalchemy orm2.0 添加数据
        :param data: list
        :return: insert_id
        """


    def delete_by_id(self, id: int):
        """
        sqlalchemy orm2.0 通过id删除数据
        :param id: int
        :return: rows
        """

    def delete(self, del_statement: Delete):
        """
        sqlalchemy orm2.0 删除数据
        :param del_statement:
        :return: rows
        """

    def update_by_id(self, data: dict, selective: bool = False):
        """
        sqlalchemy orm2.0 通过id更新数据
        :param data: dict
        :param selective: bool   是否排除为None的数据
        :return: rows
        """

    def update(self, update_stat: Update, data: dict | None = None):
        """
        sqlalchemy orm2.0 更新数据
        :param update_stat:
        :param data:
        :return: rows
        """

    def bulk_update_mappings(self, table_model=None, data_list: list[dict] | None = None):
        """
        sqlalchemy orm2.0 批量更新数据
        :param table_model:  sqlalchemy数据模型
        :param data_list:    数据列表
        :return:
        """

    def select_page_by_orm(self, statement: Select, page: Page = Page(1, 10)):
        """
        orm 分页查询
        :param statement: Select    statement
        :param page: Page(1, 10)
        :return: {"list": [], "total": 0}
        """

    def select_page_by_sql(self, sql_str: str, sql_param: dict | None = None, page: Page = Page(1, 10)):
        """
        原始sql 分页查询
        :param sql_str: str         ori_sql
        :param sql_param: dict      {}
        :param page: Page(1, 10)
        :return: {"list": [], "total": 0}
        """

    def select_all_by_sql(self, sql_str: str, sql_param: dict | None = None):
        """
        原始sql, 查询批量数据
        :param sql_str: str         ori_sql
        :param sql_param: dict      {}
        :return:
        """

    def select_all(self, statement=None):
        """
        当有2.0语法时, 根据语法查出所有数据, 当没有语法, 查表中所有
        :param statement:
        :return:
        """

    def select_one(self, statement=None):
        """
        当有2.0语法时, 根据语法查出1条数据, 当没有语法, 查表中第一条
        :param statement:
        :return:
        """

    def select_by_id(self, id: int):
        """
        2.0语法, 通过id查询数据
        :param id: int
        :return:
        """