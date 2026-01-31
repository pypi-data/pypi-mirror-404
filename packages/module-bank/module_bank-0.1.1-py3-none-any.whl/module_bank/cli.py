import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Python模块SQLite打包工具")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 打包命令
    pack_parser = subparsers.add_parser("pack", help="打包模块到SQLite")
    pack_parser.add_argument("source", help="源文件或目录")
    pack_parser.add_argument("--db", default="modules.db", help="数据库文件路径")
    pack_parser.add_argument("--name", help="模块名（默认从文件名推断）")

    # 列出命令
    list_parser = subparsers.add_parser("list", help="列出数据库中的模块")
    list_parser.add_argument("--db", default="modules.db", help="数据库文件路径")

    # 删除原代码
    delete_source_parser = subparsers.add_parser(
        "delete_source", help="删除数据库中的源代码"
    )
    delete_source_parser.add_argument(
        "--db", default="modules.db", help="数据库文件路径"
    )
    delete_source_parser.add_argument("--module", help="要删除的模块名")

    # 安装命令
    install_parser = subparsers.add_parser("install", help="安装SQLite导入器")
    install_parser.add_argument("--db", default="modules.db", help="数据库文件路径")

    args = parser.parse_args()

    if args.command == "pack":
        from .python_to_sqlite import PythonToSQLite

        packer = PythonToSQLite(args.db)

        if Path(args.source).is_dir():
            packer.pack_directory(args.source)
            print(f"已打包目录: {args.source}")
        else:
            packer.pack_module(args.source, args.name)
            print(f"已打包模块: {args.source}")

    elif args.command == "list":
        from .python_to_sqlite import PythonToSQLite

        packer = PythonToSQLite(args.db)
        modules = packer.list_modules()

        print(f"数据库中的模块 ({args.db}):")
        for module in modules:
            package_flag = " [包]" if module["is_package"] else ""
            print(f"  - {module['module_name']}{package_flag}")

    elif args.command == "delete_source":
        from .python_to_sqlite import PythonToSQLite

        packer = PythonToSQLite(args.db)
        if args.module:
            packer.delete_source_code(args.module)
        else:
            packer.delete_source_code(None)

    elif args.command == "install":
        from .python_to_sqlite import PythonToSQLite

        packer = PythonToSQLite(args.db)
        packer.install_importer()
        print(f"已安装SQLite导入器，可以从数据库导入模块了！")

        # 保持程序运行以便交互使用
        import code

        code.interact(local=locals())

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
