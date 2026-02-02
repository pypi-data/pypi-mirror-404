# *Matita* - Full Microsoft Office automation in Python ✏️

*Matita* is a Python wrapper for the [VBA Object library](https://learn.microsoft.com/en-us/office/vba/api/overview/).
You get the full power of VBA with the convenience of Python.
See the [documentation](https://matita.readthedocs.io/en/latest/documentation) for more details.

## Hello world with *matita*

### Excel 📊

```python
from matita.office import excel as xl

def hello_world():
    xl_app = xl.Application()
    xl_app.visible = True

    wkb = xl_app.workbooks.add()
    wks = wkb.worksheets(1)
    c = wks.cells(1,1)
    c.value = "Hello world!"
```

### PowerPoint 🖼️

```python
from matita.office import powerpoint as pp

def hello_world():
    pp_app = pp.Application()
    pp_app.visible = True
    prs = pp_app.presentations.add()
    sld = prs.slides.add(1, pp.ppLayoutText)
    shp = sld.shapes.addshape(pp.msoShapeRectangle, 100, 100, 200, 100)
    shp.text_frame.text_range.text = "Hello world!"
```

### Word 📄

```python
from matita.office import word as wd

def hello_world():
    wd_app = wd.Application()
    wd_app.visible = True
    doc = wd_app.documents.add()
    par = doc.content.paragraphs.add()
    par.range.text = "Hello world!"
```

### Outlook 📧

```python
from matita.office import outlook as ol

def hello_world():
    ol_app = ol.Application()
    mail = ol.MailItem(ol_app.create_item(ol.olMailItem))
    mail.body = "Hello world!"
    mail.display()
```

## Installation

```powershell
python -m pip install matita
```

## License

Copyright 2026 Luca Franceschini (lucaf.eu)

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. 

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

This program is based on the [Office VBA Reference](https://learn.microsoft.com/en-us/office/vba/api/overview) by Microsoft Corporation, [licensed](https://github.com/MicrosoftDocs/VBA-Docs/blob/main/LICENSE) under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
