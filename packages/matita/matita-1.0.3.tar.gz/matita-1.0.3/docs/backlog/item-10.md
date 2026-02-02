---
title: item-10 bug `Excel.FullSeriesCollection.Count` returns a `Excel.Series` instead of a `int`
---

Something is wrong in the parsing and/or processing.
```
    "excel.fullseriescollection.count": {
        "title": "FullSeriesCollection.Count property (Excel)",
        ...
        "property_class": "Series",
        ...
    },
```
