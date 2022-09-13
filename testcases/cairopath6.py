from cp_import import cairopath

canvas = cairopath.Canvas(600,500,0xffffff)
canvas.path().m(50,50).h(50).v(50).c(0,60,40,100,100,100) \
             .s(100,-40,100,-100).t(100,0).t(0,100) \
             .ae(100,150,100,100,angle=45,sweep=0) \
             .s(100,-100,0,-100).v(-100).h(50) \
             .stroke(0,width=5)
canvas.path('m50,50h50v50c0,60 40,100 100,100' \
           +'s100,-40 100,-100t100,0t0,100' \
           +'a100,150 45 1,0 100,100' \
           +'s100,-100 0,-100v-100h50' \
           ).stroke('#f00',width=2)
canvas.ellipse(80,60,200,100).fill('#ddd')
with canvas.rotate(-45,450,250):
  canvas.ellipse(120,80,340,250).fill('#ddd')


canvas.png('cairopath6.png')
