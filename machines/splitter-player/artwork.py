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
  5. the SDK's output keyboard along the bottom: 128 keys and 128 activity dots, which
     the SDK lays out and lights for the notes the player actually sounds (after
     transposition). The player never touches them;
  6. the caption line the SDK requires, which the player leaves empty.

The key geometry comes from the design file designs/splitter.svg: boxes r1..r24
and pads k1..k24, numbered from the left-most key.

Run it from anywhere; it rewrites panel.svg.fragment beside this script.
"""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

PREFIX = 'splitter_player' # The machine's ID, which prefixes the artwork IDs the SDK binds.

KEYS = 24 # Number of keys on the player's page.

STROKE_WIDTH = 1.0 # Stroke width for key boxes and pads.
PAD_RADIUS = 10 # Radius of a key pad, in pixels.

EDGE_STROKE_COLOR = '#000000'   # stroke of every key box and pad
ZONE1_FILL_COLOR = '#323232'  # fill of a zone 1 key
ZONE2_FILL_COLOR = '#969696'  # fill of a zone 2 key
PAD_FILL_COLOR = EDGE_STROKE_COLOR  # fill of a key pad
RANGES_FILL_COLOR = '#AFAFAF' # color of the addressable note range caption

# The SDK's output keyboard: a row 444 px wide from x = 18, with its keys at y = 174 and
# its activity dots inside them. The SDK moves and scales every key and dot each frame.
# Note that these _Y positions match the ones in the SDK's screen_player.hpp routines, but could
# be entirely different since the X,Y positions of the keys and dots are set by the SDK each frame.
# They do however help positioning the rest of our UI elements relative to the keyboard.
PLAYED_KEYS_Y = 174
PLAYED_KEYS_WHITE_DOT_Y = 211
PLAYED_KEYS_BLACK_DOT_Y = 195
PLAYED_KEYS_WHITE_FILL = '#F0F0F0'
PLAYED_KEYS_BLACK_FILL = '#000000'

MIDI_WHITE = (0, 2, 4, 5, 7, 9, 11)  # pitch classes of the white keys, from C

# Note that the parameter row is 20 px high, our physical keyboard representation 64 px and the
# SDK's output keyboard starts at y = 174, which leaves 174 - 20 - 64 = 90 px, 45 above and 45
# below ours. The design file's keyboard should reflect that vertical position at 20 + 45 = 65 px.
PHYSICAL_KEYBOARD_Y = 65 # y position of the physical keyboard representation
PHYSICAL_KEYBOARD_H = 64 # height of the physical keyboard representation
RANGES_FONT_SIZE = 17 # font size of the addressable note range caption
RANGES_Y = PHYSICAL_KEYBOARD_Y + PHYSICAL_KEYBOARD_H + round(RANGES_FONT_SIZE * 1.65 / 1.33) # y position of the addressable note range caption, we are accounting for 65% of the font size for spacing between the keyboard and the caption, then the caption itself, divided by 1.33 to roughly go from points to pixels; no need to be super accurate here.

SVG = '{http://www.w3.org/2000/svg}'


def number(value):
    """Formats a coordinate for SVG: at most four decimals, without trailing zeros.

    The device's SVG parser accepts at most four fractional digits.

    value: the coordinate.
    Returns the text.
    """
    return ('%.4f' % value).rstrip('0').rstrip('.')


def box(node):
    """Finds the bounding rectangle of a key box from the design.

    node: the box's <rect> or <path>. A path is read as pairs of absolute
          coordinates (M, L and C commands), so its curves, which only round the
          box's corners, stay inside the rectangle returned.
    Returns (left, top, right, bottom) in pixels. Corners are square.
    """
    if node.tag == SVG + 'rect':
        x, y = float(node.get('x')), float(node.get('y'))
        bounds = x, y, x + float(node.get('width')), y + float(node.get('height'))
    else:
        values = [float(n) for n in re.findall(r'-?\d+(?:\.\d+)?', node.get('d'))]
        xs, ys = values[0::2], values[1::2]
        bounds = min(xs), min(ys), max(xs), max(ys)
    return tuple(bounds)


def is_black(note):
    """Tells whether a MIDI note is a black key.

    note: the MIDI note, 0 to 127.
    """
    return note % 12 not in MIDI_WHITE


def PLAYED_KEYS_keyboard(prefix):
    """Draws the SDK's output keyboard: 128 keys, then 128 activity dots, all at rest.

    prefix: the artwork ID prefix.
    Returns the elements, white keys before black keys, then the dots, as the SDK requires.
    """
    parts = []
    for black in (False, True):
        for note in range(128):
            if is_black(note) != black:
                continue
            parts.append('<path id="%s_key_%d" transform="matrix(1 0 0 1 %s %d)" d="%s" fill="%s" '
                         'stroke="%s" stroke-width="%s"/>' % (
                             prefix, note, 0, PLAYED_KEYS_Y, 'M0 0H6V27H0Z' if black else 'M0 0H10V44H0Z',
                             PLAYED_KEYS_BLACK_FILL if black else PLAYED_KEYS_WHITE_FILL, EDGE_STROKE_COLOR, STROKE_WIDTH))
    for note in range(128):
        black = is_black(note)
        fill = PLAYED_KEYS_WHITE_FILL if black else PLAYED_KEYS_BLACK_FILL
        parts.append('<circle id="%s_played_%d" transform="matrix(1 0 0 1 0 %d)" cx="0" cy="0" r="%s" '
                     'fill="%s" stroke="%s" stroke-width="0.5"/>' % (
                         prefix, note, PLAYED_KEYS_BLACK_DOT_Y if black else PLAYED_KEYS_WHITE_DOT_Y,
                         '2.5' if black else '3', fill, fill))
    return parts


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
    Returns the path data, one rectangle per key, in page coordinates. Corners are
    square, which the key outlines drawn on top hide.
    """
    subpaths = []
    for x0, y0, x1, y1 in boxes[:last]:
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
    outline = 'fill="none" stroke="%s" stroke-width="%s"' % (EDGE_STROKE_COLOR, STROKE_WIDTH)
    parts = ['<g id="%s_panel">' % PREFIX, '<rect x="0" y="20" width="480" height="200" fill="#000000"/>']

    # Layer 1: every key in zone 2's color.
    zone2 = 'fill="%s" stroke="%s" stroke-width="%s"' % (ZONE2_FILL_COLOR, EDGE_STROKE_COLOR, STROKE_WIDTH)
    for k in range(KEYS):
        parts.append(key_box(boxes[k], zone2))

    # Layer 2: dot k is zone 1 over keys 1..k + 1, for a split at key k + 2. The SDK shows or
    # hides a dot by moving its x translation, so its shapes are in page coordinates.
    for dot in range(KEYS - 1):
        parts.append('<path id="%s_dot_%d" transform="matrix(1 0 0 1 0 0)" d="%s" fill="%s" '
                     'stroke="%s" stroke-width="%s"/>' % (
                         PREFIX, dot, overlay(boxes, dot + 1), ZONE1_FILL_COLOR, EDGE_STROKE_COLOR, STROKE_WIDTH))

    # Layer 3: the 24th dot waits off screen, never shown.
    parts.append('<circle id="%s_dot_23" transform="matrix(1 0 0 1 -50 -50)" cx="0" cy="0" r="1" '
                 'fill="%s" stroke="%s" stroke-width="%s"/>' % (PREFIX, ZONE1_FILL_COLOR, EDGE_STROKE_COLOR, STROKE_WIDTH))

    # Layer 4: filled pads, then outlines, over the overlays.
    pad_paint = 'fill="%s" stroke="%s" stroke-width="%s"' % (PAD_FILL_COLOR, EDGE_STROKE_COLOR, STROKE_WIDTH)
    for k in range(1, KEYS + 1):
        pad = nodes['k%d' % k]
        parts.append('<circle cx="%s" cy="%s" r="%s" %s/>' % (
            number(float(pad.get('cx'))), number(float(pad.get('cy'))), PAD_RADIUS, pad_paint))
    for k in range(KEYS):
        parts.append(key_box(boxes[k], outline))

    # Layer 5: a caption that will be used to display the addressable note range by the player.
    parts.append('<text id="%s_text" transform="matrix(1 0 0 1 240 %d)" fill="%s" ' % (PREFIX, RANGES_Y, RANGES_FILL_COLOR) +
                 'font-family="UniversNextPro-Light" font-size="%d">splitter</text>' % RANGES_FONT_SIZE)

    # Layer 6: the SDK's output keyboard, below our keyboard.
    parts.extend(PLAYED_KEYS_keyboard(PREFIX))

    parts.append('</g>')
    return '\n'.join(parts) + '\n'


def main():
    """Reads designs/splitter.svg at the repository root and writes panel.svg.fragment."""
    design = ET.parse(Path(__file__).parent.parent.parent / 'designs' / 'splitter.svg').getroot()
    Path(__file__).with_name('panel.svg.fragment').write_text(build(design), encoding='utf-8', newline='\n')


main()
