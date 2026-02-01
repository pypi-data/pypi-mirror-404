# W3C Example Documentation Templates

**Practical Examples for FBF.SVG Specification**

This document provides complete, reusable templates for documenting examples in the FBF.SVG specification, based on patterns from SVG 1.0.

---

## Table of Contents

1. [Example Documentation Pattern](#1-example-documentation-pattern)
2. [Simple Feature Example Template](#2-simple-feature-example-template)
3. [Complex Feature Example Template](#3-complex-feature-example-template)
4. [Comparison Example Template](#4-comparison-example-template)
5. [Tutorial-Style Example Template](#5-tutorial-style-example-template)
6. [Error Demonstration Template](#6-error-demonstration-template)
7. [Performance Example Template](#7-performance-example-template)
8. [Accessibility Example Template](#8-accessibility-example-template)

---

## 1. Example Documentation Pattern

### 1.1 Standard Example Structure

Every example in the specification should follow this structure:

```markdown
**Example [category][number]: [title]**

[Brief description of what this example demonstrates - 1-2 sentences]

```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE [root-element] PUBLIC "[public-id]" "[system-id]">
<[root-element] [required-attributes]
     xmlns="[namespace]"
     [optional-attributes]>

  <desc>[description of the example]</desc>

  <!-- Example content with comments explaining key aspects -->
  [content]

</[root-element]>
```

[Link to viewable/interactive version if available]

**Key aspects demonstrated:**
- [Aspect 1]: [explanation]
- [Aspect 2]: [explanation]
- [Aspect 3]: [explanation]

[Optional: rendered output image or description of expected result]

[Optional: notes about browser support, performance, or implementation details]
```

### 1.2 Example Naming Convention

**Format:** `[category][sequential-number]`

Examples:
- `rect01` - first rectangle example
- `rect02` - second rectangle example
- `path01` - first path example
- `animate01` - first animation example

**Categories should match:**
- Element names (rect, circle, path, text, etc.)
- Feature names (gradient, filter, animation, etc.)
- Concept names (coords, transform, style, etc.)

### 1.3 Example File Organization

```
examples/
├── basic-shapes/
│   ├── rect01.fbf.svg
│   ├── rect02.fbf.svg
│   ├── circle01.fbf.svg
│   └── ...
├── animation/
│   ├── frame01.fbf.svg
│   ├── timeline01.fbf.svg
│   └── ...
├── layers/
│   ├── layer01.fbf.svg
│   ├── composite01.fbf.svg
│   └── ...
└── collision/
    ├── collision01.fbf.svg
    ├── collision02.fbf.svg
    └── ...
```

---

## 2. Simple Feature Example Template

Use for demonstrating a single feature or attribute.

### 2.1 Template

```markdown
**Example [element][number]: [specific feature being demonstrated]**

This example demonstrates [specific feature/attribute] on the '[element-name]' element.

```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE fbf-animation PUBLIC "-//FBF.SVG//DTD FBF SVG 1.0//EN"
  "http://example.org/fbf-svg/dtd/fbf-svg-1.0.dtd">
<fbf-animation width="[width]" height="[height]"
               viewBox="[viewBox]"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <desc>Example [element][number] - [description]</desc>

  <!-- [Feature being demonstrated] -->
  <[element-name] [key-attribute]="[value]" [other-attributes]>
    [content if applicable]
  </[element-name]>

</fbf-animation>
```

[View this example as FBF.SVG](examples/[category]/[element][number].fbf.svg)

**Demonstrated feature:**

The `[attribute-name]` attribute [explanation of what it does and its effect in this example].

**Expected result:**

[Description of what the viewer should see when rendering this example]
```

### 2.2 Concrete Example (SVG rect with rounded corners)

```markdown
**Example rect02: rounded rectangle corners**

This example demonstrates the 'rx' and 'ry' attributes for creating rounded rectangle corners.

```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
  "http://www.w3.org/TR/2001/PR-SVG-20010719/DTD/svg10.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.0">

  <desc>Example rect02 - rounded rectangle with rx and ry attributes</desc>

  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398"
        fill="none" stroke="blue" stroke-width="2"/>

  <!-- Rounded rectangle -->
  <rect x="100" y="100" width="400" height="200"
        rx="50" ry="50"
        fill="green" stroke="navy" stroke-width="10"/>

</svg>
```

[View this example as SVG](examples/shapes/rect02.svg)

**Demonstrated feature:**

The `rx` and `ry` attributes define the radii of the ellipse used to round the corners
of the rectangle. In this example, both are set to 50, creating uniformly rounded corners.

**Expected result:**

A green rectangle with rounded corners, outlined in navy, centered on a blue canvas border.
```

### 2.3 FBF.SVG Adaptation Template

```markdown
**Example frame01: basic frame definition**

This example demonstrates a simple frame definition within an FBF.SVG timeline.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <desc>Example frame01 - basic single frame</desc>

  <timeline fps="24">
    <frame number="1" duration="1">
      <layer id="background" type="static">
        <rect x="0" y="0" width="800" height="600" fill="#e0e0e0"/>
      </layer>

      <layer id="content" type="animated">
        <circle cx="400" cy="300" r="50" fill="red"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Demonstrated feature:**

The `<frame>` element defines a single frame in the animation timeline. The `number`
attribute specifies the frame number (1-based), and `duration` indicates how many
frames this state should be held.

**Expected result:**

A static frame showing a red circle centered on a light gray background.
```

---

## 3. Complex Feature Example Template

Use for demonstrating multiple interacting features.

### 3.1 Template

```markdown
**Example [category][number]: [comprehensive title]**

This example demonstrates [primary feature] in combination with [secondary features].

```xml
<?xml version="1.0" standalone="no"?>
[DOCTYPE and namespace declarations]

<[root-element] [attributes]>

  <desc>Example [category][number] - [detailed description]</desc>

  <!-- [Section 1: Setup/Definitions] -->
  <defs>
    [definitions - gradients, patterns, symbols, etc.]
  </defs>

  <!-- [Section 2: Main Content] -->
  [primary content demonstrating the feature]

  <!-- [Section 3: Additional Elements] -->
  [supporting elements]

</[root-element]>
```

[View this example](link)

**Key aspects demonstrated:**

1. **[Feature 1]:** [detailed explanation]
2. **[Feature 2]:** [detailed explanation]
3. **[Feature 3]:** [detailed explanation]

**How it works:**

[Step-by-step explanation of the interaction between features]

1. [Step 1 description]
2. [Step 2 description]
3. [Step 3 description]

**Expected result:**

[Detailed description of the rendered output]

**Notes:**

[Any implementation notes, browser compatibility, or performance considerations]
```

### 3.2 Concrete Example (SVG gradient with transforms)

```markdown
**Example gradient03: transformed linear gradient**

This example demonstrates linear gradients in combination with the 'gradientTransform'
attribute and object bounding box coordinates.

```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.0//EN"
  "http://www.w3.org/TR/2001/PR-SVG-20010719/DTD/svg10.dtd">
<svg width="8cm" height="4cm" viewBox="0 0 800 400"
     xmlns="http://www.w3.org/2000/svg" version="1.0">

  <desc>Example gradient03 - linear gradient with transform</desc>

  <!-- Define gradient in defs -->
  <defs>
    <linearGradient id="MyGradient"
                    gradientUnits="objectBoundingBox"
                    gradientTransform="rotate(90 0.5 0.5)">
      <stop offset="0%" stop-color="gold"/>
      <stop offset="50%" stop-color="red"/>
      <stop offset="100%" stop-color="purple"/>
    </linearGradient>
  </defs>

  <!-- Rectangle using the gradient -->
  <rect x="100" y="100" width="600" height="200"
        fill="url(#MyGradient)" stroke="black" stroke-width="5"/>

</svg>
```

[View this example](examples/paint/gradient03.svg)

**Key aspects demonstrated:**

1. **Linear Gradient Definition:** The `<linearGradient>` element defines a gradient
   with three color stops (gold → red → purple).

2. **Object Bounding Box Coordinates:** `gradientUnits="objectBoundingBox"` means the
   gradient coordinate system is based on the bounding box of the element being filled.

3. **Gradient Transform:** `gradientTransform="rotate(90 0.5 0.5)"` rotates the gradient
   90° around the center of the bounding box.

**How it works:**

1. The gradient is initially defined as horizontal (left to right by default)
2. The `gradientTransform` rotates it 90° clockwise around the center point (0.5, 0.5)
   in bounding box coordinates
3. The result is a vertical gradient (top to bottom) applied to the rectangle

**Expected result:**

A rectangle filled with a vertical gradient transitioning from gold at the top,
through red in the middle, to purple at the bottom, with a black outline.

**Notes:**

The transform origin (0.5, 0.5) represents the center of the object bounding box,
regardless of the actual size or position of the rectangle.
```

### 3.3 FBF.SVG Adaptation Template

```markdown
**Example collision02: collision detection with animated layers**

This example demonstrates collision layer definitions combined with frame-by-frame
animation and multiple interactive layers.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="1920" height="1080"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <desc>Example collision02 - collision detection during animation</desc>

  <metadata>
    <collision-config>
      <algorithm type="bounding-box"/>
      <response-type>metadata-only</response-type>
    </collision-config>
  </metadata>

  <timeline fps="24">
    <!-- Frame 1: Initial state -->
    <frame number="1" duration="1">
      <layer id="player" type="collision">
        <rect x="100" y="500" width="50" height="50" fill="blue"/>
        <collision-bounds shape="rect" x="100" y="500" width="50" height="50"/>
      </layer>

      <layer id="obstacle" type="collision">
        <rect x="800" y="500" width="100" height="100" fill="red"/>
        <collision-bounds shape="rect" x="800" y="500" width="100" height="100"/>
      </layer>

      <layer id="background" type="static">
        <rect x="0" y="0" width="1920" height="1080" fill="#87CEEB"/>
      </layer>
    </frame>

    <!-- Frame 2-10: Player moves toward obstacle -->
    <frame number="2" duration="1">
      <layer id="player" type="collision">
        <rect x="180" y="500" width="50" height="50" fill="blue"/>
        <collision-bounds shape="rect" x="180" y="500" width="50" height="50"/>
      </layer>
    </frame>

    <!-- More frames showing progressive movement -->
    <!-- ... -->

    <!-- Frame 10: Collision occurs -->
    <frame number="10" duration="1">
      <layer id="player" type="collision">
        <rect x="750" y="500" width="50" height="50" fill="blue"/>
        <collision-bounds shape="rect" x="750" y="500" width="50" height="50"/>
        <collision-metadata>
          <collision detected="true" with-layer="obstacle" at-frame="10"/>
        </collision-metadata>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Key aspects demonstrated:**

1. **Collision Layers:** The `type="collision"` attribute on `<layer>` elements
   marks them for collision detection processing.

2. **Collision Bounds:** Each collision layer includes a `<collision-bounds>` element
   defining the precise area used for collision detection (may differ from visual bounds).

3. **Frame-by-Frame Animation:** The player layer moves across frames, eventually
   intersecting with the obstacle layer.

4. **Collision Metadata:** When a collision is detected (frame 10), metadata is
   automatically generated documenting the collision event.

**How it works:**

1. Initial frame establishes two collision layers (player and obstacle) and a static background
2. Subsequent frames incrementally move the player layer rightward
3. The collision detection algorithm (bounding-box) checks for overlap at each frame
4. At frame 10, the player's bounds intersect the obstacle's bounds
5. Collision metadata is generated and embedded in the frame

**Expected result:**

When processed by an FBF.SVG viewer with collision detection support:
- Frames 1-9: No collision detected
- Frame 10: Collision detected between player and obstacle layers
- Collision metadata available for export or runtime querying

**Notes:**

The collision algorithm specified in metadata (`bounding-box`) is a simple AABB
(axis-aligned bounding box) check. More sophisticated algorithms (pixel-perfect,
polygon-based) can be specified for more accurate detection.
```

---

## 4. Comparison Example Template

Use to show differences between approaches or to demonstrate evolution.

### 4.1 Template

```markdown
**Example [category][number]: [comparison title]**

This example compares [approach A] with [approach B], demonstrating [key difference].

**Approach A: [name]**

```xml
<?xml version="1.0" standalone="no"?>
[Full example using approach A]
```

**Approach B: [name]**

```xml
<?xml version="1.0" standalone="no"?>
[Full example using approach B]
```

**Comparison:**

| Aspect | Approach A | Approach B |
|--------|------------|------------|
| [Aspect 1] | [A's behavior] | [B's behavior] |
| [Aspect 2] | [A's behavior] | [B's behavior] |
| [Aspect 3] | [A's behavior] | [B's behavior] |

**When to use each approach:**

- **Use Approach A when:** [conditions/scenarios]
- **Use Approach B when:** [conditions/scenarios]

**Performance considerations:**

[Discussion of performance implications of each approach]
```

### 4.2 Concrete Example (FBF.SVG keyframes vs. full frames)

```markdown
**Example timeline03: keyframes vs. full frame specification**

This example compares keyframe-based animation with full frame-by-frame specification
for a simple translation animation.

**Approach A: Keyframe-based (optimized)**

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <desc>Keyframe-based animation - optimized file size</desc>

  <timeline fps="24">
    <keyframe number="1">
      <layer id="ball" type="animated">
        <circle cx="100" cy="300" r="50" fill="red"/>
      </layer>
    </keyframe>

    <keyframe number="24">
      <layer id="ball" type="animated">
        <circle cx="700" cy="300" r="50" fill="red"/>
      </layer>
    </keyframe>

    <interpolation from="1" to="24" method="linear" layer="ball"/>
  </timeline>

</fbf-animation>
```

**Approach B: Full frame specification (explicit)**

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <desc>Full frame specification - explicit control</desc>

  <timeline fps="24">
    <frame number="1" duration="1">
      <layer id="ball" type="animated">
        <circle cx="100" cy="300" r="50" fill="red"/>
      </layer>
    </frame>

    <frame number="2" duration="1">
      <layer id="ball" type="animated">
        <circle cx="126" cy="300" r="50" fill="red"/>
      </layer>
    </frame>

    <!-- Frames 3-23 with progressive cx values -->

    <frame number="24" duration="1">
      <layer id="ball" type="animated">
        <circle cx="700" cy="300" r="50" fill="red"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Comparison:**

| Aspect | Keyframe-based | Full Frame Specification |
|--------|----------------|--------------------------|
| **File size** | Smaller (2 frames + interpolation) | Larger (24 explicit frames) |
| **Authoring effort** | Lower (define endpoints only) | Higher (define every frame) |
| **Playback precision** | Interpolated (may vary slightly) | Exact (as authored) |
| **Editing flexibility** | Easier to adjust timing | More granular control |
| **Collision detection** | Requires interpolation at check time | Exact geometry per frame |

**When to use each approach:**

- **Use Keyframe-based when:**
  - File size is a concern
  - Motion is smooth and predictable
  - Interpolation algorithms produce acceptable results
  - Source material is vector-based animation

- **Use Full Frame Specification when:**
  - Precise frame-by-frame control is required
  - Source is from frame-based animation software
  - Complex motion that doesn't interpolate well
  - Collision detection requires exact geometry

**Performance considerations:**

Keyframe-based animation requires runtime interpolation, which adds computational overhead
during playback but reduces file size and download time. Full frame specification eliminates
interpolation cost but increases memory usage and file transfer time.

For a 24-frame animation, keyframe-based saves approximately 90% file size, but adds
~0.5ms interpolation overhead per frame (varies by implementation).
```

---

## 5. Tutorial-Style Example Template

Use for teaching concepts progressively.

### 5.1 Template

```markdown
**Example [category][number]: [tutorial title]**

This tutorial example demonstrates [concept] by building up complexity step-by-step.

**Step 1: [basic concept]**

[Explanation of the foundational concept]

```xml
[Simple example demonstrating step 1]
```

**Result:** [What you see after step 1]

---

**Step 2: [added feature]**

[Explanation of what's being added and why]

```xml
[Example building on step 1]
```

**Result:** [What you see after step 2]

**What changed:** [Explanation of the differences from step 1]

---

**Step 3: [further enhancement]**

[Explanation of the additional feature]

```xml
[Example building on step 2]
```

**Result:** [What you see after step 3]

**What changed:** [Explanation of the differences from step 2]

---

**Complete example:**

[Full, final version with all steps integrated]

```xml
[Complete example code]
```

**Summary:**

This example demonstrated:
1. [Step 1 takeaway]
2. [Step 2 takeaway]
3. [Step 3 takeaway]

**Next steps:**

Try modifying the example by [suggestion for experimentation].
```

### 5.2 Concrete Example (FBF.SVG collision detection setup)

```markdown
**Example collision-tutorial01: building a collision-aware animation**

This tutorial demonstrates how to add collision detection to an FBF.SVG animation
by progressively adding collision-specific markup.

**Step 1: Basic animation without collision detection**

Start with a simple animation of two moving objects.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <timeline fps="24">
    <frame number="1">
      <layer id="car">
        <rect x="50" y="250" width="100" height="50" fill="blue"/>
      </layer>
      <layer id="wall">
        <rect x="700" y="200" width="20" height="200" fill="gray"/>
      </layer>
    </frame>

    <frame number="10">
      <layer id="car">
        <rect x="500" y="250" width="100" height="50" fill="blue"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Result:** A blue car moving toward a gray wall, but no collision detection.

---

**Step 2: Add collision layer types**

Mark layers that should participate in collision detection.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <timeline fps="24">
    <frame number="1">
      <layer id="car" type="collision">  <!-- ADDED: type attribute -->
        <rect x="50" y="250" width="100" height="50" fill="blue"/>
      </layer>
      <layer id="wall" type="collision">  <!-- ADDED: type attribute -->
        <rect x="700" y="200" width="20" height="200" fill="gray"/>
      </layer>
    </frame>

    <frame number="10">
      <layer id="car" type="collision">
        <rect x="500" y="250" width="100" height="50" fill="blue"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Result:** Layers are now marked for collision detection, but bounds are not yet defined.

**What changed:** Added `type="collision"` to both `<layer>` elements to indicate they
should be checked for collisions.

---

**Step 3: Define collision bounds**

Add explicit collision bounds for precise detection.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <timeline fps="24">
    <frame number="1">
      <layer id="car" type="collision">
        <rect x="50" y="250" width="100" height="50" fill="blue"/>
        <!-- ADDED: collision bounds -->
        <collision-bounds shape="rect" x="50" y="250" width="100" height="50"/>
      </layer>
      <layer id="wall" type="collision">
        <rect x="700" y="200" width="20" height="200" fill="gray"/>
        <!-- ADDED: collision bounds -->
        <collision-bounds shape="rect" x="700" y="200" width="20" height="200"/>
      </layer>
    </frame>

    <frame number="10">
      <layer id="car" type="collision">
        <rect x="500" y="250" width="100" height="50" fill="blue"/>
        <!-- ADDED: collision bounds for this frame -->
        <collision-bounds shape="rect" x="500" y="250" width="100" height="50"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Result:** Collision detection can now precisely identify overlaps between car and wall.

**What changed:** Added `<collision-bounds>` elements to each collision layer in each
frame, defining the exact areas to check for intersections.

---

**Step 4: Configure collision detection algorithm**

Specify the collision detection method and response behavior in metadata.

```xml
<?xml version="1.0" standalone="no"?>
<fbf-animation width="800" height="600"
               xmlns="http://example.org/fbf-svg"
               version="1.0">

  <!-- ADDED: metadata with collision configuration -->
  <metadata>
    <collision-config>
      <algorithm type="bounding-box"/>
      <response-type>metadata-only</response-type>
      <tolerance>0</tolerance>
    </collision-config>
  </metadata>

  <timeline fps="24">
    <frame number="1">
      <layer id="car" type="collision">
        <rect x="50" y="250" width="100" height="50" fill="blue"/>
        <collision-bounds shape="rect" x="50" y="250" width="100" height="50"/>
      </layer>
      <layer id="wall" type="collision">
        <rect x="700" y="200" width="20" height="200" fill="gray"/>
        <collision-bounds shape="rect" x="700" y="200" width="20" height="200"/>
      </layer>
    </frame>

    <frame number="10">
      <layer id="car" type="collision">
        <rect x="500" y="250" width="100" height="50" fill="blue"/>
        <collision-bounds shape="rect" x="500" y="250" width="100" height="50"/>
      </layer>
    </frame>
  </timeline>

</fbf-animation>
```

**Result:** The collision detection system is now fully configured with algorithm settings.

**What changed:** Added `<metadata>` section with `<collision-config>` specifying:
- Algorithm type: `bounding-box` (AABB collision detection)
- Response type: `metadata-only` (generate metadata without altering playback)
- Tolerance: `0` (no tolerance; exact overlap required)

---

**Complete example:**

[View complete collision-aware animation](examples/collision/tutorial01-complete.fbf.svg)

The complete example includes all four steps integrated, with collision detection
fully configured and operational. When processed by an FBF.SVG viewer:

1. Frames 1-7: No collision detected (car approaching wall)
2. Frame 8: Collision detected (car touches wall)
3. Frames 9-10: Collision continues (car overlapping wall)

**Summary:**

This example demonstrated:
1. **Basic structure:** Creating a simple two-layer animation
2. **Collision layers:** Marking layers for collision detection
3. **Collision bounds:** Defining precise detection areas
4. **Configuration:** Specifying algorithm and behavior via metadata

**Next steps:**

Try modifying the example by:
- Changing the collision algorithm to `pixel-perfect` for more accurate detection
- Adding more layers to create a multi-object collision scenario
- Experimenting with different `response-type` values to see how collision affects playback
```

---

## 6. Error Demonstration Template

Use to show common mistakes and their corrections.

### 6.1 Template

```markdown
**Example [category]-error[number]: [error scenario]**

This example demonstrates a common error: [description of the error].

**Incorrect usage:**

```xml
[Code showing the incorrect usage]
```

**Problem:**

[Explanation of why this is incorrect and what error it causes]

**Error message (typical):**

```
[Expected error message or behavior]
```

---

**Correct usage:**

```xml
[Code showing the correct usage]
```

**Explanation:**

[Detailed explanation of the correction and why it works]

**Key takeaway:**

[Summary of the lesson learned]
```

### 6.2 Concrete Example (Missing collision bounds)

```markdown
**Example collision-error01: missing collision bounds**

This example demonstrates a common error: defining a collision layer without specifying
collision bounds.

**Incorrect usage:**

```xml
<frame number="1">
  <layer id="player" type="collision">
    <rect x="100" y="100" width="50" height="50" fill="blue"/>
    <!-- ERROR: collision bounds not defined -->
  </layer>
</frame>
```

**Problem:**

The layer is marked as `type="collision"`, indicating it should participate in collision
detection, but no `<collision-bounds>` element is provided. The viewer cannot determine
what area to use for collision detection.

**Error message (typical):**

```
Error in frame 1, layer "player": Collision layer missing required <collision-bounds> element.
Collision detection disabled for this layer.
```

---

**Correct usage:**

```xml
<frame number="1">
  <layer id="player" type="collision">
    <rect x="100" y="100" width="50" height="50" fill="blue"/>
    <collision-bounds shape="rect" x="100" y="100" width="50" height="50"/>
  </layer>
</frame>
```

**Explanation:**

The `<collision-bounds>` element explicitly defines the rectangular area (x=100, y=100,
width=50, height=50) to be used for collision detection. This may match the visual
bounds of the `<rect>` element, or may differ if collision detection should use a
smaller or larger area than the visible element.

**Key takeaway:**

Every layer with `type="collision"` MUST include a `<collision-bounds>` element in
each frame where it appears. Collision bounds are not inherited from previous frames
and must be explicitly specified.
```

---

## 7. Performance Example Template

Use to demonstrate optimization techniques or performance implications.

### 7.1 Template

```markdown
**Example [category]-perf[number]: [performance topic]**

This example compares [inefficient approach] with [optimized approach], demonstrating
the performance impact of [optimization technique].

**Inefficient approach:**

```xml
[Code showing the inefficient implementation]
```

**Performance characteristics:**

- File size: [size]
- Parse time: [estimate or measurement]
- Memory usage: [estimate or measurement]
- [Other relevant metrics]

---

**Optimized approach:**

```xml
[Code showing the optimized implementation]
```

**Performance characteristics:**

- File size: [size] ([percentage] reduction)
- Parse time: [estimate or measurement] ([percentage] faster)
- Memory usage: [estimate or measurement] ([percentage] lower)
- [Other relevant metrics]

**Optimization techniques used:**

1. [Technique 1]: [explanation]
2. [Technique 2]: [explanation]
3. [Technique 3]: [explanation]

**When to apply this optimization:**

[Guidance on when this optimization is worthwhile vs. overkill]

**Trade-offs:**

[Discussion of any trade-offs, such as reduced flexibility or increased authoring complexity]
```

### 7.2 Concrete Example (Shared layer definitions)

```markdown
**Example layer-perf01: shared vs. duplicated layer definitions**

This example compares duplicating full layer definitions in every frame with using
shared definitions and frame-specific overrides.

**Inefficient approach: Full duplication**

```xml
<timeline fps="24">
  <frame number="1">
    <layer id="background" type="static">
      <rect x="0" y="0" width="1920" height="1080" fill="#87CEEB"/>
      <rect x="0" y="880" width="1920" height="200" fill="#8B4513"/>
      <circle cx="1800" cy="150" r="80" fill="#FFD700"/>
      <!-- 20 more complex shapes -->
    </layer>
  </frame>

  <frame number="2">
    <layer id="background" type="static">
      <rect x="0" y="0" width="1920" height="1080" fill="#87CEEB"/>
      <rect x="0" y="880" width="1920" height="200" fill="#8B4513"/>
      <circle cx="1800" cy="150" r="80" fill="#FFD700"/>
      <!-- 20 more complex shapes - DUPLICATED -->
    </layer>
  </frame>

  <!-- Frames 3-100 with full duplication -->
</timeline>
```

**Performance characteristics:**

- File size: ~850 KB (for 100 frames)
- Parse time: ~120ms
- Memory usage: ~15 MB (all frames loaded)
- Redundancy: 99% duplicate content

---

**Optimized approach: Shared definitions**

```xml
<defs>
  <layer-template id="background-template">
    <rect x="0" y="0" width="1920" height="1080" fill="#87CEEB"/>
    <rect x="0" y="880" width="1920" height="200" fill="#8B4513"/>
    <circle cx="1800" cy="150" r="80" fill="#FFD700"/>
    <!-- 20 more complex shapes - DEFINED ONCE -->
  </layer-template>
</defs>

<timeline fps="24">
  <frame number="1">
    <layer id="background" type="static" template="background-template"/>
  </frame>

  <frame number="2">
    <layer id="background" type="static" template="background-template"/>
  </frame>

  <!-- Frames 3-100 referencing template -->
</timeline>
```

**Performance characteristics:**

- File size: ~15 KB (98% reduction)
- Parse time: ~8ms (93% faster)
- Memory usage: ~2 MB (87% lower)
- Redundancy: 0% (single definition, multiple references)

**Optimization techniques used:**

1. **Template definitions:** Static layer content defined once in `<defs>` section
2. **Template references:** Frames reference templates via `template` attribute
3. **Lazy instantiation:** Viewers can share a single instance across frames

**When to apply this optimization:**

- Use when layers remain unchanged across multiple frames
- Particularly effective for static backgrounds, UI overlays, or repeating elements
- Essential for long animations (50+ frames) with complex static content

**Trade-offs:**

- Increased authoring complexity (need to manage templates and references)
- Less straightforward for frame-specific variations (requires override mechanism)
- Slightly more complex for authoring tools (need template management UI)

**Implementation note:**

For optimal performance, viewers should implement copy-on-write semantics: share
the template instance until a frame-specific override is needed, then create a
modified copy.
```

---

## 8. Accessibility Example Template

Use to demonstrate accessibility features and best practices.

### 8.1 Template

```markdown
**Example [category]-a11y[number]: [accessibility topic]**

This example demonstrates how to make [feature] accessible to users with [disability/limitation].

**Basic example (without accessibility features):**

```xml
[Code showing the feature without accessibility markup]
```

**Accessibility issues:**

- [Issue 1]: [description of problem]
- [Issue 2]: [description of problem]
- [Issue 3]: [description of problem]

---

**Accessible example:**

```xml
[Code showing the same feature with accessibility markup]
```

**Accessibility features added:**

1. **[Feature 1]:** [explanation of how it improves accessibility]
2. **[Feature 2]:** [explanation of how it improves accessibility]
3. **[Feature 3]:** [explanation of how it improves accessibility]

**Benefits:**

- **Screen readers:** [how screen readers interpret this]
- **Keyboard navigation:** [how keyboard users can interact]
- **Visual impairment:** [how users with visual impairments benefit]
- **[Other benefit]:** [explanation]

**WCAG compliance:**

This example satisfies:
- WCAG [version] Level [A/AA/AAA] - [criterion number and name]
- [Additional criteria]
```

### 8.2 Concrete Example (Accessible collision metadata)

```markdown
**Example collision-a11y01: accessible collision event descriptions**

This example demonstrates how to make collision events in an FBF.SVG animation
accessible to screen reader users and assistive technologies.

**Basic example (without accessibility features):**

```xml
<frame number="25">
  <layer id="player" type="collision">
    <circle cx="500" cy="300" r="25" fill="blue"/>
    <collision-bounds shape="circle" cx="500" cy="300" r="25"/>
    <collision-metadata>
      <collision detected="true" with-layer="enemy" at-frame="25"/>
    </collision-metadata>
  </layer>
</frame>
```

**Accessibility issues:**

- **No textual description:** Screen readers cannot announce the collision event
- **No semantic information:** Assistive technologies don't know the significance
- **No alternative representation:** Users with visual impairments miss the event

---

**Accessible example:**

```xml
<frame number="25">
  <layer id="player" type="collision">
    <title>Player character</title>
    <desc>A blue circle representing the player, currently colliding with an enemy</desc>

    <circle cx="500" cy="300" r="25" fill="blue"/>
    <collision-bounds shape="circle" cx="500" cy="300" r="25"/>

    <collision-metadata>
      <collision detected="true" with-layer="enemy" at-frame="25">
        <event-description>
          The player character collides with an enemy, resulting in damage.
        </event-description>
        <aria-live>assertive</aria-live>
        <event-type>combat</event-type>
      </collision>
    </collision-metadata>
  </layer>
</frame>
```

**Accessibility features added:**

1. **Title and description elements:** Provide textual names and descriptions for
   the layer content, readable by screen readers

2. **Event description:** Natural language explanation of the collision event within
   `<event-description>`, making the game event comprehensible

3. **ARIA live region:** `<aria-live>assertive</aria-live>` signals that this event
   should be announced immediately to screen reader users

4. **Semantic event type:** `<event-type>combat</event-type>` categorizes the collision,
   allowing assistive technologies to provide appropriate feedback

**Benefits:**

- **Screen readers:** Announce "The player character collides with an enemy, resulting
  in damage" when the collision occurs

- **Keyboard navigation:** Combined with keyboard controls, users can understand
  game state without visual feedback

- **Visual impairment:** Textual descriptions provide complete information about
  events that would otherwise be purely visual

- **Cognitive accessibility:** Clear, descriptive language helps users with cognitive
  disabilities understand game mechanics

**WCAG compliance:**

This example satisfies:
- WCAG 2.1 Level A - 1.1.1 Non-text Content (textual alternatives for graphics)
- WCAG 2.1 Level A - 4.1.2 Name, Role, Value (semantic information for all components)
- WCAG 2.1 Level AA - 1.3.1 Info and Relationships (programmatically determinable information)

**Implementation note:**

FBF.SVG viewers with accessibility support should:
1. Expose `<title>` and `<desc>` elements to accessibility APIs
2. Monitor `<collision-metadata>` for events with `<aria-live>` attributes
3. Announce `<event-description>` content via screen readers when appropriate
4. Provide keyboard shortcuts to query current collision state
```

---

## Conclusion

These templates provide reusable patterns for documenting examples throughout the
FBF.SVG specification. By following these conventions:

1. **Consistency:** All examples follow the same structure, making them easy to understand
2. **Completeness:** Each example includes code, explanation, and expected results
3. **Progressive complexity:** From simple feature demos to complex tutorials
4. **Practical guidance:** Error demonstrations and performance examples guide implementers
5. **Accessibility:** Dedicated patterns for inclusive design

Use these templates when documenting FBF.SVG features to maintain a professional,
implementable specification that serves both authors and developers effectively.
