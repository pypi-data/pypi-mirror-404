# FBF Generation Cards

## Table of Contents

1. [What are FBF Generation Cards?](#what-are-fbf-generation-cards)
2. [Why Use Generation Cards?](#why-use-generation-cards)
3. [Complete YAML Schema](#complete-yaml-schema)
4. [Metadata Section](#metadata-section)
5. [Generation Parameters Section](#generation-parameters-section)
6. [Examples](#examples)
7. [Best Practices](#best-practices)
8. [Default Configuration](#default-configuration)
9. [Testing with Generation Cards](#testing-with-generation-cards)

---

## What are FBF Generation Cards?

**FBF Generation Cards** (also called **fbf-generation-cards**) are YAML configuration files that specify how to generate FBF (Frame-by-Frame) SVG animations from a sequence of SVG frames. They provide a declarative, version-controllable way to define both the metadata and the generation parameters for your animations.

Think of them as "recipes" for your animations - they contain all the information needed to:
- Describe what the animation is (metadata)
- Specify how to build it (generation parameters)
- Ensure reproducible builds across different environments
- Document animation settings in a human-readable format

### Location and Naming

Generation cards should be:
- Located alongside your animation project (typically in the same folder as your SVG frames)
- Named with a `.yaml` or `.yml` extension
- Named descriptively to match your animation (e.g., `seagull.yaml`, `walk_cycle.yaml`)

### Basic Structure

```yaml
metadata:
  # Descriptive information about the animation
  title: "My Animation"
  creators: "Artist Name"
  # ... more metadata fields

generation_parameters:
  # Technical settings for generating the FBF
  input_folder: path/to/frames
  output_path: path/to/output
  speed: 12
  # ... more generation settings
```

---

## Why Use Generation Cards?

### 1. **Reproducibility**
Generation cards ensure that your animation can be rebuilt exactly the same way every time, on any machine. This is critical for:
- Team collaboration
- Version control
- Long-term project maintenance
- Automated build pipelines

### 2. **Documentation**
They serve as self-documenting configuration that clearly shows:
- What settings were used
- Who created the animation
- What the animation is about
- How to regenerate it

### 3. **Separation of Concerns**
Keep your animation configuration separate from:
- Source code
- Build scripts
- Command-line tools

### 4. **Ease of Use**
Instead of remembering complex command-line arguments:
```bash
# Without generation card (complex, error-prone)
svg2fbf -i examples/seagull -o examples/seagull/output -f seagull.fbf.svg \
  --speed 12 --animation_type loop --title "Seagull Flight" \
  --creators "Emasoft" --keywords "seagull, bird, flying" --rights "Apache-2.0"

# With generation card (simple, clean)
svg2fbf examples/seagull/seagull.yaml
```

### 5. **Version Control Friendly**
YAML files work perfectly with Git and other version control systems, allowing you to:
- Track changes to animation parameters
- Diff configuration changes
- Revert to previous settings
- Document why settings changed (via commit messages)

---

## Complete YAML Schema

Here's the complete structure of an FBF generation card with all available fields:

```yaml
# Top-level comments are allowed and encouraged
# Use them to describe the animation or provide usage instructions

metadata:
  # === CORE METADATA ===
  title: string              # Animation title
  creators: string           # Creator(s) name(s)
  description: string        # What this animation shows/does
  keywords: string           # Comma-separated keywords for searchability
  language: string           # ISO language code (e.g., "en", "ja", "fr")
  rights: string             # License or copyright info

  # === EPISODIC METADATA (for series/episodes) ===
  episode_number: integer    # Episode number (optional)
  episode_title: string      # Episode-specific title (optional)

  # === ATTRIBUTION METADATA ===
  original_creators: string  # Original creator(s) if adaptation/derivative
  copyrights: string         # Copyright notice
  website: string            # Creator website or project URL
  original_language: string  # Original language if translated
  source: string             # Source information (URL, reference, etc.)

generation_parameters:
  # === INPUT/OUTPUT ===
  input_folder: string       # Path to folder containing SVG frames
  output_path: string        # Path where FBF file will be saved
  filename: string           # Name of output FBF file

  # === EXPLICIT FRAME LIST (alternative to input_folder scanning) ===
  frames:                    # Optional: explicit list of frame files
    - path/to/frame1.svg
    - path/to/frame2.svg
    - path/to/frame3.svg

  # === ANIMATION BEHAVIOR ===
  speed: float               # Frames per second (fps)
  animation_type: string     # Animation playback mode (see options below)
  play_on_click: boolean     # Start animation on click instead of autoplay
  max_frames: integer        # Maximum number of frames to process (null = unlimited)

  # === VISUAL SETTINGS ===
  backdrop: string           # Backdrop color (hex, rgb, or "None")
  align_mode: string         # Frame alignment: "top-left" or "center"
  keep_xml_space: boolean    # Preserve xml:space="preserve" attribute

  # === PRECISION SETTINGS ===
  digits: integer            # Decimal precision for general coordinates (default: 28)
  cdigits: integer           # Decimal precision for color values (default: 28)

  # === OUTPUT OPTIONS ===
  quiet: boolean             # Suppress console output (false = show progress)
```

### Animation Type Options

The `animation_type` parameter controls how the animation plays:

| Value | Behavior | Use Case |
|-------|----------|----------|
| `once` | Play once and stop | One-time effects, transitions |
| `loop` | Loop continuously | Cycling animations (walk cycles, spinning) |
| `pingpong_once` | Play forward then backward, stop | Reversible one-time effects |
| `pingpong_loop` | Play forward then backward, loop | Breathing effects, oscillations |

---

## Metadata Section

The `metadata` section contains descriptive information about your animation. This information becomes embedded in the generated FBF file and helps with organization, searchability, and attribution.

### Core Metadata Fields

#### `title` (string)
**Required: Strongly recommended**

The human-readable name of your animation.

```yaml
metadata:
  title: "Seagull Flight Animation"
```

**Best practices:**
- Be descriptive but concise
- Use title case
- Include the subject/action (e.g., "Character Jump", "Logo Reveal")

---

#### `creators` (string)
**Required: Strongly recommended**

The name(s) of the person or people who created this animation.

```yaml
metadata:
  creators: "Emasoft"
  # Or multiple creators
  creators: "Jane Doe, John Smith"
```

**Best practices:**
- List primary creators
- Separate multiple names with commas
- For teams, consider using team name
- Use consistent naming across projects

---

#### `description` (string)
**Required: Recommended**

A brief description of what the animation shows or does.

```yaml
metadata:
  description: "Simple seagull flying animation with basic shapes and gradients"
```

**Best practices:**
- 1-2 sentences maximum
- Describe the visual content
- Mention notable techniques (e.g., "with mesh gradients", "using CSS filters")
- Avoid marketing language, be factual

---

#### `keywords` (string)
**Required: Recommended**

Comma-separated keywords for categorization and search.

```yaml
metadata:
  keywords: "seagull, bird, flying, animation, simple"
```

**Best practices:**
- Use lowercase
- Separate with commas
- Include: subject, technique, style, mood
- Add searchable terms users might look for
- Keep to 5-10 keywords

---

#### `language` (string)
**Required: Recommended**

ISO 639-1 language code indicating the language of any text in the animation.

```yaml
metadata:
  language: "en"  # English
```

Common codes:
- `en` - English
- `ja` - Japanese
- `fr` - French
- `de` - German
- `es` - Spanish
- `it` - Italian
- `zh` - Chinese

**When to use:**
- Always specify if animation contains any text
- Use for narration, subtitles, UI elements
- If no text, still recommended to set to creator's language

---

#### `rights` (string)
**Required: Strongly recommended**

License or rights information for the animation.

```yaml
metadata:
  rights: "Apache-2.0"
  # Or
  rights: "CC-BY-4.0"
  # Or
  rights: "Copyright 2024 Example Corp. All rights reserved."
```

**Common values:**
- `Apache-2.0` - Apache License 2.0
- `MIT` - MIT License
- `CC0-1.0` - Public Domain
- `CC-BY-4.0` - Creative Commons Attribution
- `CC-BY-SA-4.0` - Creative Commons Attribution-ShareAlike
- Custom copyright notice

**Best practices:**
- Use SPDX license identifiers when possible
- Be explicit about usage rights
- Include year in copyright notices

---

### Attribution Metadata Fields

#### `original_creators` (string)
**Required: Optional**

The original creator(s) if this is an adaptation, translation, or derivative work.

```yaml
metadata:
  creators: "Jane Doe"              # Person who adapted it
  original_creators: "John Smith"   # Original creator
```

**When to use:**
- Adaptations of existing work
- Translations
- Remixes
- Based-on scenarios

---

#### `copyrights` (string)
**Required: Optional**

Formal copyright notice.

```yaml
metadata:
  copyrights: "Copyright © 2024 Emasoft. All rights reserved."
```

**Best practices:**
- Include © symbol or "Copyright" word
- Include year
- Include copyright holder name
- Can differ from `creators` (e.g., if work-for-hire)

---

#### `website` (string)
**Required: Optional**

URL to the creator's website or the project page.

```yaml
metadata:
  website: "https://example.com/animations/seagull"
```

**Best practices:**
- Use complete URLs with protocol (https://)
- Link to specific project page if available
- Link to creator portfolio otherwise
- Ensure link will remain valid long-term

---

#### `source` (string)
**Required: Optional**

Source information - where this animation came from or what it's based on.

```yaml
metadata:
  source: "Based on reference footage from National Geographic"
  # Or
  source: "https://github.com/example/original-animation"
```

**When to use:**
- Reference sources
- Original content URLs
- Archival information
- Attribution requirements

---

### Episodic Metadata Fields

For animations that are part of a series or episodic content:

#### `episode_number` (integer)
```yaml
metadata:
  episode_number: 5
```

#### `episode_title` (string)
```yaml
metadata:
  episode_number: 5
  episode_title: "The Great Migration"
```

#### `original_language` (string)
For translations or dubs:
```yaml
metadata:
  language: "en"              # Current language (English dub)
  original_language: "ja"     # Original language (Japanese)
```

---

## Generation Parameters Section

The `generation_parameters` section specifies the technical settings for building the FBF animation.

### Input/Output Parameters

#### `input_folder` (string)
**Required: Yes (unless using `frames` list)**

Path to the folder containing your SVG frame files.

```yaml
generation_parameters:
  input_folder: examples/seagull
  # Or absolute path
  input_folder: /Users/username/animations/seagull/frames
```

**Behavior:**
- Can be relative (to current working directory) or absolute
- svg2fbf scans this folder for .svg files
- Files are sorted naturally (frame1.svg, frame2.svg, ... frame10.svg)
- Non-SVG files are ignored

**Best practices:**
- Use relative paths for portability
- Keep frames in a dedicated subfolder (e.g., `input_frames/`, `frames/`, `svg_frames/`)
- Name frames with numerical suffixes for proper ordering

---

#### `frames` (list of strings)
**Required: Optional (alternative to `input_folder`)**

Explicit list of frame files in the exact order they should appear in the animation.

```yaml
generation_parameters:
  frames:
    - examples/seagull/frame_001.svg
    - examples/seagull/frame_002.svg
    - examples/seagull/frame_003.svg
    - examples/other/extra_frame.svg  # Can mix from different folders
```

**When to use:**
- You need precise control over frame order
- Frames are in multiple folders
- You want to skip certain frames
- Frame names don't sort naturally
- Cherry-picking specific frames

**Priority:**
- If `frames` list is present, it takes precedence over `input_folder` scanning
- Both can be specified, but `frames` list is used first

**Best practices:**
- Use absolute paths or paths relative to working directory
- Verify all files exist (svg2fbf will fail if any are missing)
- Comment why custom ordering is needed

---

#### `output_path` (string)
**Required: Recommended (default: `./`)**

Directory where the generated FBF file will be saved.

```yaml
generation_parameters:
  output_path: examples/seagull/fbf_output
```

**Default value:** `./` (current directory)

**Best practices:**
- Use a dedicated output folder (e.g., `fbf_output/`, `output/`, `build/`)
- Keep output separate from source frames
- Add output folders to .gitignore if build artifacts

---

#### `filename` (string)
**Required: Recommended (default: `animation.fbf.svg`)**

Name of the output FBF file.

```yaml
generation_parameters:
  filename: seagull.fbf.svg
```

**Default value:** `animation.fbf.svg`

**Naming convention:**
- Use `.fbf.svg` extension to clearly identify FBF files
- Match animation name for clarity
- Example: `walk_cycle.fbf.svg`, `logo_reveal.fbf.svg`

---

### Animation Behavior Parameters

#### `speed` (float)
**Required: Recommended (default: 1.0)**

Frames per second (fps) - controls playback speed.

```yaml
generation_parameters:
  speed: 12      # 12 fps - traditional animation
  # speed: 24    # 24 fps - film standard
  # speed: 30    # 30 fps - smooth web animation
  # speed: 1     # 1 fps - slow, deliberate
```

**Default value:** `1.0`

**Common values:**
- `1` - Very slow (useful for testing)
- `12` - Traditional hand-drawn animation
- `24` - Film standard
- `30` - Smooth web animation
- `60` - Ultra-smooth (for high-performance animations)

**Best practices:**
- Consider your source material (if rotoscoped from video)
- Higher fps = smoother but larger file (more frames shown per second)
- Lower fps = more "steppy" but can be stylistic choice
- 12-24 fps is sweet spot for most animations

---

#### `animation_type` (string)
**Required: Recommended (default: `once`)**

Controls how the animation plays and loops.

```yaml
generation_parameters:
  animation_type: loop
```

**Default value:** `once`

**Available options:**

| Value | Full Playback Behavior | Visual Example |
|-------|------------------------|----------------|
| `once` | Play frames 1→N once and stop on last frame | `1 2 3 4 5 [STOP]` |
| `loop` | Play frames 1→N, then restart from 1, repeat forever | `1 2 3 4 5 1 2 3 4 5 1 2 3...` |
| `pingpong_once` | Play forward 1→N, then backward N→1, stop | `1 2 3 4 5 4 3 2 1 [STOP]` |
| `pingpong_loop` | Play forward 1→N, backward N→1, repeat forever | `1 2 3 4 5 4 3 2 1 2 3 4 5 4 3...` |

**Use cases:**
- `once`: One-shot effects, transitions, reveals, loading animations
- `loop`: Continuous cycles (walk, run, spin, breathe)
- `pingpong_once`: Hover effects, reversible transitions
- `pingpong_loop`: Oscillating motion, breathing, pulsing

**Note:** Pingpong modes automatically create intermediate frames for smooth reversal.

---

#### `play_on_click` (boolean)
**Required: Optional (default: `false`)**

If `true`, animation waits for user click to start instead of auto-playing.

```yaml
generation_parameters:
  play_on_click: true
```

**Default value:** `false` (auto-play on load)

**Important HTML requirement:**

When `play_on_click: true`, you MUST embed the FBF using `<object>` tag, NOT `<img>`:

```html
<!-- ✓ Correct: Use <object> for interactive animations -->
<object type="image/svg+xml" data="animation.fbf.svg" width="800" height="600"></object>

<!-- ✗ Wrong: <img> does not support click interactivity -->
<img src="animation.fbf.svg" width="800" height="600">
```

**Use cases:**
- Interactive UI elements (buttons, icons)
- User-controlled animations
- Conserving resources (animation doesn't run until needed)
- Accessibility (user controls when motion starts)

---

#### `max_frames` (integer or null)
**Required: Optional (default: `null` = unlimited)**

Maximum number of frames to process from the input.

```yaml
generation_parameters:
  max_frames: 50
  # Or unlimited:
  max_frames: null
```

**Default value:** `null` (process all frames)

**When to use:**
- Testing: Process only first N frames for quick iteration
- Limiting file size: Cap very long animations
- Creating previews: First 10 frames as a preview
- Debugging: Isolate problems in specific frame ranges

**Note:** This is for PRODUCTION use. For testing, see [Testing with Generation Cards](#testing-with-generation-cards).

---

### Visual Settings Parameters

#### `backdrop` (string)
**Required: Optional (default: `"None"`)**

Background color to add behind all frames.

```yaml
generation_parameters:
  backdrop: "#f0f0f0"      # Light gray
  # backdrop: "None"       # Transparent (default)
  # backdrop: "#ff0000"    # Red
  # backdrop: "rgb(255, 0, 0)"  # Red (rgb format)
```

**Default value:** `"None"` (transparent/no backdrop)

**Accepted formats:**
- Hex colors: `#ff0000`, `#f00`
- RGB: `rgb(255, 0, 0)`
- Named colors: `red`, `blue`, `transparent`
- Special: `None` (no backdrop)

**Use cases:**
- Matte backgrounds for transparent animations
- Testing frame visibility
- Ensuring consistent background
- Creating specific visual moods

---

#### `align_mode` (string)
**Required: Optional (default: `"top-left"`)**

Controls how frames are aligned within the FBF viewBox.

```yaml
generation_parameters:
  align_mode: "top-left"
  # Or:
  align_mode: "center"
```

**Default value:** `"top-left"`

**Options:**
- `"top-left"`: Frames aligned to top-left corner (`preserveAspectRatio="xMinYMin meet"`)
- `"center"`: Frames centered (`preserveAspectRatio="xMidYMid meet"`)

**Technical details:**
- Controls the SVG `preserveAspectRatio` attribute
- Affects how frames are positioned when they don't exactly match the FBF viewBox
- `top-left` is recommended for most animations
- `center` is useful for animations that should be centered regardless of container size

**When to use `center`:**
- Logos and icons
- Centered UI elements
- Animations that should stay centered when scaled

---

#### `keep_xml_space` (boolean)
**Required: Optional (default: `false`)**

Whether to preserve the `xml:space="preserve"` attribute on the root SVG element.

```yaml
generation_parameters:
  keep_xml_space: true
```

**Default value:** `false` (remove the attribute)

**When to use:**
- Your frames have text elements with significant whitespace
- You're experiencing text rendering issues
- Source SVGs from tools that require this attribute

**Most users should leave this as `false`.**

---

### Precision Settings Parameters

#### `digits` (integer)
**Required: Optional (default: 28)**

Decimal precision for general coordinate values (paths, transforms, dimensions).

```yaml
generation_parameters:
  digits: 28    # Maximum precision (default)
  # digits: 6   # Reduced precision for smaller file size
```

**Default value:** `28`

**Range:** 1-28

**Trade-offs:**
- Higher values (20-28): Maximum accuracy, larger file size
- Medium values (6-10): Good balance, smaller files
- Lower values (1-5): Significant rounding, smallest files, may cause visual artifacts

**Best practices:**
- Default (28) is safe for all animations
- Reduce to 6-8 for web deployment if file size matters
- Test visual quality when reducing precision
- Use higher precision for animations with fine details

---

#### `cdigits` (integer)
**Required: Optional (default: 28)**

Decimal precision specifically for color values.

```yaml
generation_parameters:
  cdigits: 28   # Maximum color precision (default)
  # cdigits: 3  # Reduced precision (RGB 0-255 range)
```

**Default value:** `28`

**Range:** 1-28

**Why separate from `digits`?**
Colors often need different precision than coordinates. RGB values (0-255) or percentages (0-100%) may not need 28 decimal places.

**Best practices:**
- Default (28) is safe for all cases
- Can often reduce to 3-6 without visible color changes
- Higher precision needed for subtle gradients
- Test with your specific color palette

---

### Output Options

#### `quiet` (boolean)
**Required: Optional (default: `false`)**

Suppress console output during generation.

```yaml
generation_parameters:
  quiet: false    # Show progress (default)
  # quiet: true   # Silent mode
```

**Default value:** `false` (show output)

**When to set `true`:**
- Running in automated scripts
- Batch processing many animations
- You only care about errors
- CI/CD pipelines

**When to set `false`:**
- Development and testing
- You want to see progress
- Debugging issues
- Learning the tool

---

## Examples

### Example 1: Simple Loop Animation

**File:** `examples/seagull/seagull.yaml`

```yaml
# Simple seagull flying animation
# Usage: svg2fbf examples/seagull/seagull.yaml

metadata:
  title: "Seagull Flight Animation"
  creators: "Emasoft"
  description: "Simple seagull flying animation with basic shapes and gradients"
  keywords: "seagull, bird, flying, animation, simple"
  language: "en"
  rights: "Apache-2.0"

generation_parameters:
  input_folder: examples/seagull
  output_path: examples/seagull/fbf_output
  filename: seagull.fbf.svg
  speed: 12
  animation_type: loop
  play_on_click: false
  quiet: false
```

**What it does:**
- Loads all SVG frames from `examples/seagull/` folder
- Creates looping animation at 12 fps
- Outputs to `examples/seagull/fbf_output/seagull.fbf.svg`
- Auto-plays when loaded
- Shows progress during generation

---

### Example 2: Interactive Button with Click Trigger

**File:** `examples/splat_button/splat_button.yaml`

```yaml
# Interactive animated button with click-triggered splash effect
# Requires <object> tag for click interaction
# Usage: svg2fbf examples/splat_button/splat_button.yaml

metadata:
  title: "Interactive Splat Button"
  creators: "Emasoft"
  description: "CODE-FREE interactive animated button with click-triggered splash effect - pure SVG, no JavaScript required"
  keywords: "interactive button, click animation, splash effect, code-free"
  language: "en"
  rights: "Apache-2.0"

generation_parameters:
  input_folder: examples/splat_button/input_frames
  output_path: examples/splat_button/fbf_output
  filename: splat_button.fbf.svg
  speed: 4.0
  animation_type: pingpong_loop
  play_on_click: true      # Requires <object> tag in HTML
  quiet: false
```

**What it does:**
- Creates interactive button animation
- Waits for user click to start
- Plays forward and backward in a loop
- Slower speed (4 fps) for dramatic effect

**HTML requirement:**
```html
<object type="image/svg+xml" data="splat_button.fbf.svg" width="200" height="100"></object>
```

---

### Example 3: High-Quality Character Animation

**File:** `examples/anime_girl/anime_girl.yaml`

```yaml
# Complex character animation with mesh gradients
# High-speed smooth animation
# Usage: svg2fbf examples/anime_girl/anime_girl.yaml

metadata:
  title: "Anime Character Animation"
  creators: "Emasoft"
  description: "Complex character animation with mesh gradients and detailed artwork"
  keywords: "anime, character, animation, mesh gradients, complex"
  language: "en"
  rights: "Apache-2.0"

generation_parameters:
  input_folder: examples/anime_girl
  output_path: examples/anime_girl/fbf_output
  filename: anime_girl.fbf.svg
  speed: 24            # Film-quality smoothness
  animation_type: pingpong_loop
  play_on_click: false
  quiet: false
```

**What it does:**
- High-speed animation (24 fps) for smooth motion
- Pingpong loop for natural back-and-forth movement
- Handles complex SVG features (mesh gradients)

---

### Example 4: Explicit Frame List

**File:** `examples/custom_sequence/animation.yaml`

```yaml
# Animation with custom frame order
# Demonstrates explicit frame list usage

metadata:
  title: "Custom Sequence Animation"
  creators: "Jane Doe"
  description: "Animation with non-sequential frame order for special effect"
  keywords: "custom, sequence, special effect"
  language: "en"
  rights: "MIT"

generation_parameters:
  # Using explicit frame list instead of folder scanning
  frames:
    - examples/custom_sequence/intro.svg
    - examples/custom_sequence/main_01.svg
    - examples/custom_sequence/main_02.svg
    - examples/custom_sequence/main_03.svg
    - examples/effects/sparkle.svg       # From different folder
    - examples/custom_sequence/main_04.svg
    - examples/custom_sequence/outro.svg
  output_path: examples/custom_sequence/output
  filename: custom_animation.fbf.svg
  speed: 15
  animation_type: once
```

**What it does:**
- Uses explicit frame list for precise control
- Mixes frames from different folders
- Custom ordering that wouldn't work with alphabetical sorting
- Plays once and stops

---

### Example 5: Minimal Configuration

**File:** `examples/quick_test/test.yaml`

```yaml
# Minimal generation card for quick testing
# Only essential fields

metadata:
  title: "Test Animation"
  creators: "Test User"
  rights: "CC0-1.0"

generation_parameters:
  input_folder: examples/quick_test/frames
  speed: 12
  animation_type: loop
```

**What it does:**
- Uses only required/essential fields
- Relies on defaults for everything else
- Output goes to current directory (`./`)
- Output file is `animation.fbf.svg` (default)

---

### Example 6: All Optional Metadata

**File:** `examples/full_metadata/episode.yaml`

```yaml
# Example showing all possible metadata fields
# For episodic content with full attribution

metadata:
  # Core metadata
  title: "The Great Migration"
  creators: "Jane Doe Animation Studio"
  description: "Episode 5 of the Wildlife Series - following seagulls on their annual migration"
  keywords: "wildlife, seagulls, migration, nature, educational, series"
  language: "en"
  rights: "CC-BY-SA-4.0"

  # Episodic metadata
  episode_number: 5
  episode_title: "The Great Migration"

  # Attribution
  original_creators: "National Geographic Documentary Team"
  original_language: "en"
  copyrights: "Copyright © 2024 Jane Doe Animation Studio. Some rights reserved."
  website: "https://example.com/wildlife-series/episode-5"
  source: "Based on footage from National Geographic Special 'Bird Migrations' (2020)"

generation_parameters:
  input_folder: examples/full_metadata/frames
  output_path: examples/full_metadata/output
  filename: episode_05_migration.fbf.svg
  speed: 24
  animation_type: once
  max_frames: null
  backdrop: "None"
  align_mode: "center"
  digits: 28
  cdigits: 28
  play_on_click: false
  keep_xml_space: false
  quiet: false
```

**What it does:**
- Shows complete example with all possible fields
- Episodic content with full attribution chain
- Explicit about all settings (no reliance on defaults)
- Production-ready with complete documentation

---

## Best Practices

### 1. Always Include Core Metadata

At minimum, include these fields:
```yaml
metadata:
  title: "Your Animation Title"
  creators: "Your Name"
  rights: "License or Copyright"
```

**Why:**
- Ensures proper attribution
- Makes animations searchable and identifiable
- Legal clarity on usage rights

---

### 2. Use Descriptive Comments

Add comments to explain non-obvious choices:

```yaml
generation_parameters:
  speed: 8
  # Using 8fps instead of 12fps to match the hand-drawn aesthetic
  # and reduce file size for mobile delivery

  animation_type: pingpong_once
  # Pingpong for smooth hover effect - plays forward on hover-in,
  # backward on hover-out
```

**Why:**
- Future you (or teammates) will understand the reasoning
- Documents intentional choices vs. defaults
- Helps with maintenance and updates

---

### 3. Keep Generation Cards Near Source Files

**Recommended structure:**
```
examples/seagull/
├── seagull.yaml              ← Generation card here
├── frame_001.svg
├── frame_002.svg
├── frame_003.svg
└── fbf_output/
    └── seagull.fbf.svg       ← Generated output
```

**Why:**
- Easy to find configuration
- Portable (move whole folder, everything works)
- Clear association between config and frames

---

### 4. Version Control Your Generation Cards

**Add to Git:**
```bash
git add examples/seagull/seagull.yaml
git commit -m "Add generation card for seagull animation"
```

**Include in .gitignore:**
```gitignore
# Ignore generated FBF files (can be rebuilt from generation cards)
**/fbf_output/
*.fbf.svg

# But keep generation cards
!*.yaml
```

**Why:**
- Configurations are small and text-based (Git-friendly)
- Can rebuild FBF files from cards (no need to version control large binaries)
- Track changes to animation parameters over time

---

### 5. Test Before Committing

Always test your generation card before committing:

```bash
# Test generation
svg2fbf examples/seagull/seagull.yaml

# Verify output
open examples/seagull/fbf_output/seagull.fbf.svg
```

**Why:**
- Catch typos in paths
- Verify settings produce expected result
- Ensure card is complete and works

---

### 6. Use Relative Paths

**Prefer:**
```yaml
generation_parameters:
  input_folder: examples/seagull        # Relative
  output_path: examples/seagull/output  # Relative
```

**Over:**
```yaml
generation_parameters:
  input_folder: /Users/jane/projects/animations/seagull  # Absolute - breaks on other machines!
```

**Why:**
- Portable across different machines
- Works in team environments
- Survives project moves/renames

---

### 7. Document Complex Configurations

For animations with unusual settings, add a header comment:

```yaml
# SPECIAL CONFIGURATION NOTES:
#
# This animation uses explicit frame list because frames are generated
# from multiple sources and must be interleaved in specific order.
# DO NOT change to input_folder scanning - order matters!
#
# Speed is set to 6fps to match the original film's frame rate.
# Increasing speed will break sync with audio track.

metadata:
  # ... rest of config
```

---

### 8. Validate YAML Syntax

Use a YAML linter before committing:

```bash
# Using yamllint (if installed)
yamllint examples/seagull/seagull.yaml

# Or online validator
# https://www.yamllint.com/
```

**Common mistakes:**
```yaml
# ✗ Wrong: Inconsistent indentation
metadata:
  title: "Test"
   creators: "Name"  # 3 spaces instead of 2

# ✓ Correct: Consistent indentation
metadata:
  title: "Test"
  creators: "Name"    # 2 spaces

# ✗ Wrong: Missing quotes with special characters
description: Use these settings: speed=12, type=loop

# ✓ Correct: Quotes protect special characters
description: "Use these settings: speed=12, type=loop"
```

---

### 9. Set Explicit Values (Don't Rely on Defaults)

**For production, be explicit:**

```yaml
# ✓ Good: Explicit values, clear intent
generation_parameters:
  input_folder: examples/seagull
  output_path: examples/seagull/output
  filename: seagull.fbf.svg
  speed: 12
  animation_type: loop
  play_on_click: false
  quiet: false

# ⚠ Risky: Relies on defaults
generation_parameters:
  input_folder: examples/seagull
  # Everything else is default - what are the defaults? Will they change?
```

**Why:**
- Self-documenting
- Immune to default changes in future versions
- Clear what settings are being used

---

### 10. Use Templates for Common Patterns

Create template generation cards for your common use cases:

**File:** `templates/simple_loop.yaml`
```yaml
# Template: Simple looping animation
# Copy and customize for new animations

metadata:
  title: "CHANGE_ME"
  creators: "YOUR_NAME"
  description: "DESCRIBE_ANIMATION"
  keywords: "ADD, KEYWORDS, HERE"
  language: "en"
  rights: "Apache-2.0"

generation_parameters:
  input_folder: CHANGE_ME/frames
  output_path: CHANGE_ME/output
  filename: CHANGE_ME.fbf.svg
  speed: 12
  animation_type: loop
  play_on_click: false
  quiet: false
```

---

## Default Configuration

svg2fbf uses a three-tier configuration system:

### Priority Order (Highest to Lowest)

1. **CLI Arguments** - Command-line flags always win
2. **Generation Card (YAML)** - Values from your .yaml file
3. **Built-in Defaults** - Hardcoded fallback values

### Built-in Defaults

When a parameter is not specified in CLI or YAML, these defaults are used:

```python
# File paths
input_folder = "svg_frames/"
output_path = "./"
filename = "animation.fbf.svg"

# Animation behavior
speed = 1.0                    # 1 fps (very slow, good for testing)
animation_type = "once"        # Play once and stop
play_on_click = false          # Auto-play on load
max_frames = null              # Process all frames

# Visual settings
backdrop = "None"              # Transparent
align_mode = "top-left"        # Align to top-left corner
keep_xml_space = false         # Remove xml:space attribute

# Precision
digits = 28                    # Maximum coordinate precision
cdigits = 28                   # Maximum color precision

# Output
quiet = false                  # Show progress messages
```

### Test-Specific Defaults (pyproject.toml)

For testing with `testrunner.py`, additional defaults are defined in `pyproject.toml`:

```toml
[tool.svg2fbf.test]
# Test tolerances
image_tolerance = 0.04
pixel_tolerance = 0.0039
max_frames = 50

# Fixed for testing
fps = 1.0                      # Always 1 fps for deterministic tests
animation_type = "once"        # Always play once for testing

# Precision (must match production)
precision_digits = 28
precision_cdigits = 28

# Session creation
frame_number_format = "frame{:05d}.svg"
create_session_encoding = "utf-8"
default_frames = 2
```

**These test defaults are ONLY used by `testrunner.py`, NOT by `svg2fbf.py`.**

---

## Testing with Generation Cards

### How testrunner.py Uses Generation Cards

The test runner (`testrunner.py`) uses generation cards differently than the main tool:

**testrunner.py behavior:**
1. Loads your generation card
2. **Overrides** certain parameters for testing consistency:
   - `fps` → Always `1.0` (from pyproject.toml)
   - `animation_type` → Always `"once"` (from pyproject.toml)
   - `play_on_click` → Ignored for testing
3. Respects other parameters (paths, metadata, precision, etc.)

### Why These Overrides?

**Deterministic Testing:**
- `fps = 1.0` ensures frame timing is consistent across test runs
- `animation_type = "once"` makes rendering predictable (no loops)
- Removes animation variations that would cause false positives

### Parameters Configurable in Tests

**✓ You CAN configure these for tests:**
- `input_folder` / `frames` - What frames to test
- `output_path` / `filename` - Where test output goes
- `digits` / `cdigits` - Precision settings
- `backdrop` - Background color
- `align_mode` - Frame alignment
- `max_frames` - Limit test to N frames
- All metadata fields

**✗ You CANNOT configure these (fixed for testing):**
- `speed` / `fps` - Always 1.0
- `animation_type` - Always "once"
- `play_on_click` - Ignored

### Example Test Generation Card

**File:** `tests/sessions/session_001/config.yaml`

```yaml
# Test session generation card
# Note: fps and animation_type are overridden by testrunner.py

metadata:
  title: "Seagull Flight Test"
  creators: "Test Suite"
  description: "Test case for seagull animation frame rendering"
  keywords: "test, seagull, frames"
  language: "en"
  rights: "Apache-2.0"

generation_parameters:
  input_folder: tests/sessions/session_001/frames
  output_path: tests/sessions/session_001/fbf_output
  filename: test_seagull.fbf.svg

  # These are for documentation only - testrunner.py overrides them:
  # speed: 1.0              # Forced by testrunner
  # animation_type: "once"  # Forced by testrunner

  # These DO affect tests:
  max_frames: 10            # Test only first 10 frames
  backdrop: "#ffffff"       # White background for visibility
  align_mode: "top-left"    # Standard alignment
  digits: 28                # Full precision
  cdigits: 28               # Full color precision
```

### Running Tests with Generation Cards

```bash
# Create and run test session from folder
testrunner.py examples/seagull

# Testrunner automatically creates a generation card for the session
# and uses pyproject.toml test defaults for fps/animation_type

# Rerun existing session
testrunner.py --use-session 5
```

### Viewing Test Configuration

Default test configuration is in `pyproject.toml`:

```toml
[tool.svg2fbf.test]
fps = 1.0                    # FIXED for all tests
animation_type = "once"      # FIXED for all tests
max_frames = 50              # Default limit (can override in card)
# ... other test settings
```

**To modify test defaults:**
1. Edit `pyproject.toml` `[tool.svg2fbf.test]` section
2. Changes affect ALL future test runs
3. Existing test sessions keep their recorded settings

---

## Summary

FBF Generation Cards provide:

- **Declarative configuration** - Describe what you want, not how to build it
- **Reproducibility** - Same card = same output, every time
- **Version control** - Track configuration changes in Git
- **Documentation** - Self-documenting animation projects
- **Portability** - Move projects between machines easily
- **Testability** - Consistent test configurations via testrunner.py

**Key files to create:**
1. One generation card per animation (`.yaml` file)
2. Keep cards alongside your frame sources
3. Use the template in `templates/generation-card-template.yaml`

**Next steps:**
- See the [template file](../templates/generation-card-template.yaml) for a ready-to-use starting point
- Check `examples/` folder for real-world examples
- Read [GETTING_STARTED.md](GETTING_STARTED.md) for workflow guide
- Explore [FBF_SVG_SPECIFICATION.md](FBF_SVG_SPECIFICATION.md) for format details

---

**Document Version:** 1.0
**Last Updated:** 2024-11-09
**Maintainer:** svg2fbf project
**License:** Apache-2.0
