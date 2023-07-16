import cairocffi as cairo
from cairosvg import path as _csvg_path
from cairosvg import helpers as _csvg_helpers
import math
import numpy

def parsecolor(c):
	if type(c) in (list, tuple):
		r, g, b = c
		if not any(type(x) is float for x in c): r, g, b = r/255, g/255, b/255
	elif type(c) is int:
		r, g, b = (c//256**2)/255, (c//256%256)/255, (c%256)/255
	elif type(c) is str:
		if c[0] == '#': c = c[1:]
		if len(c) <= 3: c = ''.join([x*2 for x in c])
		if len(c) < 6: c = c.zfill(6)
		r, g, b = int(c[0:2],16)/255, int(c[2:4],16)/255, int(c[4:6],16)/255
	else:
		raise Exception('unknown color data type')
	return r, g, b

def parsesurfacetype(t):
	t = t.lower()
	if t in ('image', 'png'):
		return 'Image'
	elif t == 'svg':
		return 'SVG'
	elif t == 'pdf':
		return 'PDF'
	elif t in ('ps', 'postscript'):
		return 'PS'
	elif t in ('recording', 'record'):
		return 'Recording'
	else:
		raise Exception('unknown surface type')

_linecaps = {0: 0, 'butt': 0, 1: 1, 'round': 1, 2: 2, 'square': 2}
_linejoins = {0: 0, 'miter': 0, 1: 1, 'round': 1, 2: 2, 'bevel': 2}

# alias for Canvas init
def canvas(width, height, bgcolor=None, bgopacity=1, surfacetype='Image', filename=None):
	return Canvas(width, height, bgcolor, bgopacity, surfacetype, filename)


class Canvas:
	def __init__(self, width, height, bgcolor=None, bgopacity=1, surfacetype='Image', filename=None):
		self._createsurface(width, height, surfacetype, filename)
		self.context = cairo.Context(self.surface)
		self.filename = filename
		self.width = width
		self.height = height
		if bgcolor is not None:
			with self.context:
				self._setcolor(self.context, bgcolor, bgopacity)
				self.context.paint()

	def __enter__(self):
		pass

	def __exit__(self, errortype, errorvalue, traceback):
		self.export()

	def _setcolor(self, context, c, op=1):
		r, g, b = parsecolor(c)
		context.set_source_rgba(r, g, b, op)

	def _createsurface(self, width, height, type='Image', filename=None):
		type = parsesurfacetype(type)
		self.surfacetype = type
		if type == 'Image':
			self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		elif type == 'SVG':
			self.surface = cairo.SVGSurface(filename, width, height)
		elif type == 'PDF':
			self.surface = cairo.PDFSurface(filename, width, height)
		elif type == 'PS':
			self.surface = cairo.PSSurface(filename, width, height)
		elif type == 'Recording':
			self.surface = cairo.RecordingSurface(cairo.CONTENT_COLOR_ALPHA, (0,0,width,height))
		return self.surface

	def _setsource(self, source):
		sourcetype = type(source)
		sourcetype = [sourcetype] + list(sourcetype.__bases__)
		if Canvas in sourcetype:
			s = source.surface
		elif cairo.Surface in sourcetype:
			s = source
		elif cairo.Context in sourcetype:
			s = source.get_target()
		else:
			raise Exception('unknown source data type')
		self.context.set_source_surface(s, 0, 0)
		self.context.paint()

	def data(self, alpha=False):
		"""Return the image pixel data as a Numpy array in RGB or RGBA format"""
		# from Gizeh
		im = 0 + numpy.frombuffer(self.surface.get_data(), numpy.uint8)
		im.shape = (self.height, self.width, 4)
		im = im[:,:,[2,1,0,3]] # put RGB back in order
		if alpha:
			return im
		else:
			return im[:,:,:3]

	def export(self, type='Image', filename=None):
		"""Export the canvas to a file"""
		targettype = parsesurfacetype(type)
		context = self.context
		filename = filename or self.filename
		if filename:
			if targettype == 'Image':
				self.surface.write_to_png(filename)
			elif filename != self.filename:
				target = Canvas(self.width, self.height, surfacetype=targettype, filename=filename)._setsource(self.surface)
				if targettype == 'Image':
					target.surface.write_to_png(filename)
			else:
				context.finish()
				self.oldsurface = self.surface
				self.surface = self._createsurface(self.width, self.height, surfacetype=self.surfacetype, filename=filename)
				self.context = cairo.Context(self.surface)
				self._setsource(self.oldsurface)

	def clone(self, type='Image'):
		"""Return a copy of the canvas using a different surface type"""
		type = parsesurfacetype(type)
		return Canvas(self.width, self.height, surfacetype=type)._setsource(self.surface)

	def path(self, d=None):
		"""Create a Path object for drawing lines and curves (optionally from an SVG path string)"""
		path = Path(self)
		if d:
			path.d(d)
		return path

	def circle(self, r, cx=0, cy=0):
		"""Add a circle to the current path"""
		self.context.new_sub_path()
		return Path(self).Ac(cx, cy, r, 0, 360).parent

	def ellipse(self, rx, ry, cx=0, cy=0):
		"""Add an ellipse to the current path"""
		self.context.new_sub_path()
		with self.scale(1, ry/rx):
			Path(self).Ac(cx, cy*rx/ry, rx, 0, 360)
		return self

	def rect(self, width, height, x=0, y=0, center=False):
		"""Add a rectangle to the current path"""
		if center:
			x, y = x-width/2, y-height/2
		self.context.rectangle(x, y, width, height)
		return self

	def _fill(self, keep):
		if keep:
			self.context.fill_preserve()
		else:
			self.context.fill()

	def fill(self, color, opacity=1, evenodd=0, keep=False, affect=True):
		"""Draw the current path using a solid color or gradient"""
		if color is None:
			if not keep: self.context.new_path()
		else:
			self.context.set_fill_rule([cairo.FILL_RULE_WINDING,cairo.FILL_RULE_EVEN_ODD][evenodd > 0])
			if type(color) is Gradient:
				color.affect = affect
				with color: # temporarily reset transform if affect=False
					self.context.set_source(color.pattern)
					if opacity<1:
						with self.clip(keep):
							self.context.paint_with_alpha(opacity)
					else:
						self._fill(keep)
			else:
				self._setcolor(self.context, color, opacity)
				self._fill(keep)
		return self

	def _stroke(self, keep):
		if keep:
			self.context.stroke_preserve()
		else:
			self.context.stroke()

	def stroke(self, color, opacity=1, width=2, cap='butt', join='miter', miterlimit=10, dash=None, dashoffset=0, keep=False, affect=True):
		"""Draw the current path as an outline using a solid color or gradient"""
		if color is None:
			if not keep: self.context.new_path()
		else:
			self.context.set_line_width(width)
			if cap not in _linecaps: raise Exception('unknown line cap (supported: butt, round, square)')
			if join not in _linejoins: raise Exception('unknown line join (supported: miter, round, bevel)')
			self.context.set_line_cap([cairo.LINE_CAP_BUTT, cairo.LINE_CAP_ROUND, cairo.LINE_CAP_SQUARE][_linecaps[cap]])
			self.context.set_line_join([cairo.LINE_JOIN_MITER, cairo.LINE_JOIN_ROUND, cairo.LINE_JOIN_BEVEL][_linejoins[join]])
			self.context.set_miter_limit(miterlimit)
			if dash is not None:
				if type(dash) in (float, int): dash = [dash]
				self.context.set_dash(dash, dashoffset)
			else:
				self.context.set_dash([]);
			if type(color) is Gradient:
				color.affect = affect
				with color: # temporarily reset transform if affect=False
					self.context.set_source(color.pattern)
					self._stroke(keep)
			else:
				self._setcolor(self.context, color, opacity)
				self._stroke(keep)
		return self

	def lineargradient(self, x1=0, y1=0, x2=None, y2=None):
		"""Create a linear gradient"""
		if x2 is None: x2 = x1
		if y2 is None: y2 = y1
		return Gradient(self, 'linear', x1, y1, x2, y2)

	def radialgradient(self, r1=0, x1=0, y1=0, r2=100, x2=None, y2=None):
		"""Create a radial gradient"""
		if x2 is None: x2 = x1
		if y2 is None: y2 = y1
		return Gradient(self, 'radial', r1, x1, y1, r2, x2, y2)

	# Function wrappers/aliases
	def clip(self, keep=False):
		"""Set a clip path using the current path"""
		return Transform(self).clip(keep)
	def resetclip(self):
		"""Reset clip path"""
		return Transform(self).resetclip()
	def translate(self, tx, ty=0):
		"""Translate the viewport"""
		return Transform(self).translate(tx, ty)
	def scale(self, sx, sy=None):
		"""Scale the viewport (sy=None for uniform scaling)"""
		return Transform(self).scale(sx, sy)
	def rotate(self, a, cx=0, cy=0, rad=False):
		"""Rotate the viewport"""
		return Transform(self).rotate(a, cx, cy, rad)
	def matrix(self, m, replace=False):
		"""Transform the viewport by a matrix, or replace the current transformation matrix"""
		return Transform(self).matrix(m, replace)
	def resettransform(self):
		"""Reset the current transformation matrix"""
		return Transform(self).resettransform()
	def png(self, filename):
		"""Export the canvas as a PNG file"""
		return self.export('Image', filename)
	def svg(self, filename):
		"""Export the canvas as an SVG file"""
		return self.export('SVG', filename)
	def pdf(self, filename):
		"""Export the canvas as a PDF file"""
		return self.export('PDF', filename)
	def ps(self, filename):
		"""Export the canvas as a PostScript file"""
		return self.export('PS', filename)
	postscript = ps
	img = data
	rectangle = rect


class Path:
	def __init__(self, canvas):
		self.parent = canvas
		self.canvas = canvas
		self.context = canvas.context
		self._track(current=[0, 0])

	def _track(self, current=None, start=None, lastbezier=None, rel=False):
		old = getattr(self.parent, '_currentpoint', None)
		if rel:
			offset = old or [0, 0]
			current, start, lastbezier = self._rel2abs(offset, current, start, lastbezier)
		self.parent._currentpoint = self._settrack(current or start or old, old)
		if start is not None: self.parent._startpoint = tuple(start) # don't change if None
		self.parent._lastbezierpoint = lastbezier and tuple(lastbezier)

	def _rel2abs(self, offset, *args):
		return [arr and [arr[0]+offset[0] if arr[0] is not None else None, \
		                 arr[1]+offset[1] if arr[1] is not None else None \
		                ]+arr[2:] for arr in args]

	def _settrack(self, v1, v2):
		if v1 is None:
			return None
		elif v2 is None: # replace Nones in v1 with 0
			x = v1[0] or 0
			y = v1[1] or 0
		else: # replace Nones in v1 with values from v2
			x = v1[0] if v1[0] is not None else v2[0]
			y = v1[1] if v1[1] is not None else v2[1]
		return (x, y)
 
	def d(self, string):
		"""Parse path data from string"""
		parser = StringParser(self.parent, string, width=self.parent.width, height=self.parent.height)
		parser.draw()
		return self

	def M(self, x, y):
		"""Move to (absolute)"""
		self.context.move_to(x, y)
		self._track(start=[x, y])
		return self

	def m(self, dx, dy):
		"""Move to (relative)"""
		if self.parent._currentpoint is None or self.parent._currentpoint == (0, 0):
			self.context.move_to(dx, dy)
		else:
			self.context.rel_move_to(dx, dy)
		self._track(start=[dx, dy], rel=True)
		return self

	def L(self, x, y):
		"""Line to (absolute)"""
		self.context.line_to(x, y)
		self._track(current=[x, y])
		return self

	def l(self, dx, dy):
		"""Line to (relative)"""
		self.context.rel_line_to(dx, dy)
		self._track(current=[dx, dy], rel=True)
		return self

	def H(self, x):
		"""Horizontal line to (absolute)"""
		y = self.parent._currentpoint[1]
		self.context.line_to(x, y)
		self._track(current=[x, None])
		return self

	def h(self, dx):
		"""Horizontal line to (relative)"""
		self.context.rel_line_to(dx, 0)
		self._track(current=[dx, None], rel=True)
		return self

	def V(self, y):
		"""Vertical line to (absolute)"""
		x = self.parent._currentpoint[0]
		self.context.line_to(x, y)
		self._track(current=[None, y])
		return self

	def v(self, dy):
		"""Vertical line to (relative)"""
		self.context.rel_line_to(0, dy)
		self._track(current=[None, dy], rel=True)
		return self

	def C(self, x1, y1, x2, y2, x, y):
		"""Cubic Bezier curve (absolute)"""
		self.context.curve_to(x1, y1, x2, y2, x, y)
		self._track(current=[x, y], lastbezier=[x2, y2, 'c'])
		return self

	def c(self, dx1, dy1, dx2, dy2, dx, dy):
		"""Cubic Bezier curve (relative)"""
		self.context.rel_curve_to(dx1, dy1, dx2, dy2, dx, dy)
		self._track(current=[dx, dy], lastbezier=[dx2, dy2, 'c'], rel=True)
		return self

	def S(self, x2, y2, x, y):
		"""Smooth cubic Bezier curve (absolute)"""
		x1, y1 = self.parent._currentpoint
		if self.parent._lastbezierpoint:
			xp, yp, degree = self.parent._lastbezierpoint
			if degree == 'c':
				x0, y0 = self.parent._currentpoint
				x1, y1 = x0+(x0-xp), y0+(y0-yp)
		return self.C(x1, y1, x2, y2, x, y)

	def s(self, dx2, dy2, dx, dy):
		"""Smooth cubic Bezier curve (relative)"""
		dx1, dy1 = 0, 0
		if self.parent._lastbezierpoint:
			xp, yp, degree = self.parent._lastbezierpoint
			if degree == 'c':
				x0, y0 = self.parent._currentpoint
				dx1, dy1 = (x0-xp), (y0-yp)
		return self.c(dx1, dy1, dx2, dy2, dx, dy)

	def Q(self, x1, y1, x, y):
		"""Quadratic Bezier curve (absolute)"""
		x0, y0 = self.parent._currentpoint
		xc1, yc1 = x0+2/3*(x1-x0), y0+2/3*(y1-y0)
		xc2, yc2 = x-2/3*(x-x1), y-2/3*(y-y1)
		self.context.curve_to(xc1, yc1, xc2, yc2, x, y)
		self._track(current=[x, y], lastbezier=[x1, y1, 'q'])
		return self

	def q(self, dx1, dy1, dx, dy):
		"""Quadratic Bezier curve (relative)"""
		xc1, yc1 = 2/3*dx1, 2/3*dy1
		xc2, yc2 = dx-2/3*(dx-dx1), dy-2/3*(dy-dy1)
		self.context.rel_curve_to(xc1, yc1, xc2, yc2, dx, dy)
		self._track(current=[dx, dy], lastbezier=[dx1, dy1, 'q'], rel=True)
		return self

	def T(self, x, y):
		"""Smooth quadratic Bezier curve (absolute)"""
		x1, y1 = self.parent._currentpoint
		if self.parent._lastbezierpoint:
			xp, yp, degree = self.parent._lastbezierpoint
			if degree == 'q':
				x0, y0 = self.parent._currentpoint
				x1, y1 = x0+(x0-xp), y0+(y0-yp)
		return self.Q(x1, y1, x, y)

	def t(self, dx, dy):
		"""Smooth quadratic Bezier curve (relative)"""
		dx1, dy1 = 0, 0
		if self.parent._lastbezierpoint:
			xp, yp, degree = self.parent._lastbezierpoint
			if degree == 'q':
				x0, y0 = self.parent._currentpoint
				dx1, dy1 = (x0-xp), (y0-yp)
		return self.q(dx1, dy1, dx, dy)

	def Ac(self, xc, yc, r, a1, a2, sweep=1, rad=False):
		"""Circular arc (Cairo syntax)"""
		if not rad:
			a1, a2 = math.radians(a1), math.radians(a2)
		if sweep > 0: # clockwise
			self.context.arc(xc, yc, r, a1, a2)
		else: # counterclockwise
			self.context.arc_negative(xc, yc, r, a1, a2)
		self._track(current=[xc+r*math.cos(a2), yc+r*math.sin(a2)])
		return self

	def A(self, r, x, y, large=1, sweep=1):
		"""Circular arc (absolute)"""
		if r<=0:
			# zero radius is interpreted as straight line
			return self.L(x, y)
		x1, y1 = self.parent._currentpoint
		x2, y2 = x, y
		d = math.sqrt((x2-x1)**2+(y2-y1)**2) # distance P1 and P2
		if 2*r<d:
			# Radius too small to reach P2
			r = d/2
		# Possible arc centers are on perpendicular bisector of P1-P2
		xm, ym = (x2+x1)/2, (y2+y1)/2
		theta = math.atan2(y2-y1, x2-x1)
		mc = math.sqrt(r**2-(d/2)**2)
		if (sweep > 0) ^ (large > 0):
			# Clockwise small arc or counterclockwise large arc
			xc, yc = xm+mc*math.cos(theta+math.pi/2), ym+mc*math.sin(theta+math.pi/2)
		else:
			# Clockwise large arc or counterclockwise small arc
			xc, yc = xm+mc*math.cos(theta-math.pi/2), ym+mc*math.sin(theta-math.pi/2)
		a1, a2 = math.atan2(y1-yc, x1-xc), math.atan2(y2-yc, x2-xc)
		return self.Ac(xc, yc, r, a1, a2, sweep, True)

	def a(self, r, dx, dy, large=1, sweep=1):
		"""Circular arc (relative)"""
		x1, y1 = self.parent._currentpoint
		return self.A(r, x1+dx, y1+dy, large, sweep)

	def Ae(self, rx, ry, x, y, large=1, sweep=1, angle=0, rad=False):
		"""Elliptical arc (absolute)"""
		if not rad: angle = math.radians(angle)
		with self.parent.rotate(angle, 0, 0, rad=True).scale(rx, ry):
			tx, ty = self.parent._savedtransforms[-1].transform_point(x, y)
			self.A(1, tx, ty, large, sweep)
		return self

	def ae(self, rx, ry, dx, dy, large=1, sweep=1, angle=0, rad=False):
		"""Elliptical arc (relative)"""
		x1, y1 = self.parent._currentpoint
		return self.Ae(rx, ry, x1+dx, y1+dy, large, sweep, angle, rad)

	def z(self):
		"""Close path"""
		self.context.close_path()
		self._track(current=self.parent._startpoint)
		return self
	Z = z

	def fill(self, color, opacity=1, evenodd=0, keep=False, affect=True):
		"""Draw the current path using a solid color or gradient"""
		self.parent.fill(color, opacity, evenodd, keep, affect)
		return self

	def stroke(self, color, opacity=1, width=2, cap='butt', join='miter', miterlimit=10, dash=None, dashoffset=0, keep=False, affect=True):
		"""Draw the current path as an outline using a solid color or gradient"""
		self.parent.stroke(color, opacity, width, cap, join, miterlimit, dash, dashoffset, keep, affect)
		return self

	def clip(self, keep=False):
		"""Set a clip path using the current path"""
		return self.parent.clip(keep)


class Gradient:

	def __init__(self, canvas, type, *args):
		self.parent = canvas
		self.canvas = canvas
		self.context = canvas.context
		if type == 'linear':
			self.pattern = cairo.LinearGradient(*args)
		elif type == 'radial':
			self.pattern = cairo.RadialGradient(*[args[i] for i in [1,2,0,4,5,3]]) # cairo expects radii after centers
		else:
			raise Exception('unknown gradient type')

	def __enter__(self):
		if not self.affect:
			self.context.save()
			self.context.identity_matrix()

	def __exit__(self, errortype, errorvalue, traceback):
		if not self.affect:
			self.context.restore()

	def stop(self, offset, color, opacity=1):
		"""Add a color stop at an offset along this gradient"""
		r, g, b = parsecolor(color)
		self.pattern.add_color_stop_rgba(offset, r, g, b, opacity)
		return self

	def fill(self, opacity=1, evenodd=0, keep=False, affect=True):
		"""Draw the current path using this gradient"""
		return self.canvas.fill(self, opacity, evenodd, keep, affect)

	def stroke(self, opacity=1, width=2, cap=0, join=0, miterlimit=10, dash=None, dashoffset=0, keep=False, affect=True):
		"""Draw the current path as an outline using this gradient"""
		return self.canvas.stroke(self, opacity, width, cap, join, miterlimit, dash, dashoffset, keep, affect)


class Transform(Canvas): # allow direct chaining with shape and style functions from Canvas
	def __init__(self, canvas):
		self.parent = canvas
		self.canvas = canvas
		self.context = canvas.context
		self.context.save()
		if not hasattr(self.parent, '_savedtransforms'):
			self.parent._savedtransforms = []
		self.parent._savedtransforms.append(cairo.Matrix())

	def __enter__(self):
		pass

	def __exit__(self, errortype, errorvalue, traceback):
		self.context.restore()
		self._transformpoints(self.parent._savedtransforms[-1].inverted())
		self.parent._savedtransforms.pop()

	def _transformpoints(self, fun):
		if callable(fun):
			mat = cairo.Matrix() # identity
			res = fun(mat) # apply input transform
			if res is not None: mat = res # for cairo functions that return a new matrix instead of changing 'mat' in-place
		else: # direct matrix input
			mat = fun
		# change points
		if getattr(self.parent, '_currentpoint', None) is not None:
			self.parent._currentpoint = mat.transform_point(*self.parent._currentpoint)
		if getattr(self.parent, '_startpoint', None) is not None:
			self.parent._startpoint = mat.transform_point(*self.parent._startpoint)
		if getattr(self.parent, '_lastbezierpoint', None) is not None:
			self.parent._lastbezierpoint = mat.transform_point(*self.parent._lastbezierpoint[:2])+self.parent._lastbezierpoint[2:]
		self.parent._savedtransforms[-1] = self.parent._savedtransforms[-1] * mat

	def clip(self, keep=False):
		"""Set a clip path using the current path"""
		if keep:
			self.context.clip_preserve()
		else:
			self.context.clip()
		return self

	def translate(self, tx, ty=0):
		"""Translate the viewport"""
		self.context.translate(tx, ty)
		self._transformpoints(lambda p: p.translate(-tx, -ty))
		return self

	def scale(self, sx, sy=None):
		"""Scale the viewport (sy=None for uniform scaling)"""
		self.context.scale(sx, sy)
		self._transformpoints(lambda p: p.scale(1/sx, sy and 1/sy))
		return self

	def _rotate(self, p, a, cx, cy):
		p.translate(cx, cy)
		p.rotate(a)
		p.translate(-cx, -cy)

	def rotate(self, a, cx=0, cy=0, rad=False):
		"""Rotate the viewport"""
		if not rad: a = math.radians(a)
		self._rotate(self.context, a, cx, cy)
		self._transformpoints(lambda p: self._rotate(p, -a, cx, cy))
		return self

	def matrix(self, m, replace=False):
		"""Transform the viewport by a matrix, or replace the current transformation matrix"""
		mc = cairo.Matrix(*m)
		if replace:
			self.context.set_matrix(mc)
			self._transformpoints((mc * self.parent._savedtransforms[-1]).inverted())
		else:
			self.context.transform(mc)
			self._transformpoints(mc.inverted())
		return self

	def reset(self):
		"""Reset the current transform and clip path"""
		return self.resettransform().resetclip()

	def resettransform(self):
		"""Reset the current transformation matrix"""
		self.context.identity_matrix()
		return self

	def resetclip(self):
		"""Reset clip path"""
		self.context.reset_clip()
		return self


class StringParser:
	# hacky surrogate for cairosvg's 'Surface' and 'Node' classes
	def __init__(self, canvas, string, width=None, height=None):
		self.context = canvas.context
		self.context_width = width or canvas.surface.get_width()
		self.context_height = height or canvas.surface.get_height()
		self.dpi = 96
		self.font_size = _csvg_helpers.size(self, '12pt')
		self.d = string

	def get(self, key, default=None):
		return getattr(self, key, default)

	def draw(self):
		_csvg_path.path(self, self)
