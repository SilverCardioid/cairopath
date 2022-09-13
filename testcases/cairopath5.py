from cp_import import cairopath

canvas = cairopath.canvas(600,600,0xffffff)

grad = canvas.radialgradient(0,300,300,500) \
       .stop(0,0xff0000) \
       .stop(0.2,0xffff00) \
       .stop(0.4,0x00ff00) \
       .stop(0.6,0x00ffff) \
       .stop(0.8,0x0000ff) \
       .stop(1,0xff00ff)

canvas.rect(560,560,20,20).fill(grad,opacity=0.2)

with canvas.translate(100,0):
  canvas.circle(60,100,100).fill(grad) # translate X

canvas.translate(340,220).circle(60) \
      .resettransform().fill(grad) # translate circle without shifting gradient
with canvas.translate(340,380):
  canvas.circle(40).fill(grad,opacity=0.6,affect=False) # same
  canvas.circle(60).stroke(grad,width=5,affect=False)

canvas.translate(0,200)
with canvas.scale(1.5):
  canvas.circle(60,100,100).fill(grad) # scale, then translate Y
canvas.circle(60,100,100).fill(0xffffff,opacity=0.8) # translate Y
canvas.resettransform()

canvas.translate(400,0)
with canvas.path().m(0,0).h(50).l(150,200).l(-150,200) \
                  .h(-50).l(150,-200).z().clip():
  canvas.circle(60,100,100).fill(grad,opacity=0.6) # clip, then translate X
  with canvas.translate(0,200):
    canvas.circle(60,100,100).fill(grad) # translate Y, then clip, then translate X
  canvas.circle(35,100,100).fill(0x008080) # clip, then translate X
canvas.circle(30,100,100).fill(0xffffff,opacity=0.8) # translate X

canvas.png('cairopath5.png')
