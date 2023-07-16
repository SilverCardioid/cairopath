# cairopath
A [Cairo](https://github.com/Kozea/cairocffi) wrapper I created in 2018 to programmatically draw vector graphics, inspired by [Gizeh](https://github.com/Zulko/gizeh). As its name indicates, its main use is to simplify [Cairo's markup for paths](https://cairocffi.readthedocs.io/en/stable/api.html#cairocffi.Context.new_path), by using [SVG](https://en.wikipedia.org/wiki/Scalable_Vector_Graphics)-style single-letter commands and allowing method chaining. It also supports transformations, clips and gradients.

While working on a Cairopath function to parse SVG path strings, I came across an existing vector graphics library named [CairoSVG](https://github.com/Kozea/CairoSVG). My script has since invoked CairoSVG's path module for string input, albeit in a rather hacky way; because CairoSVG's purpose is SVG file conversion, it isn't designed to support direct input of vector data or individual use of its component scripts. [My unfinished fork of the project](https://github.com/SilverCardioid/CairoSVG/) is intended to allow easier use of CairoSVG from a script, and to use its existing code to extend Cairopath's functionality to include other SVG features like text, cloning and groups. In the meantime, though, Cairopath continues to be used in some of my other projects.

## Installation
Requirements:
* [cairocffi](https://github.com/Kozea/cairocffi) (needs a Cairo DLL; see [here](https://github.com/SilverCardioid/CairoSVG#requirements) for more information)
* [CairoSVG](https://github.com/Kozea/CairoSVG)
* numpy

Installation using Pip (includes all requirements except the Cairo DLL):
```
pip install git+https://github.com/SilverCardioid/cairopath.git
```

## Usage
The module's main class, and the only that needs to be instantiated directly, is `Canvas`. It corresponds to a Cairo `Surface` and `Context` (which are accessible as the object properties `canvas.surface` and `canvas.context` respectively).

In the [constructor](#canvas), the `surfacetype` parameter specifies one of the five Cairo surface types (`'Image'`, `'SVG'`, `'PDF'`, `'PS'` or `'Recording'`), and `filename` the destination filename. Both are optional, as a canvas's `.export()` method can be used to save the canvas in any of the corresponding file types, and will convert the surface type if necessary. Wrappers for exporting to specific formats also exist: `.pdf()`, `.png()`, `.ps()` and `.svg()`. The `.data()` method returns the image as a standard pixel array.
```python
canvas = cairopath.Canvas(600, 600, bgcolor='#fff')
canvas.png('file.png') # or: canvas.export('Image', 'file.png')
```

### Shapes and colours
The shape drawing methods of a canvas are `.circle()`, `.ellipse()`, `.rect()` and `.path()`. The latter, used for general polylines and curves, can optionally take a data string corresponding to the [`d=""` SVG attribute](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Paths). It returns a `Path` object, which provides the same commands a data string does, but in function form. The following two lines are thus equivalent ways of drawing a rhombus:
```python
canvas.path('M0,-100 L 100,0 L 0,100 L -100,0z')
canvas.path().M(0, -100).L(100, 0).L(0, 100).L(-100, 0).z()
```

As in Cairo, calling a shape function adds the shape to the "current path", which is kept in memory and only made visible when it is used by a function like `.fill()`, `.stroke()` or [`.clip()`](#transformations). Calling one of these functions empties the current path buffer, unless the parameter `keep=True` is set (which corresponds to the `_preserve` versions of these functions in Cairo). For example, to draw a circle with both a fill and a stroke, use `canvas.circle(10).fill('#ff0', keep=True).stroke('#000')`.

Colours may be one of several data types: a list or tuple of RGB values (in the range 0-1 for floats or 0-255 for ints), a hex colour code as a string (e.g. `'#ffffff'`, `'#fff'`) or integer (`0xffffff`), or a `Gradient` object (created using `.lineargradient()` or `.radialgradient()`).

### Transformations
Transform methods include `.translate()`, `.scale()`, `.rotate()` and `.matrix()`, which mostly work the same way as the corresponding [SVG functions](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/transform). `.clip()` applies the current path as a [clip path](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/clip-path).

Both transforms and clips only apply to objects drawn after the call to the transform or clip method, and can be undone by calling `.resettransform()` or `.resetclip()`. The returned `Transform` object can also be used as a context manager, in order to apply transformations to a block of code and reset them automatically afterwards (as though it's an SVG `<g>` element with a `transform` or `clip-path` attribute):
```python
with canvas.scale(2):
	# objects drawn here will be scaled

with canvas.circle(10).clip():
	# objects drawn here will be clipped to a circle
```
which is equivalent to
```python
canvas.scale(2)
# objects drawn here will be scaled
canvas.resettransform()

canvas.circle(10).clip()
# objects drawn here will be clipped to a circle
canvas.resetclip()
```

## Example
A circled five-pointed star:
```python
import math
import cairopath

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
```

## Method list
The given arguments are the default values. Arrows indicate the return type if the method returns a new object, or the variable name if it returns an existing object for chaining (note the case difference).

### Canvas
```python
canvas = cairopath.Canvas(width, height, bgcolor=None, bgopacity=1, surfacetype='Image', filename=None)
```
* `canvas.clone(type='Image')` &rarr; `Canvas`<br/>Create a new canvas of any type with the same contents.
* `canvas.data(alpha=False)` &rarr; `numpy.ndarray`<br/>Convert the canvas to an RGB(A) pixel array, of shape ''height''×''width''×3 if `alpha=False` or ''height''×''width''×4 if `alpha=True`.
* `canvas.export(type='Image', filename=None)`<br/>Save the canvas in a file format corresponding to a surface type.
* `canvas.pdf(filename)`<br/>Export to PDF file
* `canvas.png(filename)`<br/>Export to PNG file
* `canvas.ps(filename)`<br/>Export to PostScript file
* `canvas.svg(filename)`<br/>Export to SVG file

Shapes & colours:
* `canvas.path(d=None)` &rarr; [`Path`](#path)
* `canvas.circle(r, cx=0, cy=0)` &rarr; `canvas`
* `canvas.ellipse(rx, ry, cx=0, cy=0)` &rarr; `canvas`
* `canvas.rect(width, height, x=0, y=0, center=False)` &rarr; `canvas`<br/>`x` and `y` are the rectangle's centre if `center=True`, or its top left vertex otherwise.
* `canvas.fill(color, opacity=1, evenodd=0, keep=False, affect=True)` &rarr; `canvas`<br/>Draw the current path filled in. `keep=True` preserves the current path for further drawing; `affect` toggles whether transformations affect gradients.
* `canvas.stroke(color, opacity=1, width=2, cap='butt', join='miter', miterlimit=10, dash=None, dashoffset=0, keep=False, affect=True)` &rarr; `canvas`<br/>Draw the current path as an outline.
* `canvas.lineargradient(x1=0, y1=0, x2=None, y2=None)` &rarr; [`Gradient`](#gradient)
* `canvas.radialgradient(r1=0, x1=0, y1=0, r2=100, x2=None, y2=None)` &rarr; `Gradient`

Transforms (the `Transform` object has identical methods, which return their parent `Transform` object):
* `canvas.translate(tx, ty=0)` &rarr; `Transform`
* `canvas.scale(sx, sy=None)` &rarr; `Transform`<br/>Omit `sy` for uniform scaling.
* `canvas.rotate(a, cx=0, cy=0, rad=False)` &rarr; `Transform`<br/>Angles are in radians if `rad=True`, or in degrees otherwise.
* `canvas.matrix(m, replace=False)` &rarr; `Transform`<br/>Apply a transformation matrix of the form `[xx, yx, xy, yy, x0, y0]`. If `replace=True`, replace the current transformation matrix, undoing any previous transformations.
* `canvas.clip(keep=False)` &rarr; `Transform`<br/>Set current path as clip path
* `canvas.resettransform()` &rarr; `Transform`
* `canvas.resetclip()` &rarr; `Transform`

### Path
```python
path = canvas.path(d=None)
```
Like in SVG, uppercase methods use absolute coordinates, and lowercase ones use coordinates relative to the previous vertex.
* `path.d(string)` &rarr; `path` (parse data string)
* `path.M(x, y)` &rarr; `path` (start path)
* `path.m(dx, dy)` &rarr; `path` (start path)
* `path.z()` &rarr; `path` (close path)

Lines:
* `path.L(x, y)` &rarr; `path` (line)
* `path.l(dx, dy)` &rarr; `path` (line)
* `path.H(x)` &rarr; `path` (horizontal line)
* `path.h(dx)` &rarr; `path` (horizontal line)
* `path.V(y)` &rarr; `path` (vertical line)
* `path.v(dy)` &rarr; `path` (vertical line)

Beziers:
* `path.C(x1, y1, x2, y2, x, y)` &rarr; `path` (cubic)
* `path.c(dx1, dy1, dx2, dy2, dx, dy)` &rarr; `path` (cubic)
* `path.S(x2, y2, x, y)` &rarr; `path` (smooth cubic)
* `path.s(dx2, dy2, dx, dy)` &rarr; `path` (smooth cubic)
* `path.Q(x1, y1, x, y)` &rarr; `path` (quadratic)
* `path.q(dx1, dy1, dx, dy)` &rarr; `path` (quadratic)
* `path.T(x, y)` &rarr; `path` (smooth quadratic)
* `path.t(dx, dy)` &rarr; `path` (smooth quadratic)

Arcs:
* `path.A(r, x, y, large=1, sweep=1)` &rarr; `path` (circular)
* `path.a(r, dx, dy, large=1, sweep=1)` &rarr; `path` (circular)
* `path.Ae(rx, ry, x, y, large=1, sweep=1, angle=0, rad=False)` &rarr; `path` (elliptical)
* `path.ae(rx, ry, dx, dy, large=1, sweep=1, angle=0, rad=False)` &rarr; `path` (elliptical)
* `path.Ac(xc, yc, r, a1, a2, sweep=1, rad=False)` &rarr; `path` (circular, Cairo syntax)

Supports chaining with `fill` or `stroke` (returning the `path`) or with `clip` (returning a `Transform`).

### Gradient
```python
grad = canvas.lineargradient(x1=0, y1=0, x2=None, y2=None)
grad = canvas.radialgradient(r1=0, x1=0, y1=0, r2=100, x2=None, y2=None)
```
* `grad.stop(offset, color, opacity=1)` &rarr; `grad`<br/>Add a colour stop at an offset along the gradient.
*	`grad.fill(opacity=1, evenodd=0, keep=False, affect=True)` &rarr; `canvas`<br/>Fill the current path with this gradient.
*	`grad.stroke(opacity=1, width=2, cap=0, join=0, miterlimit=10, dash=None, dashoffset=0, keep=False, affect=True)` &rarr; `canvas`<br/>Outline the current path with this gradient.
