---
title: item-04 `matita.office` Classes to `None` if defining com_object is `None`
---

There are operations which return `None` (`null` or `nothing` in VBA).
To be more intuitive, the class instance should be set to `None` directly if the initiation COM object is already `None`.

```python
cell1 = wks.cells(1,1)
cell2 = wks.cells(2,2)
rng = xl_app.intersect(cell1, cell2)

print(rng.com_object is None) # True
print(rng is None) # False, should be True instead
```
