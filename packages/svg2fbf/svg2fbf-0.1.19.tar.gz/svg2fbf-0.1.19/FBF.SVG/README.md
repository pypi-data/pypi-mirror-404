# FBF.SVG Format Standard

**Frame-by-Frame SVG** — A candidate substandard of the SVG specification for declarative frame-by-frame animations

---

## Overview

**FBF.SVG** (Frame-by-Frame SVG) is a proposed **candidate substandard of the SVG specification**, analogous to SVG Tiny and SVG Basic. It defines a constrained, optimized profile for declarative frame-by-frame animations that are valid SVG 1.1/2.0 documents with additional structural and conformance requirements.

### Purpose

FBF.SVG aims to be the **MP4 of vector animations** — a standardized, open, widely compatible format for frame-by-frame vector content that:

- Is declarative (no imperative JavaScript required)
- Is secure by default (strict Content Security Policy compliance)
- Is streamable (real-time frame addition without playback interruption)
- Is self-documenting (comprehensive embedded metadata)
- Is mechanically validatable (formal XML Schema Definition)

### Origin

The FBF.SVG format originated from [OpenToonz Issue #5346](https://github.com/opentoonz/opentoonz/issues/5346), addressing the need for an open vector animation format for the OpenToonz professional 2D animation software. The first FBF.SVG files were published on [CodePen](https://codepen.io/Emasoft/pen/vYWwdZm) in June 2022.

---

## Design Principles

The FBF.SVG format is designed around eight core principles:

1. **SVG Compatibility** - Every FBF.SVG document is a valid SVG document
2. **Declarative Animation** - Uses SMIL timing, not imperative scripting
3. **Security First** - No external resources; strict Content Security Policy compliance
4. **Optimization** - Smart deduplication and shared definitions minimize file size
5. **Validatability** - Mechanically validatable against formal schema
6. **Self-Documentation** - Comprehensive embedded metadata in RDF/XML format
7. **Streaming Architecture** - Unlimited real-time frame addition without playback interruption
8. **Interactive Visual Communication** - Bidirectional LLM-to-user visual interaction protocol

---

## Conformance Levels

The FBF.SVG specification defines two conformance levels:

### FBF.SVG Basic

Core structural and animation requirements:
- ✅ Valid SVG 1.1/2.0 document structure
- ✅ Required FBF element hierarchy and ordering
- ✅ SMIL-based frame-by-frame animation
- ✅ Self-contained (no external resources)
- ✅ Security compliant (no external scripts)

### FBF.SVG Full

Basic conformance plus comprehensive metadata:
- ✅ All FBF.SVG Basic requirements
- ✅ Complete RDF/XML metadata block
- ✅ Dublin Core metadata fields
- ✅ FBF custom vocabulary
- ✅ Production-ready quality

**The svg2fbf tool generates FBF.SVG Full conformant documents.**

---

## Format Structure

### Element Hierarchy

```
SVG Root
├── metadata (RDF/XML, optional for Basic, required for Full)
├── desc (required)
├── ANIMATION_BACKDROP (extensibility point for layered composition)
│   ├── STAGE_BACKGROUND (Z-order: behind animation)
│   ├── ANIMATION_STAGE
│   │   └── ANIMATED_GROUP
│   │       └── PROSKENION
│   │           └── <animate>
│   └── STAGE_FOREGROUND (Z-order: in front of animation)
├── OVERLAY_LAYER (Z-order: superimposed on all)
├── defs
│   ├── SHARED_DEFINITIONS (shared elements)
│   └── FRAME00001, FRAME00002, ... (frame definitions)
└── script (optional, mesh gradient polyfill only)
```

### Strict Ordering Requirements

The FBF.SVG specification mandates deterministic element ordering for:

1. **Streaming optimization** - Single-pass parsing without DOM traversal
2. **Safe composition** - Three extension points for runtime content injection
3. **Z-order layering** - Deterministic rendering precedence
4. **Security validation** - Mechanical conformance verification

### Visual Representation

<p align="center">
  <img src="fbf_schema.svg" alt="FBF.SVG Structure Schema" width="900"/>
</p>

---

## Documentation

### Core Specification Documents

| Document | Status | Description |
|----------|--------|-------------|
| **[FBF_SVG_FORMAT_PROPOSAL_DRAFT.md](FBF_SVG_FORMAT_PROPOSAL_DRAFT.md)** | 📋 **W3C Submission Draft** | Formal standards body proposal with complete specification skeleton |
| **[FBF_PROS_AND_CONS.md](FBF_PROS_AND_CONS.md)** | 💬 **Discussion Core** | Collaborative analysis of arguments for/against W3C standardization |
| **[FBF_SVG_SPECIFICATION.md](FBF_SVG_SPECIFICATION.md)** | 📐 Technical Spec | Complete technical specification (v0.1.2a4) |
| **[fbf-svg.xsd](fbf-svg.xsd)** | ✅ Schema | XML Schema Definition for mechanical validation |
| **[FBF_METADATA_SPEC.md](FBF_METADATA_SPEC.md)** | 📊 Metadata | RDF/XML vocabulary and metadata requirements |
| **[FBF_FORMAT.md](FBF_FORMAT.md)** | 🛠️ Guide | Technical implementation guide for developers |
| **[FBF_SVG_PROPOSAL.md](FBF_SVG_PROPOSAL.md)** | 📜 Original | Original proposal with use cases and rationale |

### Diagrams and Schema

| File | Description |
|------|-------------|
| **[fbf_schema.svg](fbf_schema.svg)** | Visual representation of FBF structure |
| **[fbf_structure.svg](fbf_structure.svg)** | Detailed structure diagram |
| **[fbf_structure.mmd](fbf_structure.mmd)** | Mermaid source for structure diagram |

---

## Key Features

### 1. Frame-by-Frame Animation with SMIL

FBF.SVG uses SMIL (Synchronized Multimedia Integration Language) for declarative animation timing:

```xml
<animate
    attributeName="href"
    values="#FRAME00001;#FRAME00002;#FRAME00003"
    keyTimes="0;0.5;1"
    dur="1s"
    repeatCount="indefinite"/>
```

### 2. Element Deduplication

Hash-based identification eliminates redundant elements across frames:
- Identical SVG elements are stored once in `SHARED_DEFINITIONS`
- Frames reference shared elements via `<use>` elements
- Significant file size reduction for animations with static elements

### 3. Streaming Architecture

Frames-at-end design enables real-time frame appending:
- Animation control structure appears before frame definitions
- New frames can be appended without interrupting playback
- Enables live presentations, LLM-generated content, and remote rendering

### 4. Interactive Visual Communication

Bidirectional visual protocol for AI-to-user interaction:
- LLM generates interactive SVG interfaces
- User provides coordinate-based input with element identification
- LLM responds with contextual visual updates
- No imperative code generation required

### 5. Three Extension Points

Safe runtime composition via designated Z-order layers:
- **STAGE_BACKGROUND** - Behind animation (backdrop, scenery)
- **STAGE_FOREGROUND** - In front of animation (overlays, UI elements)
- **OVERLAY_LAYER** - Superimposed on all (badges, titles, subtitles, borders, PiP)

---

## Animation Types

FBF.SVG supports eight playback modes:

| Animation Type | Behavior | Use Case |
|----------------|----------|----------|
| `once` | START → END, then STOP | Splash screens, transitions |
| `once_reversed` | END → START, then STOP | Reverse transitions |
| `loop` | START → END, repeat FOREVER | Background animations |
| `loop_reversed` | END → START, repeat FOREVER | Reverse loops |
| `pingpong_once` | START → END → START, then STOP | Single bounce effect |
| `pingpong_loop` | START → END → START, repeat FOREVER | Breathing effects, character animations |
| `pingpong_once_reversed` | END → START → END, then STOP | Reverse bounce |
| `pingpong_loop_reversed` | END → START → END, repeat FOREVER | Reverse continuous bounce |

---

## Security Model

FBF.SVG enforces strict security constraints:

### ✅ Allowed
- SMIL declarative animations
- Embedded resources (base64 data URIs)
- SVG 2.0 mesh gradient polyfill (only permitted JavaScript)
- Click-triggered animations (`begin="click"`)

### ❌ Forbidden
- External resource references (images, fonts, stylesheets)
- Custom JavaScript (except mesh gradient polyfill)
- External scripts via `<script src="...">`
- iframe embedding
- XMLHttpRequest or fetch() API calls

This design ensures FBF.SVG documents are:
- Self-contained and portable
- Safe for untrusted content
- Compatible with strict Content Security Policies
- Suitable for sandboxed environments

---

## Validation

FBF.SVG documents can be validated using:

### XML Schema Validation
```bash
xmllint --schema FBF.SVG/fbf-svg.xsd animation.fbf.svg
```

### Python Validator Script
```bash
uv run python scripts/validate_fbf.py animation.fbf.svg --verbose
```

The validator checks:
- ✅ XML well-formedness
- ✅ SVG validity
- ✅ FBF structural requirements
- ✅ SMIL animation correctness
- ✅ Security constraints
- ✅ Metadata completeness (Full conformance)
- ✅ Frame reference integrity

---

## Use Cases

### Traditional Animation
- Character animation
- Motion graphics
- Explainer videos
- Educational content

### Interactive Applications
- Animated UI components
- Click-triggered transitions
- Interactive buttons and controls
- Game sprites and effects

### Advanced Applications
- LLM visual interfaces
- Real-time streaming presentations
- Remote vector rendering
- Dynamic data visualization

---

## Browser Support

FBF.SVG requires SMIL animation support:

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome/Edge | ✅ Full | Best support |
| Firefox | ✅ Full | Complete support |
| Safari | ✅ Full | Full support |
| IE11 | ❌ None | No SMIL support |

---

## Implementation Tools

### svg2fbf Generator
The reference implementation for generating FBF.SVG documents:
- [svg2fbf on GitHub](https://github.com/Emasoft/svg2fbf)
- Converts SVG frame sequences to FBF.SVG animations
- Generates FBF.SVG Full conformant documents
- Command-line tool with YAML-based configuration

### Validation Tools
- **validate_fbf.py** - Python validator script
- **fbf-svg.xsd** - XML Schema Definition for mechanical validation

---

## Contributing to the Standard

FBF.SVG is an open specification under active development. Contributions welcome:

### Specification Development
- Propose new features or clarifications
- Submit use cases and requirements
- Improve documentation and examples
- Report ambiguities or issues

See the comprehensive contribution guides:
- **[CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md)** - Vision, goals, and principles (WHAT/WHY)
- **[DEVELOPING_FORMAT.md](DEVELOPING_FORMAT.md)** - Practical procedures and style guide (HOW)

### Discussion
- [GitHub Discussions](https://github.com/Emasoft/svg2fbf/discussions)
- [Issue Tracker](https://github.com/Emasoft/svg2fbf/issues)

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| v0.1.2a4 | 2024 | Alpha | Current version |
| v0.1.0 | 2022 | Prototype | Initial CodePen release |

---

## License

The FBF.SVG specification and documentation are released under the Apache License 2.0, allowing free use, modification, and distribution.

See [LICENSE](../LICENSE) for details.

---

## Acknowledgments

FBF.SVG is part of the OpenToonz open source initiative, created to provide an open, standardized format for vector frame-by-frame animation.

**Made with ❤️ for the OpenToonz community**

---

<p align="center">
  <a href="https://github.com/Emasoft/svg2fbf">svg2fbf</a> •
  <a href="https://github.com/Emasoft/svg2fbf/issues">Issues</a> •
  <a href="https://github.com/Emasoft/svg2fbf/discussions">Discussions</a>
</p>
