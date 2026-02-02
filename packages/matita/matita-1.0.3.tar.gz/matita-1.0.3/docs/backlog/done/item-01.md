---
title: item-01 Add snake case aliases for all methods and properties
---
VBA properties and methods are written in [CamelCase](https://developer.mozilla.org/en-US/docs/Glossary/Camel_case).
In Python, the [PEP8](https://peps.python.org/pep-0008/#function-and-variable-names) naming convention is [snake_case](https://developer.mozilla.org/en-US/docs/Glossary/Snake_case).

> Function names should be lowercase, with words separated by underscores as necessary to improve readability.

Add snake_case aliases for all methods and properties to improve intuitiveness for Python developers.

```python
from matita.office import excel
wks = excel.Application().workbooks.open("file.xlsx").worksheets(1)

# Supported
wks.AutoFilter
wks.autofilter()

# New
wks.auto_filter
```
