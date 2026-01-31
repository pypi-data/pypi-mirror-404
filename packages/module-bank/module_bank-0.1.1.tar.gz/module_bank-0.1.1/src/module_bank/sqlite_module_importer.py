import sqlite3
import marshal
from pathlib import Path
from typing import Dict


class SQLiteModuleImporter:
    """从SQLite数据库导入Python模块的导入器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """创建存储模块的数据库表"""
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS python_modules (
                module_name TEXT PRIMARY KEY,
                source_code TEXT,
                bytecode BLOB,
                is_package BOOLEAN,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        self.connection.commit()

    def add_module(
        self,
        module_name: str,
        source_code: str,
        is_package: bool = False,
        metadata: Dict = None,
    ):
        """添加模块到数据库"""
        # 编译为字节码
        bytecode = compile(source_code, f"<sqlite_module:{module_name}>", "exec")
        bytecode_blob = marshal.dumps(bytecode)

        metadata_str = str(metadata) if metadata else "{}"

        self.connection.execute(
            """
            INSERT OR REPLACE INTO python_modules 
            (module_name, source_code, bytecode, is_package, metadata)
            VALUES (?, ?, ?, ?, ?)
        """,
            (module_name, source_code, bytecode_blob, is_package, metadata_str),
        )
        self.connection.commit()

    def add_module_from_file(self, file_path: str, module_name: str = None):
        """从文件添加模块"""
        file_path = Path(file_path)

        if module_name is None:
            # 从文件名推导模块名
            module_name = file_path.stem

        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        self.add_module(module_name, source_code)

    def add_package(self, package_path: str, package_name: str = None):
        """添加整个包到数据库"""
        package_path = Path(package_path)

        if package_name is None:
            package_name = package_path.name

        # 添加包目录下的所有.py文件
        for py_file in package_path.rglob("*.py"):
            # 计算模块名
            rel_path = py_file.relative_to(package_path)
            module_parts = list(rel_path.parts)
            module_parts[-1] = module_parts[-1][:-3]  # 去掉.py

            if module_parts[-1] == "__init__":
                # 包本身
                module_name = package_name
                if len(module_parts) > 1:
                    # 子包
                    module_name = f"{package_name}.{'.'.join(module_parts[:-1])}"
                self.add_module(
                    module_name,
                    py_file.read_text(encoding="utf-8"),
                    is_package=True,
                )
            else:
                # 包内的模块
                if len(module_parts) == 1:
                    # 直接子模块
                    module_name = f"{package_name}.{module_parts[0]}"
                else:
                    # 子包内的模块
                    module_name = f"{package_name}.{'.'.join(module_parts)}"

                self.add_module(
                    module_name,
                    py_file.read_text(encoding="utf-8"),
                    is_package=False,
                )
