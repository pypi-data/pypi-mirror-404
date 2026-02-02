---
title: item-07 bug `Excel.Chart.FullSeriesCollection(i)` returns a `FullSeriesCollection` instead of `Series`
---

`Excel.Chart.FullSeriesCollection` is not a collection, despite the name.
It is a set of the collection `Excel.Chart.Series`.
When a class method (like `Excel.Chart.FullSeriesCollection`) has a class with itself an `item` method (like `Excel.Item`), then `return_value_class` of the class method should be set to the same as the `item` method.
