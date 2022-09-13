from cp_import import cairopath

canvas = cairopath.Canvas(800, 200, 0xffffff)
canvas.path().m(100,40).l(60,60).l(-60,60).l(-60,-60).z().fill(0x000000)
canvas.circle(60, 300, 100).stroke('#82a', width=5)
canvas.rect(160, 100, 500, 100, center=1).fill((0, 1.0, 1.0), keep=True).stroke([0,128,0])
canvas.circle(60, 700, 100).fill(0xffff00, opacity=0.8, keep=True).stroke(0xff0000, width=8, opacity=0.4, dash=16)

canvas.png('cairopath2.png')
