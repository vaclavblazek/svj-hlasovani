#!/usr/bin/python

import sys
import cairo
from itertools import izip, cycle

import apttools

output = sys.argv[1]

inch = 25.4
point = inch / 72

a4Width = 210
a4Height = 297
stripWidth = a4Width
stripHeight = a4Height / 3.

pdf = cairo.PDFSurface(output, a4Width / point, a4Height / point)
ctx = cairo.Context(pdf)
ctx.scale(1 / point, 1 / point)
matrix = ctx.get_matrix()

def measureText(ctx, text):
    savedPath = ctx.copy_path()

    ctx.move_to(0, 0)
    ctx.text_path(text)
    extents = ctx.stroke_extents()

    ctx.new_path()
    ctx.append_path(savedPath)

    dims = (extents[2] - extents[0], extents[3] - extents[1])
    return (extents[0], extents[1]), dims

def placeText(ctx, text, pos, align=(0, 0)):
    tpos, dims = measureText(ctx, text)

    if align[0] < 0:
        x = 0
    elif align[0] > 0:
        x = pos[0] - tpos[0]
    else:
        x = pos[0] - (dims[0] / 2) - tpos[0]

    if align[1] < 0:
        y = pos[1] - dims[1] - tpos[1]
    elif align[1] > 0:
        y = 0
    else:
        y = pos[1] - (dims[1] / 2) - tpos[1]

    ctx.move_to(x, y)

    ctx.show_text(text)

apts = apttools.Apartments(sys.stdin, (13, 15, 17, 19, 21, 23, 25), 20)
print apts

first = True
for apt, strip in izip(sorted(apts.values()), cycle((0, 1, 2))):
    print apt

    if strip == 0:
        if not first:
            ctx.show_page()
            ctx.set_matrix(matrix)
            ctx.new_path()
        first = False
    else:
        ctx.translate(0, stripHeight)

    # divider
    if strip in (0, 1):
        ctx.set_line_width(0.1)
        ctx.move_to(0, stripHeight)
        ctx.line_to(stripWidth, stripHeight)
        ctx.stroke()

    # apt id
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL
                         , cairo.FONT_WEIGHT_BOLD)
    ctx.set_font_size(100)
    ctx.set_source_rgb(0, 0, 0)

    placeText(ctx, str(apt.id), (stripWidth / 2, stripHeight / 2))


    # apt localId and area
    ctx.select_font_face("Arial", cairo.FONT_SLANT_NORMAL
                         , cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(5)

    placeText(ctx, "{}/{}".format(apt.localBuilding, apt.localId)
              , (15, stripHeight - 19), align=(1, -1))

    placeText(ctx, "{}/{}".format(apt.area, apts.total)
              , (15, stripHeight - 14), align=(1, -1))
