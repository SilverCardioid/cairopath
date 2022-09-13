import math

from cp_import import cairopath

canvas = cairopath.Canvas(600, 600, bgcolor='#fff')

with canvas.translate(300, 300):
	canvas.circle(120).fill(0)
	path = canvas.path()
	path.M(0, -100)
	for i in range(1, 5):
		path.L(100*math.sin(i*4*math.pi/5), -100*math.cos(i*4*math.pi/5))
	path.z()
	path.fill(0xffcc00)

canvas.png('star.png')
