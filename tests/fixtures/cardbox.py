import sys
import build123d as b

# =====================================================================
#  EASY ADJUSTMENTS -- edit these, then re-run this script
#
#  Settings are grouped in this order (the app's Parameters panel lists
#  them in the same order):
#    1. BOX            card size, card count, number of decks
#    2. LID ART        ONE of: the name (text) OR an image OR nothing
#    3. LID FIT & LIP  how firmly the lid is held
#    4. HEX PATTERN    optional honeycomb openings
#    5. FINE-TUNING    clearances and wall thicknesses
# =====================================================================

# ---- 1. BOX ----------------------------------------------------------
CARD_LENGTH    = 88.0      # mm, actual card LENGTH (long edge)
CARD_WIDTH     = 63.0      # mm, actual card WIDTH  (short edge)
CARD_THICKNESS = 0.31      # mm, thickness of ONE card
                           #   Tip: measure the whole stack with calipers
                           #   and divide by the card count for accuracy.
NUM_CARDS      = 55        # cards PER DECK (each compartment holds this many)
NUM_DECKS      = 1         # how many independent card compartments, side by
                           #   side. Each gets its own fully separate cavity
                           #   (a solid divider between them, no shared
                           #   space) but they're covered by ONE lid that
                           #   slides over both in a single motion.
                           #   Set to 1 to get the original single-deck box.

# ---- 2. LID ART: choose ONE -- text, image, or none -------------------
LID_ART        = "text"    # [choice: blank|text|image] what goes on the lid: a name, a picture, or nothing
                           #   blank = plain lid, text = engrave the name,
                           #   image = engrave the picture. Only the settings
                           #   for the chosen mode are used (and shown in the
                           #   app); the other group is ignored, so a leftover
                           #   image path never overrides your name.

# -- TEXT mode: used only when LID_ART = "text" (shown in the app only then) --
LID_TEXT       = "Bobbie"  # [when LID_ART=text] the name engraved on the lid ("" = no engraving)
                           #   With NUM_DECKS > 1 the name is centered
                           #   across the FULL lid width (it can straddle
                           #   the internal divider) -- there's only one
                           #   engraving for the whole box, not one per deck.
TEXT_SIZE      = 18        # [when LID_ART=text] font size (mm)
FONT           = "Arial"   # [when LID_ART=text] any installed font name, e.g. "Arial"
                           #   (macOS/Windows: "Arial"; most Linux: "Liberation Sans" or "DejaVu Sans")
TEXT_DEPTH     = 0.8       # [when LID_ART=text] engraving depth (mm)
TEXT_ROTATION  = 0         # [when LID_ART=text] degrees, rotates the text in the plane
                           #   of the lid. 0 = reads along SLOT_LENGTH (the
                           #   card-length axis, X); 90 = reads along
                           #   TOTAL_WIDTH (Y) -- i.e. along the lid's long
                           #   side once decks are placed side by side,
                           #   facing the same way you'd read it while
                           #   holding the box by its lip and sliding the
                           #   lid open. Set back to 0 for a single-deck box
                           #   (NUM_DECKS=1), where X is usually the long side.

# -- IMAGE mode: used only when LID_ART = "image" (shown in the app only then) --
LID_IMAGE      = ""        # [browse] [when LID_ART=image] the picture to engrave (.svg, .png, .jpg)
                           #   Use the Browse button in the Parameters panel,
                           #   or paste a FULL path ("/Users/you/Documents/logo.svg").
                           #   PNG/JPG are auto-traced to black-and-white
                           #   shapes. Best with high-contrast, single-colour
                           #   art; photos won't trace well.
                           #   SVG: solid filled shapes work best; stroke-only
                           #   lines are ignored (convert strokes to paths).
IMAGE_SCALE    = 100       # [when LID_ART=image] size, % of the largest size that fits the lid (never stretched)
                           #   100 = as big as fits (with IMAGE_MARGIN kept clear);
                           #   50 = half that size. Width and height always scale
                           #   together, so the picture's proportions are locked.
                           #   Values over 100 can run past the lid edge.
IMAGE_MARGIN   = 4         # [when LID_ART=image] mm kept clear around the image (and away from the pull tab)
IMAGE_ROTATION = 0         # [when LID_ART=image] degrees, rotates the image in the plane of the lid
IMAGE_DEPTH    = 0.8       # [when LID_ART=image] engraving depth (mm)
IMAGE_INVERT   = False     # [when LID_ART=image] False = the drawn shapes are engraved (cut in).
                           #   True = a solid-filled square of the image's
                           #   bounding box is engraved with the shapes
                           #   left RAISED (use for dark-background art)
IMAGE_THRESHOLD = 128      # [when LID_ART=image] PNG/JPG only: 0-255 cutoff for "ink" (higher = more counts as art)
IMAGE_DARK_IS_ART = True   # [when LID_ART=image] PNG/JPG only: True = dark pixels are the art, False = light pixels are
                           #   (use False for a white logo on a dark background).
                           #   Transparent PNG areas always count as background.

# ---- 3. LID FIT & LIP: how firmly the lid is held ---------------------
LOCK_BUMP_HEIGHT = 0.24    # mm the locking bump sticks out below the lid's underside (the side WITHOUT the name/image)
                           #   This is the slight raised ridge near the pull
                           #   tab that makes the lid click into place and stay
                           #   closed. Taller = firmer lock, harder to open.
                           #   Try 0.4-0.6 for a firmer hold; 0 removes it.
                           #   It must stay under STACK_CLEARANCE (it dips
                           #   into the space above the cards) and under
                           #   half of LOCK_BUMP_WIDTH.
LOCK_BUMP_WIDTH  = 1.6     # mm width of the bump where it meets the lid
                           #   Wider = a gentler ramp (easier to open and
                           #   close); narrower = a sharper, more positive click.
                           #   Max = WALL_THICKNESS (wider would hit the front wall).
LIP_WALL_EXTRA = 0.8       # mm of EXTRA thickness on the 3 walls that hold the lid (both long sides + the closed end)
                           #   Thicker lip = sturdier rail that captures the
                           #   lid so it stops snapping or flexing out.
                           #   Grows the box by this on each of those 3 faces;
                           #   the lid and card cavities are unchanged. 0 disables.
                           #   Try 1.2-1.6 for a much stiffer lip.
LID_ENGAGE     = 1.2       # mm each lid edge sits INSIDE the side walls (default = half of WALL_THICKNESS)
                           #   Deeper = the lid is gripped more firmly and
                           #   can't be lifted or wobbled out. Limited by the
                           #   wall thickness (an error tells you the max).
SLIDER_CLEARANCE = 0.05    # mm sliding-fit gap between lid and box
                           #   Smaller = tighter, harder to slide. Printers
                           #   vary: raise to 0.1-0.15 if the lid binds.

# ---- 4. HEX PATTERN: optional honeycomb openings ----------------------
HEX_PATTERN    = False     # True = honeycomb openings on lid + box floor (one grid centred on the box); False = flat solid lid and floor
                           #   (like the original model); the engraved
                           #   name sits on a solid patch, no holes.
                           #   Each deck's honeycomb is generated and
                           #   trimmed separately so holes never cut
                           #   into the divider between decks.
HEX_BACK_MARGIN  = 2.4     # [when HEX_PATTERN=true] mm of solid lid kept along the closed (back) end
                           #   The honeycomb stops this far short of the lid's back
                           #   edge, leaving a solid wall there. 0 = holes run to the edge.
HEX_CIRCUMRADIUS = 6       # [when HEX_PATTERN=true] size of each hexagon opening (mm, corner-to-center)
HEX_SPACING      = 7       # [when HEX_PATTERN=true] center-to-center packing of the hex grid (mm); bigger = thicker webs between holes
LID_ART_STYLE    = "solid_in_hex"  # [choice: solid_in_hex|engraved_plate] [when HEX_PATTERN=true] how the name/image sits on the honeycomb lid
                           #   solid_in_hex = no plate: the honeycomb runs across the whole lid
                           #   and is left solid wherever the art is, so the art reads as
                           #   solid shapes in the pattern. engraved_plate = a solid
                           #   rectangle with the art engraved into it.
ART_THICKEN      = 0.4     # [when HEX_PATTERN=true] solid_in_hex only: mm added around the art so thin lines stay printable (0 = as drawn)
PLATE_SHAPE      = "rounded_box"  # [choice: rounded_box|hug] [when HEX_PATTERN=true] engraved_plate only: shape of the solid backing
                           #   rounded_box = a rectangle with rounded corners around the art.
                           #   hug = a solid outline that follows the letters/shape
                           #   itself, with the honeycomb running right up to it.
PLATE_CORNER_RADIUS = 4    # [when HEX_PATTERN=true] rounded_box only: corner radius in mm (0 = square corners)
NAMEPLATE_MARGIN = 4       # [when HEX_PATTERN=true] engraved_plate only: mm solid border kept around the name or image
                           #   The plate auto-sizes to the engraving's bounding box,
                           #   so a name with a descender (g, y, p) makes it a
                           #   bit taller and a very short name makes a small
                           #   plate. If it ever looks cramped against the
                           #   surrounding hexes, raise this a couple of mm.
# =====================================================================

# ---- 5. FINE-TUNING (sensible defaults; change only if you need to) ----
CARD_CLEARANCE  = 1.0      # mm gap on EACH side around the card stack
STACK_CLEARANCE = 1.0      # mm extra headroom above the stack so the lid closes
WALL_THICKNESS  = 2.4      # mm box/lid wall thickness (see note below)
DIVIDER_THICKNESS = WALL_THICKNESS
                           # mm thickness of the internal wall between decks.
                           #   Defaults to WALL_THICKNESS; bump it up if you
                           #   want a sturdier divider. It only needs to span
                           #   the card-cavity height -- see note further
                           #   down about why the lid still slides over it.
GRIP_HOLE       = 8        # mm radius of the thumb-grip cut on the end wall
GRIP_TAB        = 6        # mm length of the slider pull tab
# ---------------------------------------------------------------------
# NOTE on WALL_THICKNESS: the solid FLOOR under the cards is now the FULL
# WALL_THICKNESS (it used to print at half that, which caused a weak seam
# where the walls met the floor). The interior card height is computed to
# stay correct regardless, so the box just gets taller if you raise it.
#
# NOTE on the divider (NUM_DECKS > 1): the wall between decks only occupies
# the card-cavity HEIGHT (floor to cavity ceiling). Above that, the lid's
# sliding channel is cut as ONE continuous full-width slot -- if the divider
# were solid all the way up to the box's outer top, it would form a raised
# rail down the middle that the single wide lid couldn't slide over. This
# way the lid's flat underside rests on top of the divider and glides
# straight across it, exactly like it glides across the tops of the two
# outer side walls.
#
# NOTE on the grip scoop(s): the front thumb-access notch and every divider
# notch are cut by the SAME sphere shape, reused at each position that needs
# one (see GRIP_Y_POSITIONS below). Using one shape for both, rather than
# two independently-shaped cuts, guarantees they're always geometrically
# consistent -- there's no separate math for "the front hole" and "the
# divider notch" to keep in sync, they're just the same sphere sampled at
# different Y positions along the same corner line.
# =====================================================================


# ----- Derived dimensions (the geometry below uses these) -------------
# ---- Validate the settings up front, with plain-English errors ----------
LID_ART = str(LID_ART).strip().lower()
if LID_ART not in ("blank", "text", "image"):
    raise ValueError(
        f'LID_ART must be "blank", "text" or "image" (got {LID_ART!r}). '
        "Pick ONE: a plain lid, the name, or an image.")
if LID_ART == "image" and not LID_IMAGE.strip():
    raise ValueError(
        'LID_ART is "image" but LID_IMAGE is empty. Use Browse to pick a '
        'picture, or set LID_ART to "text" (name) or "blank".')

LID_ART_STYLE = str(LID_ART_STYLE).strip().lower()
if LID_ART_STYLE not in ("solid_in_hex", "engraved_plate"):
    raise ValueError(
        f'LID_ART_STYLE must be "solid_in_hex" or "engraved_plate" (got {LID_ART_STYLE!r}).')
PLATE_SHAPE = str(PLATE_SHAPE).strip().lower()
if PLATE_SHAPE not in ("rounded_box", "hug"):
    raise ValueError(f'PLATE_SHAPE must be "rounded_box" or "hug" (got {PLATE_SHAPE!r}).')
if PLATE_CORNER_RADIUS < 0:
    raise ValueError("PLATE_CORNER_RADIUS can't be negative (use 0 for square corners).")
if ART_THICKEN < 0:
    raise ValueError("ART_THICKEN can't be negative (use 0 for the art as drawn).")

_SIDE_WALL = WALL_THICKNESS + LIP_WALL_EXTRA          # side wall thickness at the lip
_MIN_SKIN  = 1.2                                      # mm left outside the lid groove
if LID_ENGAGE < 0 or LID_ENGAGE > _SIDE_WALL - _MIN_SKIN:
    raise ValueError(
        f"LID_ENGAGE={LID_ENGAGE} doesn't fit: the side wall is {_SIDE_WALL:.1f} mm "
        f"(WALL_THICKNESS + LIP_WALL_EXTRA) and {_MIN_SKIN} mm must stay outside the "
        f"lid groove. Use 0 to {_SIDE_WALL - _MIN_SKIN:.1f}, or raise LIP_WALL_EXTRA.")

if LOCK_BUMP_HEIGHT < 0:
    raise ValueError("LOCK_BUMP_HEIGHT can't be negative (use 0 for no bump).")
if LOCK_BUMP_HEIGHT > 0:
    if LOCK_BUMP_WIDTH <= 0 or LOCK_BUMP_HEIGHT > LOCK_BUMP_WIDTH / 2:
        raise ValueError(
            f"LOCK_BUMP_HEIGHT={LOCK_BUMP_HEIGHT} is too tall for LOCK_BUMP_WIDTH="
            f"{LOCK_BUMP_WIDTH}: the height can be at most half the width "
            f"({LOCK_BUMP_WIDTH / 2:g}). Raise the width or lower the height.")
    if LOCK_BUMP_WIDTH > WALL_THICKNESS:
        raise ValueError(
            f"LOCK_BUMP_WIDTH={LOCK_BUMP_WIDTH} is wider than WALL_THICKNESS "
            f"({WALL_THICKNESS}): the bump would run into the front wall and the "
            f"lid couldn't slide in. Use {WALL_THICKNESS:g} or less.")
    if LOCK_BUMP_HEIGHT >= STACK_CLEARANCE:
        raise ValueError(
            f"LOCK_BUMP_HEIGHT={LOCK_BUMP_HEIGHT} would touch the top card: it must be "
            f"under STACK_CLEARANCE ({STACK_CLEARANCE} mm).")

# Inner card slot = card size + clearance on every side (one deck):
SLOT_LENGTH = CARD_LENGTH + 2 * CARD_CLEARANCE
SLOT_WIDTH  = CARD_WIDTH  + 2 * CARD_CLEARANCE

# Interior floor-to-lid height we need for the stack:
NEEDED_INTERIOR = CARD_THICKNESS * NUM_CARDS + STACK_CLEARANCE
# With the full-thickness floor, the interior equals SLOT_HEIGHT exactly:
SLOT_HEIGHT = NEEDED_INTERIOR

# Multi-deck layout: decks sit side by side along Y, each DIVIDER_THICKNESS
# apart, centered as a group on Y=0.
DECK_PITCH  = SLOT_WIDTH + DIVIDER_THICKNESS
TOTAL_WIDTH = NUM_DECKS * SLOT_WIDTH + (NUM_DECKS - 1) * DIVIDER_THICKNESS
DECK_Y = [-TOTAL_WIDTH / 2 + SLOT_WIDTH / 2 + i * DECK_PITCH for i in range(NUM_DECKS)]
# Y-position of each divider (midway between adjacent decks); empty list if NUM_DECKS==1
DIVIDER_Y = [(DECK_Y[i] + DECK_Y[i + 1]) / 2 for i in range(NUM_DECKS - 1)]

# The lid-channel (mouth) cut spans the FULL width in one piece (see divider
# note above). A tiny overlap into the cavity avoids a coincident-face seam
# where the two cuts meet -- without it, OCC's boolean engine can leave a
# knife-edge sliver that either fails or prints unreliably.
MOUTH_OVERLAP = 0.05
MOUTH_BOTTOM  = SLOT_HEIGHT / 2 - MOUTH_OVERLAP
MOUTH_TOP     = SLOT_HEIGHT / 2 + WALL_THICKNESS + MOUTH_OVERLAP
MOUTH_H       = MOUTH_TOP - MOUTH_BOTTOM
MOUTH_Z       = (MOUTH_TOP + MOUTH_BOTTOM) / 2
# ---------------------------------------------------------------------

# GRIP_Z is the cavity-ceiling height -- the natural corner line where the
# front wall's inner face meets the top of every cavity/divider. Centering
# the grip sphere here means the material above it (already open, because
# it's inside the lid's sliding channel) clips the sphere almost exactly in
# half, giving a clean half-round scoop rather than an arbitrary deep bite.
GRIP_Z = SLOT_HEIGHT / 2
# Every Y position that gets a grip sphere: the box's own center (the main
# thumb hole) plus every divider. For NUM_DECKS==2 the single divider sits
# exactly at Y=0, so this list collapses to one shared sphere -- literally
# the same cut serving as both the front hole and the divider notch.
GRIP_Y_POSITIONS = sorted(set([0.0] + DIVIDER_Y))


def hex_lattice_points():
    """Centres of the honeycomb cells, as ONE grid for the whole box.

    The grid is anchored on the middle of the box (a hexagon sits exactly at
    X=0, Y=0), so the pattern mirrors left/right and front/back from the
    centre -- with several decks it flows continuously across the dividers
    instead of restarting in every deck. (A lattice anchored on a cell
    centre is symmetric about both axes.) The cell spacing is the same as
    the old per-deck grid: neighbours 2*HEX_SPACING apart, columns
    sqrt(3)*HEX_SPACING apart, every other column shifted half a step."""
    r = HEX_SPACING
    dx = 3 ** 0.5 * r
    dy = 2 * r
    nx = int((SLOT_LENGTH / 2) // dx) + 2
    ny = int((TOTAL_WIDTH / 2) // dy) + 2
    pts = []
    for i in range(-nx, nx + 1):
        shift = dy / 2 if i % 2 else 0.0
        for j in range(-ny, ny + 1):
            pts.append((i * dx, j * dy + shift))
    return pts


def solid_art_faces(grow=None):
    """The lid art as faces in XY, grown by `grow` mm (default ART_THICKEN).
    Used for the solid_in_hex style and for the hugging backing."""
    grow = ART_THICKEN if grow is None else grow
    faces = list(make_text_sketch(b.Plane.XY).faces())
    if grow > 0 and faces:
        with b.BuildSketch() as sk:
            for f in faces:
                b.insert(f)
            b.offset(amount=grow)
        faces = list(sk.sketch.faces())
    return faces


def _floating_cells(points, art_faces):
    """Hex cells that fully contain a piece of art. Cutting those would leave
    the piece floating loose (attached to nothing), so the whole cell stays
    solid instead."""
    drop = set()
    for a in art_faces:
        abb = a.bounding_box()
        for idx, (px, py) in enumerate(points):
            if idx in drop:
                continue
            r = HEX_CIRCUMRADIUS
            if (abb.min.X < px - r or abb.max.X > px + r or
                    abb.min.Y < py - r or abb.max.Y > py + r):
                continue
            with b.BuildSketch() as cell:
                with b.Locations((px, py)):
                    b.RegularPolygon(HEX_CIRCUMRADIUS, 6, major_radius=False)
            ca = cell.sketch.faces()[0]
            inter = ca & a
            if inter and abs(sum(f.area for f in inter.faces()) - a.area) < 1e-3 * max(a.area, 1):
                drop.add(idx)
    return drop


def make_multideck_hex_sketch(plane, exclude_wh=None, back_margin=0.0, keep_dividers=True,
                              art_faces=None):
    """Honeycomb of hexagonal holes for the floor or lid: one grid centred on
    the box, trimmed to the card-cavity footprint, with every divider strip
    left solid (so holes never cut into the wall between decks).
    exclude_wh=(w,h) keeps a solid rectangle in the middle (the nameplate).
    back_margin keeps that many mm solid along the closed (+X) end -- used on
    the lid so it has a solid back wall instead of holes running to its edge.
    keep_dividers=True leaves a solid strip over each divider between decks
    (needed on the FLOOR, where holes would cut into the divider's base). The
    lid passes False: it sits above the dividers, so the pattern simply runs
    unbroken across the middle.

    NOTE: built with ADD/INTERSECT/SUBTRACT modes inside a single BuildSketch
    rather than the '+'/'-' operators on Sketch objects -- unioning two
    multi-face hex compounds with '+' throws a 'Null TopoDS_Shape'
    boolean-fuse error in this build123d version."""
    pts = hex_lattice_points()
    if art_faces:
        skip = _floating_cells(pts, art_faces)
        pts = [p for i, p in enumerate(pts) if i not in skip]
    with b.BuildSketch(plane) as sketch:
        with b.Locations(*pts):
            b.RegularPolygon(HEX_CIRCUMRADIUS, 6, major_radius=False)
        b.Rectangle(SLOT_LENGTH, TOTAL_WIDTH, mode=b.Mode.INTERSECT)
        if art_faces:
            for f in art_faces:
                b.insert(f, mode=b.Mode.SUBTRACT)
        if keep_dividers:
            for dy in DIVIDER_Y:
                with b.Locations((0, dy)):
                    b.Rectangle(SLOT_LENGTH + 2, DIVIDER_THICKNESS, mode=b.Mode.SUBTRACT)
        if back_margin > 0:
            with b.Locations((SLOT_LENGTH / 2 - back_margin + (back_margin + 2) / 2, 0)):
                b.Rectangle(back_margin + 2, TOTAL_WIDTH + 2, mode=b.Mode.SUBTRACT)
        if exclude_wh is not None:
            rr = min(PLATE_CORNER_RADIUS, exclude_wh[0] / 2 - 0.01, exclude_wh[1] / 2 - 0.01)
            if rr > 0:
                b.RectangleRounded(exclude_wh[0], exclude_wh[1], rr, mode=b.Mode.SUBTRACT)
            else:
                b.Rectangle(exclude_wh[0], exclude_wh[1], mode=b.Mode.SUBTRACT)
    return sketch.sketch


def _find_image_path():
    import os
    p = os.path.expanduser(LID_IMAGE.strip())
    candidates = [p]
    if not os.path.isabs(p):
        try:
            candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), p))
        except NameError:          # __file__ undefined in some runners
            pass
    for c in candidates:
        if os.path.isfile(c):
            return c
    raise FileNotFoundError(
        f"LID_IMAGE not found: {LID_IMAGE!r} (looked in: {', '.join(candidates)})")


def _trace_raster_to_svg(path):
    """Trace a PNG/JPG into a temporary black-on-white SVG (even-odd fill) and
    return its path. Uses Pillow to read + threshold, potracer to vectorise."""
    import os, tempfile
    try:
        from PIL import Image
        import numpy as np
        import potrace
    except ImportError as e:
        if getattr(sys, "frozen", False):
            hint = ("This copy of EZPy2STL was built without image tracing. "
                    "Rebuild/update the app (v0.5.1 or later), or use an SVG.")
        else:
            hint = ("Install with: pip install pillow potracer  "
                    "-- or use an SVG instead.")
        raise ImportError(f"Tracing PNG/JPG needs 'pillow' and 'potracer' ({e}). {hint}") from e
    img = Image.open(path)
    img.load()
    rgba = img.convert("RGBA")
    rgba.thumbnail((600, 600))                       # plenty of detail, fast
    arr = np.asarray(rgba, dtype=float)
    # flatten onto white, so transparent areas read as background
    alpha = arr[..., 3:4] / 255.0
    rgb = arr[..., :3] * alpha + 255.0 * (1 - alpha)
    grey = rgb @ np.array([0.299, 0.587, 0.114])
    art = (grey < IMAGE_THRESHOLD) if IMAGE_DARK_IS_ART else (
        (grey >= IMAGE_THRESHOLD) & (alpha[..., 0] > 0.5))
    if art.sum() == 0 or art.all():
        raise ValueError(
            "Tracing found no usable shape (image is all one tone). Adjust "
            "IMAGE_THRESHOLD or flip IMAGE_DARK_IS_ART.")
    # pad by 1px so art touching the edge still forms closed outlines
    art = np.pad(art, 1)
    h, w = art.shape
    plist = potrace.Bitmap(~art).trace(turdsize=8, alphamax=1.0, opttolerance=0.4)
    parts = []
    for curve in plist:
        sp = curve.start_point
        d = [f"M{sp.x:.2f} {sp.y:.2f}"]
        for seg in curve.segments:
            if seg.is_corner:
                d.append(f"L{seg.c.x:.2f} {seg.c.y:.2f}L{seg.end_point.x:.2f} {seg.end_point.y:.2f}")
            else:
                d.append(f"C{seg.c1.x:.2f} {seg.c1.y:.2f} {seg.c2.x:.2f} {seg.c2.y:.2f} "
                         f"{seg.end_point.x:.2f} {seg.end_point.y:.2f}")
        parts.append("".join(d) + "Z")
    fd, out = tempfile.mkstemp(suffix=".svg", prefix="lid_trace_")
    with os.fdopen(fd, "w") as fh:
        fh.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
                 f'width="{w}" height="{h}"><path fill-rule="evenodd" d="{" ".join(parts)}"/></svg>')
    return out


_IMAGE_FACES = None      # cache: the image is loaded/traced once per run, not per call


def _load_image_faces():
    """Import the image (SVG, or PNG/JPG traced to SVG first), fit it to the
    lid (times IMAGE_SCALE %), rotated by IMAGE_ROTATION and centred on the
    origin. Returns a list of Faces in XY. Cached: building the lid asks for
    the image twice (to size the nameplate, then to engrave), and tracing a
    PNG is the slow part."""
    global _IMAGE_FACES
    if _IMAGE_FACES is None:
        _IMAGE_FACES = _build_image_faces()
    return _IMAGE_FACES


def _build_image_faces():
    import os
    path = _find_image_path()
    ext = path.lower().rsplit(".", 1)[-1]
    traced_tmp = None
    if ext in ("png", "jpg", "jpeg"):
        path = traced_tmp = _trace_raster_to_svg(path)
    elif ext != "svg":
        raise ValueError("LID_IMAGE must be .svg, .png, .jpg or .jpeg")
    try:
        shapes = b.import_svg(path)
    finally:
        if traced_tmp:                       # don't leave temp SVGs behind
            try:
                os.remove(traced_tmp)
            except OSError:
                pass
    faces = [f for f in shapes if isinstance(f, b.Face)]
    if not faces:
        raise ValueError(
            "LID_IMAGE contains no filled shapes. If it is line art, convert "
            "strokes to paths (Inkscape: Path > Stroke to Path) and re-save.")
    # rotate first, so the fit is computed for the orientation actually used
    faces = [f.rotate(b.Axis.Z, IMAGE_ROTATION) for f in faces]
    bb = b.Compound(faces).bounding_box()
    if bb.size.X <= 0 or bb.size.Y <= 0:
        raise ValueError("LID_IMAGE has zero size")
    # Largest uniform scale that fits the lid's usable top area: the pull tab
    # end is kept clear (symmetrically, since the engraving is centred) and
    # IMAGE_MARGIN is left around the edge. One factor for X and Y, so the
    # picture's proportions never change.
    avail_x = SLOT_LENGTH - 2 * GRIP_TAB - 2 * IMAGE_MARGIN
    avail_y = TOTAL_WIDTH - 2 * IMAGE_MARGIN
    if avail_x <= 0 or avail_y <= 0:
        raise ValueError("IMAGE_MARGIN is too large for this lid")
    k = min(avail_x / bb.size.X, avail_y / bb.size.Y) * (IMAGE_SCALE / 100.0)
    faces = [f.scale(k) for f in faces]
    # re-measure and centre on the origin (a Shape scales about its own
    # origin, so centring before scaling would drift).
    ctr = b.Compound(faces).bounding_box().center()
    return [f.moved(b.Location((-ctr.X, -ctr.Y, 0))) for f in faces]


def _image_sketch(plane):
    faces = _load_image_faces()
    with b.BuildSketch(plane) as sketch:
        if IMAGE_INVERT:
            comp = b.Compound(faces)
            bb = comp.bounding_box()
            with b.Locations((bb.center().X, bb.center().Y)):
                b.Rectangle(bb.size.X + 2, bb.size.Y + 2)
            for f in faces:
                b.insert(f, mode=b.Mode.SUBTRACT)
        else:
            for f in faces:
                b.insert(f)
    return sketch.sketch


def has_lid_art():
    """True when the chosen LID_ART mode actually has something to engrave."""
    if LID_ART == "image":
        return True                      # LID_IMAGE presence is validated above
    if LID_ART == "text":
        return bool(LID_TEXT.strip())
    return False


def make_text_sketch(plane):
    """The engraving for the chosen LID_ART mode: the image, or the name."""
    if LID_ART == "image":
        return _image_sketch(plane)
    with b.BuildSketch(plane) as sketch:
        b.Text(LID_TEXT, font_size=TEXT_SIZE,
               font=FONT, font_style=b.FontStyle.BOLD, rotation=TEXT_ROTATION)
    return sketch.sketch


def nameplate_size():
    """Width/height of the solid patch to reserve for the engraving (text or
    image). Measured from the SAME sketch that gets engraved, so the patch
    always matches the real footprint, including rotation."""
    bb = make_text_sketch(b.Plane.XY).bounding_box()
    return (bb.size.X + 2 * NAMEPLATE_MARGIN,
            bb.size.Y + 2 * NAMEPLATE_MARGIN)


def make_slider(clearance=0.0):

    with b.BuildPart() as lid:

        with b.Locations((-0.5 * WALL_THICKNESS,
                          0,
                          SLOT_HEIGHT / 2 + 0.5 * WALL_THICKNESS)):
            b.Box(SLOT_LENGTH + WALL_THICKNESS,
                  TOTAL_WIDTH + 2 * LID_ENGAGE,
                  WALL_THICKNESS)

        b.chamfer(lid.edges().filter_by(b.Axis.X).sort_by(b.Axis.Z)[-2:],
                  angle=45,
                  length=WALL_THICKNESS / 4)

        b.chamfer(lid.edges().filter_by(b.Axis.Y).sort_by(b.Axis.X).sort_by(b.Axis.Z, reverse=True)[0],
                  angle=30,
                  length=WALL_THICKNESS / 2)

        if clearance > 0:
            b.offset(amount=clearance)

    return lid


with b.BuildPart(b.Plane.XY) as cardbox:

    # Outer shell. LIP_WALL_EXTRA thickens only the 3 lid-lip walls (both long
    # sides + the closed end); the open/grip end stays put. Shifting the box by
    # +LIP/2 in X keeps the open end and the centered card cavities in place.
    with b.Locations((LIP_WALL_EXTRA / 2, 0, 0)):
        b.Box(SLOT_LENGTH + 2 * WALL_THICKNESS + LIP_WALL_EXTRA,
              TOTAL_WIDTH + 2 * WALL_THICKNESS + 2 * LIP_WALL_EXTRA,
              SLOT_HEIGHT + 2 * WALL_THICKNESS)

    outer_edges_y = cardbox.edges().filter_by(b.Axis.Y)
    outer_edges_y += cardbox.edges().filter_by(b.Axis.X).sort_by(b.Axis.Z)[:2]

    # floor hex holes: project from a plane centered on the cavities (not on the
    # now-offset outer top face), so the holes stay aligned with the card slots.
    # Built per-deck (see make_multideck_hex_sketch) so the divider's base
    # stays solid and structurally connected to the floor.
    if HEX_PATTERN:
        floor_hex = make_multideck_hex_sketch(b.Plane.XY.offset(SLOT_HEIGHT / 2 + WALL_THICKNESS))

    # card cavities -- one per deck, each leaving a FULL WALL_THICKNESS floor
    # beneath it, and leaving the divider solid between adjacent decks.
    for yc in DECK_Y:
        with b.Locations((0, yc, 0)):
            b.Box(SLOT_LENGTH, SLOT_WIDTH, SLOT_HEIGHT, mode=b.Mode.SUBTRACT)

    # open the top for the lid mouth -- ONE continuous full-width cut (not
    # per-deck). This is what lets a single wide lid slide over the divider;
    # see the divider note near the top of the file for why.
    with b.Locations((0, 0, MOUTH_Z)):
        b.Box(SLOT_LENGTH, TOTAL_WIDTH, MOUTH_H, mode=b.Mode.SUBTRACT)

    b.chamfer(outer_edges_y,
              length=0.5 * WALL_THICKNESS, angle=30)

    # Grip scoop(s) -- see the GRIP_Z / GRIP_Y_POSITIONS note above. Radius
    # (8mm) is much larger than WALL_THICKNESS or DIVIDER_THICKNESS (3mm),
    # so each sphere fully punches through whichever wall it's centered on;
    # at Y=0 that's the front wall (the main thumb hole), at any divider's Y
    # it's that divider's leading edge.
    for gy in GRIP_Y_POSITIONS:
        with b.Locations((-SLOT_LENGTH / 2, gy, GRIP_Z)):
            b.Sphere(GRIP_HOLE, mode=b.Mode.SUBTRACT)

    # The sphere doesn't just cut one circle -- everywhere its surface pokes
    # through a flat face it leaves a circular curve: the front wall's outer
    # face (the main thumb-hole rim), but ALSO each divider's own side faces
    # (where the divider's solid material meets the neighboring deck's open
    # cavity). Only filleting the front rim leaves those divider-side curves
    # sharp, so instead of filtering by position (which only catches edges
    # centered at a grip Y), every circular edge is checked against every
    # grip sphere by testing whether an actual point on the curve sits at
    # distance GRIP_HOLE from that sphere's center -- true for any curve
    # that's genuinely part of that sphere's surface, regardless of which
    # face it came from.
    grip_sphere_centers = [(-SLOT_LENGTH / 2, gy, GRIP_Z) for gy in GRIP_Y_POSITIONS]

    def _on_grip_sphere(edge):
        p = edge.position_at(0.0)
        for cx, cy, cz in grip_sphere_centers:
            d = ((p.X - cx) ** 2 + (p.Y - cy) ** 2 + (p.Z - cz) ** 2) ** 0.5
            if abs(d - GRIP_HOLE) < 0.05:
                return True
        return False

    grip_rims = [e for e in cardbox.edges().filter_by(b.GeomType.CIRCLE) if _on_grip_sphere(e)]
    if grip_rims:
        b.fillet(grip_rims, radius=WALL_THICKNESS / 4)

    b.insert(make_slider(SLIDER_CLEARANCE).part, mode=b.Mode.SUBTRACT)

    # honeycomb openings punched down through the floor (like the original)
    if HEX_PATTERN:
        b.insert(floor_hex)
        b.extrude(amount=-(SLOT_HEIGHT + 2 * WALL_THICKNESS), mode=b.Mode.SUBTRACT)


def build_lid(engrave):
    """Build one lid. engrave=False -> full pattern / blank (no name).
    engrave=True -> reserve a nameplate and engrave the LID_ART choice (name or image).
    The lid is a single piece spanning the full TOTAL_WIDTH -- it covers
    every deck in one slide, there's no per-deck lid option here."""
    with make_slider() as slider:

        top_face_plane = b.Plane(slider.faces().sort_by(b.Axis.Z)[-1])
        # Same centre as the box floor (the middle of the card cavities), so
        # the lid's honeycomb lines up with the floor's and the engraving is
        # centred on the box -- not on the lid slab, whose centre sits
        # ~0.85 mm toward the pull tab.
        top_plane = b.Plane(origin=(0, 0, top_face_plane.origin.Z),
                            x_dir=top_face_plane.x_dir, z_dir=top_face_plane.z_dir)

        # only the engraved lid reserves a solid nameplate (sized to the text)
        art_on = engrave and has_lid_art()
        solid_art = art_on and HEX_PATTERN and LID_ART_STYLE == "solid_in_hex"
        hug = art_on and not solid_art and HEX_PATTERN and PLATE_SHAPE == "hug"
        plate = nameplate_size() if (art_on and not solid_art and not hug) else None
        art_faces = (solid_art_faces() if solid_art else
                     solid_art_faces(NAMEPLATE_MARGIN) if hug else None)

        # honeycomb openings through the lid (skipping the nameplate area and the
        # back wall). One unbroken grid -- the lid has no divider of its own.
        if HEX_PATTERN:
            b.insert(make_multideck_hex_sketch(top_plane, exclude_wh=plate,
                                              back_margin=HEX_BACK_MARGIN,
                                              keep_dividers=False,
                                              art_faces=art_faces))
            b.extrude(amount=-WALL_THICKNESS, mode=b.Mode.SUBTRACT)

        # engrave the name into the centered nameplate (centered across the
        # FULL lid width -- one name for the whole box, may straddle the
        # divider if NUM_DECKS > 1)
        if art_on and not solid_art:
            b.insert(make_text_sketch(top_plane))
            depth = (min(IMAGE_DEPTH, WALL_THICKNESS - 0.4) if LID_ART == "image"
                     else TEXT_DEPTH)
            b.extrude(amount=-depth, mode=b.Mode.SUBTRACT)

        # slider pull tab + locking bump on the open end -- spans the full
        # width so one push moves the whole lid regardless of deck count
        with b.Locations((-SLOT_LENGTH / 2 + 0.5 * WALL_THICKNESS, 0,
                          SLOT_HEIGHT / 2 + 0.5 * WALL_THICKNESS)):
            b.Box(GRIP_TAB, TOTAL_WIDTH,
                  WALL_THICKNESS, mode=b.Mode.ADD)
            if LOCK_BUMP_HEIGHT > 0:
                # Circular-segment bump: chord LOCK_BUMP_WIDTH on the lid's
                # underside, LOCK_BUMP_HEIGHT deep. Its circle's centre sits
                # (R - height) above the underside, so only the lower arc
                # shows below the lid; the rest is hidden inside the lid.
                r = (LOCK_BUMP_WIDTH ** 2 / 4 + LOCK_BUMP_HEIGHT ** 2) / (2 * LOCK_BUMP_HEIGHT)
                centre_above_underside = r - LOCK_BUMP_HEIGHT
                with b.Locations((0, 0, centre_above_underside - 0.5 * WALL_THICKNESS)):
                    b.Cylinder(r, TOTAL_WIDTH,
                               180, align=(b.Align.CENTER, b.Align.MIN, b.Align.CENTER),
                               mode=b.Mode.ADD, rotation=(-90, 0, 0))

    return slider.part


# NOTE: the output filenames below are fixed, so re-running with a different
# NUM_CARDS, NUM_DECKS, or LID_TEXT OVERWRITES the previous STLs. If you make
# lids for several people, either move/rename the files between runs, or
# auto-name the named lid by the engraved word so they never collide -- e.g.
# replace the "CardboxLid_named.stl" filename with:
#     f"CardboxLid_{LID_TEXT.strip().replace(' ', '_')}.stl"
# which would write CardboxLid_Bobbie.stl, CardboxLid_Galit.stl, etc.

b.export_stl(cardbox.part, "CardboxUSPoker_flat.stl")

# Lid: ONE file. With a name or image chosen (LID_ART), only the engraved lid
# is made; the plain lid is made only when there's nothing to engrave.
if has_lid_art():
    b.export_stl(build_lid(engrave=True).rotate(b.Axis.X, 180),
                 "CardboxLid_named.stl")
else:
    b.export_stl(build_lid(engrave=False).rotate(b.Axis.X, 180),
                 "CardboxLid_blank.stl")
