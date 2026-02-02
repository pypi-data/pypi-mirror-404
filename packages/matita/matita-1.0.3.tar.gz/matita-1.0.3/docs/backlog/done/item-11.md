---
title: item-11 Fix invalid collection return class types
---

E.g. There is no class `Excel.Area`. Is `Range.Areas` a collection of Ranges?

Could be fixed by updating the documentation.
If the return class of the `Item` method of a collection is defined, it should be prioritised over the class inferred by the name.

```
class Areas:

    def __init__(self, areas=None):
        self.com_object= areas

    def __call__(self, item):
        return Area(self.com_object(item))
```

The documentation mentions that `Areas` is a collection of `Range`s, but it is mentioned in the remarks and not parsed correctly.

> There's no singular Area object; individual members of the Areas collection are Range objects. The Areas collection contains one Range object for each discrete, contiguous range of cells within the selection. If the selection contains only one area, the Areas collection contains a single Range object that corresponds to that selection.

As of v1.0.1, `return_value_class` is null for `excel.areas.item`.
If the `return_value_class` is parsed for the `Areas.Item` method, that fixes the return type there.

As of v1.0.1, the non-existent `Area` class would still initiate `Areas.__call__`.
If I can successfully use `Item` even but collections, that should still fix the issue.
There is an implicit expectation, that there always a `Item` method for each collection and set.

```python
        if self.is_collection:
            item_class = self.object_name
            if self.object_name.endswith("s"):
                item_class = self.object_name[:-1]
            elif self.object_name.endswith("Collection"):
                item_class = self.object_name.removesuffix("Collection")
            else:
                logging.warning(f"Unexpected collection name, unable to identify item class of '{self.process_api_name}'.")
            code.append(f"    def __call__(self, item):")
            code.append(f"        return {item_class}(self.com_object(item))")
            code.append(f"")
        elif self.is_set:
            code.append(f"    def __call__(self, index):")
            code.append(f"        return self.Item(index)")
            code.append(f"")
```
