---
title: item-08 Smart return type for `Outlook.Application.CreateItem`
---

[`Outlook.Application.CreateItem`](https://learn.microsoft.com/en-gb/office/vba/api/outlook.application.createitem) can return different types depending on the given argument.

Now it returns die COM object directly.
It could return directly the COM object wrapped in the correct class.

```python
# Now
# return instance must be wrapped in `MailItem` class
mail = ol.MailItem(ol_app.create_item(ol.olMailItem))

# After
# return `matita.outlook.MailItem` instance directly
mail = ol_app.create_item(ol.olMailItem) 
```
