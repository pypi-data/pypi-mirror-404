# svg2fbf Test Suite

Comprehensive test suite for svg2fbf, including both unit tests and end-to-end frame comparison tests.

> 📖 **For detailed architecture, procedures, and troubleshooting**, see [CLAUDE.md](CLAUDE.md)

## Test System Overview

This test suite consists of **two completely separate testing systems**:

### 1. Unit Tests
- **Purpose**: Test individual functions and components in isolation
- **Tool**: pytest
- **Output**: `tests/logs/`
- **Characteristics**:
  - Fast execution
  - No frame-by-frame comparisons
  - Focus on code logic, error handling, edge cases
  - Run with: `uv run pytest tests/`

### 2. E2E Test Sessions (Frame Comparison Tests)
- **Purpose**: Validate that svg2fbf produces pixel-perfect output through full pipeline testing
- **Tool**: `testrunner.py` (standalone test runner)
- **Output**: `tests/sessions/` and `tests/results/`
- **Characteristics**:
  - Full pipeline: SVG → FBF → Frame capture → Pixel comparison
  - Slower execution (rendering involved)
  - Validates end-to-end correctness
  - Run with: `uv run python testrunner.py`

### How E2E Test Sessions Work

E2E test sessions validate that svg2fbf produces bit-identical output by:

1. **Rendering input SVG frames to PNG** (ground truth)
2. **Generating FBF animation** with svg2fbf
3. **Capturing animation frames as PNG** from the .fbf.svg file
4. **Comparing pixel-by-pixel** (fail-fast on first difference)

## ⚠️ CRITICAL WARNING: Test-Generated FBF Files Are NOT Valid for Production

**DO NOT USE FBF FILES FROM TEST SESSIONS FOR PRODUCTION OR AS EXAMPLES!**

When using the `testrunner.py` script for E2E test sessions, the generated FBF.SVG files are **NOT suitable for production use** for the following reasons:

### 1. Missing Metadata
Without a proper YAML configuration file, `testrunner.py` cannot generate FBF files with complete metadata:
- ❌ No title, creators, or description
- ❌ No keywords, language, or rights information
- ❌ Missing RDF/XML metadata required for **FBF.SVG Full Conformance**
- ❌ Violates the FBF.SVG specification metadata requirements

### 2. E2E Test-Specific Generation Settings
E2E test session FBF files use specialized settings optimized for **frame comparison testing only**:
- **1 FPS only** - For reliable Puppeteer frame capture timing
- **Auto-start** - `begin="0s"` instead of `begin="click"` (no interactivity)
- **Play once** - `repeatCount="1"` instead of `"indefinite"` (no looping)
- **No user interaction** - Testing requires deterministic, non-interactive playback
- **Minimal precision** - May use lower coordinate precision for faster generation

### 3. For Production Use
**Always use `svg2fbf.py` directly** with:
- ✅ A proper YAML configuration file (recommended)
- ✅ Complete metadata via CLI parameters
- ✅ Appropriate animation settings (FPS, loop type, interactivity)
- ✅ Production-grade precision settings

### 4. Exception: Using YAML Files with E2E Test Sessions
You **CAN** pass a YAML generation file to `testrunner.py` for E2E test sessions using the unified syntax:
```bash
testrunner.py --yamlfile nameoftheyamlfile.yml -- <path1> [path2] [path3] ...
```

The unified `--` separator accepts mixed inputs (folders and/or individual SVG files). Examples:
```bash
# Folder mode
testrunner.py --yamlfile config.yml -- /path/to/folder

# File list mode
testrunner.py --yamlfile config.yml -- frame1.svg frame2.svg frame3.svg

# Mixed inputs
testrunner.py --yamlfile config.yml -- /path/to/folder extra_file.svg
```

**However**, this is **only for special E2E test sessions** that need to:
- Test the ability of svg2fbf to generate valid FBF.SVG files with valid metadata
- Test interactivity features with Playwright test scripts
- Validate metadata conformance (Full Conformance vs Basic Conformance)

**Normal frame comparison E2E test sessions do NOT require a YAML file to be passed to testrunner.py.**

### Where E2E Test Session FBF Files Are Stored
E2E test session FBF files are saved in:
- `tests/sessions/test_session_XXX_Nframes/` - E2E test session storage
- `tests/results/session_XXX_Nframes/YYYYMMDD_HHMMSS/fbf_output/` - E2E test run outputs

**These directories are for E2E testing only. Never distribute these files or use them as examples.**

### Example of Correct Production Generation
```bash
# Create proper YAML config
cat > animation.yaml <<EOF
metadata:
  title: "My Animation"
  creators: "Your Name"
  description: "Proper production animation"
  keywords: "animation, production"
  language: "en"
  rights: "CC BY-SA 4.0"

generation_parameters:
  input_folder: "frames/"
  output_path: "output/"
  filename: "animation.fbf.svg"
  speed: 24.0
  animation_type: "loop"
  play_on_click: true
  digits: 28
  cdigits: 28
EOF

# Generate production-ready FBF
uv run python svg2fbf.py animation.yaml
```

---

## E2E Test Strategy

E2E test sessions use the following approach:

- **Random SVG selection** from validated pool
- **Multiple batch sizes** (2, 5, 10, 50 frames)
- **Fail-fast**: Stop at first frame difference
- **Detailed error reporting** with frame metadata
- **SVG validation** to prevent test failures from invalid inputs

## Requirements

### For Unit Tests
Installed automatically via uv:
- pytest>=8.4.2
- pytest-asyncio>=0.23.0

### For E2E Test Sessions

#### Python Dependencies
Installed automatically via uv:
- pytest>=8.4.2
- pytest-asyncio>=0.23.0
- pillow>=10.0.0
- requests>=2.31.0
- numpy>=2.2.6 (already installed)
- lxml>=6.0.2 (already installed)

#### Node.js Dependencies

- **Node.js** and **npm** must be installed
- **Puppeteer** 24.15.0+ (installed automatically on first E2E test run)

## Installation

1. **Install Python dependencies:**
   ```bash
   uv sync
   ```

2. **For E2E test sessions**: Node.js will be verified and Puppeteer installed automatically on first E2E test run.

## Running Tests

### Unit Tests

Run all unit tests:
```bash
uv run pytest tests/
```

Run with verbose output:
```bash
uv run pytest tests/ -v
```

### E2E Test Sessions

E2E test sessions are managed by `testrunner.py`, not pytest:

```bash
# Run E2E test session on a folder of SVG frames
uv run python testrunner.py /path/to/svg_frames

# Rerun existing E2E test session
uv run python testrunner.py --use-session 100
```

See the "Standalone Test Runner" section below for complete E2E test session documentation.

## E2E Test Session Configuration Options

These configuration options apply only to E2E test sessions, not unit tests:

### Keep temporary files for inspection:
```bash
uv run pytest tests/ --keep-temp
```
Test artifacts saved in `/tmp/pytest-of-<user>/...`

### Generate visual diff images for failures:
```bash
uv run pytest tests/ --render-diffs
```
Creates `diff_frame_XXXX.png` highlighting pixel differences in red.

### Generate HTML comparison report:
```bash
uv run pytest tests/ --html-report
```
**Features:**
- Side-by-side comparison of all frames (input vs output)
- Grayscale diff maps showing difference intensity
- Percentage difference for each frame
- Summary statistics (passed/failed frames, average difference)
- Self-contained HTML with embedded images (no external files needed)
- Click images to open in full size
- **Note:** Disables fail-fast behavior to collect all frame comparisons

**Example:**
```bash
uv run pytest tests/ -k "test_frame_rendering_accuracy[2]" --html-report
```

Report saved to: `<tmp_path>/comparison_report_<N>frames.html`

### Maximum frames to test:
```bash
uv run pytest tests/ --max-frames=100
```
Default: 50 frames max

## Standalone Test Runner (E2E Test Sessions)

The `testrunner.py` script manages E2E test sessions completely independently from pytest unit tests.

### Creating E2E Test Sessions

The test runner provides a unified approach for creating E2E test sessions from mixed inputs:

**Create E2E Test Session (unified input handling)**
```bash
uv run python testrunner.py create -- <path1> [path2] [path3] ...
```

**Accepts mixed inputs:**
- Folders: Recursively copies all contents (SVG frames + dependencies)
- Individual files: Copies specified files + extracts dependencies
- Mixed: Any combination of folders and files

**Features:**
- Auto-detects input type using Path.is_dir() and Path.is_file()
- **Deterministic auto-numbering** using candidates ladder system:
  - Files always get the same numbers regardless of input order
  - Preserves existing numbering patterns in filenames
  - Priority-based matching: `_NNNNN.svg` > `-NNNNN.svg` > `.NNNNN.svg` > embedded numbers
- Validates viewBox in all SVG files (auto-calculated if missing)
- Extracts and copies ALL dependencies (fonts, images, external files)
- Preserves relative paths within input_frames/
- Moves defective SVGs to `examples_dev/defective_svg/`
- Moves obsolete FBF files to `examples_dev/obsolete_fbf_format/`

**What happens:**
- Copies all inputs to input_frames/ directory
- For individual SVG files: extracts and copies dependencies
- Validates and repairs viewBox attributes (union bbox for animations)
- Auto-numbers frames sequentially if needed
- Creates new E2E test session ID: `test_session_XXX_Nframes`
- Reports how to run the E2E test session

**Examples:**
```bash
# Single folder
uv run python testrunner.py create -- /path/to/folder

# Multiple individual files
uv run python testrunner.py create -- file1.svg file2.svg file3.svg

# Mixed inputs (folders + files)
uv run python testrunner.py create -- /path/to/folder1 /path/to/folder2 extra_file.svg

# With auto-numbering
uv run python testrunner.py create -- /path/to/folder --autonumber

# Random selection from examples (excludes .fbf.svg files)
uv run python testrunner.py create --random 15 -- examples/
just random-test 15  # Convenient alias

# Random selection from W3C SVG 1.1 Test Suite (root level only, no recursion)
uv run python testrunner.py create --random 50 -- "FBF.SVG/SVG 1.1 W3C Test Suit/w3c_50frames/"
just test-random-w3c 50  # Convenient alias
```

Dependency extraction:
- Parses each SVG for file references (images, fonts, CSS @import)
- Copies dependencies preserving directory structure
- Example: `fonts/tahoma.woff` → `input_frames/fonts/tahoma.woff`

### Running E2E Test Sessions

Use `testrunner.py` to run E2E test sessions (completely separate from pytest unit tests):

```bash
# Run E2E test session on a folder of SVG frames (creates new session or reuses existing)
uv run python testrunner.py /path/to/svg_frames

# Rerun existing E2E test session using short session ID (recommended)
uv run python testrunner.py --use-session 100

# Rerun existing E2E test session using full session ID (also works)
uv run python testrunner.py --use-session test_session_100_35frames

# Override tolerance thresholds from pyproject.toml
uv run python testrunner.py /path/to/svg_frames --image-tolerance 0.01 --pixel-tolerance 0.002
```

**Features:**
- Simple command-line interface
- E2E test session-based management (1:1 correspondence between session ID and input frames)
- Support for short session IDs (e.g., `100` instead of `test_session_100_35frames`)
- **Frame count is ALWAYS determined by counting `.svg` files** (never a user choice)
- Other files (images, data files, etc.) are ignored when counting frames
- Uses tolerance thresholds from `pyproject.toml` by default
- CLI options `--image-tolerance` and `--pixel-tolerance` override defaults
- Automatically generates HTML report and opens in Safari
- Preserves results to `tests/sessions/test_session_XXX_NNframes/runs/YYYYMMDD_HHMMSS/`

**Important: Frame Count**
- The `NNframes` in `test_session_XXX_NNframes` reflects the EXACT count of `.svg` files only
- Adding/removing/reordering SVG files creates a NEW E2E test session with different ID
- Any other files in the folder (PNG images, JSON data, etc.) are IGNORED

**Tolerance Defaults** (defined in `pyproject.toml`):
- `image_tolerance`: 0.04% (percentage of pixels allowed to differ)
- `pixel_tolerance`: 0.0039 (~1/256, per-pixel RGB difference threshold)

**Example:**
```bash
# Use defaults from pyproject.toml
uv run python testrunner.py /tmp/my_animation_frames

# Use stricter tolerances for pixel-perfect validation
uv run python testrunner.py /tmp/my_animation_frames --image-tolerance 0.0 --pixel-tolerance 0.0

# Use lenient tolerances for debugging
uv run python testrunner.py /tmp/my_animation_frames --image-tolerance 0.1 --pixel-tolerance 0.01
```

## E2E Test Session Artifact Preservation

All E2E test session results are automatically preserved for debugging and replication.

### What's Preserved:
- **Input batch** - Original SVG frames (for E2E test session replication)
- **FBF file** - Generated animation (`.fbf.svg`)
- **HTML report** - Visual comparison report
- **Input frames** - Rendered PNGs from input SVGs (ground truth)
- **Output frames** - Captured PNGs from FBF animation

### Directory Structure:
```
tests/sessions/
└── test_session_100_35frames/          # E2E test session (unique input frames)
    ├── input_frames/                   # Session-level: Original SVG files
    │   ├── frame001.svg
    │   ├── frame002.svg
    │   └── ...
    ├── session_metadata.json           # Session fingerprint
    └── runs/
        └── 20251106_180416/            # Run 1 (timestamped)
            ├── input_frames_png/       # Ground truth PNGs
            │   ├── input_frame_0001.png
            │   ├── input_frame_0002.png
            │   └── ...
            ├── output_frames_png/      # FBF captured PNGs
            │   ├── frame_0001.png
            │   ├── frame_0002.png
            │   └── ...
            ├── fbf_output/
            │   └── test_animation.fbf.svg
            ├── diff_png/               # Grayscale difference maps
            │   ├── diff_gray_frame_0001.png
            │   ├── diff_gray_frame_0002.png
            │   └── ...
            └── comparison_report.html
```

### Unit Test Logs:
Unit tests output logs to `tests/logs/` (separate from E2E test session artifacts).

### Temporary Files:
E2E test execution uses `/tmp/pytest-svg2fbf/` for temporary files (auto-cleaned on reboot).

### Cleanup:
```bash
# Remove all preserved E2E test session results
rm -rf tests/sessions/

# Remove E2E test session results older than 7 days
find tests/sessions/ -type d -mtime +7 -exec rm -rf {} +

# Check disk usage
du -sh tests/sessions/
```

**Note**: `tests/sessions/` is gitignored - manual cleanup required.

## SVG Validation Cache (E2E Test Sessions)

The SVG validation cache is used by E2E test sessions to track invalid SVG files:

### View invalid SVG cache:
```bash
uv run pytest tests/ --show-invalid-cache
```

### Clear invalid SVG cache (force re-validation):
```bash
uv run pytest tests/ --clear-invalid-cache
```

### Cache file location:
```
tests/invalid_svg_example_frames.json
```

This file is tracked in git to share validation results across the team.

## Test Architecture

```
tests/
├── logs/                                # Unit test output logs
├── sessions/                            # E2E test sessions (gitignored)
│   └── test_session_XXX_Nframes/       # Individual E2E test sessions
│       ├── input_frames/               # Session SVG frames
│       └── runs/                       # Timestamped test runs
├── conftest.py                          # pytest configuration & fixtures
├── test_*.py                            # Unit test files
├── testrunner.py                        # E2E test session manager (standalone)
├── invalid_svg_example_frames.json      # cache of invalid SVGs (E2E tests)
├── utils/
│   ├── svg_validator.py                 # SVG validation (E2E tests)
│   ├── batch_generator.py               # random SVG batch generation (E2E tests)
│   ├── puppeteer_renderer.py            # Python wrapper for Puppeteer (E2E tests)
│   ├── image_comparison.py              # pixel-perfect comparison (E2E tests)
│   └── svg_extractor.py                 # SVG collection utilities (E2E tests)
├── node_scripts/
│   ├── render_svg.js                    # render single SVG to PNG (E2E tests)
│   └── render_fbf_animation.js          # capture animation frames (E2E tests)
└── fixtures/
    └── test_batches/                    # temporary test batches (gitignored)
```

## How E2E Test Sessions Work

E2E test sessions follow this pipeline:

### 1. SVG Validation

Before E2E testing, all SVGs in `examples/` are validated:

- ✅ **XML syntax** - Well-formed XML
- ✅ **Fonts** - Defined, embedded, or system fonts
- ✅ **Images** - Local files exist, remote URLs accessible
- ✅ **Browser rendering** - Renders without errors

Invalid SVGs are cached in `invalid_svg_example_frames.json` and skipped in future runs.

### 2. E2E Test Session Batch Generation

For each E2E test:
- Randomly select N validated SVGs
- Copy to temp folder with proper naming: `frame_FRAME00001.svg`, etc.
- Different combinations test different code paths

### 3. Ground Truth Rendering (E2E)

Each input SVG is rendered to PNG using Puppeteer:
- Headless Chrome for consistent rendering
- Fixed viewport (1920x1080)
- sRGB color space
- Wait for fonts and images to load

### 4. svg2fbf Execution (E2E)

Generate FBF animation:
```bash
svg2fbf \
  --input_folder=<batch> \
  --output_path=<output> \
  --filename=test.fbf.svg \
  --speed=10 \
  --animation_type=once \  # CRITICAL: Must be "once" not "loop"
  --digits=5 \
  --cdigits=5
```

### 5. Animation Frame Capture (E2E)

Puppeteer captures each frame from FBF animation:
- Load .fbf.svg in headless Chrome
- SMIL animation auto-starts (no click needed)
- Capture at exact frame times (mid-frame to avoid edge artifacts)
- Save as PNG sequence

### 6. Pixel-Perfect Comparison (E2E)

Compare input PNG vs output PNG:
- Every pixel RGBA value must match exactly
- Even 1-pixel difference = test failure
- Report: frame number, diff percentage, first diff location
- **Fail fast**: Stop at first difference

## E2E Test Session Output Example

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        FRAME RENDERING MISMATCH DETECTED                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Frame 3/10 FAILED pixel-perfect comparison!

📍 Frame Information:
   Input PNG:   input_frame_0003.png
   Output PNG:  frame_0003.png
   Source SVG:  examples/anime_girl/frame_003.svg

🔬 Difference Details:
   Different pixels:  1,247
   Total pixels:      2,073,600
   Difference:        0.0601%
   First diff at:     (127, 453)

⚙️  Test Configuration:
   Batch size:        10 frames
   FPS:               10.0
   Animation type:    once
   Viewport:          1920x1080

📁 File Locations:
   Input frames:      /tmp/.../input_frames/
   Output frames:     /tmp/.../output_frames/
   FBF SVG:           /tmp/.../test_animation.fbf.svg

🛑 STOPPING TEST (fail-fast on first frame difference)
```

## Common Issues

### E2E Test Session Issues

#### "No valid SVG files found"

**Cause**: No valid SVGs in `examples/` folder

**Fix**:
1. Ensure `examples/` directory exists
2. Check SVGs are valid: `pytest tests/ --show-invalid-cache`
3. Fix invalid SVGs or add more examples

#### "Puppeteer failed to render"

**Cause**: Chrome/Puppeteer not working (E2E test sessions only)

**Fix**:
1. Ensure Node.js installed: `node --version`
2. Reinstall Puppeteer: `cd tests && npm install`
3. Check Chrome can launch: Run sanity test

#### "Frame rendering mismatch"

**Cause**: svg2fbf produced different output (E2E test sessions)

**Fix**:
1. Check `--keep-temp` flag to inspect files
2. Use `--render-diffs` to see visual diff
3. Run svg2fbf manually with same inputs for debugging
4. Check if specific SVG feature not supported

#### "npm not found"

**Cause**: Node.js not installed (required for E2E test sessions)

**Fix**:
Install Node.js from https://nodejs.org/ or via package manager:
- macOS: `brew install node`
- Ubuntu: `sudo apt install nodejs npm`

## svg2fbf CLI Arguments Used in E2E Test Sessions

E2E test sessions use these fixed arguments:

| Argument | Value | Why |
|----------|-------|-----|
| `--animation_type` | `once` | REQUIRED: Other modes loop forever, can't capture finite frames |
| `--speed` | `10` | Fixed FPS for consistent timing (10 FPS = 100ms per frame) |
| `--digits` | `5` | Coordinate precision |
| `--cdigits` | `5` | Control point precision |
| `--play_on_click` | ❌ NOT USED | Auto-start simplifies testing (no click simulation) |

## Extending Tests

### Unit Tests

Add new unit test files following pytest conventions:
```python
# tests/test_myfeature.py
def test_myfeature():
    """Test description for the table output."""
    # Your test code here
    assert expected == actual
```

### E2E Test Sessions

#### Add new batch size:
```python
@pytest.mark.parametrize("frame_count", [2, 5, 10, 50, 100])  # Add 100
def test_frame_rendering_accuracy(...):
    ...
```

#### Test specific animation types:
```python
def test_loop_animation(...):
    # Modify TEST_ANIMATION_TYPE to "loop"
    # Add frame limit to prevent infinite capture
    ...
```

### Tolerance-based comparison (E2E):

The test system uses a **two-level tolerance approach**:

```python
# Pixel-level tolerance (color difference per pixel)
pixel_tolerance = 0.0039  # ~1/256 ≈ 1 RGB value difference
threshold_rgb = pixel_tolerance * 255  # Convert to 0-255 scale
diff_mask = np.any(abs_diff > threshold_rgb, axis=2)

# Image-level tolerance (percentage of pixels allowed to differ)
image_tolerance = 0.04  # 0.04% of pixels can differ
diff_percentage = (diff_pixels / total_pixels) * 100
is_identical = diff_percentage <= image_tolerance
```

Customize via CLI:
```bash
# Use custom tolerances
uv run pytest tests/ --pixel-tolerance=0.001 --image-tolerance=0.01

# See tests/CLAUDE.md for more details
```

## Performance

### Unit Tests
Typical unit test execution: < 1 second per test (depends on test complexity)

### E2E Test Sessions
Typical E2E test session times (M1 Mac, 50 frame batch):

- SVG validation: ~30s (first run only, cached after)
- Input rendering: ~20s (Puppeteer startup + 50 SVGs)
- svg2fbf execution: ~10s
- Animation capture: ~15s (50 frames at 10 FPS)
- Comparison: ~1s (fast NumPy operations)

**Total: ~76 seconds for 50-frame E2E test session**

## Contributing

When adding new tests:

1. **Follow naming convention**: `test_<descriptive_name>`
2. **Add docstrings**: Explain test purpose and strategy
3. **Use fixtures**: Reuse session-scoped fixtures
4. **Add to parametrize**: If testing variants
5. **Document edge cases**: Comment unusual test cases

## License

Apache License 2.0 (same as svg2fbf)
