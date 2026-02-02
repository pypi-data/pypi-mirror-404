from matita.office import outlook as ol

def hello_world():
    ol_app = ol.Application()
    mail = ol.MailItem(ol_app.create_item(ol.olMailItem))
    mail.body = "Hello world!"
    mail.display()

if __name__ == "__main__":
    hello_world()
