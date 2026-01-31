import sqlite3
import importlib
import importlib.abc
import importlib.util
from .sqlite_module_loader import SQLiteModuleLoader


class SQLiteMetaPathFinder(importlib.abc.MetaPathFinder):
    """SQLite元路径查找器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        # 缓存模块查找结果
        self.module_cache = {}
        self._load_module_cache()

    def _load_module_cache(self):
        """加载所有模块到缓存"""
        cursor = self.connection.execute(
            "SELECT module_name, is_package FROM python_modules"
        )
        for row in cursor.fetchall():
            self.module_cache[row["module_name"]] = row["is_package"]

    def find_spec(self, fullname, path=None, target=None):
        """查找模块规范"""
        # 检查模块是否在数据库中
        if fullname in self.module_cache:
            # 创建模块规范
            spec = importlib.util.spec_from_loader(
                fullname,
                SQLiteModuleLoader(self.connection, fullname, self.db_path),
                origin=f"sqlite://{self.db_path}",
                is_package=self.module_cache[fullname],
            )
            return spec

        # 如果不是完整模块名，检查是否可能是包的子模块
        # 例如：my_package.package_module
        if "." in fullname:
            # 检查完整模块名是否在数据库中
            if fullname in self.module_cache:
                spec = importlib.util.spec_from_loader(
                    fullname,
                    SQLiteModuleLoader(self.connection, fullname, self.db_path),
                    origin=f"sqlite://{self.db_path}",
                    is_package=self.module_cache[fullname],
                )
                return spec

        return None
