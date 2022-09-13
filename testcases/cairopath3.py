from cp_import import cairopath

canvas = cairopath.Canvas(600,600,0xffffff)
canvas.rect(160,100,0,0).fill(0x004488)

canvas.translate(300,200)
canvas.rect(160,100,0,0).fill(0xee2211)

canvas.rotate(90) # rotated relative to previous translate
canvas.rect(160,100,0,0).fill(0x00aa33)
canvas.resettransform()

canvas.rotate(60,0,600)
canvas.rect(160,100,0,0).fill(0xffcc00)
canvas.resettransform()

canvas.translate(300,0).rotate(90)
canvas.rect(160,100,0,0).fill(0x663399)

canvas.png('cairopath3.png')
