# LexoRank-Python

Lightweight, dependency-free Python implementation of LexoRank algorithm for fractional indexing, enabling efficient drag-and-drop sorting, dynamic list reordering, and insertion at any position without full list reordering. Perfect for building sortable task lists, Kanban boards, script editors, or any UI requiring persistent, stable sort keys.

## Core Features

- **Fractional Indexing**: Generate sortable rank keys that work with standard string comparison
- **Insert Between**: Create new ranks between two existing ranks using the `between()` method
- **Bucket Mechanism**: Basic bucket support (0, 1, 2) for handling insertion density
- **Next/Prev Generation**: Generate adjacent ranks with `gen_next()` and `gen_prev()` methods
- **Database Compatible**: Rank strings can be directly stored and sorted in databases

## Limitations

- **No Automatic Rebalancing**: Current implementation lacks automatic rebalancing for long-term insertion density management
- **Manual Intervention Required**: High-density insertion scenarios may require manual rebalancing
- **String Length Growth**: Continued insertion in the same region may lead to increasingly long rank strings

## Use Cases

- Sortable task lists in project management tools
- Kanban board card ordering
- Script/scene ordering in creative applications
- Any UI requiring persistent, stable sort keys

LexoRank-Python
用于分数索引的LexoRank算法的轻量级、无依赖性的Python实现，实现了高效的拖放排序、动态列表重新排序和插入任何位置的操作，而无需完全重新排序列表。非常适合构建可排序的任务列表、看板、脚本编辑器或任何需要持久、稳定排序键的UI。

## 核心功能

- **分数索引**：生成可使用标准字符串比较的排序键
- **中间插入**：使用 `between()` 方法在两个现有排名之间创建新排名
- **桶机制**：基本的桶支持（0、1、2）以处理插入密度
- **前后生成**：使用 `gen_next()` 和 `gen_prev()` 方法生成相邻排名
- **数据库兼容**：排名字符串可直接存储并在数据库中排序

## 局限性

- **无自动重新平衡**：当前实现在长期插入密度管理方面缺少自动重新平衡
- **需要手动干预**：高密度插入场景可能需要手动重新平衡
- **字符串长度增长**：在同一区域持续插入可能导致排名字符串越来越长

## 使用场景

- 项目管理工具中的可排序任务列表
- 看板卡片排序
- 创意应用中的脚本/场景排序
- 任何需要持久、稳定排序键的UI

## 安装

使用 pip:
```bash
pip install py-lexorank
```

或使用 uv (更快的包管理器):
```bash
uv pip install py-lexorank
```

## 使用方法

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