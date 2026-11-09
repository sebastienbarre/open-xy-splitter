"""Generates the Splitter page's retained artwork, panel.svg.fragment (480 x 220 px).

The OP-XY draws a player's page from artwork it cannot recolor: a player can only
show or hide up to 24 pre-drawn shapes ("dots", splitter_player_dot_0..23). So the page is
made of layers, from bottom to top:

  1. the 24 key boxes, all in zone 2's color;
  2. 23 zone 1 overlays (dots 0..22). Dot k covers keys 1..k + 1, the keys before a
     split at key k + 2, in zone 1's color. Only one is shown at a time,
     chosen by the player, so the keyboard looks split in two zones;
  3. a 24th dot that is never shown, because the SDK requires all 24;
  4. the key pads (filled discs) and the key outlines, drawn again so the overlays
     do not hide them;
  5. the caption line the SDK requires, which the player leaves empty.

The key geometry comes from the design file designs/splitter.svg: boxes r1..r24
and pads k1..k24, numbered from the left-most key.

The design's coordinates are fractional, so a line would straddle two pixel rows
and look blurred or thick. The script snaps them to the pixel grid: every box edge
and pad centre moves to the middle of a pixel, so each 1 px stroke covers exactly
one row or column of pixels, and pads become circles of a whole radius. The design
file stays the reference and is not changed.

Run it from anywhere; it rewrites panel.svg.fragment beside this script.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ZONE1_FILL = '#323232'  # fill of a zone 1 key
ZONE2_FILL = '#969696'  # fill of a zone 2 key
EDGE = '#000000'   # stroke of every key box and pad
PAD_FILL = EDGE  # fill of a key pad
STROKE_WIDTH = 1.0
KEYS = 24
# Radius of a key pad, in pixels. A whole number keeps the circle's top, bottom,
# left and right on pixel centres, where a 1 px stroke is sharpest.
PAD_RADIUS = 10
# The machine's ID, which prefixes the artwork IDs the SDK binds.
PREFIX = 'splitter_player'
# Top left corner of the keyboard in the design. An overlay's geometry is relative
# to it and the overlay is moved there by its transform, because the SDK moves a
# dot by rewriting its transform.
ORIGIN = (18, 78)

SVG = '{http://www.w3.org/2000/svg}'


def number(value):
    """Formats a coordinate for SVG: at most four decimals, without trailing zeros.

    The device's SVG parser accepts at most four fractional digits.

    value: the coordinate.
    Returns the text.
    """
    return ('%.4f' % value).rstrip('0').rstrip('.')


def grid(value):
    """Snaps a coordinate to the middle of the nearest pixel.

    A 1 px stroke centred there covers exactly one pixel row or column.

    value: the coordinate, in pixels.
    Returns the snapped coordinate, a whole number plus one half. The same input
    always gives the same output, so edges shared by two keys stay shared.
    """
    return int(value + 0.5) + 0.5


def box(node):
    """Finds the bounding rectangle of a key box from the design, snapped to the grid.

    node: the box's <rect> or <path>. A path is read as pairs of absolute
          coordinates (M, L and C commands), so its curves, which only round the
          box's corners, stay inside the rectangle returned.
    Returns (left, top, right, bottom) in pixels, each from grid(). Corners are
    square: the design's rounding is under a pixel.
    """
    if node.tag == SVG + 'rect':
        x, y = float(node.get('x')), float(node.get('y'))
        bounds = x, y, x + float(node.get('width')), y + float(node.get('height'))
    else:
        values = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', node.get('d'))]
        xs, ys = values[0::2], values[1::2]
        bounds = min(xs), min(ys), max(xs), max(ys)
    return tuple(grid(v) for v in bounds)


def key_box(bounds, paint):
    """Draws a key box as an SVG rectangle.

    bounds: the box's rectangle, as returned by box().
    paint:  the fill, stroke and stroke-width attributes to draw it with.
    Returns the element text.
    """
    x0, y0, x1, y1 = bounds
    return '<rect x="%s" y="%s" width="%s" height="%s" %s/>' % (
        number(x0), number(y0), number(x1 - x0), number(y1 - y0), paint)


def overlay(boxes, last):
    """Draws a zone 1 overlay: the first keys of the keyboard in zone 1's color.

    boxes: the bounding rectangle of each key, from the left-most.
    last:  the number of keys to cover, from the left-most.
    Returns the path data, one rectangle per key, relative to ORIGIN. Corners are
    square, which the key outlines drawn on top hide.
    """
    subpaths = []
    for x0, y0, x1, y1 in boxes[:last]:
        x0, x1 = x0 - ORIGIN[0], x1 - ORIGIN[0]
        y0, y1 = y0 - ORIGIN[1], y1 - ORIGIN[1]
        subpaths.append('M%s %s L%s %s L%s %s L%s %s Z' % (
            number(x0), number(y0), number(x1), number(y0),
            number(x1), number(y1), number(x0), number(y1)))
    return ' '.join(subpaths)


def build(design):
    """Builds the artwork.

    design: the design file's root element, with the boxes r1..r24 and pads k1..k24.
    Returns the artwork as text, one element per line.
    """
    nodes = {n.get('id'): n for n in design.iter() if n.get('id')}
    boxes = [box(nodes['r%d' % k]) for k in range(1, KEYS + 1)]
    outline = 'fill="none" stroke="%s" stroke-width="%s"' % (EDGE, STROKE_WIDTH)
    parts = ['<g id="%s_panel">' % PREFIX, '<rect x="0" y="20" width="480" height="200" fill="#000000"/>']

    # Layer 1: every key in zone 2's color.
    zone2 = 'fill="%s" stroke="%s" stroke-width="%s"' % (ZONE2_FILL, EDGE, STROKE_WIDTH)
    for k in range(KEYS):
        parts.append(key_box(boxes[k], zone2))

    # Layer 2: dot k is zone 1 over keys 1..k + 1, for a split at key k + 2.
    for dot in range(KEYS - 1):
        parts.append('<path id="%s_dot_%d" transform="matrix(1 0 0 1 %d %d)" d="%s" fill="%s" '
                     'stroke="%s" stroke-width="%s"/>' % (
                         PREFIX, dot, ORIGIN[0], ORIGIN[1], overlay(boxes, dot + 1), ZONE1_FILL, EDGE, STROKE_WIDTH))

    # Layer 3: the 24th dot waits off screen, never shown.
    parts.append('<circle id="%s_dot_23" transform="matrix(1 0 0 1 -50 -50)" cx="0" cy="0" r="1" '
                 'fill="%s" stroke="%s" stroke-width="%s"/>' % (PREFIX, ZONE1_FILL, EDGE, STROKE_WIDTH))

    # Layer 4: filled pads, then outlines, over the overlays.
    pad_paint = 'fill="%s" stroke="%s" stroke-width="%s"' % (PAD_FILL, EDGE, STROKE_WIDTH)
    for k in range(1, KEYS + 1):
        pad = nodes['k%d' % k]
        parts.append('<circle cx="%s" cy="%s" r="%s" %s/>' % (
            number(grid(float(pad.get('cx')))), number(grid(float(pad.get('cy')))), PAD_RADIUS, pad_paint))
    for k in range(KEYS):
        parts.append(key_box(boxes[k], outline))

    # Layer 5: the SDK requires a caption; the player leaves it empty.
    parts.append('<text id="%s_text" transform="matrix(1 0 0 1 240 215)" fill="#F2F2F2" '
                 'font-family="UniversNextPro-Light" font-size="22">splitter</text>' % PREFIX)
    parts.append('</g>')
    return '\n'.join(parts) + '\n'


def main():
    """Reads designs/splitter.svg at the repository root and writes panel.svg.fragment."""
    design = ET.parse(Path(__file__).parent.parent.parent / 'designs' / 'splitter.svg').getroot()
    Path(__file__).with_name('panel.svg.fragment').write_text(build(design), encoding='utf-8', newline='\n')


main()
