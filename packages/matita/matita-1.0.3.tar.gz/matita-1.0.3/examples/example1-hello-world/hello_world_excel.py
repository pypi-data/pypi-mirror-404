from matita.office import excel as xl

def hello_world():
    xl_app = xl.Application()
    xl_app.visible = True

    wkb = xl_app.workbooks.add()
    wks = wkb.worksheets(1)
    c = wks.cells(1,1)
    c.value = "Hello world!"

if __name__ == "__main__":
    hello_world()
