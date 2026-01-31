# FBF.SVG Format Specification v0.1

**Status**: Candidate Substandard for SVG (Working Draft)
**Version**: 0.1.2a5
**Date**: 2025-11-09
**Editors**: Emasoft (713559+Emasoft@users.noreply.github.com)

---

## Abstract

The **FBF.SVG** (Frame-by-Frame SVG) format is a proposed substandard of the SVG (Scalable Vector Graphics) specification that defines a constrained, optimized profile for declarative frame-by-frame animations. FBF.SVG files are valid SVG 1.1/2.0 documents with additional structural, semantic, and conformance requirements that enable efficient animation playback through SMIL timing while maintaining strict security and performance characteristics.

This specification positions FBF.SVG as a **candidate substandard** of SVG, analogous to how SVG Tiny and SVG Basic are substandards of SVG Full. The goal is to establish FBF.SVG as a recognized, validatable format for frame-by-frame vector animation.

---

## Status of This Document

This is a **Working Draft** specification of the FBF.SVG format. It is subject to change without notice as the format evolves toward standardization. The current implementation (svg2fbf v0.1.2a4) generates files conforming to this specification, but both the specification and implementation are in alpha development.

**Feedback** on this specification should be directed to the svg2fbf project issue tracker:
https://github.com/Emasoft/svg2fbf/issues

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Conformance](#2-conformance)
3. [Relationship to SVG](#3-relationship-to-svg)
4. [FBF.SVG Document Structure](#4-fbfsvg-document-structure)
5. [Structural Requirements](#5-structural-requirements)
6. [Element Restrictions](#6-element-restrictions)
7. [Attribute Requirements](#7-attribute-requirements)
8. [Animation Requirements](#8-animation-requirements)
9. [Metadata Requirements](#9-metadata-requirements)
10. [Security Model](#10-security-model)
11. [Validation](#11-validation)
12. [References](#12-references)
13. [Appendix A: FBF.SVG Schema](#appendix-a-fbfsvg-schema)
14. [Appendix B: Example FBF.SVG Document](#appendix-b-example-fbfsvg-document)

---

## 1. Introduction

### 1.1 Purpose

The FBF.SVG format addresses the need for a standardized, efficient representation of frame-by-frame vector animations. While SVG supports various animation mechanisms (SMIL, CSS animations, JavaScript), there is no established profile specifically optimized for frame-based animation sequences with strong security and performance guarantees.

### 1.2 Scope

This specification defines:

- A **structural profile** for SVG documents containing frame-by-frame animations
- **Conformance requirements** for FBF.SVG generators and validators
- **Security constraints** that prohibit dynamic scripting except for approved polyfills
- **Metadata schema** for comprehensive animation documentation
- **Validation rules** for programmatic format verification

### 1.3 Non-Goals

This specification does NOT define:

- A replacement for SVG animation mechanisms
- A video codec or binary format
- Interactive or event-driven animations
- Streaming or progressive animation delivery

### 1.4 Design Principles

FBF.SVG adheres to the following principles:

1. **SVG Compatibility**: Every FBF.SVG document MUST be a valid SVG document
2. **Declarative Animation**: Animation MUST use SMIL, not imperative scripting
3. **Security First**: No external resources except approved polyfills; strict CSP compliance
4. **Optimization**: Deduplication and shared definitions minimize file size
5. **Validatability**: Documents MUST be mechanically validatable against schema
6. **Self-Documentation**: Comprehensive metadata embedded in RDF/XML format
7. **Strict Structure**: Mandatory element ordering enables streaming optimization and safe extensibility
8. **Controlled Extensibility**: Three designated extension points (STAGE_BACKGROUND, STAGE_FOREGROUND, OVERLAY_LAYER) enable predictable, z-ordered customization without disrupting animation hierarchy

---

## 2. Conformance

### 2.1 Conformance Levels

This specification defines two conformance levels:

#### 2.1.1 FBF.SVG Basic Conformance

A document conforming to **FBF.SVG Basic** MUST:

1. Be a valid SVG 1.1 or SVG 2.0 document
2. Contain the mandatory structural elements (see Section 5)
3. Use SMIL animation for frame sequencing (see Section 8)
4. Include `<desc>` element identifying the document as FBF.SVG
5. Contain no script elements except approved polyfills

#### 2.1.2 FBF.SVG Full Conformance

A document conforming to **FBF.SVG Full** MUST satisfy all Basic Conformance requirements AND:

1. Include RDF/XML metadata in `<metadata>` element (see Section 9)
2. Follow naming conventions for element IDs (FRAME001, FRAME002, etc.)
3. Use `preserveAspectRatio` on root SVG element
4. Include generator metadata (svg2fbf version, generation date)
5. Validate against the FBF.SVG XSD Schema (Appendix A)

### 2.2 Conformance Classes

Two conformance classes are defined:

- **FBF.SVG Generator**: Software that produces FBF.SVG documents
- **FBF.SVG Validator**: Software that verifies FBF.SVG conformance

---

## 3. Relationship to SVG

### 3.1 Substandard Positioning

FBF.SVG is positioned as a **substandard** (constrained profile) of SVG, analogous to:

- **SVG Tiny**: Optimized for mobile devices, limited feature set
- **SVG Basic**: Between Tiny and Full, for desktop/server rendering
- **FBF.SVG**: Optimized for frame-by-frame animation, SMIL-based timing

### 3.2 SVG Feature Support

FBF.SVG documents:

- MUST support all SVG 1.1 Basic Shapes (rect, circle, ellipse, line, polyline, polygon, path)
- MUST support SVG 1.1 gradients (linearGradient, radialGradient)
- MAY support SVG 2.0 mesh gradients (with polyfill injection)
- MUST support SVG transforms (translate, rotate, scale, matrix)
- MUST support SVG filters (but discouraged for performance)
- MUST support SVG clipping and masking
- MUST support embedded resources (base64 images, fonts)
- MUST NOT support dynamic scripting (except approved polyfills)
- MUST NOT support external resource loading at runtime

### 3.3 SMIL Subset

FBF.SVG uses a strict subset of SMIL animation:

**Allowed**:
- `<animate>` element with `attributeName="xlink:href"`
- `values` attribute containing frame ID list
- `dur` attribute (animation duration)
- `repeatCount` attribute ("1", "indefinite", integer)
- `begin` attribute (timing, including "click" for interactive start)
- `fill` attribute ("freeze", "remove")

**Forbidden**:
- All other SMIL animation types (`<animateMotion>`, `<animateTransform>`, `<set>`)
- Complex timing syntax (syncbase, wallclock, indefinite loops except `repeatCount`)
- Event-based animation except `begin="click"` on root ANIMATED_GROUP

---

## 4. FBF.SVG Document Structure

### 4.1 Canonical Structure

Every FBF.SVG document MUST follow this structure:

```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="..."
     preserveAspectRatio="...">

  <!-- Header elements -->
  <metadata><!-- RDF/XML metadata (REQUIRED for Full Conformance) --></metadata>
  <desc><!-- FBF format description (REQUIRED) --></desc>

  <!-- Animation structure -->
  <g id="ANIMATION_BACKDROP">
    <g id="STAGE_BACKGROUND"><!-- Empty for background elements --></g>
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" xlink:href="#FRAME00001">
          <animate attributeName="xlink:href"
                   values="#FRAME00001;#FRAME00002;#FRAME00003;..."
                   dur="...s"
                   repeatCount="..."/>
        </use>
      </g>
    </g>
    <g id="STAGE_FOREGROUND"><!-- Empty for foreground elements --></g>
  </g>

  <!-- Overlay layer (outside backdrop) -->
  <g id="OVERLAY_LAYER"><!-- Empty for overlay elements --></g>

  <!-- Definitions -->
  <defs>
    <g id="SHARED_DEFINITIONS"><!-- Shared elements --></g>
    <g id="FRAME00001"><!-- Frame 1 content --></g>
    <g id="FRAME00002"><!-- Frame 2 content --></g>
    <!-- Additional frames... -->
  </defs>

  <!-- Optional mesh gradient polyfill script (ONLY if meshgradient present) -->
  <script type="text/javascript">...</script>
</svg>
```

### 4.2 Element Ordering

The following ordering MUST be respected:

**Top-Level Elements**:
1. `<metadata>` (if present)
2. `<desc>`
3. `<g id="ANIMATION_BACKDROP">`
4. `<g id="OVERLAY_LAYER">`
5. `<defs>`
6. `<script>` (if needed for polyfill)

**Within ANIMATION_BACKDROP**:
1. `<g id="STAGE_BACKGROUND">` — renders behind animation
2. `<g id="ANIMATION_STAGE">` — contains the frame animation
3. `<g id="STAGE_FOREGROUND">` — renders in front of animation

---

## 5. Structural Requirements

> **"Just because we stand on the shoulders of a giant - the amazing SVG format - we cannot expect the job of developing FBF.SVG to be any easier."**
>
> — *Emanuele Sabetta*

---

### 5.0 Z-Order Hierarchy Overview

FBF.SVG defines a strict visual layering hierarchy through its structural elements. The following table shows the complete z-order from bottom to top:

| Layer | Element ID | Location | Z-Order | Purpose | Content |
|-------|-----------|----------|---------|---------|---------|
| 1 (bottom) | `STAGE_BACKGROUND` | Inside ANIMATION_BACKDROP | Lowest | Background extension | Static backgrounds, watermarks behind animation |
| 2 | `ANIMATION_STAGE` | Inside ANIMATION_BACKDROP | Middle | Frame animation | Animated frame content (ANIMATED_GROUP → PROSKENION) |
| 3 | `STAGE_FOREGROUND` | Inside ANIMATION_BACKDROP | Higher | Foreground extension | Overlays in front of animation (e.g., "PREVIEW" text) |
| 4 (top) | `OVERLAY_LAYER` | Outside ANIMATION_BACKDROP | Highest | Global overlay extension | Top-level overlays (titles, badges, PiP, controls) |

**Visual Rendering Order**:
```
┌─────────────────────────────────────────────────────────┐
│ OVERLAY_LAYER (top-most, above everything)             │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ ANIMATION_BACKDROP                                  │ │
│ │ ┌─────────────────────────────────────────────────┐ │ │
│ │ │ STAGE_FOREGROUND (in front of animation)       │ │ │
│ │ ├─────────────────────────────────────────────────┤ │ │
│ │ │ ANIMATION_STAGE (frame animation)              │ │ │
│ │ ├─────────────────────────────────────────────────┤ │ │
│ │ │ STAGE_BACKGROUND (behind animation)            │ │ │
│ │ └─────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

**Extension Point Summary**:
- **STAGE_BACKGROUND**: For elements that should appear behind the animation (e.g., canvas fills, background patterns)
- **STAGE_FOREGROUND**: For elements that should appear in front of the animation but within the animation context (e.g., semi-transparent overlays, frame borders)
- **OVERLAY_LAYER**: For elements that should appear above everything, independent of the animation context (e.g., titles, subtitles, player controls, branding)

---

### 5.1 Root SVG Element

**REQUIRED Attributes**:
- `xmlns="http://www.w3.org/2000/svg"` (SVG namespace)
- `xmlns:xlink="http://www.w3.org/1999/xlink"` (XLink namespace for `<use>`)
- `viewBox="minX minY width height"` (viewport coordinates)

**RECOMMENDED Attributes**:
- `preserveAspectRatio` (aspect ratio handling, default: "xMidYMid meet")
- `version="1.1"` or `version="2.0"`
- `xml:space="default"` (whitespace handling)

**FORBIDDEN Attributes**:
- `onload`, `onclick`, or any event handler attributes

### 5.2 ANIMATION_BACKDROP Group

**Element**: `<g id="ANIMATION_BACKDROP">`

**Purpose**: Compositional container for the animation stage and its associated extension layers, providing controlled extensibility through three distinct z-order groups.

**Requirements**:
- MUST have `id="ANIMATION_BACKDROP"`
- MUST be direct child of root `<svg>` element
- MUST contain exactly three direct children in this order:
  1. `<g id="STAGE_BACKGROUND">`
  2. `<g id="ANIMATION_STAGE">`
  3. `<g id="STAGE_FOREGROUND">`

**Extensibility Architecture**:

The ANIMATION_BACKDROP provides **two internal extension points** with defined z-ordering relative to the animation content:

1. **STAGE_BACKGROUND** (first child) — renders **behind** animation frames
2. **STAGE_FOREGROUND** (third child) — renders **in front of** animation frames

This architecture enables safe, predictable customization while maintaining animation integrity.

**Example with Extension Layers**:
```xml
<g id="ANIMATION_BACKDROP">
  <!-- STAGE_BACKGROUND: Behind animation -->
  <g id="STAGE_BACKGROUND">
    <rect fill="#f0f0f0" width="800" height="600"/>
    <text x="10" y="590" font-size="12" fill="#999">Background watermark</text>
  </g>

  <!-- ANIMATION_STAGE: The frame animation (DO NOT MODIFY) -->
  <g id="ANIMATION_STAGE">
    <g id="ANIMATED_GROUP">
      <use id="PROSKENION" xlink:href="#FRAME00001">
        <animate attributeName="xlink:href" .../>
      </use>
    </g>
  </g>

  <!-- STAGE_FOREGROUND: In front of animation -->
  <g id="STAGE_FOREGROUND">
    <text x="400" y="30" text-anchor="middle" font-size="24" fill="rgba(255,255,255,0.8)">
      PREVIEW
    </text>
  </g>
</g>
```

**Z-Order Behavior**:
- STAGE_BACKGROUND content is visually **behind** all animation frames
- STAGE_FOREGROUND content is visually **in front of** all animation frames
- ANIMATION_STAGE content (frames) renders between the two extension layers

**Note**: The ANIMATION_STAGE element and its nested hierarchy (ANIMATED_GROUP → PROSKENION) MUST remain structurally intact and unmodified. The extension points (STAGE_BACKGROUND, STAGE_FOREGROUND) are the designated locations for all customization.

### 5.3 STAGE_BACKGROUND Group

**Element**: `<g id="STAGE_BACKGROUND">`

**Purpose**: Extension point for background elements that render **behind** the animation content.

**Requirements**:
- MUST have `id="STAGE_BACKGROUND"`
- MUST be first direct child of `ANIMATION_BACKDROP` group
- MAY be empty (default state for generated FBF.SVG documents)
- MAY contain arbitrary SVG content (added dynamically by players/applications)

**Use Cases**:
- Static background fills or patterns
- Watermarks positioned behind animation
- Contextual background imagery
- Brand elements that should not obscure animation content

**Z-Order**: Renders **behind** all animation frames (lowest visual layer within ANIMATION_BACKDROP)

### 5.4 ANIMATION_STAGE Group

**Element**: `<g id="ANIMATION_STAGE">`

**Purpose**: Core container for the animated frame sequence.

**Requirements**:
- MUST have `id="ANIMATION_STAGE"`
- MUST be second direct child of `ANIMATION_BACKDROP` group (between STAGE_BACKGROUND and STAGE_FOREGROUND)
- MUST contain exactly one child: `<g id="ANIMATED_GROUP">`

**Z-Order**: Renders **above** STAGE_BACKGROUND and **below** STAGE_FOREGROUND

### 5.5 STAGE_FOREGROUND Group

**Element**: `<g id="STAGE_FOREGROUND">`

**Purpose**: Extension point for foreground elements that render **in front of** the animation content.

**Requirements**:
- MUST have `id="STAGE_FOREGROUND"`
- MUST be third direct child of `ANIMATION_BACKDROP` group (after ANIMATION_STAGE)
- MAY be empty (default state for generated FBF.SVG documents)
- MAY contain arbitrary SVG content (added dynamically by players/applications)

**Use Cases**:
- Semi-transparent overlays (e.g., "PREVIEW" watermark)
- Frame borders or vignette effects
- Foreground UI elements that need to stay above animation
- Protective overlays for copyright/branding

**Z-Order**: Renders **in front of** all animation frames (highest visual layer within ANIMATION_BACKDROP)

### 5.6 OVERLAY_LAYER Group

**Element**: `<g id="OVERLAY_LAYER">`

**Purpose**: Top-level extension point for overlay elements that render **above** the entire ANIMATION_BACKDROP hierarchy.

**Requirements**:
- MUST have `id="OVERLAY_LAYER"`
- MUST be direct child of root `<svg>` element
- MUST appear after `ANIMATION_BACKDROP` and before `<defs>`
- MAY be empty (default state for generated FBF.SVG documents)
- MAY contain arbitrary SVG content (added dynamically by players/applications)

**Use Cases**:
- Global overlays (titles, badges, logos)
- Subtitle/caption text
- Picture-in-picture (PiP) auxiliary content
- Controls and UI chrome that must be above all animation content
- Floating elements (notifications, status indicators)

**Z-Order**: Renders **above** all content in ANIMATION_BACKDROP (including STAGE_FOREGROUND), providing the highest visual layer in the document

**Example**:
```xml
<g id="OVERLAY_LAYER">
  <!-- Title overlay -->
  <text x="400" y="50" text-anchor="middle" font-size="32" font-weight="bold"
        fill="white" stroke="black" stroke-width="1">
    Animation Title
  </text>

  <!-- Corner logo -->
  <image x="700" y="10" width="80" height="80"
         xlink:href="data:image/png;base64,..."/>
</g>
```

**Design Rationale**: OVERLAY_LAYER exists outside ANIMATION_BACKDROP to provide a compositionally independent layer that cannot be affected by transforms or styling applied to the backdrop hierarchy.

### 5.7 ANIMATED_GROUP Group

**Element**: `<g id="ANIMATED_GROUP">`

**Purpose**: Orchestrates the frame-by-frame animation timing.

**Requirements**:
- MUST have `id="ANIMATED_GROUP"`
- MUST be direct child of `ANIMATION_STAGE` group
- MUST contain exactly one child: `<use id="PROSKENION">`
- MAY have `cursor="pointer"` if interactive (click to start)

### 5.8 PROSKENION Use Element

**Element**: `<use id="PROSKENION" xlink:href="#FRAME001">`

**Purpose**: References the currently visible frame. Name derived from Greek theatrical term (προσκήνιον) for the stage area.

**Requirements**:
- MUST have `id="PROSKENION"`
- MUST be `<use>` element type
- MUST have `xlink:href` pointing to first frame (e.g., `"#FRAME001"`)
- MUST contain exactly one child: `<animate>` element
- MUST NOT have `x`, `y`, `width`, `height` attributes (uses referenced frame's coordinates)

### 5.9 Animate Element

**Element**: `<animate attributeName="xlink:href" values="..." dur="..." repeatCount="..."/>`

**Purpose**: SMIL animation that switches frames by updating `xlink:href` attribute.

**REQUIRED Attributes**:
- `attributeName="xlink:href"` (animates the reference target)
- `values="frame_id_list"` (semicolon-separated frame IDs, e.g., `"#FRAME001;#FRAME002;#FRAME003"`)
- `dur="Xs"` (total animation duration in seconds, e.g., `"2.5s"`)
- `repeatCount="count"` (number of repetitions: `"1"`, `"indefinite"`, or integer)

**OPTIONAL Attributes**:
- `begin="0s"` or `begin="click"` (start timing: immediately or on user click)
- `fill="freeze"` (maintain final frame after animation ends, default for `repeatCount="1"`)
- `fill="remove"` (return to initial state after animation, unusual for FBF.SVG)

**FORBIDDEN Attributes**:
- `keyTimes`, `keySplines`, `calcMode` (not needed for discrete frame switching)

### 5.10 Definitions Element

**Element**: `<defs>`

**Purpose**: Contains all reusable element definitions.

**Requirements**:
- MUST be direct child of root `<svg>` element
- MUST appear after `ANIMATION_BACKDROP` group
- MUST contain `<g id="SHARED_DEFINITIONS">` as first child
- MUST contain all frame groups (`FRAME001`, `FRAME002`, ...) as children

**Content Organization**:
1. `<g id="SHARED_DEFINITIONS">` — shared/deduplicated elements
2. `<g id="FRAME001">` — first frame content
3. `<g id="FRAME002">` — second frame content
4. ... (additional frames sequentially)

---

## 6. Element Restrictions

### 6.1 Allowed SVG Elements

FBF.SVG documents MAY contain the following SVG elements:

**Structural**: `<svg>`, `<g>`, `<defs>`, `<use>`, `<symbol>`

**Shapes**: `<rect>`, `<circle>`, `<ellipse>`, `<line>`, `<polyline>`, `<polygon>`, `<path>`

**Text**: `<text>`, `<tspan>`, `<textPath>`

**Gradients**: `<linearGradient>`, `<radialGradient>`, `<meshgradient>`, `<stop>`, `<meshpatch>`, `<meshrow>`

**Filters**: `<filter>`, `<feBlend>`, `<feColorMatrix>`, `<feGaussianBlur>`, etc. (all SVG 1.1 filter primitives)

**Clipping/Masking**: `<clipPath>`, `<mask>`

**Markers**: `<marker>`

**Patterns**: `<pattern>`

**Images**: `<image>` (with base64-encoded data URIs only)

**Metadata**: `<metadata>`, `<desc>`, `<title>`

**Animation**: `<animate>` (only as child of `PROSKENION`)

**Script** (conditional): `<script>` (only for approved mesh gradient polyfill)

### 6.2 Forbidden SVG Elements

The following elements MUST NOT appear in FBF.SVG documents:

**Interactive**: `<a>`, `<cursor>`

**Advanced Animation**: `<animateMotion>`, `<animateTransform>`, `<animateColor>`, `<set>`

**Declarative Animation**: `<discard>`

**Fonts**: `<font>`, `<glyph>`, `<missing-glyph>`, `<font-face>` (use embedded base64 fonts instead)

**Foreign Objects**: `<foreignObject>` (introduces HTML/CSS complexity)

**Multiple Animations**: Multiple `<animate>` elements on PROSKENION (only one allowed)

### 6.3 Script Restrictions

**General Rule**: `<script>` elements are **FORBIDDEN** in FBF.SVG documents.

**Exception**: Exactly **one** `<script>` element is permitted if and only if:

1. The FBF.SVG document contains `<meshgradient>` elements
2. The script contains the approved mesh gradient polyfill
3. The script appears as the last child of the root `<svg>` element
4. The script has `type="text/javascript"`
5. The script content matches the canonical polyfill hash (see Section 10.3)

**Rationale**: Mesh gradients are SVG 2.0 features with limited browser support. The polyfill enables cross-browser compatibility while maintaining security.

---

## 7. Attribute Requirements

### 7.1 ID Naming Conventions

All element IDs in FBF.SVG documents MUST follow these conventions:

**Reserved IDs** (REQUIRED):
- `ANIMATION_BACKDROP` — backdrop group (container for stage layers)
- `STAGE_BACKGROUND` — background extension point (renders behind animation)
- `ANIMATION_STAGE` — stage group (contains animation)
- `STAGE_FOREGROUND` — foreground extension point (renders in front of animation)
- `OVERLAY_LAYER` — overlay extension point (renders above all backdrop content)
- `ANIMATED_GROUP` — animation orchestration group
- `PROSKENION` — frame reference use element
- `SHARED_DEFINITIONS` — shared element container

**Frame IDs** (REQUIRED):
- `FRAMExxxxx` — where `xxxxx` is a zero-padded 5-digit integer (e.g., `FRAME00001`, `FRAME00023`)
- Frame IDs MUST be sequential starting from `FRAME00001`
- Frame IDs MUST match the order in the `<animate values="...">` attribute

**Shared Element IDs** (RECOMMENDED):
- Deduplicated elements SHOULD use descriptive IDs prefixed with `shared_` (e.g., `shared_gradient_sky_01`)

### 7.2 ViewBox Requirements

The root `<svg>` element MUST have a `viewBox` attribute with the format:

```
viewBox="minX minY width height"
```

**Requirements**:
- All four values MUST be present
- Values MAY be negative (e.g., for centered coordinates)
- `width` and `height` MUST be positive
- Values SHOULD be preserved from the first input frame to maintain aspect ratio

**Example**:
```xml
<svg viewBox="0 0 800 600">...</svg>
<svg viewBox="-100 -100 200 200">...</svg>  <!-- Centered coordinates -->
```

### 7.3 Namespace Requirements

**REQUIRED Namespaces**:
- `xmlns="http://www.w3.org/2000/svg"` (SVG namespace)
- `xmlns:xlink="http://www.w3.org/1999/xlink"` (XLink for `<use>` references)

**OPTIONAL Namespaces**:
- `xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"` (RDF metadata)
- `xmlns:dc="http://purl.org/dc/elements/1.1/"` (Dublin Core metadata)
- `xmlns:fbf="http://opentoonz.github.io/fbf/1.0#"` (FBF-specific metadata)

---

## 8. Animation Requirements

### 8.1 Frame Sequencing

**Mechanism**: FBF.SVG uses SMIL discrete animation to switch between frame groups.

**Implementation**:
1. All frames are defined as `<g id="FRAMExxxxx">` groups inside `<defs>`
2. The `PROSKENION` `<use>` element references the current frame via `xlink:href`
3. An `<animate>` element updates `xlink:href` to cycle through frames

**Values Attribute**:
```xml
<animate attributeName="xlink:href"
         values="#FRAME00001;#FRAME00002;#FRAME00003;#FRAME00004"
         dur="0.4s"
         repeatCount="indefinite"/>
```

**Timing**:
- `dur` (duration) MUST equal `frameCount / fps`
- Each frame is displayed for `dur / frameCount` seconds
- SMIL ensures accurate timing across all browsers

### 8.2 Animation Types

FBF.SVG supports eight animation types through different `repeatCount` and `values` configurations:

| Type | `repeatCount` | `values` Pattern | Behavior |
|------|---------------|------------------|----------|
| `once` | `"1"` | `#F1;#F2;...;#Fn` | Play forward once, freeze on last frame |
| `once_reversed` | `"1"` | `#Fn;...;#F2;#F1` | Play backward once, freeze on first frame |
| `loop` | `"indefinite"` | `#F1;#F2;...;#Fn` | Loop forward forever |
| `loop_reversed` | `"indefinite"` | `#Fn;...;#F2;#F1` | Loop backward forever |
| `pingpong_once` | `"1"` | `#F1;...;#Fn;...;#F1` | Forward then backward once |
| `pingpong_loop` | `"indefinite"` | `#F1;...;#Fn;...;#F1` | Ping-pong forever |
| `pingpong_once_reversed` | `"1"` | `#Fn;...;#F1;...;#Fn` | Backward then forward once |
| `pingpong_loop_reversed` | `"indefinite"` | `#Fn;...;#F1;...;#Fn` | Reverse ping-pong forever |

### 8.3 Interactive Animation

FBF.SVG supports **click-to-start** animation:

**Attributes**:
- `<animate begin="click" .../>` — animation starts on user click
- `<g id="ANIMATED_GROUP" cursor="pointer">` — visual cursor feedback

**Behavior**:
1. Animation is paused until user clicks the animation area
2. Click triggers `begin` event, starting SMIL animation
3. Further clicks have no effect (SMIL handles single begin)

**Accessibility**: Click-to-start SHOULD be documented in `<desc>` or `<title>` elements.

### 8.4 Frame Optimization

**Deduplication**:
- Elements appearing identically in multiple frames MUST be moved to `SHARED_DEFINITIONS`
- Frame groups MUST reference shared elements using `<use xlink:href="#shared_id"/>`

**Optimization Goal**: Minimize file size while maintaining animation fidelity.

---

## 9. Metadata Requirements

### 9.1 Metadata Element

FBF.SVG Full Conformance REQUIRES a `<metadata>` element containing RDF/XML metadata.

**Structure**:
```xml
<metadata>
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:fbf="http://opentoonz.github.io/fbf/1.0#">
    <rdf:Description rdf:about="">
      <!-- Dublin Core fields -->
      <dc:title>Animation Title</dc:title>
      <dc:creator>Creator Name</dc:creator>
      <dc:date>2025-01-07T12:00:00</dc:date>

      <!-- FBF-specific fields -->
      <fbf:frameCount>24</fbf:frameCount>
      <fbf:fps>12.0</fbf:fps>
      <fbf:duration>2.0</fbf:duration>
      <!-- ... additional metadata ... -->
    </rdf:Description>
  </rdf:RDF>
</metadata>
```

### 9.2 Required Metadata Fields (Full Conformance)

**Generator Information**:
- `fbf:generator` — Generator software name and version (e.g., "svg2fbf 0.1.2a4")
- `fbf:generatorVersion` — Generator version number
- `dc:date` — Generation date/time (ISO 8601 format)

**Animation Properties**:
- `fbf:frameCount` — Total number of frames (integer)
- `fbf:fps` — Frames per second (decimal)
- `fbf:duration` — Total animation duration in seconds (decimal)

**Authoring Information**:
- `dc:title` — Animation title
- `dc:creator` — Creator(s) name(s)

### 9.3 Optional Metadata Fields

See [FBF_METADATA_SPEC.md](FBF_METADATA_SPEC.md) for complete metadata schema (50+ fields).

---

## 10. Security Model

### 10.1 No External Resources

**Requirement**: FBF.SVG documents MUST NOT reference external resources at runtime.

**Prohibited**:
- `<image xlink:href="http://example.com/image.png"/>` — external URL
- `<use xlink:href="external.svg#element"/>` — external SVG fragment
- `@import url(...)` — external CSS
- External font URLs

**Allowed**:
- `<image xlink:href="data:image/png;base64,..."/>` — embedded base64 images
- Inline CSS in `<style>` elements (converted to attributes during generation)

**Rationale**: Prevents network dependencies, tracking, and timing attacks.

### 10.2 Content Security Policy

FBF.SVG documents SHOULD be served with strict Content Security Policy:

```
Content-Security-Policy:
  default-src 'none';
  img-src data:;
  style-src 'unsafe-inline';
  script-src 'unsafe-inline'
```

**Exceptions**:
- `script-src 'unsafe-inline'` only if mesh gradient polyfill present
- `style-src 'unsafe-inline'` if inline styles used (discouraged)

### 10.3 Mesh Gradient Polyfill Security

**Hash Validation**:

The approved mesh gradient polyfill MUST match this SHA-256 hash:
```
SHA256: [HASH_PLACEHOLDER - to be computed from canonical polyfill]
```

**Verification**:
- Validators MUST compute script hash and compare to canonical hash
- Mismatched scripts MUST fail validation
- This prevents injection of malicious JavaScript

**Polyfill Source**: The canonical polyfill is maintained at:
```
https://github.com/Emasoft/svg2fbf/blob/main/mesh_gradient_polyfill.js
```

---

## 11. Validation

### 11.1 Validation Levels

**XML Well-Formedness**:
- Document MUST be well-formed XML
- All elements MUST be properly nested and closed
- Attributes MUST be properly quoted

**SVG Validity**:
- Document MUST validate against SVG 1.1 or SVG 2.0 DTD
- All SVG elements and attributes MUST be valid per SVG spec

**FBF.SVG Basic Conformance**:
- Document MUST contain required structural elements (see Section 5)
- Document MUST use SMIL animation correctly (see Section 8)
- Document MUST NOT contain forbidden elements/attributes (see Section 6)

**FBF.SVG Full Conformance**:
- Document MUST pass Basic Conformance
- Document MUST contain RDF/XML metadata (see Section 9)
- Document MUST follow naming conventions (see Section 7.1)
- Document MUST validate against FBF.SVG XSD Schema (Appendix A)

### 11.2 Validation Tools

**Reference Validator**:

A Python-based validator is provided:
```bash
python validate_fbf.py input.fbf.svg
```

**Validation Outputs**:
- `VALID` — Document passes all checks
- `INVALID` — Document fails one or more checks (with error details)
- `WARNING` — Document is valid but has non-critical issues

See Section 11.3 for validator implementation.

### 11.3 Validator Implementation

The reference validator (`validate_fbf.py`) performs:

1. **XML Parsing** — Parse document with lxml
2. **SVG Validation** — Validate against SVG 1.1/2.0 schema
3. **XSD Validation** — Validate against FBF.SVG XSD schema (Appendix A)
4. **Structural Checks** — Verify required elements and IDs:
   - Presence of ANIMATION_BACKDROP, STAGE_BACKGROUND, ANIMATION_STAGE, STAGE_FOREGROUND, OVERLAY_LAYER
   - Correct nesting: STAGE_BACKGROUND, ANIMATION_STAGE, STAGE_FOREGROUND as children of ANIMATION_BACKDROP
   - Correct ordering: STAGE_BACKGROUND before ANIMATION_STAGE before STAGE_FOREGROUND
   - OVERLAY_LAYER positioned after ANIMATION_BACKDROP and before defs
5. **Attribute Checks** — Verify naming conventions and required attributes
6. **Security Checks** — Verify no external resources, script hash (if present)
7. **Metadata Validation** — Verify RDF/XML structure and required fields
8. **Animation Validation** — Verify SMIL timing and frame references

**Return Codes**:
- `0` — Valid FBF.SVG document
- `1` — Invalid structure
- `2` — Invalid metadata
- `3` — Security violation
- `4` — XML parsing error

---

## 12. DOM Interfaces

### 12.1 FBF Element Interfaces

FBF.SVG extends the standard SVG DOM with specialized interfaces for dynamic manipulation of the three extension points (STAGE_BACKGROUND, STAGE_FOREGROUND, OVERLAY_LAYER) and real-time frame streaming.

#### 12.1.1 FBFExtensionElement Interface

The **FBFExtensionElement** interface provides methods for safely appending custom elements to the three FBF.SVG extension points (STAGE_BACKGROUND, STAGE_FOREGROUND, OVERLAY_LAYER) without disrupting the animation hierarchy.

**IDL Definition**:

```webidl
interface FBFExtensionElement : SVGGElement {
  /**
   * Appends a custom SVG element to the specified extension layer.
   *
   * @param newElement The SVG element to append (e.g., <rect>, <image>, <g>)
   * @param layerId The target extension layer ID: "STAGE_BACKGROUND", "STAGE_FOREGROUND", or "OVERLAY_LAYER"
   * @returns The appended element
   * @throws DOMException NO_MODIFICATION_ALLOWED_ERR if layer is read-only
   * @throws DOMException HIERARCHY_REQUEST_ERR if newElement is not a valid SVG element
   * @throws DOMException NOT_FOUND_ERR if specified layer does not exist
   * @throws DOMException NOT_SUPPORTED_ERR if layerId is not a valid extension layer
   */
  SVGElement appendToLayer(in SVGElement newElement, in DOMString layerId)
    raises(DOMException);

  /**
   * Removes all custom elements from the specified extension layer.
   *
   * @param layerId The target extension layer ID
   * @throws DOMException NO_MODIFICATION_ALLOWED_ERR if layer is read-only
   * @throws DOMException NOT_FOUND_ERR if specified layer does not exist
   */
  void clearLayer(in DOMString layerId)
    raises(DOMException);

  /**
   * Returns the number of custom elements in the specified extension layer.
   *
   * @param layerId The target extension layer ID
   * @returns Count of custom elements in the layer
   * @throws DOMException NOT_FOUND_ERR if specified layer does not exist
   */
  unsigned long getLayerElementCount(in DOMString layerId)
    raises(DOMException);

  /**
   * Returns a reference to the specified extension layer element.
   *
   * @param layerId The target extension layer ID
   * @returns The layer element (SVGGElement)
   * @throws DOMException NOT_FOUND_ERR if specified layer does not exist
   */
  SVGGElement getLayer(in DOMString layerId)
    raises(DOMException);
};
```

**Valid Layer IDs**:
- `"STAGE_BACKGROUND"` — Background extension layer (renders behind animation)
- `"STAGE_FOREGROUND"` — Foreground extension layer (renders in front of animation)
- `"OVERLAY_LAYER"` — Overlay extension layer (renders above entire backdrop)

**Exception Handling**:

- **NO_MODIFICATION_ALLOWED_ERR** — Raised when attempting to modify a read-only layer
- **HIERARCHY_REQUEST_ERR** — Raised when `newElement` is not a valid SVG element or would create invalid nesting
- **NOT_FOUND_ERR** — Raised when the specified extension layer does not exist in the document
- **NOT_SUPPORTED_ERR** — Raised when `layerId` is not one of the valid extension layer IDs

**Implementation Notes**:

1. **Z-Order Preservation**: Elements are appended to the specified layer, maintaining the layer's position in the z-order hierarchy
2. **Element Validation**: Implementations MUST validate that `newElement` is a valid SVG element and does not contain forbidden elements (see Section 6)
3. **Animation Preservation**: The ANIMATION_STAGE and its nested hierarchy (ANIMATED_GROUP → PROSKENION) MUST remain intact and unmodified
4. **Security**: Implementations MUST reject elements containing external resource references (`xlink:href`, `href` to external URLs)

**Usage Example**:

```javascript
// Get the FBF document root
const fbfDoc = document.documentElement;

// Add background watermark (renders behind animation)
const bgWatermark = document.createElementNS('http://www.w3.org/2000/svg', 'text');
bgWatermark.setAttribute('x', '10');
bgWatermark.setAttribute('y', '590');
bgWatermark.setAttribute('font-size', '12');
bgWatermark.setAttribute('fill', '#999');
bgWatermark.textContent = '© 2025 MyBrand';
fbfDoc.appendToLayer(bgWatermark, 'STAGE_BACKGROUND');

// Add foreground "PREVIEW" overlay (renders in front of animation)
const previewText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
previewText.setAttribute('x', '400');
previewText.setAttribute('y', '300');
previewText.setAttribute('text-anchor', 'middle');
previewText.setAttribute('font-size', '48');
previewText.setAttribute('fill', 'rgba(255,0,0,0.3)');
previewText.textContent = 'PREVIEW';
fbfDoc.appendToLayer(previewText, 'STAGE_FOREGROUND');

// Add title overlay (renders above everything)
const titleText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
titleText.setAttribute('x', '400');
titleText.setAttribute('y', '50');
titleText.setAttribute('text-anchor', 'middle');
titleText.setAttribute('font-size', '32');
titleText.setAttribute('fill', 'white');
titleText.setAttribute('stroke', 'black');
titleText.setAttribute('stroke-width', '1');
titleText.textContent = 'Animation Title';
fbfDoc.appendToLayer(titleText, 'OVERLAY_LAYER');
```

#### 12.1.2 FBFStreamingElement Interface

The **FBFStreamingElement** interface provides methods for dynamic frame addition during real-time streaming playback (see Section 13).

**IDL Definition**:

```webidl
interface FBFStreamingElement : SVGDefsElement {
  /**
   * Appends a new frame definition to the <defs> element and updates
   * the SMIL animation sequence to include the new frame.
   *
   * @param frameElement The <g> element containing the frame definition
   * @param frameId The sequential frame ID (e.g., "FRAME00042")
   * @returns The appended frame element
   * @throws DOMException INVALID_STATE_ERR if frameId is not sequential
   * @throws DOMException HIERARCHY_REQUEST_ERR if frameElement is invalid
   */
  SVGGElement appendStreamingFrame(in SVGGElement frameElement, in DOMString frameId)
    raises(DOMException);

  /**
   * Returns the next expected frame ID in the sequence.
   *
   * @returns Next frame ID (e.g., "FRAME00042")
   */
  DOMString getNextFrameId();

  /**
   * Returns the total number of frames currently in the document.
   *
   * @returns Frame count
   */
  readonly attribute unsigned long currentFrameCount;
};
```

**Exception Handling**:

- **INVALID_STATE_ERR** — Raised when `frameId` is not the next sequential frame (e.g., skipping from FRAME00041 to FRAME00043)
- **HIERARCHY_REQUEST_ERR** — Raised when `frameElement` does not conform to FBF frame structure requirements

**Implementation Notes**:

1. **Sequential IDs**: Frame IDs MUST be sequential (FRAME00001, FRAME00002, etc.) without gaps
2. **SMIL Update**: Implementations MUST update the `<animate>` element's `values` attribute to include the new frame reference
3. **Non-Blocking**: Frame addition SHOULD NOT interrupt or restart playback of existing frames
4. **Memory Management**: Implementations MAY implement timed fragmentation (see Section 13.2) to limit memory usage

### 12.2 Accessing FBF Interfaces

FBF-certified players and web applications access these interfaces through standard DOM methods:

```javascript
// Access extension layer interfaces
const stageBackground = document.getElementById('STAGE_BACKGROUND');
const stageForeground = document.getElementById('STAGE_FOREGROUND');
const overlayLayer = document.getElementById('OVERLAY_LAYER');

// Check for FBF extension interface support
const fbfDoc = document.documentElement;
if (fbfDoc && fbfDoc.appendToLayer) {
  // FBF extension interface available
  fbfDoc.appendToLayer(customElement, 'STAGE_BACKGROUND');
}

// Access streaming interface
const defs = document.querySelector('defs');
if (defs && defs.appendStreamingFrame) {
  // Streaming interface available
}
```

**Feature Detection**:

Applications SHOULD test for FBF interface availability before attempting to use FBF-specific methods.

---

## 13. Streaming Capabilities

### 13.1 Design Rationale: Frames at End

The FBF.SVG format places all frame definitions (`<g id="FRAME00001">`, `<g id="FRAME00002">`, etc.) **at the end of the document** within the `<defs>` element. This structural decision enables **unlimited streaming** of FBF animations.

**Benefits**:

1. **Progressive Rendering**: Players can parse and display the document structure (backdrop, stage, initial frames) before all frames arrive
2. **Real-Time Frame Addition**: New frames can be appended dynamically without requiring document reconstruction
3. **Memory Efficiency**: Players can implement timed fragmentation to discard frames no longer needed for playback
4. **Network Optimization**: Streaming servers can generate and transmit frames incrementally as they become available

**Structural Requirements**:

- **Fixed Header**: The document structure (metadata, backdrop, stage, defs/SHARED_DEFINITIONS) is transmitted first and remains constant
- **Append-Only Frames**: New frames are appended to the end of `<defs>` in sequential order
- **SMIL Update**: The `<animate>` element's `values` attribute is updated incrementally to reference new frames

### 13.2 Real-Time Streaming Use Cases

FBF.SVG's streaming architecture supports diverse real-time animation scenarios:

#### 13.2.1 Live Presentation Streaming

**Scenario**: Real-time conversion of presentation slides or whiteboard content to vector animation.

**Implementation**:
- Server captures presentation frames (e.g., from screen sharing, digital whiteboard)
- Each frame is vectorized and transmitted as a new FBF frame definition
- Client player appends frames dynamically and updates the animation timeline
- Viewer experiences smooth playback with minimal latency

**Advantages**:
- Vector format ensures crisp rendering at any zoom level
- Small file sizes compared to video streaming
- Seekable timeline with frame-accurate positioning

#### 13.2.2 LLM-Generated 2D Avatars

**Scenario**: AI-driven character animation where poses/expressions are generated on-demand by a language model.

**Implementation**:
- LLM generates SVG representations of character poses based on dialogue/context
- Each generated pose becomes a new FBF frame
- Client player smoothly transitions between poses using SMIL timing
- Avatar responds dynamically to user interaction or conversation flow

**Advantages**:
- Infinite animation variety without pre-rendering
- Lightweight vector representation enables real-time generation
- Declarative SMIL timing handles smooth transitions

#### 13.2.3 Vector GUI Streaming

**Scenario**: Remote desktop or application streaming using vector graphics instead of pixel-based video.

**Implementation**:
- Server captures GUI state changes and renders them as SVG frames
- Each GUI update (window movement, button clicks, text input) becomes a new frame
- Client reconstructs GUI state from vector frames with perfect clarity
- Interactive elements can be overlaid on the streamed content

**Advantages**:
- Resolution-independent rendering (scales to any display)
- Smaller bandwidth than raster video for GUI content
- Text remains selectable and searchable

#### 13.2.4 AI Roleplay Visual Feedback

**Scenario**: Interactive storytelling where AI generates scene illustrations matching the narrative.

**Implementation**:
- User interacts with AI characters in text-based roleplay
- AI generates SVG illustrations of scenes, character poses, locations
- Each narrative beat triggers generation of a new visual frame
- Player displays frames synchronized with dialogue/narration

**Advantages**:
- Visual feedback enhances immersion without pre-created assets
- SVG format allows stylistic consistency via shared definitions
- Lightweight enough for mobile/web deployment

### 13.3 Streaming Protocol

**Frame Transmission**:

1. **Initial Document**: Client receives FBF header (metadata, backdrop, defs/SHARED_DEFINITIONS, initial frames)
2. **Progressive Frames**: Server transmits additional frames as XML fragments:
   ```xml
   <g id="FRAME00042">
     <!-- Frame content -->
   </g>
   ```
3. **DOM Appending**: Client appends frame to `<defs>` using `appendStreamingFrame()` (Section 12.1.2)
4. **SMIL Update**: Client updates `<animate values="...">` to include new frame reference
5. **Playback Continuation**: Animation continues seamlessly without interruption

**Synchronization**:

- **Sequential IDs**: Frame IDs MUST increment sequentially (FRAME00001, FRAME00002, etc.)
- **No Gaps**: Players MUST reject frames with non-sequential IDs
- **Buffering**: Players SHOULD buffer incoming frames to handle network jitter

### 13.4 Memory Management: Timed Fragmentation

**Inspiration**: Concolato et al. (2007) demonstrated techniques for controlling memory usage during SVG animation playback by fragmenting documents and discarding frames no longer needed.

**Application to FBF Streaming**:

1. **Sliding Window**: Players MAY maintain a fixed-size buffer of active frames (e.g., 100 frames)
2. **Frame Eviction**: When buffer is full, player removes oldest frames from DOM
3. **Seek Limitations**: Evicted frames cannot be replayed without re-fetching from server
4. **Configurable**: Buffer size can be adjusted based on device capabilities

**Implementation**:

```javascript
// Pseudo-code for timed fragmentation
class FBFStreamingPlayer {
  constructor(maxBufferFrames = 100) {
    this.maxBufferFrames = maxBufferFrames;
    this.activeFrames = [];
  }

  appendFrame(frameElement, frameId) {
    // Add frame to DOM
    this.defs.appendChild(frameElement);
    this.activeFrames.push({ id: frameId, element: frameElement });

    // Evict oldest frame if buffer full
    if (this.activeFrames.length > this.maxBufferFrames) {
      const oldest = this.activeFrames.shift();
      this.defs.removeChild(oldest.element);
    }

    // Update SMIL animation
    this.updateAnimationValues();
  }
}
```

**Trade-offs**:
- **Memory Efficiency**: Limits memory growth for long-running streams
- **Seek Constraints**: Cannot seek to evicted frames without re-buffering
- **Latency**: May require server round-trip to replay earlier content

### 13.5 Streaming Conformance

**FBF Streaming-Compliant Player Requirements**:

1. **Progressive Parsing**: MUST support parsing and rendering FBF documents before all frames arrive
2. **Dynamic Frame Addition**: MUST implement `appendStreamingFrame()` interface (Section 12.1.2)
3. **Sequential Validation**: MUST reject non-sequential frame IDs
4. **Non-Blocking Append**: Frame addition MUST NOT interrupt ongoing playback
5. **SMIL Update**: MUST update animation timeline when new frames added

**Optional Features**:
- Timed fragmentation for memory control
- Server-side frame generation APIs
- Bidirectional streaming (client → server feedback)

---

## 14. Interactive Visual Communication Protocol

### 14.1 Concept Overview

FBF.SVG enables a fundamentally new paradigm for human-AI interaction: **direct visual communication**. Rather than limiting AI models (particularly Large Language Models) to text-based output with occasional static image generation, FBF.SVG streaming allows AI models to communicate through **dynamically generated, interactive visual interfaces**.

**Traditional AI Communication**:
```
User: "How do I configure this motherboard jumper?"
LLM: "The CPU voltage jumper (JP5) should be set to pins 2-3 for 3.3V operation..."
```

**FBF.SVG Visual Communication**:
```
User: "How do I configure this motherboard jumper?"
LLM: [Generates FBF frame showing motherboard diagram with JP5 highlighted,
      voltage options color-coded, current position marked with red circle,
      target position marked with green arrow]
User: [Touches green arrow region]
LLM: [Generates next frame showing detailed close-up of jumper pins,
      with step-by-step visual sequence]
```

**Paradigm Shift**:

Traditional approaches require the AI to either:
1. **Describe verbally** — Limited by language precision, user's spatial reasoning
2. **Search for existing diagrams** — Dependent on external resources, may not match user's specific context
3. **Generate static images** — No interactivity, no real-time adaptation

FBF.SVG enables:
1. **Direct visual expression** — AI generates exactly what it wants to show
2. **Context-aware visualization** — Tailored to current conversation, user's device, interaction history
3. **Bidirectional visual interaction** — User responds through visual selection, AI adapts immediately

### 14.2 Architectural Model

#### 14.2.1 Bidirectional Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM (Server-Side)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Process user input (text + coordinates + selections) │  │
│  │  2. Determine visual response strategy                   │  │
│  │  3. Generate SVG frame content                           │  │
│  │  4. Stream frame to client                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────┬──────────────────┬──────────────────┘
                            │ SVG Frames       │ User Actions
                            ↓                  ↑
┌─────────────────────────────────────────────────────────────────┐
│                    FBF Player (Client-Side)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  1. Receive and append SVG frames                        │  │
│  │  2. Render current frame                                 │  │
│  │  3. Capture user interactions (click, touch, gestures)   │  │
│  │  4. Translate to SVG coordinates + element IDs           │  │
│  │  5. Send interaction data to LLM                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 14.2.2 Communication Layers

**Visual Output Layer** (LLM → User):
- **Frame Generation**: LLM outputs SVG frame definitions in real-time
- **Progressive Rendering**: Client displays frames as they arrive
- **Visual Semantics**: Shapes, colors, positions, text all chosen contextually by LLM

**Interactive Input Layer** (User → LLM):
- **Coordinate Capture**: Click/touch events translated to SVG coordinate space
- **Element Identification**: Clicked SVG elements reported by ID or class
- **Gesture Recognition**: Multi-touch, drag, pinch gestures mapped to SVG regions
- **Semantic Feedback**: Client sends structured data about user's visual selections

### 14.3 Advantages Over Traditional Approaches

#### 14.3.1 vs. Traditional Fixed GUIs

**Traditional GUI Limitations**:
- **Static Structure**: Buttons, menus, forms predefined at design time
- **Context-Blind**: Same interface for all users, all scenarios
- **Limited Adaptability**: Requires programming to change UI flow
- **One-Size-Fits-All**: Cannot optimize for current task or user expertise level

**FBF.SVG Dynamic GUI**:
- **Generative Structure**: LLM creates UI elements on-demand for current context
- **Context-Aware**: Interface adapts to conversation topic, user preferences, device capabilities
- **Infinite Flexibility**: LLM can show anything relevant without pre-programmed constraints
- **Personalized Interaction**: UI complexity/verbosity adjusts to user's demonstrated understanding

**Example**: User asks "Show me healthy meal options"

*Traditional GUI*: Fixed list with checkboxes, filter dropdowns (requires pre-coding all options, layouts, filter logic)

*FBF.SVG*: LLM generates visual menu showing meal images, color-coded by dietary restrictions (vegan=green border, gluten-free=blue badge), arranged by user's typical preferences (breakfast items at top if morning), with visual allergen indicators

#### 14.3.2 vs. Web Artifacts (Anthropic's Current Approach)

**Web Artifact Limitations**:
- **Requires Programming**: LLM must generate HTML/CSS/JavaScript code
- **Code Execution Overhead**: Browser must parse, compile, execute JavaScript
- **Security Constraints**: Sandboxing, CSP policies limit functionality
- **Debugging Complexity**: Generated code may have bugs, require iteration
- **Library Dependencies**: Complex UIs require frameworks (React, etc.), increasing generation complexity

**FBF.SVG Direct Visualization**:
- **No Programming**: LLM outputs pure SVG shapes, text, paths — declarative, not imperative
- **Instant Rendering**: Browser renders SVG natively without compilation
- **Inherently Secure**: No script execution (except optional polyfill), no XSS risks
- **Zero Dependencies**: Self-contained, no external libraries needed
- **Guaranteed Correctness**: SVG has well-defined semantics, harder to "break" than JavaScript

**Example**: User asks "Show me a timeline of historical events"

*Web Artifact Approach*:
```javascript
// LLM must generate JavaScript code:
const events = [{date: "1776", label: "US Independence"}, ...];
const svg = d3.select("#timeline")
  .append("svg")
  .attr("width", 800);
// ... 50+ lines of D3.js code for axis, scales, event markers ...
```
Risks: D3.js syntax errors, scale miscalculations, DOM manipulation bugs

*FBF.SVG Approach*:
```xml
<!-- LLM generates SVG directly: -->
<g id="FRAME00001">
  <line x1="50" y1="300" x2="750" y2="300" stroke="black" stroke-width="2"/>
  <circle cx="150" cy="300" r="8" fill="red"/>
  <text x="150" y="330" text-anchor="middle" font-size="12">1776</text>
  <text x="150" y="345" text-anchor="middle" font-size="10">US Independence</text>
  <!-- ... more events ... -->
</g>
```
Deterministic, declarative, impossible to have runtime errors

#### 14.3.3 vs. Static Image Generation

**Static Image Limitations**:
- **No Interactivity**: User cannot click, select, or interact with content
- **Raster Format**: Pixelated at high zoom, large file sizes
- **No Semantic Structure**: Image is opaque bitmap, cannot query "what is at coordinate X,Y?"
- **Single Frame**: Requires regenerating entire image to show updates

**FBF.SVG Advantages**:
- **Fully Interactive**: Every shape is a DOM element with ID, can be clicked/touched
- **Vector Scalability**: Infinite zoom without quality loss
- **Semantic Richness**: Each element has meaning, LLM can reference by ID
- **Incremental Updates**: New frames show changes, no need to redraw everything

### 14.4 Technical Capabilities

#### 14.4.1 Visual Expression Modalities

FBF.SVG enables LLMs to express information through multiple visual channels:

**1. Spatial Arrangement**:
- **Hierarchies**: Tree structures, org charts, file systems
- **Sequences**: Timelines, process flows, step-by-step instructions
- **Relationships**: Network diagrams, mind maps, connection graphs
- **Comparisons**: Side-by-side layouts, before/after views

**2. Color Coding**:
- **Categorical**: Different colors for different classes (file types, risk levels, user roles)
- **Gradient**: Continuous scales (temperature, priority, confidence)
- **Semantic**: Red=danger/error, green=success/safe, yellow=warning, blue=information

**3. Shape Vocabulary**:
- **Icons**: Circles for items, rectangles for containers, arrows for flow
- **Annotations**: Highlight regions (colored rectangles), callout lines, emphasis markers
- **Symbols**: Check marks for completion, X for errors, question marks for unclear items

**4. Text Integration**:
- **Labels**: Identify components, name options
- **Instructions**: Short textual guidance embedded in visual context
- **Annotations**: Explain why certain visual elements are highlighted

**5. Animation/Transitions**:
- **Progressive Disclosure**: Show steps sequentially in separate frames
- **State Changes**: Highlight what changed between frames
- **Focus Direction**: Guide user's attention through visual sequence

#### 14.4.2 User Input Modalities

**1. Point Selection**:
- **Click/Touch Coordinates**: User taps screen, client sends `{x: 245, y: 387}` to LLM
- **Element Identification**: Client resolves coordinates to SVG element ID, sends `{elementId: "option_3"}`
- **Semantic Context**: LLM knows user selected "option_3", responds accordingly

**2. Region Selection**:
- **Bounding Box**: User drags to select multiple elements, client sends `{x1: 100, y1: 200, x2: 300, y2: 400}`
- **Multi-Select**: Client identifies all elements within box, sends list of IDs
- **Lasso Selection**: Free-form polygon selection for irregular regions

**3. Gesture Input**:
- **Swipe**: Left/right swipes for navigation (previous/next frame requests)
- **Pinch/Zoom**: Client sends viewport scale, LLM can generate detail/overview frames
- **Long Press**: Context menu or additional information request

**4. Structured Feedback**:
```json
{
  "action": "select",
  "elementId": "jumper_pin_2",
  "coordinates": {"x": 340, "y": 215},
  "timestamp": "2025-11-08T14:32:15Z",
  "viewport": {"width": 800, "height": 600, "scale": 1.5}
}
```

#### 14.4.3 State Management

**Client-Side State**:
- **Current Frame Index**: Which frame is being displayed
- **Interaction History**: Log of user's selections/actions
- **Viewport State**: Zoom level, pan position
- **Selection State**: Currently highlighted/selected elements

**Server-Side State** (LLM maintains):
- **Conversation Context**: What has been discussed, shown, selected
- **Visual History**: What frames were generated, what user interacted with
- **User Model**: Inferred expertise level, preferences, accessibility needs
- **Task State**: Progress through multi-step procedure, completion status

**Synchronization**:
- Client sends state updates with each interaction
- LLM uses state to generate contextually appropriate next frame
- No server-side DOM manipulation needed (unlike web apps)

### 14.5 Use Case Categories

#### 14.5.1 Instructional Visualization

**Problem**: Complex procedures require visual demonstration, verbal descriptions are insufficient

**Examples**:

**Equipment Repair**:
- User: "How do I replace the capacitor C17 on this board?"
- LLM: [Generates frame showing board layout, C17 highlighted in red, neighboring components labeled, safety warnings color-coded]
- User: [Touches C17]
- LLM: [Generates close-up frame showing desoldering technique, temperature recommendations, polarity indicators]

**Software Configuration**:
- User: "Help me set up dual monitors"
- LLM: [Generates frame showing monitor icons, cable types color-coded, port positions marked]
- User: [Touches HDMI cable icon]
- LLM: [Generates frame showing HDMI port locations on computer, correct orientation illustrated]

**Medical/Lab Procedures**:
- User: "How do I read this urinalysis test strip?"
- LLM: [Generates frame showing color chart, current strip colors, matches highlighted, interpretation text for abnormal values]
- User: [Touches glucose pad area]
- LLM: [Generates detailed frame explaining glucose level interpretation, causes of elevation, when to seek medical advice]

#### 14.5.2 Interactive Selection Interfaces

**Problem**: Users need to choose from options that are better shown than described

**Examples**:

**Visual Catalogs**:
- User: "Show me available wallpapers"
- LLM: [Generates grid of wallpaper thumbnails, each as SVG element with unique ID]
- User: [Touches wallpaper_07]
- LLM: [Generates full-screen preview with download button]

**Menu Systems**:
- User: "What vegetarian options do you have?"
- LLM: [Generates visual menu with dish photos (as embedded data URIs), prices, dietary icons, allergen indicators]
- User: [Touches "tofu_curry" element]
- LLM: [Generates detailed view with ingredients, nutrition info, customization options as interactive buttons]

**File/Document Browsers**:
- User: "Show me my recent scans"
- LLM: [Generates thumbnail grid of scanned documents, date/time stamps, file size indicators]
- User: [Touches document_5]
- LLM: [Generates full document preview with OCR text overlay, export options]

#### 14.5.3 Technical and Scientific Visualization

**Problem**: Color, shape, spatial relationships are essential for correct interpretation

**Examples**:

**Circuit Analysis**:
- User: "Is this circuit correct?"
- LLM: [Generates schematic with voltage levels color-coded (green=within spec, red=overvoltage), current flow arrows, potential short circuits highlighted]
- User: [Touches red node]
- LLM: [Generates explanation of why voltage is incorrect, suggested component value changes visualized]

**Chemical Structures**:
- User: "Show me the mechanism for this reaction"
- LLM: [Generates molecular structures with electron movement arrows, bond breaking/forming visualized in sequence across multiple frames]

**Data Analysis**:
- User: "Visualize this dataset's outliers"
- LLM: [Generates scatter plot with outliers in red, clusters color-coded, statistical boundaries shown as dashed lines]
- User: [Touches outlier point]
- LLM: [Generates detail view showing that data point's attributes, why it's anomalous]

#### 14.5.4 Contextual Adaptive Interfaces

**Problem**: Different contexts require different UI structures, traditional GUIs cannot adapt in real-time

**Examples**:

**Expertise Adaptation**:
- Novice user: LLM generates simplified UI with icons, tooltips, step-by-step wizard
- Expert user: LLM generates compact UI with technical shortcuts, advanced options visible

**Device Adaptation**:
- Mobile (small screen): LLM generates vertical layout, large touch targets, swipe navigation
- Desktop (large screen): LLM generates multi-column layout, hover tooltips, keyboard shortcuts indicated

**Task Adaptation**:
- Quick lookup: LLM generates single frame with answer, minimal navigation
- Complex configuration: LLM generates multi-step visual wizard, progress indicator, back/forward navigation

### 14.6 Protocol Specification

#### 14.6.1 Frame Generation Messages (LLM → Client)

**Format**: FBF.SVG frame definition with interaction metadata

```xml
<g id="FRAME00042" data-interactive="true" data-context="menu_selection">
  <!-- Visual content -->
  <rect id="option_1" x="50" y="100" width="200" height="60" fill="#4CAF50"
        class="selectable" data-action="select_item" data-value="vegetarian_bowl"/>
  <text x="150" y="135" text-anchor="middle" fill="white">Vegetarian Bowl</text>

  <rect id="option_2" x="50" y="180" width="200" height="60" fill="#2196F3"
        class="selectable" data-action="select_item" data-value="tofu_curry"/>
  <text x="150" y="215" text-anchor="middle" fill="white">Tofu Curry</text>

  <!-- Metadata for client -->
  <metadata>
    <fbf:interactive xmlns:fbf="http://opentoonz.github.io/fbf/1.0#">
      <fbf:selectableElements>option_1,option_2</fbf:selectableElements>
      <fbf:defaultAction>select_item</fbf:defaultAction>
    </fbf:interactive>
  </metadata>
</g>
```

**Key Attributes**:
- `data-interactive="true"` — Frame accepts user input
- `class="selectable"` — Element can be clicked/touched
- `data-action` — What action this element represents
- `data-value` — Semantic value to send to LLM on selection

#### 14.6.2 User Input Messages (Client → LLM)

**Selection Event**:
```json
{
  "type": "element_select",
  "frameId": "FRAME00042",
  "elementId": "option_1",
  "coordinates": {"x": 150, "y": 130},
  "action": "select_item",
  "value": "vegetarian_bowl",
  "timestamp": "2025-11-08T14:35:22Z"
}
```

**Coordinate Event** (when element not identified):
```json
{
  "type": "coordinate_select",
  "frameId": "FRAME00042",
  "coordinates": {"x": 385, "y": 271},
  "timestamp": "2025-11-08T14:35:22Z"
}
```

**Gesture Event**:
```json
{
  "type": "gesture",
  "gestureType": "swipe_right",
  "frameId": "FRAME00042",
  "startCoordinates": {"x": 100, "y": 300},
  "endCoordinates": {"x": 400, "y": 300},
  "velocity": 850,
  "timestamp": "2025-11-08T14:35:22Z"
}
```

#### 14.6.3 Session Protocol

**1. Initialization**:
```
Client → LLM: Session start request with capabilities
LLM → Client: Initial FBF document (header + ANIMATION_BACKDROP + initial frames)
```

**2. Interaction Loop**:
```
Client: Display current frame, monitor for user input
User: Interacts (click/touch/gesture)
Client → LLM: Interaction message
LLM: Process interaction, generate response
LLM → Client: New frame(s)
Client: Append frame(s), update animation timeline
[Repeat]
```

**3. State Synchronization**:
- Client sends viewport state, interaction history with each message
- LLM maintains conversation context, visual history
- No server-side rendering needed (unlike web apps)

### 14.7 Implementation Requirements

#### 14.7.1 LLM Training Requirements

For effective FBF.SVG visual communication, LLMs should be trained to:

1. **SVG Syntax Proficiency**: Generate valid, efficient SVG markup
2. **Visual Design Principles**: Understand color theory, layout, typography, information hierarchy
3. **Coordinate Geometry**: Calculate positions, sizes, alignments for visual elements
4. **Interactive Design Patterns**: Know common UI patterns (buttons, menus, forms) and when to use them
5. **Context-Aware Generation**: Adapt visual output to conversation context, user actions, device constraints
6. **Accessibility**: Generate SVG with proper ARIA labels, sufficient contrast, readable text sizes

**Training Data**:
- Pairs of (conversational context, appropriate FBF.SVG frame)
- Examples of user interactions mapped to visual responses
- Multi-turn visual conversations showing progressive refinement

#### 14.7.2 Client Implementation Requirements

FBF.SVG visual communication clients MUST implement:

1. **Coordinate Translation**: Map screen coordinates to SVG coordinate space (accounting for viewport, zoom)
2. **Element Hit Detection**: Determine which SVG element was clicked/touched at given coordinates
3. **Event Serialization**: Convert DOM events to structured JSON messages for LLM
4. **Frame Buffering**: Smooth playback during streaming frame arrival
5. **Accessibility Features**: Screen reader support, keyboard navigation, alternative input methods

**Optional Features**:
- Gesture recognition (swipe, pinch, rotate)
- Haptic feedback on element selection
- Voice input integration ("tap the red button")
- Multi-modal interaction (voice + visual simultaneously)

### 14.8 Security and Privacy Considerations

#### 14.8.1 Input Validation

Clients MUST validate user input before sending to LLM:
- Sanitize coordinate values (prevent injection of extreme values)
- Verify element IDs match current frame (prevent spoofing)
- Rate-limit interaction messages (prevent flooding)

#### 14.8.2 Content Security

LLMs MUST NOT generate FBF frames containing:
- External resource references (prevent phishing, tracking)
- Embedded scripts (except approved polyfill)
- Sensitive information in element IDs/attributes (could leak in logs)

#### 14.8.3 Privacy Protection

Coordinate-based input reveals user interaction patterns:
- Clients SHOULD allow disabling coordinate precision (send only element IDs, not exact coordinates)
- Interaction logs MUST be encrypted in transit
- LLM providers SHOULD allow users to disable interaction logging

### 14.9 Future Extensions

**Multi-User Collaboration**:
- Multiple users interacting with same FBF.SVG stream
- Real-time cursor positions visible to all participants
- LLM generates frames showing collaborative annotations

**Augmented Reality Integration**:
- FBF.SVG overlays on camera feed
- Interactive annotations on physical objects
- Real-world coordinate mapping to SVG elements

**Haptic and Audio Feedback**:
- Tactile responses to button presses (vibration patterns)
- Spatial audio cues for element locations (accessibility)
- Sound effects synchronized with visual transitions

**Bidirectional Drawing**:
- User sketches on frame, LLM receives path data
- LLM interprets sketches, generates refined SVG
- Collaborative diagram creation

---

## 15. References

### 15.1 Normative References

- **SVG 1.1** - Scalable Vector Graphics (SVG) 1.1 (Second Edition)
  https://www.w3.org/TR/SVG11/

- **SVG 2.0** - Scalable Vector Graphics (SVG) 2
  https://www.w3.org/TR/SVG2/

- **SMIL** - Synchronized Multimedia Integration Language (SMIL 3.0)
  https://www.w3.org/TR/SMIL3/

- **RDF** - Resource Description Framework (RDF): Concepts and Abstract Syntax
  https://www.w3.org/TR/rdf-concepts/

- **Dublin Core** - Dublin Core Metadata Element Set, Version 1.1
  https://www.dublincore.org/specifications/dublin-core/dces/

- **XML Schema** - XML Schema Part 1: Structures (Second Edition)
  https://www.w3.org/TR/xmlschema-1/

### 15.2 Informative References

- **SVG Tiny 1.2** - Scalable Vector Graphics (SVG) Tiny 1.2 Specification
  https://www.w3.org/TR/SVGTiny12/

- **CSP** - Content Security Policy Level 3
  https://www.w3.org/TR/CSP3/

- **OpenToonz** - OpenToonz Animation Software
  https://opentoonz.github.io

- **Concolato et al. (2007)** - Timed-fragmentation of SVG documents to control the playback memory usage
  In Proceedings of the 2007 ACM symposium on Document engineering (pp. 121-124)
  https://dl.acm.org/doi/abs/10.1145/1284420.1284453

  *Foundational research that inspired FBF.SVG's streaming architecture and memory management approach (see Section 13.4)*

---

## Appendix A: FBF.SVG Schema

See [fbf-svg.xsd](fbf-svg.xsd) for the complete XSD schema definition.

---

## Appendix B: Example FBF.SVG Document

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     viewBox="0 0 800 600"
     preserveAspectRatio="xMidYMid meet">

  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/"
             xmlns:fbf="http://opentoonz.github.io/fbf/1.0#">
      <rdf:Description rdf:about="">
        <dc:title>Example Animation</dc:title>
        <dc:creator>Example Creator</dc:creator>
        <fbf:frameCount>3</fbf:frameCount>
        <fbf:fps>12.0</fbf:fps>
        <fbf:duration>0.25</fbf:duration>
        <fbf:generator>svg2fbf 0.1.2a4</fbf:generator>
      </rdf:Description>
    </rdf:RDF>
  </metadata>

  <desc>
    FBF.SVG Format - Frame-by-Frame SVG Animation
    Specification: https://github.com/Emasoft/svg2fbf/docs/FBF_SVG_SPECIFICATION.md
  </desc>

  <g id="ANIMATION_BACKDROP">
    <g id="STAGE_BACKGROUND">
      <rect fill="#ffffff" width="800" height="600"/>
    </g>
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" xlink:href="#FRAME00001">
          <animate attributeName="xlink:href"
                   values="#FRAME00001;#FRAME00002;#FRAME00003"
                   dur="0.25s"
                   repeatCount="indefinite"/>
        </use>
      </g>
    </g>
    <g id="STAGE_FOREGROUND">
      <!-- Empty: available for foreground overlays -->
    </g>
  </g>

  <g id="OVERLAY_LAYER">
    <!-- Empty: available for top-level overlays -->
  </g>

  <defs>
    <g id="SHARED_DEFINITIONS">
      <linearGradient id="shared_gradient_01" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#ff0000"/>
        <stop offset="100%" stop-color="#0000ff"/>
      </linearGradient>
    </g>

    <g id="FRAME00001">
      <circle cx="100" cy="300" r="50" fill="url(#shared_gradient_01)"/>
    </g>

    <g id="FRAME00002">
      <circle cx="400" cy="300" r="50" fill="url(#shared_gradient_01)"/>
    </g>

    <g id="FRAME00003">
      <circle cx="700" cy="300" r="50" fill="url(#shared_gradient_01)"/>
    </g>
  </defs>
</svg>
```

---

## Acknowledgments

This specification builds upon:

- W3C SVG Working Group for SVG specifications
- SMIL Working Group for animation timing
- NumPy Project for numerical computation
- Scour Project for SVG optimization techniques

---

**End of Specification**
