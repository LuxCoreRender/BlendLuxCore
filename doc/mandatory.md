The stuff in the code_style.md document should be followed, but it is ultimately just about 
the readability of the source code.
The following is really important though. If these guidelines are not followed, it can cause 
massive problems - and not just now, but also years in the future.

### Enums

**Always** add an index for each element. 
If the index is missing, we can not reorder elements later and we can not rename identifiers 
without breaking old .blend files.

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
