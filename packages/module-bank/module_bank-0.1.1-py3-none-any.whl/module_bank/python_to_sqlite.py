import sys
from pathlib import Path
from typing import List
from .sqlite_module_importer import SQLiteModuleImporter
from .sqlite_meta_path_finder import SQLiteMetaPathFinder


class PythonToSQLite:
    """Python到SQLite的打包工具"""

    def __init__(self, db_path: str = "python_modules.db"):
        self.db_path = db_path
        self.importer = SQLiteModuleImporter(db_path)

    def pack_directory(
        self,
        directory_path: str,
        package_name: str = None,
        include_patterns: List[str] = None,
        exclude_patterns: List[str] = None,
    ):
        """打包整个目录 - 修复版"""
        directory = Path(directory_path)
        if package_name is None:
            package_name = directory.name  # 包名

        if include_patterns is None:
            include_patterns = ["*.py"]
        if exclude_patterns is None:
            exclude_patterns = ["__pycache__", "*.pyc"]

        # 遍历目录
        for py_file in directory.rglob("*.py"):
            # 检查排除模式
            if any(py_file.match(pattern) for pattern in exclude_patterns):
                continue

            # 检查包含模式
            if any(py_file.match(pattern) for pattern in include_patterns):
                # 计算相对于包的路径
                rel_path = py_file.relative_to(directory)
                module_parts = list(rel_path.parts)
                module_parts[-1] = module_parts[-1][:-3]  # 去掉.py

                if module_parts[-1] == "__init__":
                    # 这是包
                    if len(module_parts) > 1:
                        # 子包，例如：subpackage/__init__.py
                        module_name = f"{package_name}.{'.'.join(module_parts[:-1])}"
                    else:
                        # 主包，例如：__init__.py
                        module_name = package_name

                    print(f"打包包: {module_name} (来自: {py_file})")
                    self.importer.add_module(
                        module_name,
                        py_file.read_text(encoding="utf-8"),
                        is_package=True,
                    )
                else:
                    # 普通模块
                    module_name = f"{package_name}.{'.'.join(module_parts)}"

                    print(f"打包模块: {module_name} (来自: {py_file})")
                    self.importer.add_module(
                        module_name,
                        py_file.read_text(encoding="utf-8"),
                        is_package=False,
                    )

    def pack_module(self, module_path: str, module_name: str = None):
        """打包单个模块"""
        module_path = Path(module_path)

        if module_name is None:
            module_name = module_path.stem

        with open(module_path, "r", encoding="utf-8") as f:
            source_code = f.read()

        print(f"打包独立模块: {module_name} (来自: {module_path})")
        self.importer.add_module(module_name, source_code, is_package=False)

    def install_importer(self):
        """安装导入器到sys.meta_path"""
        finder = SQLiteMetaPathFinder(self.db_path)
        # 添加到meta_path开头，优先于文件系统查找
        sys.meta_path.insert(0, finder)
        return finder

    def list_modules(self):
        """列出数据库中的所有模块"""
        cursor = self.importer.connection.execute(
            "SELECT module_name, is_package FROM python_modules ORDER BY module_name"
        )
        return [dict(row) for row in cursor.fetchall()]

    def delete_source_code(self, module_name):
        """删除数据库中的源代码"""
        if module_name is None:
            cursor = self.importer.connection.execute(
                "UPDATE python_modules SET source_code = NULL"
            )
        else:
            cursor = self.importer.connection.execute(
                "UPDATE python_modules SET source_code = NULL WHERE module_name = ?",
                (module_name,),
            )
        self.importer.connection.commit()
        return cursor.rowcount > 0

    def verify_package_structure(self):
        """验证包的完整性"""
        cursor = self.importer.connection.execute(
            "SELECT module_name, is_package FROM python_modules"
        )
        modules = {row["module_name"]: row["is_package"] for row in cursor.fetchall()}

        print("数据库中的模块结构：")
        for module_name, is_package in sorted(modules.items()):
            package_flag = " [包]" if is_package else ""
            print(f"  - {module_name}{package_flag}")

        # 检查包的完整性
        for module_name, is_package in modules.items():
            if "." in module_name and not is_package:
                parent_package = module_name.rsplit(".", 1)[0]
                if parent_package not in modules:
                    print(
                        f"警告：模块 {module_name} 的父包 {parent_package} 不在数据库中"
                    )
                elif not modules[parent_package]:
                    print(
                        f"警告：模块 {module_name} 的父包 {parent_package} 不是一个包"
                    )
