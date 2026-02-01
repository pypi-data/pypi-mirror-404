# FBF Metadata Specification

## Overview

The FBF format uses RDF (Resource Description Framework) metadata embedded in the `<metadata>` element to describe the animation's properties, generation parameters, and content characteristics.

## Metadata Categories

### 1. Animation Properties

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:frameCount` | integer | **Yes** | Total number of frames | `24` |
| `fbf:fps` | decimal | **Yes** | Frames per second (playback speed) | `12.0` |
| `fbf:duration` | decimal | **Yes** | Total duration in seconds | `2.0` |
| `fbf:playbackMode` | enum | **Yes** | Animation playback mode | `once`, `loop`, `pingpong_loop`, etc. |
| `fbf:width` | integer | **Yes** | Canvas width in pixels | `800` |
| `fbf:height` | integer | **Yes** | Canvas height in pixels | `600` |
| `fbf:viewBox` | string | **Yes** | ViewBox coordinates | `0 0 800 600` |
| `fbf:aspectRatio` | string | No | Aspect ratio | `4:3`, `16:9`, `1:1` |
| `fbf:firstFrameWidth` | integer | No | Original first frame width | `1920` |
| `fbf:firstFrameHeight` | integer | No | Original first frame height | `1080` |

### 2. Authoring & Provenance

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `dc:title` | string | No | Animation title | `"Seagull Flight Animation"` |
| `fbf:episodeNumber` | integer | No | Episode number in series | `1`, `42` |
| `fbf:episodeTitle` | string | No | Episode-specific title | `"The Cowboy"` |
| `fbf:creators` | string | No | Current animation creators (comma-separated) | `"Artist Name, Studio XYZ"` |
| `fbf:originalCreators` | string | No | Original content creators | `"Stanley Kubrick"` |
| `dc:creator` | string | No | Primary creator (legacy single value) | `"John Doe"` |
| `dc:description` | string | No | Animation description | `"A seagull flying over the ocean"` |
| `dc:date` | ISO8601 | No | Creation date | `2024-11-06T23:30:00Z` |
| `dc:language` | ISO639 | No | Content language code | `en`, `it`, `fr` |
| `fbf:originalLanguage` | ISO639 | No | Original production language | `en-US`, `ja-JP` |
| `fbf:copyrights` | string | No | Copyright statement | `"2025 Film Company, Hollywood"` |
| `dc:rights` | string | No | License/usage rights | `"CC BY 4.0"`, `"All Rights Reserved"` |
| `fbf:website` | URL | No | Official website or info page | `"https://example.com/animation"` |
| `fbf:keywords` | string | No | Search keywords (comma-separated) | `"movie-spoof, WW2, comedy, short-video"` |
| `dc:source` | string | No | Original source/software | `"OpenToonz"`, `"Adobe Animate"` |
| `fbf:sourceFramesPath` | string | No | Original frames location | `"svg_frames/"` |

### 3. Generator Information

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:generator` | string | **Yes** | Generator software name | `"svg2fbf"` |
| `fbf:generatorVersion` | string | **Yes** | Generator version (semver) | `"0.1.0"` |
| `fbf:generatedDate` | ISO8601 | **Yes** | File generation timestamp | `2024-11-06T23:30:00Z` |
| `fbf:formatVersion` | string | **Yes** | FBF spec version | `"1.0"` |
| `fbf:precisionDigits` | integer | No | Coordinate precision | `28` |
| `fbf:precisionCDigits` | integer | No | Control point precision | `28` |

### 4. Content Features

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:useCssClasses` | boolean | No | Contains CSS classes | `true`, `false` |
| `fbf:hasBackdropImage` | boolean | No | Has static backdrop bitmap | `true`, `false` |
| `fbf:useExternalMedia` | boolean | No | References external media files | `true`, `false` |
| `fbf:useExternalFonts` | boolean | No | References external fonts | `true`, `false` |
| `fbf:useEmbeddedImages` | boolean | No | Contains base64-embedded images | `true`, `false` |
| `fbf:useMeshGradient` | boolean | **Yes** | Uses SVG 2.0 mesh gradients | `true`, `false` |
| `fbf:hasInteractivity` | boolean | No | Has interactive elements | `true`, `false` |
| `fbf:interactivityType` | enum | No | Type of interactivity | `click_to_start`, `hover`, `none` |
| `fbf:hasJavaScript` | boolean | No | Contains JavaScript (forbidden except mesh polyfill) | `true`, `false` |
| `fbf:hasCSS` | boolean | No | Contains CSS styles | `true`, `false` |
| `fbf:containsText` | boolean | No | Contains text elements | `true`, `false` |
| `fbf:colorProfile` | string | No | Color profile used | `sRGB`, `Adobe RGB` |

### 5. Optimization Metrics

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:totalElements` | integer | No | Total SVG elements across all frames | `15420` |
| `fbf:sharedElements` | integer | No | Elements in SHARED_DEFINITIONS | `850` |
| `fbf:uniqueElements` | integer | No | Unique elements (not shared) | `14570` |
| `fbf:deduplicationRatio` | decimal | No | Percentage of deduplicated elements | `55.2` |
| `fbf:originalSize` | integer | No | Sum of input frame sizes (bytes) | `5000000` |
| `fbf:optimizedSize` | integer | No | Final FBF file size (bytes) | `500000` |
| `fbf:compressionRatio` | decimal | No | Size reduction percentage | `90.0` |
| `fbf:processingTime` | decimal | No | Generation time in seconds | `0.075` |

### 6. Quality & Compatibility

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:browserCompatibility` | string | No | Minimum browser requirements | `"SVG 1.1, SMIL Animation"` |
| `fbf:estimatedMemory` | integer | No | Estimated RAM usage (MB) | `25` |
| `fbf:maxFrameComplexity` | integer | No | Max elements in single frame | `650` |
| `fbf:avgFrameComplexity` | integer | No | Average elements per frame | `480` |
| `fbf:hasNegativeCoords` | boolean | No | Uses negative viewBox coordinates | `true`, `false` |
| `fbf:usesTransforms` | boolean | No | Contains transform attributes | `true`, `false` |
| `fbf:usesGradients` | boolean | No | Contains gradient definitions | `true`, `false` |
| `fbf:usesFilters` | boolean | No | Contains SVG filters | `true`, `false` |
| `fbf:usesPatterns` | boolean | No | Contains pattern definitions | `true`, `false` |

### 7. Additional Technical Metadata

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| `fbf:keepXmlSpace` | boolean | No | Preserves xml:space attribute | `false` |
| `fbf:keepAspectRatio` | boolean | No | Has preserveAspectRatio | `true` |
| `fbf:quiet` | boolean | No | Generated in quiet mode | `false` |
| `fbf:maxFramesLimit` | integer | No | Frame limit applied during generation | `50` |
| `fbf:inputFrameFormat` | string | No | Original frame filename pattern | `"frame_{:05d}.svg"` |
| `fbf:frameNumberingStart` | integer | No | First frame number | `1` |

---

## Playback Mode Enumeration

Valid values for `fbf:playbackMode`:

| Value | Description |
|-------|-------------|
| `once` | Play START → END, then STOP |
| `once_reversed` | Play END → START, then STOP |
| `loop` | Play START → END, repeat FOREVER |
| `loop_reversed` | Play END → START, repeat FOREVER |
| `pingpong_once` | Play START → END → START, then STOP |
| `pingpong_loop` | Play START → END → START, repeat FOREVER |
| `pingpong_once_reversed` | Play END → START → END, then STOP |
| `pingpong_loop_reversed` | Play END → START → END, repeat FOREVER |

---

## Interactivity Type Enumeration

Valid values for `fbf:interactivityType`:

| Value | Description |
|-------|-------------|
| `none` | No interactivity |
| `click_to_start` | Animation starts on click |
| `click_to_toggle` | Click toggles play/pause |
| `hover` | Animation on hover |
| `custom` | Custom JavaScript interactivity |

---

## Example RDF Metadata Block

```xml
<metadata>
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:cc="http://creativecommons.org/ns#"
           xmlns:fbf="http://opentoonz.github.io/fbf/1.0#">

    <!-- Basic Animation Properties -->
    <rdf:Description rdf:about="">
      <dc:format>image/svg+xml</dc:format>
      <dc:type rdf:resource="http://purl.org/dc/dcmitype/MovingImage"/>

      <!-- Animation Metadata -->
      <dc:title>Seagull Flight Animation</dc:title>
      <dc:creator>John Doe</dc:creator>
      <dc:description>A seagull gracefully flying over ocean waves</dc:description>
      <dc:date>2024-11-06T23:30:00Z</dc:date>
      <dc:language>en</dc:language>
      <dc:rights>CC BY 4.0</dc:rights>
      <dc:source>Adobe Animate CC 2024</dc:source>

      <!-- Animation Properties -->
      <fbf:frameCount>24</fbf:frameCount>
      <fbf:fps>12.0</fbf:fps>
      <fbf:duration>2.0</fbf:duration>
      <fbf:playbackMode>loop</fbf:playbackMode>
      <fbf:width>800</fbf:width>
      <fbf:height>600</fbf:height>
      <fbf:viewBox>0 0 800 600</fbf:viewBox>
      <fbf:aspectRatio>4:3</fbf:aspectRatio>

      <!-- Generator Information -->
      <fbf:generator>svg2fbf</fbf:generator>
      <fbf:generatorVersion>0.1.0</fbf:generatorVersion>
      <fbf:generatedDate>2024-11-06T23:30:00Z</fbf:generatedDate>
      <fbf:formatVersion>1.0</fbf:formatVersion>
      <fbf:precisionDigits>28</fbf:precisionDigits>
      <fbf:precisionCDigits>28</fbf:precisionCDigits>

      <!-- Content Features -->
      <fbf:useCssClasses>false</fbf:useCssClasses>
      <fbf:hasBackdropImage>false</fbf:hasBackdropImage>
      <fbf:useExternalMedia>false</fbf:useExternalMedia>
      <fbf:useExternalFonts>false</fbf:useExternalFonts>
      <fbf:useEmbeddedImages>true</fbf:useEmbeddedImages>
      <fbf:useMeshGradient>false</fbf:useMeshGradient>
      <fbf:hasInteractivity>false</fbf:hasInteractivity>
      <fbf:interactivityType>none</fbf:interactivityType>
      <fbf:hasJavaScript>true</fbf:hasJavaScript>
      <fbf:hasCSS>false</fbf:hasCSS>
      <fbf:containsText>false</fbf:containsText>
      <fbf:colorProfile>sRGB</fbf:colorProfile>

      <!-- Optimization Metrics -->
      <fbf:totalElements>15420</fbf:totalElements>
      <fbf:sharedElements>850</fbf:sharedElements>
      <fbf:uniqueElements>14570</fbf:uniqueElements>
      <fbf:deduplicationRatio>55.2</fbf:deduplicationRatio>
      <fbf:originalSize>5000000</fbf:originalSize>
      <fbf:optimizedSize>500000</fbf:optimizedSize>
      <fbf:compressionRatio>90.0</fbf:compressionRatio>
      <fbf:processingTime>0.075</fbf:processingTime>

      <!-- Quality & Compatibility -->
      <fbf:browserCompatibility>SVG 1.1, SMIL Animation</fbf:browserCompatibility>
      <fbf:hasNegativeCoords>false</fbf:hasNegativeCoords>
      <fbf:usesTransforms>true</fbf:usesTransforms>
      <fbf:usesGradients>true</fbf:usesGradients>
      <fbf:usesFilters>false</fbf:usesFilters>
      <fbf:usesPatterns>false</fbf:usesPatterns>

      <!-- Technical Settings -->
      <fbf:keepXmlSpace>false</fbf:keepXmlSpace>
      <fbf:keepAspectRatio>true</fbf:keepAspectRatio>
      <fbf:sourceFramesPath>examples/seagull/</fbf:sourceFramesPath>
    </rdf:Description>

  </rdf:RDF>
</metadata>
```

---

## Namespace Declaration

The FBF metadata namespace should be declared in the SVG root element:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:cc="http://creativecommons.org/ns#"
     xmlns:fbf="http://opentoonz.github.io/fbf/1.0#"
     ...>
```

---

## Implementation (Phase 1 - All Fields to Implement)

**User-requested core fields (MUST implement):**

- `fbf:frameCount` - Number of frames
- `fbf:firstFrameWidth` - First frame original width
- `fbf:firstFrameHeight` - First frame original height
- `fbf:fps` - Frames per second
- `dc:title` - Animation title
- `fbf:episodeNumber` - Episode number in series
- `fbf:episodeTitle` - Episode-specific title
- `fbf:creators` - Current animation creators (plural, comma-separated)
- `fbf:originalCreators` - Original content creators
- `dc:creator` - Primary creator (legacy single value)
- `fbf:copyrights` - Copyright statement
- `fbf:website` - Official website or info page
- `fbf:originalLanguage` - Original production language
- `fbf:keywords` - Search keywords (comma-separated)
- `fbf:generatorVersion` - svg2fbf version that generated the file
- `fbf:useCssClasses` - Uses CSS classes
- `fbf:hasBackdropImage` - Has bitmap background image
- `fbf:useExternalMedia` - Uses external media files
- `fbf:useExternalFonts` - Uses external fonts
- `fbf:useEmbeddedImages` - Uses embedded images
- `fbf:useMeshGradient` - Uses SVG 2.0 mesh gradients (requires polyfill)
- `fbf:hasInteractivity` - Has interactivity
- `fbf:interactivityType` - Type of interactivity (click to start, etc.)
- `fbf:playbackMode` - Playback mode (once, loop, pingpong, etc.)

**Essential format fields:**

- `fbf:duration` - Total animation duration
- `fbf:width`, `fbf:height`, `fbf:viewBox` - Canvas dimensions
- `fbf:generator` - Generator software name
- `fbf:generatedDate` - File generation timestamp
- `fbf:formatVersion` - FBF specification version

**Extended metadata fields:**

- `dc:description` - Animation description
- `dc:date` - Creation date
- `dc:rights` - Copyright/license
- `dc:source` - Original source software
- `fbf:precisionDigits`, `fbf:precisionCDigits` - Precision settings
- `fbf:hasJavaScript` - Contains JavaScript (only mesh polyfill allowed)
- `fbf:hasCSS` - Contains CSS styles
- `fbf:aspectRatio` - Aspect ratio

---

## Notes

1. **Required fields** ensure minimum viable metadata for FBF players
2. **Dublin Core (dc:)** fields provide standard bibliographic metadata
3. **Creative Commons (cc:)** fields support licensing
4. **FBF namespace (fbf:)** contains format-specific metadata
5. All boolean fields default to `false` if not specified
6. ISO 8601 format for dates: `YYYY-MM-DDTHH:MM:SSZ`
7. Decimal precision uses dot notation: `12.0`, not `12,0`

---

## JavaScript Exception: Mesh Gradient Polyfill

**IMPORTANT**: The FBF format **FORBIDS** the use of JavaScript, with **ONE EXCEPTION**:

### The Mesh Gradient Polyfill

The FBF format **MUST** include a JavaScript polyfill to render SVG 2.0 `<meshgradient>` elements in browsers that do not yet support them natively. This is the ONLY permitted JavaScript in FBF files.

**Why this exception:**
- Mesh gradients are an SVG 2.0 feature with limited browser support
- The polyfill ensures cross-browser compatibility
- It provides a graceful degradation path for modern SVG features
- The polyfill is self-contained, non-interactive, and executes only on document load

**Implementation:**
- svg2fbf MUST automatically inject the mesh gradient polyfill into every generated FBF file
- The polyfill is added as a `<script>` element at the end of the SVG document
- The script has `id="mesh_polyfill"` and `type="text/javascript"`
- When `fbf:useMeshGradient` is `true`, the file contains `<meshgradient>` elements
- The polyfill detects and renders these gradients as canvas-based images

**Polyfill source:**
The minified polyfill is approximately 15KB and converts mesh gradients to rasterized images at runtime using HTML5 Canvas API.

**Security considerations:**
- The polyfill contains NO external network calls
- It operates entirely within the SVG document sandbox
- It does NOT enable user interactivity
- It does NOT modify the DOM structure beyond rendering gradients

---

## Future Considerations

Additional metadata that might be useful in future versions:

- `fbf:audioTrack` - Reference to external audio (for future audio support)
- `fbf:subtitles` - Embedded subtitle/caption data
- `fbf:chapters` - Chapter markers for navigation
- `fbf:thumbnail` - Base64 thumbnail for preview
- `fbf:tags` - Searchable keywords
- `fbf:rating` - Content rating (G, PG, etc.)
- `fbf:accessibility` - Accessibility features description
- `fbf:colorBlindSafe` - Color-blind friendly flag
- `fbf:HDR` - HDR content flag

---

## YAML Configuration File

svg2fbf supports YAML configuration files for specifying metadata and generation parameters. This allows batch processing and reproducible builds without long command lines.

### File Structure

```yaml
# animation_config.yaml

# Metadata Section - User-specified fields that cannot be inferred
metadata:
  title: "The Bomb"
  episode_number: 1
  episode_title: "The Cowboy"
  creators: "Artist Name, Studio XYZ"
  original_creators: "Stanley Kubrick"
  copyrights: "2025 Film Company, Hollywood"
  website: "https://example.com/animation"
  language: "en"
  original_language: "en-US"
  keywords: "movie-spoof, WW2, comedy, short-video, strangelove"
  description: "A humorous spoof of the classic scene"
  rights: "All Rights Reserved"
  source: "Adobe Animate CC 2024"

# Generation Parameters Section - svg2fbf runtime settings
generation_parameters:
  # Frame source (explicit list takes priority over input_folder)
  frames:
    - "path/to/frame_001.svg"
    - "path/to/frame_002.svg"
    - "path/to/frame_005.svg"  # Can skip, reorder, duplicate frames
    - "path/to/frame_003.svg"

  # Alternative: specify folder (frames will be auto-detected and sorted)
  # input_folder: "examples/seagull/"

  # Output settings
  output_path: "output/"
  filename: "animation.fbf.svg"

  # Animation settings
  speed: 24.0  # fps
  animation_type: "loop"  # once, loop, pingpong_once, pingpong_loop

  # Precision settings
  digits: 28
  cdigits: 28

  # Optional features
  backdrop: null  # Path to backdrop image (null = none)
  play_on_click: false
  keep_xml_space: false
  quiet: false
  max_frames: null  # null = no limit
```

### Usage

**Option 1: CLI parameter**
```bash
uv run svg2fbf --config animation_config.yaml
```

**Option 2: CLI parameters override YAML values**
```bash
# YAML provides base config, CLI overrides specific values
uv run svg2fbf --config animation_config.yaml --speed 12.0 --title "Different Title"
```

**Priority Order:**
1. CLI parameters (highest priority)
2. YAML config file
3. svg2fbf defaults (lowest priority)

### Field Mapping

YAML keys map to CLI parameters and metadata fields:

| YAML Key | CLI Parameter | Metadata Field | Auto-Inferred |
|----------|---------------|----------------|---------------|
| `metadata.title` | `--title` | `dc:title` | No |
| `metadata.episode_number` | `--episode-number` | `fbf:episodeNumber` | No |
| `metadata.episode_title` | `--episode-title` | `fbf:episodeTitle` | No |
| `metadata.creators` | `--creators` | `fbf:creators` | No |
| `metadata.original_creators` | `--original-creators` | `fbf:originalCreators` | No |
| `metadata.copyrights` | `--copyrights` | `fbf:copyrights` | No |
| `metadata.website` | `--website` | `fbf:website` | No |
| `metadata.language` | `--language` | `dc:language` | No |
| `metadata.original_language` | `--original-language` | `fbf:originalLanguage` | No |
| `metadata.keywords` | `--keywords` | `fbf:keywords` | No |
| `metadata.description` | `--description` | `dc:description` | No |
| `metadata.rights` | `--rights` | `dc:rights` | No |
| `metadata.source` | `--source` | `dc:source` | No |
| - | - | `fbf:frameCount` | **Yes** (count frames) |
| - | - | `fbf:fps` | **Yes** (from speed parameter) |
| - | - | `fbf:duration` | **Yes** (frameCount ÷ fps) |
| - | - | `fbf:width`, `fbf:height` | **Yes** (from first frame) |
| - | - | `fbf:viewBox` | **Yes** (from first frame) |
| - | - | `fbf:generator` | **Yes** (always "svg2fbf") |
| - | - | `fbf:generatorVersion` | **Yes** (from SEMVERSION) |
| - | - | `fbf:generatedDate` | **Yes** (current timestamp) |
| - | - | `fbf:playbackMode` | **Yes** (from animation_type) |
| - | - | `fbf:useMeshGradient` | **Yes** (scan for `<meshgradient>`) |
| - | - | `fbf:useEmbeddedImages` | **Yes** (scan for base64 images) |
| - | - | `fbf:hasBackdropImage` | **Yes** (check backdrop parameter) |

### Example: Minimal Config

```yaml
# Minimal config - only specify what you need
metadata:
  title: "Seagull Flight"
  creators: "Nature Animator"

generation_parameters:
  input_folder: "examples/seagull/"
  speed: 12.0
  animation_type: "loop"
```

All other fields will be auto-inferred by svg2fbf.
