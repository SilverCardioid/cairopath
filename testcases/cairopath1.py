from cp_import import cairopath

canvas = cairopath.Canvas(300, 200, (1.0, 1.0, 1.0))
path = cairopath.Path(canvas)
path.M(100, 75) \
    .A(25, 125, 100) \
    .a(25, 25, 25, 1, 0) \
    .A(25, 175, 100, 0) \
    .h(25) \
    .a(25, 0, 50)
path.stroke((0,0.5,0))

canvas.png('cairopath1.png')
