*[Versão em português](python-conventions.md)*

# Code Conventions — Python

> Complements [`code-conventions.en.md`](./code-conventions.en.md). Applies only to Python
> projects.

---

## Docstrings (Google Style)

Three levels:

**1. Module** — every `.py` starts with a descriptive block:
```python
"""
One-line summary of what the module does.

Responsibilities:
- First responsibility of the module.
- Second responsibility of the module.
"""
```

**2. Function / method** — required when there are ≥ 2 parameters or the return is not
obvious:
```python
def process_item(item: Item, options: Options) -> Result:
    """Process an item according to the given options.

    Args:
        item: Input item to be processed.
        options: Options that control the processing.

    Returns:
        The result of the processing.
    """
```

**3. Class** — docstring on the class and on non-trivial public methods:
```python
class Pipeline:
    """Orchestrates the execution steps of a process.

    Attributes:
        steps: Steps in execution order.
    """
```

---

## Type Hints

- **Every parameter and return** of a function/method must be typed — no exception.
- Native Python 3.10+ syntax: `X | None` instead of `Optional[X]`; `list[int]` instead of
  `List[int]`.
- For forward references (e.g. a type that references itself), add
  `from __future__ import annotations` at the top.
- Avoid `Any` — it hides errors.

```python
# ✅ correct
def process(item: Item) -> Result: ...
def publish(resource: Resource, target: str) -> bool: ...

# ❌ wrong
def process(item):          # no annotations
def publish(...) -> Any:    # Any hides errors
```
