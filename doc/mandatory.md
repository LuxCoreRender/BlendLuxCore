The stuff in the code_style.md document should be followed, but it is
ultimately just about the readability of the source code.
The following is really important though. If these guidelines are not followed,
it can cause massive problems - and not just now, but also years in the future.

### Imports / Reloadability
To implement reloadability, some very important rules are to be enforced.

First of all, please respect PEP 8:
"Imports are always put at the top of the file, just after any module comments
and docstrings, and before module globals and constants."

Second, be careful to avoid circular imports.
To achieve this, a hierarchy between submodules has been defined. In this
hierarchy, submodule A must not depend on (ie import) submodule B of a higher
rank.

The hierarchy is as follows, from lowest to highest rank:
0. `icons`
1. `utils`
2. `pyluxcore`
3. `properties`
4. `export`
5. `nodes`
6. `operators`
7. `handlers`
8. `engine`
9. `ui`

For instance, it means that `properties` submodule must not import `ui` (but,
of course, `ui` can import `properties`).

A point to emphasize is that `utils` MUST NOT IMPORT ANY OTHER SUBMODULE of
BLC.
If you need to implement some utilities for a given submodule `A`, please
add a submodule `A.utils` to `A`.



### EnumProperty

**Always** add an index for each element. 
If the index is missing, we can not reorder elements later and we can not
rename identifiers without breaking old .blend files.

Wrong: 
```python
items = [
    ("first_item", "First Item", "This is the first item"),
    ("second_item", "Second Item", "This is the second item"),
]
```

Correct:
```python
items = [
    ("first_item", "First Item", "This is the first item", 0),
    ("second_item", "Second Item", "This is the second item", 1),
]
```
(note the 0 and 1 after the descriptions)
