# Python Module Bank - SQLite 模块打包系统

一个将Python模块打包到SQLite数据库，并支持从数据库直接导入模块的工具系统。

## 🌟 特性

- **单文件分发** - 将所有模块打包到单个SQLite数据库文件
- **源代码保护** - 模块以编译后的字节码形式存储
- **动态导入** - 运行时直接从数据库加载模块，无需文件系统
- **完整包支持** - 支持包结构和子模块导入
- **CLI工具** - 提供完整的命令行接口
- **导入钩子** - 无缝集成Python导入系统

## 📦 安装

### 从源码安装

```bash
git clone http://124.71.68.6:3000/chakcy/module_bank.git
cd module-bank
pip install -e .
```

### 依赖要求

- Python 3.7+
- 无需额外依赖（仅使用标准库）

## 🚀 快速开始

### 1. 创建示例模块

```python
# my_module.py
def hello():
    print("Hello from my_module!")
    return "success"
```

### 2. 打包模块到数据库

```python
# pack_example.py
from module_bank import PythonToSQLite

packer = PythonToSQLite("my_modules.db")
packer.pack_module("my_module.py", "my_module")
packer.pack_directory("my_package/")
```

### 3. 从数据库导入

```python
from module_bank import PythonToSQLite

# 安装导入器
packer = PythonToSQLite("my_modules.db")
finder = packer.install_importer()

# 现在可以从数据库导入模块了！
import my_module
import my_package.package_module

my_module.hello()
my_package.package_module.hello()
```

## 📖 详细使用

### 命令行工具

```python
# 打包模块或目录
mb pack my_package --db modules.db

# 列出数据库中的模块
mb list --db modules.db

# 安装导入器并进入交互模式
mb install --db modules.db
```

### 编程接口

#### 打包模块

```python
from module_bank import PythonToSQLite

packer = PythonToSQLite("modules.db")

# 打包单个模块
packer.pack_module("module.py", "module_name")

# 打包整个目录（自动识别包结构）
packer.pack_directory("my_package/")

# 验证包结构
packer.verify_package_structure()
```

#### 导入模块

```python
from module_bank import PythonToSQLite
import sys

packer = PythonToSQLite("modules.db")

# 安装导入器到sys.meta_path
finder = packer.install_importer()

# 列出所有可用模块
modules = packer.list_modules()
for module in modules:
    print(f"{module['module_name']} {'[包]' if module['is_package'] else ''}")

# 导入数据库中的模块
import my_package
import my_package.submodule
```

## 🏗️ 架构设计

### 核心组件

```python
src/module_bank/
├── python_to_sqlite.py     # 主打包类
├── sqlite_module_importer.py # 数据库存储管理器
├── sqlite_meta_path_finder.py # 元路径查找器
├── sqlite_module_loader.py # 模块加载器
├── cli.py                 # 命令行接口
└── __init__.py           # 模块导出
```

### 数据流

```text
1. 打包阶段:
   .py文件 → 编译为字节码 → 存储到SQLite数据库

2. 导入阶段:
   导入请求 → MetaPathFinder查找 → ModuleLoader加载 → 执行模块
```

### 数据库模式

```sql
CREATE TABLE python_modules (
    module_name TEXT PRIMARY KEY,
    source_code TEXT,      -- 源代码（可选）
    bytecode BLOB,         -- 编译后的字节码
    is_package BOOLEAN,    -- 是否是包
    metadata TEXT,         -- 元数据（JSON格式）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## 🔧 高级功能

### 排除模式

```python
# 打包时排除特定文件
packer.pack_directory(
    "my_project/",
    exclude_patterns=["*_test.py", "*.pyc", "__pycache__"]
)
```

### 元数据存储

```python
# 为模块添加元数据
packer.importer.add_module(
    "my_module",
    source_code,
    is_package=False,
    metadata={"version": "1.0", "author": "me"}
)
```

### 混合导入

```python
# 可以同时使用文件系统和数据库导入
# 数据库导入器优先级更高
import sys
from module_bank import PythonToSQLite

packer = PythonToSQLite("modules.db")
finder = packer.install_importer()  # 插入到meta_path开头

# 如果需要文件系统优先，可以调整插入位置
sys.meta_path.append(finder)
```

## ⚠️ 注意事项

### 安全性

- 模块字节码直接执行，确保数据库来源可信
- 生产环境建议添加代码签名验证

### 兼容性

- 字节码不跨Python版本兼容
- 不支持C扩展模块
- 不支持需要文件系统资源的模块（如__file__依赖）

### 性能

- **启动时**：有一次性数据库查询和反序列化开销
- **运行时**：与传统导入性能相同（使用sys.modules缓存）
- **最佳适用**：长期运行的服务、桌面应用

### 更新模块

```python
# 重新打包会自动更新
packer.pack_module("updated_module.py", "module_name")
```

### 删除模块

```sql
-- 直接从数据库删除
DELETE FROM python_modules WHERE module_name = 'module_to_remove';
```

### 备份与恢复

```bash
# 数据库是单个文件，易于备份
cp modules.db modules.backup.db

# 恢复
cp modules.backup.db modules.db
```

## 📚 应用场景

1. 商业软件分发 - 保护源代码知识产权
2. 插件系统 - 动态加载数据库中的插件模块
3. 教育平台 - 安全分发练习代码
4. 微服务 - 打包多个服务模块到单个文件
5. 嵌入式系统 - 减少文件系统依赖

---
**注意**: 本工具主要用于模块分发和部署场景，不适合开发阶段的频繁修改。
