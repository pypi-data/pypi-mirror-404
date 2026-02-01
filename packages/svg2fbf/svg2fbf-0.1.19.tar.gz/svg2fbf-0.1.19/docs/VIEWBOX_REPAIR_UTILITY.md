# SVG ViewBox Repair Utility

## Overview

The `svg-repair-viewbox` utility is included with svg2fbf to automatically calculate and add viewBox attributes to SVG files. It uses Puppeteer/headless Chrome for accurate bounding box calculation.

## Installation

**Zero configuration required!** The utility automatically installs all dependencies on first use.

```bash
# 1. Install svg2fbf
uv tool install svg2fbf

# 2. Run svg-repair-viewbox (dependencies auto-install on first use)
svg-repair-viewbox /path/to/svg/files
```

## What Gets Installed Automatically

On first use, `svg-repair-viewbox` will automatically:

1. **Detect your system** - Identifies OS (macOS, Linux, Windows) and package manager
2. **Install Node.js** - If not already present, installs using:
   - macOS: `brew install node`
   - Ubuntu/Debian: `apt install nodejs npm`
   - Fedora/RHEL: `dnf install nodejs npm`
   - Arch: `pacman -S nodejs npm`
   - Windows: `choco install nodejs` or `winget install OpenJS.NodeJS`
3. **Install Puppeteer** - Locally in the package directory via `npm install` (~170MB download includes Chromium)

## Usage

### Basic Usage

```bash
# Repair a single SVG file
svg-repair-viewbox image.svg

# Repair multiple SVG files
svg-repair-viewbox frame001.svg frame002.svg frame003.svg

# Repair all SVG files in a directory
svg-repair-viewbox /path/to/svg/directory

# Quiet mode
svg-repair-viewbox --quiet *.svg
```

### For Animation Sequences

The utility uses a **union bbox strategy** for animation frames:

1. Calculates individual bounding box for each frame
2. Computes union bbox encompassing all frames
3. Applies the SAME viewBox to ALL frames

This prevents frame-to-frame jumping in animations.

## How It Works

### Bounding Box Calculation

```
User runs: svg-repair-viewbox frames/
    ↓
Check dependencies (auto-install if missing)
    ↓
For each SVG file:
  1. Launch headless Chrome via Puppeteer
  2. Render SVG in browser
  3. Call getBBox() with {fill: true, stroke: true, markers: true}
  4. Return accurate bounds including all visual elements
    ↓
Calculate union bbox (min/max across all frames)
    ↓
Apply union viewBox to all files
```

### Why Use Puppeteer?

Calculating SVG bounding boxes accurately requires a full rendering engine because:

- **Transforms**: `<g transform="matrix(...)">` affects all descendants
- **Stroke width**: `stroke-width="5"` extends bounds beyond fill
- **Markers**: Arrow heads, end caps add to bounds
- **Filters**: Blur, shadows extend visual bounds
- **Nested SVGs**: Each has its own coordinate system
- **CSS styles**: External or inline styles affect rendering

Puppeteer's `getBBox()` handles all of this correctly by actually rendering the SVG.

## Example Output

### First Run (Auto-Install)

```bash
$ svg-repair-viewbox animation_frames/

⚙️  First-time setup: Installing required dependencies...

======================================================================
🔧 svg-repair-viewbox Automatic Dependency Setup
======================================================================

🎯 Detected package manager: brew

📦 Installing Node.js...
✅ Node.js installed successfully (v20.10.0)

📦 Installing Puppeteer (this will download ~170MB Chromium)...
✅ Puppeteer installed successfully

======================================================================
✅ All dependencies installed successfully!
======================================================================

Found 23 SVG file(s)

======================================================================
   🎬 ANIMATION SEQUENCE VIEWBOX REPAIR
======================================================================
   Files with viewBox: 0
   Files missing viewBox: 23

   📐 Calculating union bbox across 23 frames...
      Frame 01: x=  -2.04, y=  -2.05, w= 237.19, h= 452.63
      Frame 02: x=  -2.00, y=  -2.01, w= 238.13, h= 452.21
      Frame 03: x=  -2.05, y=  -2.03, w= 240.08, h= 451.29
      ...

   ✅ Union bbox: x=-2.06, y=-2.06, width=247.62, height=453.10
      This viewBox will be applied to ALL 23 frames

   🔧 Applying union viewBox to all frames...
      ✓ Frame 01: frame00001.svg
      ✓ Frame 02: frame00002.svg
      ...

   ✅ Successfully applied union viewBox to 23 frames!
======================================================================

✅ Successfully repaired 23 file(s)
```

### Subsequent Runs (Dependencies Already Installed)

```bash
$ svg-repair-viewbox animation_frames/

Found 23 SVG file(s)

======================================================================
   🎬 ANIMATION SEQUENCE VIEWBOX REPAIR
======================================================================
   Files with viewBox: 23
   Files missing viewBox: 0
   ✓ All frames have viewBox - checking consistency...
   ✅ All frames have identical viewBox: -2.06 -2.06 247.62 453.1
   No repair needed!

✅ All files already have correct viewBox attributes
```

## Troubleshooting

### Auto-Install Fails

If automatic installation fails, you can install manually:

```bash
# 1. Install Node.js
# macOS:
brew install node

# Linux:
sudo apt install nodejs npm

# Windows:
# Download from https://nodejs.org

# 2. Install Puppeteer (check error message for exact path)
cd ~/.local/share/uv/tools/svg2fbf/share/svg2fbf  # or path shown in error
npm install

# 3. Try again
svg-repair-viewbox /path/to/files
```

### Permission Errors on Linux/macOS

If auto-install fails due to permissions, the local installation should work without sudo. If you still encounter issues, try:

```bash
# Navigate to package directory (path shown in error message)
cd ~/.local/share/uv/tools/svg2fbf/share/svg2fbf
npm install
```

### Behind Corporate Firewall

Puppeteer downloads Chromium from Google servers. If blocked:

```bash
# Use alternative mirror (navigate to package directory first)
cd ~/.local/share/uv/tools/svg2fbf/share/svg2fbf
PUPPETEER_DOWNLOAD_HOST=https://registry.npmmirror.com/-/binary/chromium-browser-snapshots npm install
```

### Use System Chrome Instead

```bash
# Navigate to package directory
cd ~/.local/share/uv/tools/svg2fbf/share/svg2fbf

# Skip Chromium download and install
PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true npm install

# Point to your Chrome installation
export PUPPETEER_EXECUTABLE_PATH=/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome

# Run svg-repair-viewbox
svg-repair-viewbox /path/to/files
```

## Technical Details

### Supported Package Managers

- **macOS**: Homebrew (`brew`)
- **Debian/Ubuntu**: APT (`apt-get`)
- **Fedora/RHEL**: DNF/YUM (`dnf`, `yum`)
- **Arch Linux**: Pacman (`pacman`)
- **OpenSUSE**: Zypper (`zypper`)
- **Windows**: Chocolatey (`choco`), Winget (`winget`)

### Node.js Version Requirements

- **Minimum**: Node.js 16+
- **Recommended**: Node.js 18+ or 20+ (LTS versions)

### Puppeteer Version

- **Installed**: Latest stable version
- **Chromium**: Bundled automatically (version varies)

## API Usage (Python)

You can also use the repair utility programmatically:

```python
from pathlib import Path
from svg_viewbox_repair import repair_animation_sequence_viewbox

# Repair SVG files
svg_files = [Path("frame1.svg"), Path("frame2.svg"), Path("frame3.svg")]
repaired_count = repair_animation_sequence_viewbox(svg_files, verbose=True)

print(f"Repaired {repaired_count} files")
```

## When to Use

Use `svg-repair-viewbox` when:

- ✅ SVG files missing viewBox attributes
- ✅ Animation frames have inconsistent viewBoxes
- ✅ Converting from other formats (AI, Figma exports often lack viewBox)
- ✅ Legacy SVG files with only width/height attributes

You don't need it if:

- ❌ All SVG files already have correct, consistent viewBox
- ❌ Using svg2fbf with properly exported SVGs
- ❌ Working with single static SVGs (not animations)

## Related Documentation

- [FBF.SVG Specification](FBF_SVG_SPECIFICATION.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
- [Main README](../README.md)

## Support

For issues or questions:

- GitHub Issues: https://github.com/Emasoft/svg2fbf/issues
- Documentation: https://github.com/Emasoft/svg2fbf
