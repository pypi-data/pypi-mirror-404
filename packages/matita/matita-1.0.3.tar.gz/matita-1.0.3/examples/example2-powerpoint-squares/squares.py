import random

from matita.office import powerpoint as pp

def squares():
    pp_app = pp.Application()
    prs = pp_app.presentations.add()
    sld = prs.slides.Add(1, pp.ppLayoutBlank)
    pp_app.window_state = pp.ppWindowMinimized

    num_squares = 1000
    for i in range(num_squares):
        side = random.random() * prs.page_setup.slideheight / 3
        left = -side + random.random() * (side + prs.page_setup.slide_width)
        top = -side + random.random() * (side + prs.page_setup.slide_height)
        shp = sld.shapes.add_shape(pp.msoShapeRectangle, left, top, side, side)
        shp.line.visible = False
        shp.fill.fore_color.rgb = random.randint(0, 256 ** 3)
        eff = sld.timeline.main_sequence.add_effect(
            Shape=shp,
            effectId=pp.msoAnimEffectFly,
            Level=pp.msoAnimateLevelNone,
            trigger=pp.msoAnimTriggerAfterPrevious,
        )
        direction = random.choice([
            pp.msoAnimDirectionLeft,
            pp.msoAnimDirectionTop,
            pp.msoAnimDirectionRight,
            pp.msoAnimDirectionBottom
        ])
        eff.effect_parameters.direction = direction
        eff.timing.duration = 0.2
        print(f"Added {i}/{num_squares} squares.")

    pp_app.window_state = pp.ppWindowMaximized
    print("Squares added, try starting the slide show.")

if __name__ == "__main__":
    squares()
