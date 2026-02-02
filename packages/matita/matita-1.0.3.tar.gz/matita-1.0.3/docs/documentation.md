---
title: Documentation
---

## Quickstart

You start by creating an object for the application you need.

Unlike starting Microsoft Office normally, all application objects are by default invisible.
I recommend making the application visible as long as you are developing.
Once your code is stable, you may decide to keep the application invisible unless an exception arises.

```python
from matita.office import access as ac, excel as xl, outlook as ol, powerpoint as pp, word as wd

ac_app = ac.Application()
ac_app.visible = True

xl_app = xl.Application()
xl_app.visible = True

ol_app = ol.Application()
ol_app.visible = True

pp_app = pp.Application()
pp_app.visible = True

wd_app = wd.Application()
wd_app.visible = True
```

With the `Application` instance, you can start creating [documents](https://learn.microsoft.com/en-gb/office/vba/api/word.documents), [workbooks](https://learn.microsoft.com/en-gb/office/vba/api/excel.workbooks), [presentations](https://learn.microsoft.com/en-gb/office/vba/api/powerpoint.presentations), [emails](https://learn.microsoft.com/en-gb/office/vba/api/outlook.application.createitem), and more.

```python
# Create a new Excel workbook
wkb = xl_app.workbooks.add()

# Create a new PowerPoint presentation
ppt = pp_app.presentations.add()

# Create a new Word document
doc = wd_app.documents.add()
```

You can also open existing files.

```python
# Open an existing Access database
ac_db = ac_app.databases.OpenCurrentDatabase("C:\\path\\to\\your\\database.accdb")

# Open an existing Excel workbook
wkb = xl_app.workbooks.open("C:\\path\\to\\your\\workbook.xlsx")   

# Open an existing PowerPoint presentation
ppt = pp_app.presentations.open("C:\\path\\to\\your\\presentation.pptx")

# Open an existing Word document
doc = wd_app.documents.open("C:\\path\\to\\your\\document.docx")
```

You have access to all objects, methods, and properties of the VBA Object Library for:
- [Access](https://learn.microsoft.com/en-gb/office/vba/api/overview/access)
- [Excel](https://learn.microsoft.com/en-gb/office/vba/api/overview/excel)
- [Outlook](https://learn.microsoft.com/en-gb/office/vba/api/overview/outlook)
- [PowerPoint](https://learn.microsoft.com/en-gb/office/vba/api/overview/powerpoint)
- [Word](https://learn.microsoft.com/en-gb/office/vba/api/overview/word)

See the [Office VBA Reference](https://learn.microsoft.com/en-us/office/vba/api/overview) for details.

## Package Structure

```
matita
    - office
        - access
        - excel
        - office
        - outlook
        - powerpoint
        - word
    - reference
        - markdown
        - models
```

### `matita.office`

The modules `access`, `excel`, `outlook`, `powerpoint`, `word` include classes and enumerations for the corresponding application.

The `office` module includes additional enumerations available to all applications.

### `matita.reference`

The subpackage `matita.reference` parses the git submodule `office-vba-reference`, which is the repository of the [Office VBA Reference](https://learn.microsoft.com/en-us/office/vba/api/overview) by Microsoft.
The `markdown` module creates a `MarkdownTree` instance for each page of the documentation.

The `models` module creates a `VbaDocs` instance based on the parsed information.
The `VbaDocs` instance first exports its information to [`data/office-vba-api.json`](https://github.com/lucafrance/matita/blob/main/data/office-vba-api.json).
The information is then exported as the `office.matita` modules.

## Comparison with other Python packages

`Matita` wraps Microsoft Office [COM](https://learn.microsoft.com/en-us/windows/win32/com/the-component-object-model) objects created with [`win32com`](https://pypi.org/project/pywin32/) and provides a Pythonic interface that closely matches the VBA syntax.

Every `matita.office` class includes an underlying COM object, accessible via the `com_object` property.

```python
from matita.office import word as wd

wd_app = wd.Application()
print(type(wd_app)) # <class 'matita.office.word.Application'>
print(type(wd_app.com_object)) # <class 'win32com.client.CDispatch'>
wd_app.Quit()
```

This approach is [similar to the one of `xlwings`](https://docs.xlwings.org/en/latest/missing_features.html), which offers additional Excel automation features.

This is different from other popular Python packages for Office automation, such as [`openpyxl`](https://openpyxl.readthedocs.io) for Excel, [`python-docx`](https://python-docx.readthedocs.io) for Word, or [`python-pptx`](https://pypi.org/project/python-pptx/) for PowerPoint, which implement their own object models and do not use the VBA Object Library.


### `matita` vs `win32com` (part of `pywin32`)

`win32com` is the typical way in Python to dispatch COM objects.
There are some quirks with `win32com` objects due differences in how COM and Python work.

```python
import win32com.client

xl_app = win32com.client.gencache.EnsureDispatch("Excel.Application")
xl_app.Visible = True

wkb = xl_app.Workbooks.Add()
wks = wkb.Worksheets(1)
c = wks.Cells(1,1)

# Constants (like `xlR1C1`) must be retrieved separately.
constants = win32com.client.constants

# Some properties are available over separate getter and setter methods.
print(c.Address(ReferenceStyle=constants.xlR1C1)) # Fails
print(c.GetAddress(ReferenceStyle=constants.xlR1C1)) # R1C1

# Some methods exist but don't work as expected.
# The getter method is needed in those cases.
# There is no general way to know what should be used when.
# https://stackoverflow.com/q/63112880
print(rng.Resize(2,3).Address) # $C$2, wrong result
print(rng.GetResize(2,3).Address) # $A$1:$C$2, correct result

wkb.Close(False)
xl_app.Quit()
```

`matita` addresses the quirks and adds improvements to be more intuitive.


```python
from matita.office import excel as xl

xl_app = xl.Application()
# lower case aliases for all properties and methods
xl_app.visible = True
wkb = xl_app.workbooks.add()
c = wks.cells(1,1)

# Methods are available in their original name
# Constants (like `xlR1C1`) are available in the same module
print(c.address(ReferenceStyle=xl.xlR1C1)) #R1C1


# Methods are working as expected in their original name
print(rng.resize(2,3).address()) # $A$1:$C$2, correct result

wkb.close(False)
xl_app.quit()
```


## Limitations of `matita`

The following objects are unsupported, because their name conflicts with reserved keywords in Python.
- [Break object (Word)](https://learn.microsoft.com/en-us/office/vba/api/word.break)
- [Global object (Word)](https://learn.microsoft.com/en-us/office/vba/api/word.global)

The following objects are unsupported, because non-scalar arguments are not implemented.
- [Report.Circle method (Access)](https://learn.microsoft.com/en-gb/office/vba/api/access.report.circle)
- [Report.Line method (Access)](https://learn.microsoft.com/en-gb/office/vba/api/access.report.line)
