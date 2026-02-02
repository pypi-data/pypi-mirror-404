# LexoRank Utility Library

lexorank-py is a lightweight, dependency-free Python implementation of the LexoRank algorithm for fractional indexing — enabling efficient drag-and-drop sorting, dynamic list reordering, and insert-anywhere operations without full list rebalancing.
Perfect for building sortable task lists, kanban boards, script editors, or any UI requiring persistent, stable sort keys. 

## Directory Structure

```
py-lexorank/
├── src/py_lexorank/              # Python import package: py_lexorank
│   ├── __init__.py
│   ├── lexorank_key.py           # Business API (recommended)
│   └── lexorank/                 # LexoRank core (algorithm)
│       ├── __init__.py
│       ├── __main__.py           # CLI: python -m py_lexorank.lexorank ...
│       ├── lexo_decimal.py
│       ├── lexo_integer.py
│       ├── lexo_rank.py
│       ├── lexo_rank_bucket.py
│       └── numeral_systems.py
├── examples/                     # Examples (repo-only, not shipped in pip package)
│   └── demo.py
├── tests/
│   └── test_lexorank.py
├── pyproject.toml
└── README.md
```

## Project Overview

LexoRank is a sorting algorithm that allows inserting new elements at arbitrary positions in a list without reordering the entire list. It achieves this by generating new sort keys between two existing sort keys.

### Core Concepts

- **Sort Key**: A string used for database sorting that produces the correct order when sorted lexicographically
- **Fractional Indexing**: The technique of generating new keys between two existing sort keys
- **Bucket**: Used to isolate sorting spaces for different groups, preventing ranks from becoming overly long
- **Number System**: Uses base36 number system for numerical representation

## Usage

### Basic Installation and Usage

Simply import `LexoRankKey` to get started:

```python
from py_lexorank import LexoRankKey

# Initialize the first record for an empty list
first_rank = LexoRankKey.init_for_empty_list()

# Insert between two records
second_rank = LexoRankKey.insert_after(first_rank)
middle_rank = LexoRankKey.insert_between(first_rank, second_rank)

# Insert at the beginning
before_first = LexoRankKey.insert_before(first_rank)

# Generic insertion interface
new_rank = LexoRankKey.insert(prev_rank, next_rank)
```

### Common Usage Scenarios

#### 1. Insert First Record for Empty List
```python
# When the list is empty, insert the first record
first_rank = LexoRankKey.init_for_empty_list()
```

#### 2. Append to End of List
```python
# Append new record to the end of existing list
new_rank = LexoRankKey.insert_after(last_rank)
```

#### 3. Insert Between Two Records
```python
# Insert new record between two known records (common: drag-and-drop sorting)
new_rank = LexoRankKey.insert_between(left_rank, right_rank)
```

#### 4. Insert at Beginning of List
```python
# Insert new record at the beginning of the list
new_rank = LexoRankKey.insert_before(first_rank)
```

#### 5. Generic Insert Interface
```python
# Most flexible insertion method, suitable for all scenarios
new_rank = LexoRankKey.insert(prev_rank, next_rank)
```

### Command Line Tool

LexoRank provides a command-line tool for development and debugging:

```bash
# Option 1: installed console script (recommended)
py-lexorank middle

# Option 2: python -m
# Get minimum rank
python -m py_lexorank.lexorank min

# Get middle rank
python -m py_lexorank.lexorank middle

# Get maximum rank
python -m py_lexorank.lexorank max

# Get next rank for specified rank
python -m py_lexorank.lexorank next "0|0i0000:"

# Get previous rank for specified rank
python -m py_lexorank.lexorank prev "0|0i0000:"

# Generate new rank between two ranks
python -m py_lexorank.lexorank between "0|000000:" "0|zzzzzz:"
```

### Demo Script

Here's the professional and clear English translation suitable for a GitHub README:

Run the demo script to explore various usage scenarios:

1. Run directly (starts with an empty list and auto-inserts the first item):  
```bash
PYTHONPATH=src python examples/demo.py
```

2. Generate a batch of items (starts with an empty list, inserts the first item automatically, then generates X additional ranks in increasing order):  
```bash
PYTHONPATH=src python examples/demo.py --count 20
```   

3. Generate items starting from a specific rank (creates X new ranks in increasing order after the given starting rank):  
   > 💡 Note: The rank contains a | character, which must be quoted in shells like zsh or bash.  
```bash
PYTHONPATH=src python examples/demo.py --start '0|hzzzzz:' --count 10
```

## Tests

From the repo root:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## File Details

Source lives in `src/py_lexorank/`:

- `src/py_lexorank/lexorank_key.py`: business API (string in/out, recommended)
- `src/py_lexorank/lexorank/`: core algorithm + CLI
- `examples/demo.py`: demo / data generator (repo-only)
- `tests/test_lexorank.py`: unit tests

## Business Application Scenarios

### 1. Task List Sorting

In project management applications, users frequently need to adjust the order of tasks. Using LexoRank avoids updating the entire list on each reorder:

```python
from py_lexorank import LexoRankKey

# Create new task and insert into list
def add_task_after(task_list, target_task_id):
    target_task = get_task(target_task_id)
    next_task = get_next_task(target_task_id)
    
    new_rank = LexoRankKey.insert_between(target_task.rank, next_task.rank)
    create_task(rank=new_rank)
```

### 2. Menu Item Sorting

In menu editors, users can adjust menu item order through drag-and-drop:

```python
from py_lexorank import LexoRankKey

# Drag-and-drop sorting: Move item from old_pos to new_pos
def move_menu_item(item_id, old_pos, new_pos):
    if new_pos == 0:  # Move to beginning
        new_rank = LexoRankKey.insert_before(get_first_item().rank)
    elif new_pos == get_last_position():  # Move to end
        new_rank = LexoRankKey.insert_after(get_last_item().rank)
    else:  # Move to middle
        prev_item = get_previous_item(new_pos)
        next_item = get_next_item(new_pos)
        new_rank = LexoRankKey.insert_between(prev_item.rank, next_item.rank)
    
    update_item_rank(item_id, new_rank)
```

### 3. Scene Sorting

In video production applications, users can sort scenes:

```python
from lexorank_key import LexoRankKey

def reorder_scenes(scene_ids, new_order):
    """Reorder scenes according to new order"""
    ordered_scenes = []
    for i, scene_id in enumerate(new_order):
        if i == 0:
            # First scene uses initial rank or rank based on first existing scene
            if len(ordered_scenes) > 0:
                rank = LexoRankKey.insert_before(ordered_scenes[0].rank)
            else:
                rank = LexoRankKey.init_for_empty_list()
        else:
            # Subsequent scenes inserted after previous scene
            rank = LexoRankKey.insert_after(ordered_scenes[-1].rank)
        
        ordered_scenes.append(Scene(id=scene_id, rank=rank))
    
    # Batch update all scene ranks
    bulk_update_scene_ranks(ordered_scenes)
```

## Notes

### Concurrency Safety

When multiple requests concurrently insert into the same gap, duplicate ranks may be generated. It is recommended to:

1. Set unique constraints in the database
2. Add appropriate locks or retry mechanisms at the business layer
3. Handle insertion conflict situations

### Performance Considerations

- LexoRank strings will gradually become longer with frequent insertion operations
- When rank strings become too long, renumbering operations may be necessary
- For sorting large amounts of data, periodic defragmentation is beneficial


## Installation

Install using pip:
```bash
pip install py-lexorank
```

Or using uv (faster package manager):
```bash
uv pip install py-lexorank
```

## Testing

Run unit tests to verify functionality:

```bash
python -m lexorank.test_lexorank
```

Or run test file directly:

```bash
python lexorank/test_lexorank.py
```

## Publishing to PyPI

To publish to PyPI, use the following commands:

Using uv (recommended):
```bash
uv build
uv run twine upload dist/*
```

Or using traditional tools:
```bash
python -m build
twine upload dist/*
```

## License

This project is licensed under the MIT License.
