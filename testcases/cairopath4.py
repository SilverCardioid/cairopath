from cp_import import cairopath

canvas = cairopath.Canvas(800,200,0xffffff)

g1 = canvas.lineargradient(40,0,160,0) \
           .stop(0,0xff0000).stop(1,0x0000ff)
g2 = canvas.radialgradient(0,300,60,100,300,60) \
           .stop(0.1,0xff0000).stop(0.707,0xffff00).stop(0.9,0xff0000)
g3 = canvas.radialgradient(0,500,100,100) \
           .stop(0.32,0xff0000).stop(0.32,0xffffff)
g4 = canvas.lineargradient(700,40,700,160) \
           .stop(0,0xff0000,1).stop(1,0xff0000,0)

canvas.path().m(0,0).h(100).v(200).h(100).z().m(200,0).v(100).h(-200).v(100).z() \
      .clip()
canvas.path().m(100,40).l(60,60).l(-60,60).l(-60,-60).z() \
      .fill(g1,keep=True).stroke(0x000000)
canvas.resetclip()

canvas.circle(60,300,100) \
      .stroke(g2,width=10)

canvas.rect(160,100,500,100,center=1) \
      .fill(g3,keep=True) \
      .stroke([0,128,0])

canvas.circle(60,700,100) \
      .fill(0xffff00,opacity=0.8,keep=True) \
      .stroke(g4,width=8,opacity=0.4,dash=16)

canvas.png('cairopath4.png')
