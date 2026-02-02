from matita.office import word as wd

def hello_world():
    wd_app = wd.Application()
    wd_app.visible = True
    doc = wd_app.documents.add()
    par = doc.content.paragraphs.add()
    par.range.text = "Hello world!"

if __name__ == "__main__":
    hello_world()
