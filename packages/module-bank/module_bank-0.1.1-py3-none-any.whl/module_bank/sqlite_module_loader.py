import sqlite3
import importlib
import importlib.abc
import marshal
import types


class SQLiteModuleLoader(importlib.abc.Loader):
    """SQLite模块加载器"""

    def __init__(
        self, db_connection: sqlite3.Connection, module_name: str, db_path: str = None
    ):
        self.db_connection = db_connection
        self.module_name = module_name
        self.db_path = db_path
        self.db_connection.row_factory = sqlite3.Row

    def create_module(self, spec):
        """创建模块对象"""
        # 获取模块信息
        cursor = self.db_connection.execute(
            "SELECT is_package FROM python_modules WHERE module_name = ?",
            (self.module_name,),
        )
        row = cursor.fetchone()

        if row and row["is_package"]:
            # 创建包模块
            module = types.ModuleType(self.module_name)
            module.__path__ = []  # 包需要有__path__属性
            module.__package__ = self.module_name
            return module
        else:
            # 创建普通模块
            return None  # 使用默认创建方式

    def exec_module(self, module):
        """执行模块代码"""
        cursor = self.db_connection.execute(
            "SELECT bytecode, source_code, is_package FROM python_modules WHERE module_name = ?",
            (self.module_name,),
        )
        row = cursor.fetchone()

        if not row:
            raise ImportError(f"No module named '{self.module_name}' in database")

        # 从字节码加载
        bytecode = marshal.loads(row["bytecode"])

        # 在模块的命名空间中执行字节码
        exec(bytecode, module.__dict__)

        # 如果是包，设置__path__属性
        if row["is_package"]:
            module.__path__ = []
            module.__package__ = self.module_name

        # 设置模块的__file__属性为数据库路径
        module.__file__ = f"sqlite://{self.db_path}/{self.module_name}"

        return module
