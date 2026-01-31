# merge_svg_with_contain() - Corrected Implementation

This is the authoritative pseudocode for scaling and merging an imported SVG (svg2) into a target viewBox (svg1's dimensions).

## Purpose
Transform svg2 to fit into svg1's viewBox by wrapping svg2's content in a group with a matrix transform, then updating svg2's dimensions to match svg1.

## Key Concepts
- **svg1**: First frame SVG (defines target viewBox/dimensions)
- **svg2**: Imported SVG (backdrop, frame, overlay, etc.) to be scaled
- **Uniform scale**: Preserve aspect ratio by using `min(scaleX, scaleY)`
- **In-place modification**: Modify svg2 itself, return svg2 (not svg1)
- **Step 8**: Set svg2's width/height/viewBox to match target AFTER wrapping

## Pseudocode

```python
# INPUTS
# svg1_root: root <svg> element of main SVG (first frame) - used ONLY for target dimensions
# svg2_root: root <svg> element of imported SVG (backdrop) - MODIFIED IN-PLACE
# align_mode: string, either "top-left" or "center"

# RETURNS
# svg2_root: The MODIFIED svg2_root with wrapped content and updated dimensions


# helper: strip trailing unit and keep only numeric part
def parse_length_strip_units(value_str):
    if value_str is None:
        return None

    value_str = value_str.strip()
    if value_str == "":
        return None

    i = 0
    while i < len(value_str) and (value_str[i].isdigit() or value_str[i] in "+-."):
        i += 1

    number_part = value_str[:i]
    # unit_part = value_str[i:].strip()  # ignored on purpose

    return float(number_part)


# helper: get viewBox as (x, y, w, h), synthesizing from width/height if missing
def get_viewbox(svg_root):
    vb_str = svg_root.getAttribute("viewBox")  # None or "" if missing

    if vb_str is not None and vb_str.strip() != "":
        x, y, w, h = map(float, vb_str.split())
        return x, y, w, h

    # no viewBox: synthesize from width/height
    width_str  = svg_root.getAttribute("width")
    height_str = svg_root.getAttribute("height")

    w = parse_length_strip_units(width_str)   # may be None
    h = parse_length_strip_units(height_str)

    if w is None or h is None:
        raise Exception("Cannot determine viewBox: missing both viewBox and usable width/height")

    x = 0.0
    y = 0.0
    return x, y, w, h


def merge_svg_with_contain(svg1_root, svg2_root, align_mode="center"):
    """
    Transform svg2 to fit into svg1's viewBox.
    
    CRITICAL: Modifies svg2_root IN-PLACE, returns svg2_root (NOT svg1)
    """
    
    # STEP 1: read / synthesize viewBoxes
    x1, y1, w1, h1 = get_viewbox(svg1_root)  # TARGET dimensions (first frame)
    x2, y2, w2, h2 = get_viewbox(svg2_root)  # SOURCE dimensions (backdrop)

    # STEP 2: compute uniform contain scale factor
    sx = w1 / w2
    sy = h1 / h2
    s  = min(sx, sy)  # Preserve aspect ratio

    # STEP 3: compute translation based on align_mode
    if align_mode == "top-left":
        # align top-left corners
        tx = x1 - s * x2
        ty = y1 - s * y2

    elif align_mode == "center":
        # align centers
        c1x = x1 + w1 / 2.0
        c1y = y1 + h1 / 2.0
        c2x = x2 + w2 / 2.0
        c2y = y2 + h2 / 2.0

        tx = c1x - s * c2x
        ty = c1y - s * c2y

    else:
        raise Exception("Unknown align_mode, use 'top-left' or 'center'")

    # STEP 4: build transform string for SVG (matrix(a b c d e f))
    transform_str = f"matrix({s} 0 0 {s} {tx} {ty})"

    # STEP 5: create wrapper group in svg2 (NOT svg1!)
    wrapper_g = svg2_root.ownerDocument.createElement("g")
    wrapper_g.setAttribute("transform", transform_str)

    # STEP 6: move (NOT clone) children of svg2 into wrapper_g
    children_to_move = []
    for child in svg2_root.childNodes:
        if child.nodeType == ELEMENT_NODE:
            # Skip metadata, title, desc (keep defs separate if needed)
            if child.tagName not in ["metadata", "title", "desc"]:
                children_to_move.append(child)
    
    for child in children_to_move:
        svg2_root.removeChild(child)
        wrapper_g.appendChild(child)

    # STEP 7: append wrapper_g to svg2_root (NOT svg1!)
    svg2_root.appendChild(wrapper_g)

    # STEP 8: Set svg2_root's dimensions and viewBox to match target (svg1)
    # CRITICAL: This step was missing and caused confusion!
    # Now svg2 has scaled content AND target dimensions
    svg2_root.setAttribute("width", f"{w1}px")
    svg2_root.setAttribute("height", f"{h1}px")
    svg2_root.setAttribute("viewBox", f"{x1} {y1} {w1} {h1}")

    # RETURN svg2 (the modified imported SVG)
    return svg2_root
```

## Result Structure

After calling `merge_svg_with_contain(first_frame_svg, backdrop_svg)`:

**backdrop_svg now contains:**
```xml
<svg width="200px" height="200px" viewBox="0 0 200 200">
  <g transform="matrix(0.5 0 0 0.5 0 25)">
    <!-- All original backdrop content here -->
    <rect .../>
    <circle .../>
    <text .../>
  </g>
</svg>
```

The backdrop content is:
1. **Wrapped** in a group with matrix transform
2. **Scaled and positioned** to fit the target viewBox
3. **Ready to be copied** into STAGE_BACKGROUND as-is

## Common Mistakes to Avoid

1. ❌ **Returning svg1** - WRONG! Return svg2 (the modified backdrop)
2. ❌ **Appending to svg1** - WRONG! Modify svg2 in-place
3. ❌ **Cloning children** - WRONG! Move them (removeChild + appendChild)
4. ❌ **Forgetting Step 8** - CRITICAL! Must set svg2's dimensions to match target
5. ❌ **Skipping defs** - Be careful! May need to handle defs separately

## Usage Example

```python
# Load first frame and backdrop
first_frame_doc = load_svg("frame00001.svg")
backdrop_doc = load_svg("backdrop.svg")

# Get root elements
first_frame_root = first_frame_doc.documentElement
backdrop_root = backdrop_doc.documentElement

# Transform backdrop to fit first frame's viewBox
merge_svg_with_contain(first_frame_root, backdrop_root, align_mode="center")

# Now backdrop_root has:
# - Content wrapped in transform group
# - Dimensions matching first frame
# - Ready to copy to STAGE_BACKGROUND

# Copy backdrop group to STAGE_BACKGROUND
stage_background = output_doc.getElementById("STAGE_BACKGROUND")
for child in backdrop_root.childNodes:
    if child.nodeType == ELEMENT_NODE and child.tagName == "g":
        imported = output_doc.importNode(child, deep=True)
        imported.setAttribute("id", "BACKDROP_CONTENT")
        stage_background.appendChild(imported)
        break
```

## Test Cases

| Source | Target | Expected Transform | Notes |
|--------|--------|-------------------|-------|
| 500x500 | 200x200 | `matrix(0.4 0 0 0.4 0 0)` | Scale down uniformly |
| 150x150 | 200x200 | `matrix(1.333 0 0 1.333 0 0)` | Scale UP uniformly |
| 400x200 | 200x200 | `matrix(0.5 0 0 0.5 0 50)` | Scale + center vertically |
| 300x300 | 200x200 | `matrix(0.667 0 0 0.667 0 0)` | Scale down uniformly |

