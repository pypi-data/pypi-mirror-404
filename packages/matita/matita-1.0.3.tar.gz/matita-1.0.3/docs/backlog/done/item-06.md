---
title: item-06 Add support for `Worksheet.Rows(index)` ans `Worksheet.Columns(index)`
---

```
# Works now
wks.rows.item(2).style = "Heading 1"

# Not supported
wks.rows(2).style = "Heading 1"
```

`Excel.Range` has an `item` property, but is not a collection, therefore as of v1.0.3 the `__call__` method is not created yet.
I assume that every time the `item` method is available, the `__call__` method should be created as well.
