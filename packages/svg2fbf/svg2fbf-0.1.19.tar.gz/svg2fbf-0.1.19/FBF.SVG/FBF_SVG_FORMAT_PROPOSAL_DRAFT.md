# Frame-by-Frame SVG (FBF.SVG)
## W3C Candidate Substandard Proposal - Draft

**Version:** 0.1.2a4 (Draft)
**Date:** November 2024
**Status:** Pre-Submission Draft
**Editors:** Emanuele Sabetta ([@Emasoft](https://github.com/Emasoft))
**Feedback:** [GitHub Issues](https://github.com/Emasoft/svg2fbf/issues)

---

## Abstract

This document proposes **FBF.SVG** (Frame-by-Frame SVG) as a candidate profile specification within the SVG family of standards, analogous to existing SVG profiles such as SVG Tiny and SVG Basic. FBF.SVG defines a constrained, optimized subset of SVG designed specifically for declarative frame-by-frame vector animation.

FBF.SVG documents are valid SVG 1.1/2.0 documents with additional structural requirements, security constraints, and metadata specifications. The format prioritizes streaming capability, mechanical validation, security-by-design, and bidirectional visual communication protocols for AI-to-human interaction.

**Target Audience:** Animation tool developers, content creators, LLM implementers, browser vendors, and W3C standards community.

---

## Status of This Document

This section describes the status of this document at the time of its publication. **Other documents may supersede this document.**

This is a **pre-submission draft** of the FBF.SVG format proposal for consideration as a W3C Candidate Substandard within the SVG specification family. The document is being developed for community review and reference implementation testing.

**This document is not yet a W3C standard.** Publication as a draft does not imply endorsement by the W3C Membership. This is still a draft document and may be updated, replaced, or obsoleted by other documents at any time. It is inappropriate to cite this document as other than work in progress.

**Comments and Feedback:** Comments and suggestions on this document are welcome. Please file issues at the [GitHub Issues](https://github.com/Emasoft/svg2fbf/issues) tracker or contact the editors directly.

### Expected Evolution
- **Current Phase:** Community review and reference implementation testing
- **Next Phase:** Formal submission to W3C SVG Working Group for consideration
- **Target:** W3C Candidate Recommendation status

### Known Implementations
- **svg2fbf** (Reference Implementation) - Python-based FBF.SVG generator ([GitHub](https://github.com/Emasoft/svg2fbf))
- **Browser Support** - All modern browsers with SMIL support (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Motivation and Use Cases](#2-motivation-and-use-cases)
3. [Relationship to Existing SVG Profiles](#3-relationship-to-existing-svg-profiles)
4. [Design Principles](#4-design-principles)
5. [Conformance Levels](#5-conformance-levels)
6. [Format Specification](#6-format-specification)
7. [Security Model](#7-security-model)
8. [Metadata Requirements](#8-metadata-requirements)
9. [Animation Semantics](#9-animation-semantics)
10. [Streaming Architecture](#10-streaming-architecture)
11. [Interactive Visual Communication](#11-interactive-visual-communication)
12. [Examples](#12-examples)
13. [Validation and Testing](#13-validation-and-testing)
14. [Implementation Considerations](#14-implementation-considerations)
15. [Internationalization](#15-internationalization)
16. [Accessibility](#16-accessibility)
17. [Security Considerations](#17-security-considerations)
18. [Privacy Considerations](#18-privacy-considerations)
19. [Future Directions](#19-future-directions)
20. [Acknowledgments](#20-acknowledgments)
21. [References](#21-references)
22. [Appendices](#22-appendices)

---

## 1. Introduction

[This section provides an overview of the Frame-by-Frame SVG (FBF.SVG) format, its purpose, scope, and relationship to existing W3C standards.]

### 1.1 About FBF.SVG

Frame-by-Frame SVG (FBF.SVG) is a constrained SVG profile designed specifically for declarative frame-by-frame vector animation. The format originated from the OpenToonz open source project ([Issue #5346](https://github.com/opentoonz/opentoonz/issues/5346)), which identified the need for an open, web-compatible format suitable for professional 2D animation workflows.

FBF.SVG is analogous to existing SVG profiles such as SVG Tiny and SVG Basic, defining a specialized subset of SVG with additional structural requirements, security constraints, and metadata specifications. The format prioritizes:

- **Declarative animation** (no imperative code required)
- **Streaming capability** (real-time frame addition)
- **Security-by-design** (strict CSP compliance)
- **Mechanical validation** (conformance checking)
- **Self-documentation** (embedded metadata)
- **File size optimization** (deduplication and compression)

**Target Audience:** Animation tool developers, content creators, LLM implementers, browser vendors, and W3C standards community.

**First Published:** June 2022 on CodePen (reference implementation)

### 1.2 MIME Type and File Extensions

**MIME Type:** `image/svg+xml; profile=fbf` (or `image/svg+xml`)

**File Extension:** `.fbf.svg` (or `.svg`)

**Note:** The MIME type `image/svg+xml; profile=fbf` is proposed but not yet formally registered with IANA. FBF.SVG documents MAY use the standard SVG MIME type `image/svg+xml` for backward compatibility.

**TODO:** Formal MIME type registration with IANA is required before W3C Recommendation status.

### 1.3 Namespace and Identifiers

**SVG Namespace:** `http://www.w3.org/2000/svg`

FBF.SVG documents use the standard SVG namespace. All FBF-specific elements are standard SVG elements with constrained usage patterns and required IDs.

**FBF Custom Namespace (Metadata):** `http://opentoonz.github.io/fbf/1.0#`

**XML Namespace Prefix:** `fbf:` (for custom FBF metadata vocabulary)

**Schema Identifier:** `fbf-svg.xsd`

**Example Namespace Declaration:**
```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:fbf="http://opentoonz.github.io/fbf/1.0#"
     version="1.1">
  <!-- FBF.SVG content -->
</svg>
```

### 1.4 W3C Compatibility

FBF.SVG is designed for compatibility with the following W3C specifications:

- **SVG 1.1 (Second Edition)** - W3C Recommendation 16 August 2011
- **SVG 2.0** - W3C Working Draft (or later)
- **SMIL Animation 3.0** - W3C Recommendation 1 December 2008
- **RDF/XML Syntax Specification** - W3C Recommendation 10 February 2004
- **Dublin Core Metadata Terms** - DCMI Recommendation

**Conformance Requirement:** Every FBF.SVG document MUST be a valid SVG 1.1 or SVG 2.0 document. FBF.SVG does not introduce new SVG elements, attributes, or rendering semantics. It defines:

- **Structural constraints** (mandatory element hierarchy and ordering)
- **Security constraints** (restrictions on external resources and scripting)
- **Metadata requirements** (RDF/XML vocabulary for animation properties)
- **Conformance criteria** (mechanical validation rules)

### 1.5 Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

**Key Terms:**
- **FBF Document** - An SVG document conforming to this specification
- **FBF.SVG profile** - The constrained subset of SVG defined by this specification
- **Frame** - A single visual state in the animation sequence, defined as a `<g>` element
- **Frame Definition** - The `<g>` element within `<defs>` containing frame content
- **Frame ID** - A unique identifier following the pattern `FRAME` + 5-digit zero-padded number
- **Animation Structure** - The required hierarchy of elements controlling playback
- **Shared Definitions** - Deduplicated SVG elements referenced by multiple frames
- **Extension Point** - A designated `<g>` element allowing safe runtime composition
- **PROSKENION** - The `<use>` element that references and displays the current frame
- **Animation Type** - The playback mode (once, loop, pingpong, etc.)

### 1.6 Definitions (Glossary)

This section provides definitions for technical terms used throughout this specification.

**Animation Backdrop**

The root container element (`<g id="ANIMATION_BACKDROP">`) that establishes the layered composition structure with three child layers at different Z-order depths: STAGE_BACKGROUND (behind), ANIMATION_STAGE (middle), and STAGE_FOREGROUND (front).

(See [Section 6.1](#61-element-hierarchy-normative))

**Animation Stage**

The middle layer container (`<g id="ANIMATION_STAGE">`) that contains the ANIMATED_GROUP and PROSKENION elements, where frame sequencing animation occurs.

(See [Section 6.1](#61-element-hierarchy-normative))

**Animation Type**

An enumerated value specifying the playback behavior of the animation. Valid values: `once`, `once_reversed`, `loop`, `loop_reversed`, `pingpong_once`, `pingpong_loop`, `pingpong_once_reversed`, `pingpong_loop_reversed`.

(See [Section 9.2](#92-animation-types-normative))

**Conforming FBF.SVG Document**

An SVG document that satisfies all normative requirements of this specification, including element hierarchy, security constraints, and (for Full conformance) metadata requirements.

(See [Section 5](#5-conformance-levels))

**Conforming FBF.SVG Generator**

A tool or application that produces FBF.SVG documents conforming to this specification.

(See [Section 5.4](#54-conforming-fbfsvg-generators))

**Conforming FBF.SVG Interpreter**

A parser or processor that correctly interprets FBF.SVG documents according to this specification.

(See [Section 5.5](#55-conforming-fbfsvg-interpreters))

**Conforming FBF.SVG Viewer**

A user agent (browser or standalone application) that correctly renders FBF.SVG documents.

(See [Section 5.6](#56-conforming-fbfsvg-viewers))

**Deduplication**

The process of identifying repeated SVG elements across frames and moving them to SHARED_DEFINITIONS to reduce file size.

**Extension Point**

A designated container element (STAGE_BACKGROUND, STAGE_FOREGROUND, OVERLAY_LAYER) that allows safe addition of content without disrupting the core animation structure.

(See [Section 10.2](#102-streaming-use-cases))

**Frame**

A single visual state in the animation sequence, represented as a `<g>` element with a unique frame ID.

**Frame Definition**

A `<g>` element within the `<defs>` section containing the SVG content for a single frame.

**Frame ID**

A unique identifier for a frame, following the pattern `FRAME` + 5-digit zero-padded number (e.g., `FRAME00001`, `FRAME00042`).

(See [Section 6.4](#64-frame-naming-normative))

**Frame Rate (FPS)**

The number of frames displayed per second, specified in the animation metadata.

**Overlay Layer**

The topmost container element (`<g id="OVERLAY_LAYER">`) for content that should appear in front of all other layers.

**PROSKENION**

The `<use>` element with `id="PROSKENION"` that references the current frame and contains the SMIL `<animate>` element controlling frame sequencing.

**Shared Definitions**

A container element (`<g id="SHARED_DEFINITIONS">`) within `<defs>` containing SVG elements referenced by multiple frames, used for deduplication.

**Stage Background**

The back layer container (`<g id="STAGE_BACKGROUND">`) for content that should appear behind the animation.

**Stage Foreground**

The front layer container (`<g id="STAGE_FOREGROUND">`) for content that should appear in front of the animation but behind the overlay layer.

**Streaming**

The capability to append frame definitions to a document during playback without interrupting animation.

(See [Section 10](#10-streaming-architecture))

---

## 2. Motivation and Use Cases

### 2.1 Problem Statement

Current SVG animation approaches present limitations for frame-by-frame animation:

1. **SMIL Limitations** - While SMIL provides declarative animation, no standardized structure exists for frame-by-frame sequences
2. **Security Concerns** - Script-based animation requires `<script>` elements, violating CSP policies
3. **File Size** - Naive frame sequences result in massive files due to element duplication
4. **Streaming** - No standardized approach for real-time frame addition
5. **Metadata** - No structured metadata for animation properties
6. **Validation** - No mechanical validation for conformance

### 2.2 Primary Use Cases

#### 2.2.1 Traditional Frame-by-Frame Animation
**User:** Professional animator using OpenToonz/Blender/Inkscape
**Need:** Export animation sequences to web-compatible vector format
**Benefit:** Open, portable format with browser support

#### 2.2.2 Interactive UI Components
**User:** Web developer creating animated buttons/controls
**Need:** Code-free interactive animations with click triggers
**Benefit:** No JavaScript required, CSP-compliant

#### 2.2.3 LLM Visual Communication
**User:** Language model generating visual interfaces
**Need:** Declarative SVG generation for user interaction
**Benefit:** Bidirectional visual protocol without imperative code

#### 2.2.4 Real-Time Streaming
**User:** Live presentation tool, whiteboard application
**Need:** Append frames during playback without interruption
**Benefit:** Streaming architecture with frames-at-end design

#### 2.2.5 Educational Content
**User:** E-learning platform, tutorial creator
**Need:** Vector animations with embedded metadata and accessibility
**Benefit:** Self-documenting, accessible, validatable content

### 2.3 Benefits Over Alternatives

| Requirement | FBF.SVG | GIF/APNG | Canvas/WebGL | SVG+Script |
|-------------|---------|----------|--------------|------------|
| Vector Graphics | ✅ | ❌ | ❌ | ✅ |
| Declarative | ✅ | ✅ | ❌ | ❌ |
| CSP-Compliant | ✅ | ✅ | ⚠️ | ❌ |
| Streamable | ✅ | ❌ | ⚠️ | ⚠️ |
| Validatable | ✅ | ⚠️ | ❌ | ❌ |
| Metadata | ✅ | ⚠️ | ❌ | ⚠️ |
| File Size | ✅ | ⚠️ | N/A | ⚠️ |

---

## 3. Relationship to Existing SVG Profiles

### 3.1 SVG Profile Family

FBF.SVG is proposed as a **profile** within the SVG specification family, following the precedent of:

- **SVG Tiny 1.2** (mobile devices)
- **SVG Basic 1.1** (handheld devices)
- **SVG Print 1.2** (static document printing)

### 3.2 Comparison to SVG Profiles

| Feature | SVG Full | SVG Tiny | SVG Basic | **FBF.SVG** |
|---------|----------|----------|-----------|-------------|
| Target | Desktop | Mobile | Handheld | **Animation** |
| Scripting | Full | Limited | Partial | **Restricted** |
| SMIL | Full | Full | Full | **Required** |
| External Resources | Allowed | Limited | Limited | **Forbidden** |
| Metadata | Optional | Limited | Limited | **Required (Full)** |
| Structure | Flexible | Flexible | Flexible | **Strict** |

### 3.3 Compatibility

**Every FBF.SVG document is a valid SVG 1.1/2.0 document.**

FBF.SVG does not introduce new:
- Elements (uses existing SVG elements)
- Attributes (uses existing SVG attributes)
- Rendering semantics (uses standard SVG rendering)

FBF.SVG adds:
- **Structural constraints** (element ordering, hierarchy)
- **Security constraints** (external resource restrictions)
- **Metadata requirements** (RDF/XML vocabulary)
- **Conformance criteria** (mechanical validation)

---

## 4. Design Principles

FBF.SVG is designed around eight core principles:

### 4.1 SVG Compatibility
**Principle:** Every FBF.SVG document MUST be a valid SVG 1.1 or SVG 2.0 document.

**Rationale:** Ensures existing SVG renderers can display FBF.SVG content without modification.

### 4.2 Declarative Animation
**Principle:** Animation MUST be achieved through SMIL declarative syntax, not imperative scripting.

**Rationale:** Enables mechanical validation, CSP compliance, and implementation simplicity.

### 4.3 Security First
**Principle:** FBF.SVG documents MUST be self-contained with strict CSP compliance.

**Rationale:** Prevents XSS attacks, enables sandboxed rendering, suitable for untrusted content.

### 4.4 Optimization
**Principle:** Smart deduplication and shared definitions SHOULD minimize file size.

**Rationale:** Frame-by-frame animation involves significant element repetition; deduplication is essential.

### 4.5 Validatability
**Principle:** FBF.SVG conformance MUST be mechanically validatable.

**Rationale:** Enables automated testing, quality assurance, and conformance certification.

### 4.6 Self-Documentation
**Principle:** FBF.SVG documents SHOULD contain comprehensive embedded metadata.

**Rationale:** Enables content discovery, attribution, licensing, and archival preservation.

### 4.7 Streaming Architecture
**Principle:** Frame definitions MUST appear after animation structure to enable streaming.

**Rationale:** Allows real-time frame addition without playback interruption.

### 4.8 Interactive Visual Communication
**Principle:** FBF.SVG SHOULD support bidirectional AI-to-user visual interaction.

**Rationale:** Enables LLMs to generate interactive interfaces without imperative code.

---

## 5. Conformance

(This section is normative)

This chapter defines conformance requirements for FBF.SVG documents, generators, interpreters, and viewers.

### 5.1 Conforming FBF.SVG Documents

A conforming FBF.SVG document is an SVG document that:

1. MUST be a valid SVG 1.1 (Second Edition) or SVG 2.0 document
2. MUST conform to the element hierarchy defined in [Section 6.1](#61-element-hierarchy-normative)
3. MUST conform to security constraints defined in [Section 7](#7-security-model)
4. MUST use SMIL animation for frame sequencing as described in [Section 9](#9-animation-semantics)
5. MUST NOT reference external resources (fonts, images, scripts) except as permitted in [Section 7.2](#72-security-constraints-normative)
6. SHOULD include RDF/XML metadata (REQUIRED for Full conformance, see [Section 5.3](#53-fbfsvg-full-conformance))

FBF.SVG defines two document conformance levels: **Basic** and **Full**.

### 5.2 FBF.SVG Basic Conformance

A document conforming to FBF.SVG Basic is a conforming FBF.SVG document that satisfies all requirements in [Section 5.1](#51-conforming-fbfsvg-documents).

**Minimum requirements:**

1. ✅ Valid SVG 1.1 or 2.0 document
2. ✅ Required element hierarchy ([Section 6.1](#61-element-hierarchy-normative))
3. ✅ SMIL-based frame animation ([Section 9](#9-animation-semantics))
4. ✅ Self-contained (no external resources)
5. ✅ Security compliant ([Section 7](#7-security-model))

**Optional:**
- Metadata (recommended but not required)
- RDF/XML vocabulary (recommended but not required)

**Use Case:** Quick prototyping, internal tools, non-production content

### 5.3 FBF.SVG Full Conformance

A document conforming to FBF.SVG Full is a conforming FBF.SVG Basic document that additionally:

1. MUST include a complete RDF/XML metadata block ([Section 8](#8-metadata-requirements))
2. MUST include all required Dublin Core metadata fields
3. MUST include all required FBF custom vocabulary fields
4. MUST follow strict ID naming conventions ([Section 6.4](#64-frame-naming-normative))

**Production-ready conformance level:**

1. ✅ All FBF.SVG Basic requirements
2. ✅ Complete RDF/XML metadata block ([Section 8.1](#81-metadata-structure-normative-for-full-conformance))
3. ✅ Dublin Core metadata fields ([Section 8.2](#82-required-metadata-fields-full-conformance))
4. ✅ FBF custom vocabulary ([Section 8.4](#84-fbf-vocabulary-namespace))
5. ✅ Strict ID naming conventions

**Use Case:** Production content, archival, distribution, LLM-generated content

**Note:** The reference implementation (svg2fbf) generates FBF.SVG Full conformant documents.

### 5.4 Conforming FBF.SVG Generators

A conforming FBF.SVG generator is a tool or application that:

1. MUST produce documents conforming to [Section 5.1](#51-conforming-fbfsvg-documents) (Basic) or [Section 5.3](#53-fbfsvg-full-conformance) (Full)
2. MUST validate output against fbf-svg.xsd schema
3. SHOULD implement frame deduplication as described in [Section 6](#6-format-specification)
4. SHOULD generate Full conformance metadata ([Section 8](#8-metadata-requirements))
5. SHOULD provide options for both Basic and Full conformance output

**Known Conforming Generators:**
- svg2fbf v0.1.2a4 (reference implementation) - Full conformance

### 5.5 Conforming FBF.SVG Interpreters

A conforming FBF.SVG interpreter is a parser or processor that:

1. MUST correctly parse all SVG 1.1/2.0 elements used in FBF.SVG documents
2. MUST support SMIL animation declarative timing
3. MUST implement frame sequencing per [Section 9](#9-animation-semantics)
4. SHOULD parse and expose metadata ([Section 8](#8-metadata-requirements))
5. MUST NOT execute scripts or load external resources unless explicitly permitted ([Section 7](#7-security-model))

### 5.6 Conforming FBF.SVG Viewers

A conforming FBF.SVG viewer is a user agent (browser, standalone application, or rendering engine) that:

1. MUST implement a conforming FBF.SVG interpreter ([Section 5.5](#55-conforming-fbfsvg-interpreters))
2. MUST correctly render all SVG 1.1/2.0 elements used in FBF.SVG documents
3. MUST enforce security constraints ([Section 7](#7-security-model))
4. SHOULD provide playback controls (play, pause, seek, frame-by-frame navigation)
5. SHOULD support all animation types ([Section 9.2](#92-animation-types-normative))
6. MAY provide additional features (frame export, timeline scrubbing, editing)

**Known Conforming Viewers:**
- Chrome 90+ (full SMIL support)
- Firefox 88+ (full SMIL support)
- Safari 14+ (full SMIL support)
- Edge 90+ (full SMIL support)

---

## 6. Format Specification

### 6.1 Element Hierarchy (Normative)

FBF.SVG documents MUST conform to the following strict element hierarchy:

```xml
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
  <!-- 1. Metadata (optional for Basic, required for Full) -->
  <metadata>
    <rdf:RDF>...</rdf:RDF>
  </metadata>

  <!-- 2. Description (required) -->
  <desc>Animation description</desc>

  <!-- 3. Animation Backdrop (required) -->
  <g id="ANIMATION_BACKDROP">
    <!-- 3a. Stage Background (extension point) -->
    <g id="STAGE_BACKGROUND">
      <!-- Z-order: behind animation -->
    </g>

    <!-- 3b. Animation Stage (required) -->
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" href="#FRAME00001">
          <!-- SMIL animation -->
          <animate attributeName="href"
                   values="#FRAME00001;#FRAME00002;..."
                   dur="..." repeatCount="..."/>
        </use>
      </g>
    </g>

    <!-- 3c. Stage Foreground (extension point) -->
    <g id="STAGE_FOREGROUND">
      <!-- Z-order: in front of animation -->
    </g>
  </g>

  <!-- 4. Overlay Layer (extension point) -->
  <g id="OVERLAY_LAYER">
    <!-- Z-order: superimposed on all -->
  </g>

  <!-- 5. Definitions (required) -->
  <defs>
    <!-- 5a. Shared Definitions (first child) -->
    <g id="SHARED_DEFINITIONS">
      <!-- Deduplicated elements -->
    </g>

    <!-- 5b. Frame Definitions (sequential) -->
    <g id="FRAME00001">...</g>
    <g id="FRAME00002">...</g>
    <g id="FRAME00003">...</g>
    <!-- ... -->
  </defs>

  <!-- 6. Script (optional, mesh gradient polyfill only) -->
  <script type="text/javascript">
    <!-- ONLY SVG 2.0 mesh gradient polyfill permitted -->
  </script>
</svg>
```

### 6.2 Required Elements

The following elements MUST be present:

| Element | ID | Purpose | Required |
|---------|-----|---------|----------|
| `<desc>` | - | Animation description | ✅ Basic |
| `<g>` | `ANIMATION_BACKDROP` | Root container | ✅ Basic |
| `<g>` | `STAGE_BACKGROUND` | Background layer | ✅ Basic |
| `<g>` | `ANIMATION_STAGE` | Animation container | ✅ Basic |
| `<g>` | `ANIMATED_GROUP` | Timing orchestration | ✅ Basic |
| `<use>` | `PROSKENION` | Frame reference | ✅ Basic |
| `<animate>` | - | SMIL timing | ✅ Basic |
| `<g>` | `STAGE_FOREGROUND` | Foreground layer | ✅ Basic |
| `<g>` | `OVERLAY_LAYER` | Overlay layer | ✅ Basic |
| `<defs>` | - | Definitions container | ✅ Basic |
| `<g>` | `SHARED_DEFINITIONS` | Shared elements | ✅ Basic |
| `<g>` | `FRAME00001`, `FRAME00002`, ... | Frame definitions | ✅ Basic |
| `<metadata>` | - | RDF/XML metadata | ✅ Full only |

### 6.3 Element Definitions

This section provides detailed documentation for FBF-specific elements using the standard 7-part template.

#### 6.3.1 The 'ANIMATION_BACKDROP' Element

The ANIMATION_BACKDROP element is the root container for the FBF animation structure. It provides an extensibility point for layered composition with three child layers at different Z-order depths.

**DTD:**

```xml
<!ELEMENT g (STAGE_BACKGROUND?, ANIMATION_STAGE, STAGE_FOREGROUND?) >
<!ATTLIST g
  id CDATA #FIXED "ANIMATION_BACKDROP"
  %stdSVGAttrs;
>
```

**Attributes:**

- **id** = `"ANIMATION_BACKDROP"`

  Fixed identifier for the animation backdrop container. This ID MUST be exactly "ANIMATION_BACKDROP" (case-sensitive).

  Default: N/A (required, fixed value)
  Animatable: no

**Example:**

```xml
<g id="ANIMATION_BACKDROP">
  <!-- Optional: Background layer (behind animation) -->
  <g id="STAGE_BACKGROUND">
    <rect width="800" height="600" fill="#f0f0f0"/>
  </g>

  <!-- Required: Animation stage (contains frames) -->
  <g id="ANIMATION_STAGE">
    <g id="ANIMATED_GROUP">
      <use id="PROSKENION" href="#FRAME00001">
        <animate attributeName="href"
                 values="#FRAME00001;#FRAME00002;#FRAME00003"
                 keyTimes="0;0.5;1"
                 dur="1s"
                 repeatCount="indefinite"/>
      </use>
    </g>
  </g>

  <!-- Optional: Foreground layer (in front of animation) -->
  <g id="STAGE_FOREGROUND">
    <text x="10" y="20" fill="black">Copyright 2024</text>
  </g>
</g>
```

**Processing Model:**

The ANIMATION_BACKDROP element establishes three rendering layers in Z-order:

1. **STAGE_BACKGROUND** (rendered first, behind animation)
   - Optional layer for static backdrop content
   - MAY be empty or omitted
   - Rendered at Z-index 0 (back)

2. **ANIMATION_STAGE** (rendered second, contains animated frames)
   - Required layer containing ANIMATED_GROUP and PROSKENION
   - Contains the frame sequencing animation
   - Rendered at Z-index 1 (middle)

3. **STAGE_FOREGROUND** (rendered third, in front of animation)
   - Optional layer for overlay content (captions, watermarks)
   - MAY be empty or omitted
   - Rendered at Z-index 2 (front)

A conforming FBF.SVG viewer MUST render these layers in the specified order. Content in later layers MUST occlude content in earlier layers according to standard SVG rendering rules.

**See also:**
- [Section 6.1](#61-element-hierarchy-normative) (Element Hierarchy)
- [Section 10.2](#102-streaming-use-cases) (Extension Points)
- [Section 6.3.2](#632-the-animation_stage-element) (ANIMATION_STAGE element)

#### 6.3.2 The 'ANIMATION_STAGE' Element

The ANIMATION_STAGE element is the container for the core frame animation. It MUST contain an ANIMATED_GROUP element, which in turn contains the PROSKENION element.

**DTD:**

```xml
<!ELEMENT g (ANIMATED_GROUP) >
<!ATTLIST g
  id CDATA #FIXED "ANIMATION_STAGE"
  %stdSVGAttrs;
>
```

**Attributes:**

- **id** = `"ANIMATION_STAGE"`

  Fixed identifier for the animation stage container. This ID MUST be exactly "ANIMATION_STAGE" (case-sensitive).

  Default: N/A (required, fixed value)
  Animatable: no

**Example:**

```xml
<g id="ANIMATION_STAGE">
  <g id="ANIMATED_GROUP">
    <use id="PROSKENION" href="#FRAME00001">
      <animate attributeName="href"
               values="#FRAME00001;#FRAME00002"
               keyTimes="0;1"
               dur="0.5s"
               repeatCount="indefinite"/>
    </use>
  </g>
</g>
```

**Processing Model:**

The ANIMATION_STAGE element serves as a transformation and positioning container for the animated content. Transformations applied to ANIMATION_STAGE affect all frames uniformly, enabling:

- **Scaling:** Resize the entire animation
- **Translation:** Reposition the animation within the viewport
- **Rotation:** Rotate all frames together
- **Clipping:** Define visible region for animation

A conforming FBF.SVG viewer MUST apply transformations to ANIMATION_STAGE before rendering the frame content referenced by PROSKENION.

**See also:**
- [Section 6.3.3](#633-the-proskenion-element) (PROSKENION element)
- [Section 9](#9-animation-semantics) (Animation Semantics)

#### 6.3.3 The 'PROSKENION' Element

The PROSKENION element is a `<use>` element that references the current frame and contains the SMIL animation controlling frame sequencing.

**DTD:**

```xml
<!ELEMENT use (animate) >
<!ATTLIST use
  id CDATA #FIXED "PROSKENION"
  href CDATA #REQUIRED
  %stdSVGAttrs;
>
```

**Attributes:**

- **id** = `"PROSKENION"`

  Fixed identifier for the frame reference element. This ID MUST be exactly "PROSKENION" (case-sensitive). The name derives from the Greek theatrical term for the area in front of the stage curtain.

  Default: N/A (required, fixed value)
  Animatable: no

- **href** = `"<iri>"`

  IRI reference to the initial frame. The value MUST be a fragment identifier pointing to a frame definition (typically `#FRAME00001`).

  Default: none (required)
  Animatable: yes (via SMIL `<animate>` element)

**Example:**

```xml
<use id="PROSKENION" href="#FRAME00001">
  <!-- SMIL animation controlling frame sequencing -->
  <animate
    attributeName="href"
    values="#FRAME00001;#FRAME00002;#FRAME00003"
    keyTimes="0;0.333;0.667;1"
    dur="1s"
    repeatCount="indefinite"
    calcMode="discrete"/>
</use>
```

**Processing Model:**

The PROSKENION element implements frame sequencing through SMIL animation of its `href` attribute. The processing model is:

1. **Initial State:** At time t=0, the PROSKENION `href` attribute points to the initial frame (typically `FRAME00001`)

2. **Animation Evaluation:** As the animation timeline progresses, the SMIL `<animate>` element updates the `href` attribute according to the `values` and `keyTimes` specified

3. **Frame Rendering:** At each frame transition, the viewer resolves the new `href` value and renders the referenced frame content

4. **Discrete Transitions:** Frame changes are instantaneous (not interpolated). The `calcMode` SHOULD be set to `"discrete"` to ensure frame boundaries are sharp.

A conforming FBF.SVG viewer MUST support SMIL animation of the `href` attribute on `<use>` elements. The viewer MUST re-resolve the `href` reference and update the displayed content immediately upon each frame transition.

**See also:**
- [Section 9.1](#91-frame-sequencing) (Frame Sequencing)
- [Section 9.2](#92-animation-types-normative) (Animation Types)
- [SMIL3] Section on discrete animation

**TODO:** Add complete 7-part documentation for remaining elements:
- STAGE_BACKGROUND
- STAGE_FOREGROUND
- OVERLAY_LAYER
- SHARED_DEFINITIONS
- Frame definitions (FRAME00001, etc.)

### 6.4 Element Ordering (Normative)

Elements MUST appear in the following order:

1. `<metadata>` (optional for Basic, required for Full)
2. `<desc>` (required)
3. `<g id="ANIMATION_BACKDROP">` (required)
4. `<g id="OVERLAY_LAYER">` (required)
5. `<defs>` (required)
6. `<script>` (optional, mesh gradient polyfill only)

**Rationale:** Deterministic ordering enables:
- Single-pass parsing without backtracking
- Streaming optimization
- Safe runtime composition
- Mechanical validation

### 6.5 Frame Naming (Normative)

Frame IDs MUST follow the pattern: `FRAME` + 5-digit zero-padded number

**Valid:**
- `FRAME00001`
- `FRAME00002`
- `FRAME00099`
- `FRAME00100`

**Invalid:**
- `FRAME1` (not zero-padded)
- `FRAME_00001` (underscore not permitted)
- `frame00001` (lowercase not permitted)

**Rationale:** Consistent naming enables:
- Mechanical validation
- Sequential ordering verification
- Frame count determination
- Automated processing

### 6.6 FBF.SVG Syntax (Normative)

This section defines formal grammar for FBF-specific syntax using BNF notation.

#### 6.6.1 Animation Type Values

Animation type values specify the playback behavior of the FBF animation.

**BNF Grammar:**

```bnf
animation-type ::= "once"
                 | "once_reversed"
                 | "loop"
                 | "loop_reversed"
                 | "pingpong_once"
                 | "pingpong_loop"
                 | "pingpong_once_reversed"
                 | "pingpong_loop_reversed"
```

**Semantics:**

- `once` - Play forward from first to last frame, then stop
- `once_reversed` - Play backward from last to first frame, then stop
- `loop` - Play forward repeatedly
- `loop_reversed` - Play backward repeatedly
- `pingpong_once` - Play forward then backward once, then stop
- `pingpong_loop` - Play forward then backward repeatedly
- `pingpong_once_reversed` - Play backward then forward once, then stop
- `pingpong_loop_reversed` - Play backward then forward repeatedly

**See also:** [Section 9.2](#92-animation-types-normative)

#### 6.6.2 Frame ID Naming Pattern

Frame identifiers follow a strict naming convention to enable mechanical validation.

**BNF Grammar:**

```bnf
frame-id ::= "FRAME" frame-number
frame-number ::= digit digit digit digit digit
digit ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

**Constraints:**

- Frame numbers MUST be exactly 5 digits
- Frame numbers MUST be zero-padded (e.g., `00001`, not `1`)
- Frame IDs are case-sensitive (`FRAME` in uppercase)
- Frame numbers MUST be sequential starting from `00001`

**Examples:**

**Valid:**
```
FRAME00001
FRAME00042
FRAME00999
FRAME12345
FRAME99999
```

**Invalid:**
```
FRAME1          (not zero-padded)
frame00001      (lowercase prefix)
FRAME_00001     (underscore not permitted)
FRAME000001     (6 digits, not 5)
```

#### 6.6.3 Required Element IDs

FBF.SVG documents use fixed element IDs for the animation structure.

**BNF Grammar:**

```bnf
required-id ::= "ANIMATION_BACKDROP"
              | "STAGE_BACKGROUND"
              | "ANIMATION_STAGE"
              | "ANIMATED_GROUP"
              | "PROSKENION"
              | "STAGE_FOREGROUND"
              | "OVERLAY_LAYER"
              | "SHARED_DEFINITIONS"
```

**Constraints:**

- These IDs MUST be used exactly as specified (case-sensitive)
- Each ID MUST appear exactly once in the document
- IDs MUST be associated with the correct element type (see [Section 6.2](#62-required-elements))

**TODO:** Add complete BNF for all FBF-specific syntax patterns, including:
- SMIL animation attribute values
- Metadata field constraints
- Element ordering rules

---

## 7. Security Model

### 7.1 Threat Model

FBF.SVG is designed for **untrusted content** scenarios:
- User-generated content platforms
- LLM-generated visual interfaces
- Sandboxed rendering environments
- Strict Content Security Policy contexts

### 7.2 Security Constraints (Normative)

#### 7.2.1 Forbidden: External Resources

FBF.SVG documents MUST NOT contain references to external resources:

**Forbidden:**
```xml
<!-- ❌ External image -->
<image href="http://example.com/image.png"/>

<!-- ❌ External stylesheet -->
<link href="http://example.com/style.css"/>

<!-- ❌ External script -->
<script src="http://example.com/script.js"/>

<!-- ❌ External font -->
<style>
  @import url('http://example.com/font.css');
</style>
```

**Allowed:**
```xml
<!-- ✅ Embedded base64 image -->
<image href="data:image/png;base64,iVBORw0KG..."/>

<!-- ✅ Inline styles -->
<style>
  .class { fill: red; }
</style>
```

#### 7.2.2 Forbidden: Custom Scripts

FBF.SVG documents MUST NOT contain custom JavaScript.

**Exception:** SVG 2.0 mesh gradient polyfill is the ONLY permitted `<script>` content.

**Rationale:** Mesh gradients are part of SVG 2.0 specification but lack universal browser support. The polyfill enables cross-browser compatibility.

#### 7.2.3 CSP Compliance

FBF.SVG documents MUST be compatible with the following Content Security Policy:

```
Content-Security-Policy:
  default-src 'none';
  img-src data:;
  style-src 'unsafe-inline';
  script-src 'none';
```

**Exception:** When mesh gradient polyfill is present:
```
script-src 'unsafe-inline';
```

### 7.3 Security Testing

Conformance validators MUST verify:
1. ✅ No external resource references (href, src, @import)
2. ✅ No custom `<script>` elements (except mesh polyfill)
3. ✅ No inline event handlers (onclick, onload, etc.)
4. ✅ All resources embedded as data URIs

---

## 8. Metadata Requirements

### 8.1 Metadata Structure (Normative for Full Conformance)

FBF.SVG Full conformance requires RDF/XML metadata within the `<metadata>` element.

**Structure:**
```xml
<metadata>
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
           xmlns:dc="http://purl.org/dc/elements/1.1/"
           xmlns:fbf="http://svg2fbf.org/ns/fbf#">
    <rdf:Description rdf:about="">
      <!-- Dublin Core fields -->
      <dc:title>Animation Title</dc:title>
      <dc:creator>Creator Name</dc:creator>
      <dc:date>2024-11-10</dc:date>
      <dc:description>Description</dc:description>
      <dc:language>en</dc:language>
      <dc:rights>License</dc:rights>

      <!-- FBF custom fields -->
      <fbf:frameCount>50</fbf:frameCount>
      <fbf:fps>24.0</fbf:fps>
      <fbf:duration>2.0833</fbf:duration>
      <fbf:animationType>loop</fbf:animationType>
      <fbf:generatorName>svg2fbf</fbf:generatorName>
      <fbf:generatorVersion>0.1.2a4</fbf:generatorVersion>
    </rdf:Description>
  </rdf:RDF>
</metadata>
```

### 8.2 Required Metadata Fields (Full Conformance)

| Field | Namespace | Type | Required | Description |
|-------|-----------|------|----------|-------------|
| `title` | dc | string | ✅ Full | Animation title |
| `creator` | dc | string | ✅ Full | Current creator(s) |
| `date` | dc | ISO 8601 | ✅ Full | Creation/modification date |
| `frameCount` | fbf | integer | ✅ Full | Total number of frames |
| `fps` | fbf | float | ✅ Full | Frames per second |
| `duration` | fbf | float | ✅ Full | Total duration in seconds |
| `animationType` | fbf | enum | ✅ Full | Animation playback mode |

### 8.3 Optional Metadata Fields

| Field | Namespace | Type | Description |
|-------|-----------|------|-------------|
| `description` | dc | string | Animation synopsis |
| `language` | dc | ISO 639 | Content language |
| `rights` | dc | string | License/usage rights |
| `source` | dc | string | Original creation tool |
| `episodeNumber` | fbf | integer | Episode in series |
| `episodeTitle` | fbf | string | Episode-specific title |
| `website` | fbf | URI | Official website |

### 8.4 FBF Vocabulary Namespace

**Namespace URI:** `http://svg2fbf.org/ns/fbf#`
**Prefix:** `fbf`

Full vocabulary specification: See [FBF_METADATA_SPEC.md](FBF_METADATA_SPEC.md)

---

## 9. Animation Semantics

### 9.1 Frame Sequencing

FBF.SVG uses SMIL `<animate>` to sequence frames via the `href` attribute of the `PROSKENION` `<use>` element.

**Mechanism:**
```xml
<use id="PROSKENION" href="#FRAME00001">
  <animate
    attributeName="href"
    values="#FRAME00001;#FRAME00002;#FRAME00003"
    keyTimes="0;0.5;1"
    dur="1s"
    repeatCount="indefinite"/>
</use>
```

### 9.2 Animation Types (Normative)

FBF.SVG defines eight animation playback modes:

| Type | Behavior | repeatCount | keyTimes |
|------|----------|-------------|----------|
| `once` | START → END, STOP | `1` | Linear |
| `once_reversed` | END → START, STOP | `1` | Reverse |
| `loop` | START → END, repeat | `indefinite` | Linear |
| `loop_reversed` | END → START, repeat | `indefinite` | Reverse |
| `pingpong_once` | START → END → START, STOP | `1` | Palindrome |
| `pingpong_loop` | START → END → START, repeat | `indefinite` | Palindrome |
| `pingpong_once_reversed` | END → START → END, STOP | `1` | Reverse palindrome |
| `pingpong_loop_reversed` | END → START → END, repeat | `indefinite` | Reverse palindrome |

### 9.3 Timing Calculation

**Frame duration:** `frame_duration = 1.0 / fps`
**Total duration:** `total_duration = frame_count * frame_duration`
**keyTimes:** Equally spaced from 0 to 1

**Example (24 fps, 3 frames):**
- Frame duration: 1/24 = 0.04167s
- Total duration: 3 * 0.04167 = 0.125s
- keyTimes: `0; 0.5; 1`

### 9.4 Interactive Triggers

FBF.SVG MAY support user-triggered animation via SMIL `begin` attribute:

```xml
<animate begin="click" dur="1s" repeatCount="1"/>
```

**Use Case:** Animated buttons, interactive controls

---

## 10. Streaming Architecture

### 10.1 Frames-at-End Design

FBF.SVG places frame definitions (`<defs>`) AFTER animation structure.

**Rationale:** Enables real-time frame appending without interrupting playback:
1. Parser processes animation structure first
2. SMIL animation begins referencing initial frames
3. Additional frames appended to `<defs>` during playback
4. Animation continues seamlessly with new frames

### 10.2 Streaming Use Cases

- **Live presentations:** Real-time slide conversion to vector
- **LLM content generation:** On-demand frame creation
- **Remote rendering:** Streaming vector visualization
- **Interactive tutorials:** Progressive frame revelation

### 10.3 Implementation Notes

- Frame references use `href="#FRAME00001"` (not hardcoded indexes)
- SMIL `values` attribute updated dynamically as frames added
- No DOM manipulation of animation structure required

---

## 11. Interactive Visual Communication

### 11.1 LLM Visual Protocol

FBF.SVG supports bidirectional visual communication between language models and users.

**Traditional Text Interaction:**
```
LLM → Text description → User reads text → User acts
```

**FBF.SVG Visual Interaction:**
```
LLM → FBF.SVG interface → User clicks/selects → Coordinates sent to LLM → LLM updates visual
```

### 11.2 Benefits

- **Declarative:** LLM generates pure SVG, no imperative code
- **Context-adaptive:** Interfaces adjust to conversation state
- **Bidirectional:** User input coordinates returned to LLM
- **Deterministic:** No runtime errors from generated code

### 11.3 Example Use Cases

- **Technical repair:** Component identification in diagrams
- **Visual information retrieval:** Dynamic menu generation
- **Diagnostic analysis:** Schematic with interactive elements

---

## 12. Examples

### 12.1 Minimal FBF.SVG Basic Document

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.1"
     viewBox="0 0 800 600" width="800" height="600">

  <desc>Minimal FBF.SVG Basic Example</desc>

  <g id="ANIMATION_BACKDROP">
    <g id="STAGE_BACKGROUND"></g>
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" href="#FRAME00001">
          <animate attributeName="href"
                   values="#FRAME00001;#FRAME00002"
                   keyTimes="0;1"
                   dur="1s"
                   repeatCount="indefinite"/>
        </use>
      </g>
    </g>
    <g id="STAGE_FOREGROUND"></g>
  </g>

  <g id="OVERLAY_LAYER"></g>

  <defs>
    <g id="SHARED_DEFINITIONS"></g>

    <g id="FRAME00001">
      <circle cx="400" cy="300" r="50" fill="red"/>
    </g>

    <g id="FRAME00002">
      <circle cx="400" cy="300" r="75" fill="blue"/>
    </g>
  </defs>
</svg>
```

### 12.2 FBF.SVG Full Document with Metadata

See [Appendix A](#appendix-a-complete-fbf-svg-full-example) for complete example.

---

## 13. Validation and Testing

### 13.1 Validation Requirements

FBF.SVG conformance validators MUST check:

1. ✅ XML well-formedness
2. ✅ SVG validity (namespace, version)
3. ✅ Element hierarchy correctness
4. ✅ Required element presence
5. ✅ Element ordering
6. ✅ Frame ID naming convention
7. ✅ Security constraints (no external resources)
8. ✅ SMIL animation correctness
9. ✅ Metadata completeness (Full conformance only)

### 13.2 Reference Validator

The reference implementation includes a Python validator:

```bash
uv run python scripts/validate_fbf.py animation.fbf.svg
```

**Exit Codes:**
- `0` - Valid
- `1` - Invalid structure
- `2` - Invalid metadata
- `3` - Security violation

### 13.3 XML Schema Validation

XSD schema available: [fbf-svg.xsd](fbf-svg.xsd)

```bash
xmllint --schema fbf-svg.xsd animation.fbf.svg
```

---

## 14. Implementation Considerations

### 14.1 Generator Requirements

Tools generating FBF.SVG documents SHOULD:

1. Implement element deduplication for file size optimization
2. Generate sequential frame IDs starting from `FRAME00001`
3. Calculate accurate timing values for SMIL animation
4. Embed all external resources as base64 data URIs
5. Generate complete RDF/XML metadata (for Full conformance)
6. Validate output against XSD schema

### 14.2 Player Requirements

Browsers/players rendering FBF.SVG documents MUST:

1. Support SVG 1.1 or 2.0
2. Support SMIL declarative animation
3. Honor `<use>` element with `href` animation
4. Respect `repeatCount` and timing attributes

**No special player implementation required** - standard SVG renderers work.

### 14.3 Performance Considerations

- **File size:** Use element deduplication to minimize redundancy
- **Rendering:** Modern browsers handle SMIL efficiently
- **Memory:** Large frame counts (>200) may impact memory usage
- **Streaming:** Frame appending should be rate-limited

---

## 15. Internationalization

### 15.1 Text Content

FBF.SVG documents SHOULD specify content language in metadata:

```xml
<dc:language>en</dc:language>
```

### 15.2 Text Rendering

Frame content MAY use `<text>` elements with proper language attributes:

```xml
<text xml:lang="ja">日本語テキスト</text>
```

### 15.3 Bi-Directional Text

FBF.SVG supports SVG `direction` and `unicode-bidi` attributes for RTL languages.

---

## 16. Accessibility

### 16.1 Alternative Text

FBF.SVG documents SHOULD include descriptive `<desc>` elements:

```xml
<desc>Character walking animation showing 8-frame walk cycle</desc>
```

### 16.2 ARIA Support

FBF.SVG MAY include ARIA attributes for screen reader support:

```xml
<svg role="img" aria-label="Animated button">
```

### 16.3 Animation Control

Interactive FBF.SVG documents SHOULD provide user control over animation playback (pause/play).

---

## 17. Security Considerations

See [Section 7](#7-security-model) for complete security model.

**Summary:**
- No external resources (prevents XSS)
- No custom scripts (CSP-compliant)
- Self-contained documents (sandboxed rendering)
- Mechanical validation (conformance checking)

---

## 18. Privacy Considerations

FBF.SVG documents:

- **Do not track users** (no analytics, beacons)
- **Do not make network requests** (self-contained)
- **May contain creator metadata** (attribution, licensing)
- **May be analyzed** (metadata extraction, frame counting)

**Recommendation:** Generators should allow metadata stripping for privacy-sensitive content.

---

## 19. Future Directions

### 19.1 Potential Extensions

- **Audio synchronization:** SMIL audio integration
- **Interactive overlays:** Click-triggered content
- **Advanced streaming:** Adaptive quality based on bandwidth
- **Compression:** Specialized FBF.SVG compression format
- **3D integration:** WebXR/3D scene embedding

### 19.2 Browser Implementation

- **Native FBF.SVG support:** Browser recognition of FBF.SVG mime type
- **Developer tools:** FBF.SVG debugging and timeline inspection
- **Performance optimizations:** Specialized rendering paths

### 19.3 Standardization Path

1. Community review (current phase)
2. Reference implementation testing
3. W3C SVG Working Group submission
4. W3C Candidate Recommendation
5. W3C Recommendation

---

## 20. Acknowledgments

FBF.SVG originated from the OpenToonz open source project and community feedback.

**Contributors:**
- Emanuele Sabetta ([@Emasoft](https://github.com/Emasoft)) - Format design, reference implementation
- OpenToonz Community - Use case requirements, testing

**Special Thanks:**
- W3C SVG Working Group
- Scour Project (SVG optimization algorithms)
- NumPy Project

---

## 21. References

### 21.1 Normative References

**[SVG11]**
Scalable Vector Graphics (SVG) 1.1 (Second Edition)
Jon Ferraiolo, Jun Fujisawa, Dean Jackson. W3C. 16 August 2011. W3C Recommendation.
Latest version: https://www.w3.org/TR/SVG11/
Referenced version: https://www.w3.org/TR/2011/REC-SVG11-20110816/

**[SVG2]**
Scalable Vector Graphics (SVG) 2.0
Nikos Andronikos, Rossen Atanassov, Tavmjong Bah, Amelia Bellamy-Royds, Brian Birtles, Cyril Concolato, Erik Dahlström, Chris Lilley, Cameron McCormack, Doug Schepers, Dirk Schulze, Richard Schwerdtfeger, Satoru Takagi, Jonathan Watt. W3C.
Latest version: https://www.w3.org/TR/SVG2/
Editor's Draft: https://svgwg.org/svg2-draft/

**[SMIL3]**
Synchronized Multimedia Integration Language (SMIL 3.0)
Dick Bulterman, Jack Jansen, Pablo Cesar, Sjoerd Mullender, Daniel Zucker, Eric Hyche, Marisa DeMeglio, Julien Quint, Thierry Michel, Kenichi Kubota, Katsuhiko Yamaoka. W3C. 1 December 2008. W3C Recommendation.
Latest version: https://www.w3.org/TR/SMIL3/
Referenced version: https://www.w3.org/TR/2008/REC-SMIL3-20081201/

**[RFC2119]**
Key words for use in RFCs to Indicate Requirement Levels
S. Bradner. IETF. March 1997.
URL: https://www.ietf.org/rfc/rfc2119.txt

**[RDF-SYNTAX]**
RDF/XML Syntax Specification (Revised)
Dave Beckett, Brian McBride. W3C. 10 February 2004. W3C Recommendation.
Latest version: https://www.w3.org/TR/rdf-syntax-grammar/
Referenced version: https://www.w3.org/TR/2004/REC-rdf-syntax-grammar-20040210/

**[DCTERMS]**
Dublin Core Metadata Terms
DCMI Usage Board. 20 January 2020. DCMI Recommendation.
Latest version: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
Referenced version: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/2020-01-20/

### 21.2 Informative References

**[CSP]**
Content Security Policy Level 3
Mike West, Antonio Sartori. W3C. 13 September 2021. W3C Working Draft.
Latest version: https://www.w3.org/TR/CSP/
Referenced version: https://www.w3.org/TR/2021/WD-CSP3-20210913/

**[OPENTOONZ-5346]**
OpenToonz Issue #5346: Vector animation format proposal
OpenToonz Project. GitHub. June 2022.
URL: https://github.com/opentoonz/opentoonz/issues/5346

**[XML]**
Extensible Markup Language (XML) 1.0 (Fifth Edition)
Tim Bray, Jean Paoli, C. M. Sperberg-McQueen, Eve Maler, François Yergeau. W3C. 26 November 2008. W3C Recommendation.
Latest version: https://www.w3.org/TR/xml/
Referenced version: https://www.w3.org/TR/2008/REC-xml-20081126/

**[XML-NAMES]**
Namespaces in XML 1.0 (Third Edition)
Tim Bray, Dave Hollander, Andrew Layman, Richard Tobin, Henry S. Thompson. W3C. 8 December 2009. W3C Recommendation.
Latest version: https://www.w3.org/TR/xml-names/
Referenced version: https://www.w3.org/TR/2009/REC-xml-names-20091208/

**[DOM2]**
Document Object Model (DOM) Level 2 Core Specification
Arnaud Le Hors, Philippe Le Hégaret, Lauren Wood, Gavin Nicol, Jonathan Robie, Mike Champion, Steve Byrne. W3C. 13 November 2000. W3C Recommendation.
Latest version: https://www.w3.org/TR/DOM-Level-2-Core/
Referenced version: https://www.w3.org/TR/2000/REC-DOM-Level-2-Core-20001113/

---

## 22. Appendices

### Appendix A: Complete FBF.SVG Full Example

[See FBF_SVG_SPECIFICATION.md for complete example]

### Appendix B: XSD Schema

[See fbf-svg.xsd]

### Appendix C: Animation Type Reference

[See Section 9.2]

### Appendix D: Security Test Vectors

[Examples of forbidden content for validation testing]

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 0.1.2a4 | 2024-11 | Initial proposal draft |

---

**End of Document**

---

<p align="center">
  <strong>Made with ❤️ for the OpenToonz community</strong><br>
  <a href="https://github.com/Emasoft/svg2fbf">svg2fbf</a> •
  <a href="https://github.com/Emasoft/svg2fbf/issues">Issues</a> •
  <a href="https://github.com/Emasoft/svg2fbf/discussions">Discussions</a>
</p>
