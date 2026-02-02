from matita.office import powerpoint as pp

def hello_world():
    pp_app = pp.Application()
    pp_app.visible = True
    prs = pp_app.presentations.add()
    sld = prs.slides.add(1, pp.ppLayoutText)
    shp = sld.shapes.addshape(pp.msoShapeRectangle, 100, 100, 200, 100)
    shp.text_frame.text_range.text = "Hello world!"

if __name__ == "__main__":
    hello_world()
