# LexoRank Python工具库

lexorank-py是用于分数索引的lexorank算法的轻量级、无依赖性的Python实现，实现了高效的拖放排序、动态列表重新排序和插入任何位置的操作，而无需完全重新平衡列表。
非常适合构建可排序的任务列表、看板、脚本编辑器或任何需要持久、稳定排序键的UI。

## 目录结构

```
lexorank-utils/
├── lexorank/                 # LexoRank 核心实现
│   ├── __init__.py           # 包初始化文件
│   ├── __main__.py           # CLI 工具入口
│   ├── demo.py               # 演示脚本
│   ├── lexo_decimal.py       # 定点小数实现
│   ├── lexo_integer.py       # 大整数实现
│   ├── lexo_rank.py          # LexoRank 核心实现
│   ├── lexo_rank_bucket.py   # 分桶实现
│   ├── numeral_systems.py    # 进制系统定义
│   └── test_lexorank.py      # 测试文件
├── lexorank_key.py           # 业务层API封装
└── README.md                 # 本文档
```

## 项目概述

LexoRank 是一种排序算法，允许在列表中任意位置插入新元素而无需重新排列整个列表。它通过在两个已存在的排序键之间生成新的排序键来实现这一点。

### 核心概念

- **排序键（Rank Key）**：用于数据库排序的字符串，按字典序排序即可得到正确的顺序
- **分数索引（Fractional Indexing）**：在两个排序键之间生成新键的技术
- **分桶（Bucket）**：用于隔离不同分组的排序空间，避免 rank 过度变长
- **进制系统**：使用 base36 进制系统进行数值表示

## 使用方法

### 基础安装和使用

直接导入 `LexoRankKey` 类即可开始使用：

```python
from lexorank_key import LexoRankKey

# 初始化空列表的第一条记录
first_rank = LexoRankKey.init_for_empty_list()

# 在两条记录之间插入
second_rank = LexoRankKey.insert_after(first_rank)
middle_rank = LexoRankKey.insert_between(first_rank, second_rank)

# 插入到最前面
before_first = LexoRankKey.insert_before(first_rank)

# 通用插入接口
new_rank = LexoRankKey.insert(prev_rank, next_rank)
```

### 常见使用场景

#### 1. 空列表插入第一条记录
```python
# 当列表为空时，插入第一条记录
first_rank = LexoRankKey.init_for_empty_list()
```

#### 2. 追加到列表末尾
```python
# 在现有列表末尾追加新记录
new_rank = LexoRankKey.insert_after(last_rank)
```

#### 3. 在两条记录之间插入
```python
# 在两个已知记录之间插入新记录（常用：拖拽排序）
new_rank = LexoRankKey.insert_between(left_rank, right_rank)
```

#### 4. 插入到列表开头
```python
# 在列表开头插入新记录
new_rank = LexoRankKey.insert_before(first_rank)
```

#### 5. 通用插入接口
```python
# 最灵活的插入方式，适用于所有场景
new_rank = LexoRankKey.insert(prev_rank, next_rank)
```

### 命令行工具

LexoRank 提供了命令行工具用于开发和调试：

```bash
# 获取最小 rank
python -m lexorank min

# 获取中间 rank
python -m lexorank middle

# 获取最大 rank
python -m lexorank max

# 获取指定 rank 的下一个 rank
python -m lexorank next "0|0i0000:"

# 获取指定 rank 的上一个 rank
python -m lexorank prev "0|0i0000:"

# 在两个 rank 之间生成新的 rank
python -m lexorank between "0|000000:" "0|zzzzzz:"
```

### 演示脚本

运行演示脚本来查看各种使用场景：

1. 直接运行（默认空列表自动插入第一条）
```bash
python lexorank/demo.py
```
2. 指定批量生成数量（默认空列表自动插入第一条，根据生成的第一条一次生成 X 个递增 rank）
```bash
python lexorank/demo.py --count 20
```
3. 指定起始 rank（从某个已有 rank 后面开始批量生成X 个递增 rank）
注意：rank 里有 |，在 zsh 里必须用引号包起来
```bash
python lexorank/demo.py --start '0|hzzzzz:' --count 10
```

## 文件详细说明

### lexorank/lexo_rank.py

这是 LexoRank 的核心实现类，提供了排序键的主要功能：


### lexorank/lexo_rank_bucket.py

实现了 LexoRank 的分桶概念，用于隔离不同的排序空间：


### lexorank/lexo_decimal.py

实现定点小数运算，用于在两个 rank 之间计算中值：

### lexorank/lexo_integer.py

实现大整数运算，作为 LexoDecimal 的基础：


### lexorank/numeral_systems.py

定义进制系统，当前使用 base36：

### lexorank_key.py

业务层 API 封装，提供面向字符串的操作接口：

- **LexoRankKey 类**：业务层入口类，所有方法接受和返回字符串

### lexorank/demo.py

演示脚本，展示常见使用场景：

- **基本场景演示**：空列表、追加、中间插入等
- **批量生成工具**：用于生成测试数据
- **命令行参数支持**：支持参数化运行

### lexorank/test_lexorank.py

单元测试文件，验证所有功能的正确性：


### lexorank/__main__.py

命令行接口实现，提供开发和调试工具。

## 业务场景应用

### 1. 任务列表排序

在项目管理应用中，用户经常需要调整任务的顺序。使用 LexoRank 可以避免每次重排都更新整个列表：

```python
from lexorank_key import LexoRankKey

# 创建新任务并插入到列表中
def add_task_after(task_list, target_task_id):
    target_task = get_task(target_task_id)
    next_task = get_next_task(target_task_id)
    
    new_rank = LexoRankKey.insert_between(target_task.rank, next_task.rank)
    create_task(rank=new_rank)
```

### 2. 菜单项排序

在菜单编辑器中，用户可以通过拖拽调整菜单项的顺序：

```python
from lexorank_key import LexoRankKey

# 拖拽排序：将项目从 old_pos 移动到 new_pos
def move_menu_item(item_id, old_pos, new_pos):
    if new_pos == 0:  # 移到开头
        new_rank = LexoRankKey.insert_before(get_first_item().rank)
    elif new_pos == get_last_position():  # 移到末尾
        new_rank = LexoRankKey.insert_after(get_last_item().rank)
    else:  # 移到中间
        prev_item = get_previous_item(new_pos)
        next_item = get_next_item(new_pos)
        new_rank = LexoRankKey.insert_between(prev_item.rank, next_item.rank)
    
    update_item_rank(item_id, new_rank)
```

### 3. 场景排序

在视频制作应用中，用户可以对场景进行排序：

```python
from lexorank_key import LexoRankKey

def reorder_scenes(scene_ids, new_order):
    """根据新顺序重新排列场景"""
    ordered_scenes = []
    for i, scene_id in enumerate(new_order):
        if i == 0:
            # 第一个场景使用初始 rank 或者基于第一个现有场景的 rank
            if len(ordered_scenes) > 0:
                rank = LexoRankKey.insert_before(ordered_scenes[0].rank)
            else:
                rank = LexoRankKey.init_for_empty_list()
        else:
            # 后续场景插入到前一个场景之后
            rank = LexoRankKey.insert_after(ordered_scenes[-1].rank)
        
        ordered_scenes.append(Scene(id=scene_id, rank=rank))
    
    # 批量更新所有场景的 rank
    bulk_update_scene_ranks(ordered_scenes)
```

## 注意事项

### 并发安全

当多个请求并发向同一缝隙插入时，可能会生成重复的 rank。建议：

1. 在数据库中设置唯一约束
2. 在业务层添加适当的锁或重试机制
3. 处理插入冲突的情况

### 性能考虑

- LexoRank 字符串会随着频繁的插入操作逐渐变长
- 当 rank 字符串变得过长时，可能需要执行重新编号操作
- 对于大量数据的排序，定期进行碎片整理是有益的

## 安装

使用 pip 安装：
```bash
pip install py-lexorank
```

或使用 uv (更快的包管理器)：
```bash
uv pip install py-lexorank
```

## 测试

运行单元测试验证功能：

```bash
python -m lexorank.test_lexorank
```

或直接运行测试文件：

```bash
python lexorank/test_lexorank.py
```

## 发布到 PyPI

要发布到 PyPI，使用以下命令：

使用 uv (推荐)：
```bash
uv build
uv run twine upload dist/*
```

或使用传统工具：
```bash
python -m build
twine upload dist/*
```

## 许可证

本项目遵循 MIT 许可证。