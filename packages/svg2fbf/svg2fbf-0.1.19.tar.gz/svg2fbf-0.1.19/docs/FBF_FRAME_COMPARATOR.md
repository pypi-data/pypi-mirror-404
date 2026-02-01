# FBF Frame Comparator (Tool #0)

**Status**: ✅ **COMPLETED** - Fully functional

Compare two FBF.SVG animation files by rendering and comparing their frames pixel-by-pixel. This tool verifies that structural changes, optimizations, or fixes don't break the visual output of FBF animations.

## Features

✅ **Automatic Frame Detection** - Parses SMIL `animate` elements to detect frame count
✅ **Pixel-Perfect Comparison** - Uses numpy-based comparison with configurable tolerance
✅ **Visual Diff Maps** - Generates grayscale diff maps showing difference intensity
✅ **HTML Reports** - Beautiful side-by-side comparison reports
✅ **Frame-by-Frame Analysis** - Detailed metrics for each frame
✅ **Organized Results** - Saves all artifacts to `tests/results/`

## Quick Start

### Basic Comparison

```bash
uv run python compare_fbf.py <file1.fbf.svg> <file2.fbf.svg>
```

**Example:**
```bash
uv run python compare_fbf.py \
    examples/splat_button/fbf_output/splat_button.fbf.svg.bak \
    examples/splat_button/fbf_output/splat_button.fbf.svg
```

### What It Does

1. **Detects frame count** from both FBF files
2. **Renders all frames** to PNG using Puppeteer (headless Chrome)
3. **Compares pixel-by-pixel** using numpy arrays
4. **Generates diff maps** for frames that differ
5. **Creates HTML report** with side-by-side comparisons
6. **Saves results** to `tests/results/comparison_<file1>_vs_<file2>/`

## Output Structure

```
tests/results/comparison_<file1>_vs_<file2>/
├── file1_frames/              # Rendered frames from file 1
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ...
├── file2_frames/              # Rendered frames from file 2
│   ├── frame_0001.png
│   ├── frame_0002.png
│   └── ...
├── diff_images/               # Grayscale diff maps (only for different frames)
│   ├── frame_01_diff.png
│   └── ...
└── comparison_report.html     # Visual comparison report
```

## HTML Report Features

- **Summary Statistics**: Total frames, identical count, different count
- **Frame-by-Frame Comparison**: Side-by-side images with diff maps
- **Visual Pass/Fail Indicators**: Green for identical, red for different
- **Percentage Differences**: Exact pixel difference percentages
- **Clickable File Links**: Direct links to FBF files
- **Responsive Design**: Works on desktop and mobile
- **Self-Contained**: All images embedded as base64 (no external dependencies)

## Use Cases

### 1. Verify Bug Fixes Don't Break Output

```bash
# Before fix
cp output/animation.fbf.svg output/animation.fbf.svg.bak

# Apply fix to svg2fbf
# ... make changes ...

# Regenerate animation
uv run svg2fbf -i frames/ -o output/ -f animation.fbf.svg

# Compare
uv run python compare_fbf.py output/animation.fbf.svg.bak output/animation.fbf.svg
```

### 2. Regression Testing

```bash
# Store baseline
cp production/animation.fbf.svg baselines/v1.0.0.fbf.svg

# After new svg2fbf version
uv run svg2fbf -i frames/ -o output/ -f animation.fbf.svg

# Compare against baseline
uv run python compare_fbf.py baselines/v1.0.0.fbf.svg output/animation.fbf.svg
```

### 3. Parameter Changes

```bash
# Different animation speeds
uv run svg2fbf -i frames/ -o tmp/ -f slow.fbf.svg -s 12
uv run svg2fbf -i frames/ -o tmp/ -f fast.fbf.svg -s 24

# Compare frame content (should be identical despite different timing)
uv run python compare_fbf.py tmp/slow.fbf.svg tmp/fast.fbf.svg
```

## Technical Details

### Frame Detection Algorithm

Parses the FBF file to find the SMIL `<animate>` element:

```python
def detect_fbf_frame_count(fbf_path: Path) -> int:
    tree = ET.parse(fbf_path)
    root = tree.getroot()

    # Find animate element with xlink:href attribute
    for elem in root.iter():
        if elem.tag.endswith('animate') and elem.get('attributeName') == 'xlink:href':
            values = elem.get('values', '')
            frames = [v.strip() for v in values.split(';') if v.strip()]
            return len(frames)
```

### Rendering Pipeline

Uses the same infrastructure as `test_frame_rendering.py`:

1. **PuppeteerRenderer** - Launches headless Chrome via Node.js
2. **render_fbf_animation.js** - Captures frames at specific timestamps
3. **PNG Output** - Saves frames as PNG files with consistent settings

### Comparison Method

Uses `ImageComparator.compare_images_pixel_perfect()`:

```python
is_identical, diff_info = ImageComparator.compare_images_pixel_perfect(
    frame1_path,
    frame2_path,
    tolerance=0.0,          # Pixel-perfect by default
    pixel_tolerance=1/256   # Allow 1 RGB value difference
)

# diff_info contains:
# - diff_pixels: int
# - total_pixels: int
# - diff_percentage: float
# - first_diff_location: (y, x)
# - dimensions_match: bool
```

### Diff Map Generation

Creates grayscale images where:
- **Black (0)**: Pixels are identical
- **Gray (1-254)**: Difference magnitude (darker = more different)
- **White (255)**: Maximum difference

```python
ImageComparator.generate_grayscale_diff_map(
    frame1_path,
    frame2_path,
    diff_image_path
)
```

## Exit Codes

- **0**: All frames identical (success)
- **1**: Differences found or errors occurred

## Current Limitations

1. **No tolerance configuration** - Always uses pixel-perfect comparison
2. **No parallel rendering** - Renders frames sequentially
3. **No auto-open report** - Must manually open HTML file
4. **No JSON export** - Only HTML report format
5. **No CLI entry point** - Must run via `uv run python`

## Planned Improvements

See `docs/ROADMAP.md` section 1.4 for upcoming enhancements:

- [ ] Add CLI tolerance options (`--pixel-tolerance`, `--image-tolerance`)
- [ ] Add `--open` flag to auto-open HTML report in browser
- [ ] Add progress indicators for long comparisons
- [ ] Export results to JSON for automation
- [ ] Add to `pyproject.toml` as CLI entry point (`compare-fbf`)
- [ ] Support batch comparisons (multiple file pairs)
- [ ] Compare FPS/timing metadata
- [ ] Parallel frame rendering for speed
- [ ] Baseline regression detection

## Integration with Test Suite

The comparator shares infrastructure with `test_frame_rendering.py`:

**Shared Utilities:**
- `tests/utils/puppeteer_renderer.py` - Frame rendering
- `tests/utils/image_comparison.py` - Pixel comparison
- `tests/node_scripts/render_fbf_animation.js` - Puppeteer script

**Why Shared Infrastructure?**
- Consistent rendering behavior
- Same pixel comparison logic
- Unified test/comparison workflow
- Code reuse and maintainability

## Example Output

```
🔍 Comparing FBF files:
   File 1 (original): splat_button.fbf.svg.bak
   File 2 (updated):  splat_button.fbf.svg

📁 Output directory: tests/results/comparison_splat_button.svg_vs_splat_button

📊 Detected 11 frames in File 1
📊 Detected 11 frames in File 2

🎬 Rendering frames from File 1 (original)...
   ✓ Rendered 11 frames

🎬 Rendering frames from File 2 (updated)...
   ✓ Rendered 11 frames

📊 Comparing 11 frames...

   Frame 01: ✓ IDENTICAL
   Frame 02: ✓ IDENTICAL
   Frame 03: ✓ IDENTICAL
   Frame 04: ✓ IDENTICAL
   Frame 05: ✓ IDENTICAL
   Frame 06: ✓ IDENTICAL
   Frame 07: ✓ IDENTICAL
   Frame 08: ✓ IDENTICAL
   Frame 09: ✓ IDENTICAL
   Frame 10: ✓ IDENTICAL
   Frame 11: ✓ IDENTICAL

📄 Generating comparison report...
   ✓ Report saved to: tests/results/comparison_splat_button.svg_vs_splat_button/comparison_report.html

✅ SUCCESS: All frames are identical!
   The FBF files produce the same visual output.
```

## Related Tools

- **svg2fbf** - Generates FBF animations from SVG frames
- **test_frame_rendering.py** - Tests svg2fbf output accuracy
- **testrunner.py** - Session-based testing for svg2fbf

## License

Apache License 2.0 (same as svg2fbf)
