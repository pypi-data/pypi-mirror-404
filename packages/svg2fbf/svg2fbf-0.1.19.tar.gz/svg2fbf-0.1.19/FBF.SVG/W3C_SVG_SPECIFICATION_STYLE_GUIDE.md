# W3C SVG Specification Style Guide
## Analysis of SVG Tiny 1.2 for FBF.SVG Proposal

**Source Document:** W3C SVG Tiny 1.2 Specification (Working Draft, 15 September 2008)
**Analysis Date:** 2025-11-10
**Purpose:** Extract structural patterns, writing style, and formatting conventions for FBF.SVG proposal

---

## Table of Contents

1. [Document Structure](#1-document-structure)
2. [Writing Style and Technical Language](#2-writing-style-and-technical-language)
3. [Conformance Language Patterns](#3-conformance-language-patterns)
4. [Example Presentation](#4-example-presentation)
5. [References and Citations](#5-references-and-citations)
6. [Diagrams and Visual Elements](#6-diagrams-and-visual-elements)
7. [Abstract and Status Sections](#7-abstract-and-status-sections)
8. [Appendices Structure](#8-appendices-structure)
9. [Formatting Conventions](#9-formatting-conventions)
10. [Recommendations for FBF.SVG](#10-recommendations-for-fbfsvg)

---

## 1. Document Structure

### 1.1 Overall Architecture

W3C specifications follow a formal standards document structure with clear progression from foundational concepts through technical details to comprehensive appendices.

**Front Matter:**
- Title and metadata (version date, editors, copyright notice)
- Abstract (single focused paragraph)
- Status of This Document (multi-paragraph with process details)
- Complete table of contents with standard and expanded versions

**Main Content:**
- Numbered chapters (1-19 in SVG Tiny 1.2)
- Sequential organization from introduction to advanced topics

**Back Matter:**
- Letter-designated appendices (A-T)
- Specialized reference materials

### 1.2 Chapter Organization Pattern

The SVG specification demonstrates progressive technical deepening:

1. **Introduction (Chapter 1)**
   - About the specification
   - Profile definition
   - Defining documents
   - MIME types and compatibility
   - Definitions
   - Terminology and conventions

2. **Foundational Concepts (Chapters 2-3)**
   - High-level concepts (informative)
   - Rendering model (normative)

3. **Building Blocks (Chapters 4-10)**
   - Basic data types
   - Document structure
   - Styling
   - Coordinate systems
   - Paths, shapes, text

4. **Advanced Features (Chapters 11-16)**
   - Painting, multimedia, interactivity
   - Linking, scripting, animation

5. **Supporting Systems (Chapters 17-19)**
   - Fonts, metadata, extensibility

### 1.3 Numbering System

**Pattern:** Decimal notation with three levels of depth
- Chapters: `1`, `2`, `3`...`19`
- Major sections: `1.1`, `1.2`, `1.3`
- Subsections: `1.2.1`, `1.2.2`
- Sub-subsections: `1.2.1.1` (rarely used)

**Appendices:** Letter designations with internal numbering
- `A.1`, `A.2`, `A.3`
- `B.1`, `B.2`, `B.3`

### 1.4 Information Flow

The document accommodates both:
- **Sequential reading:** Progressive complexity, building on prior concepts
- **Reference lookup:** Extensive cross-linking, indexed appendices

**Flow pattern:**
1. Abstract context (what, why)
2. Foundational definitions (core vocabulary)
3. Implementation details (how)
4. Normative requirements (must/should)
5. Informative guidance (best practices)

---

## 2. Writing Style and Technical Language

### 2.1 Requirement Definition Structures

**Formal declarative patterns for requirements:**

```
Pattern 1: Direct obligation
"nested 'svg' elements are unsupported elements and must not be rendered"

Pattern 2: Conditional requirement
"If 'timelineBegin' is 'onLoad', then..."

Pattern 3: Embedded obligation
"must be computed exclusive of..."
```

**Voice patterns:**
- **Passive voice dominates:** "must be computed," "are required to"
- **Present tense:** Consistent for current behaviors
- **Imperative mood:** For implementer instructions

### 2.2 Technical Terminology Introduction

Three mechanisms for introducing terms:

#### 2.2.1 Formal Definitions
Dedicated glossary sections with italicized terms followed by explanatory prose:

```
**bounding box**: A paint represents a way of putting color values
onto the canvas [detailed explanation follows]
```

#### 2.2.2 Inline References
Using element notation with bracketed names and anchor links:

```
['svg'](#struct-SVGElement)
['viewBox'](#struct-ViewBox)
```

#### 2.2.3 Layered Complexity
Progressive revelation starting simple, then adding nuance:

1. Accessible explanation (plain language)
2. Technical precision (formal definition)
3. Edge cases and constraints
4. Implementation details

### 2.3 Concept Introduction Strategy

**Standard progression for complex ideas:**

1. **Plain language overview**
   - "A paint represents a way of putting color values onto the canvas"

2. **Formal definition with precise scope**
   - Technical constraints and mathematical precision

3. **Contextual examples or cross-references**
   - Code samples or visual diagrams

4. **Implementation constraints and edge cases**
   - Error handling, boundary conditions

### 2.4 Transition Phrases

**Common connective patterns:**
- "See [topic]" — cross-references
- "Note that" — clarifications
- "For further details" — directing to detailed sections
- "For example" or "For instance" — introducing illustrations
- "The following describes" — previewing content organization

### 2.5 Complex Concept Decomposition

**Example: Bounding box section structure**

1. Intuitive summary
2. Geometric formula
3. Visual example with code
4. Edge cases ("must enclose all portions... not just end points")
5. Implementation rules
6. Computational requirements

This scaffolding allows readers at different technical levels to extract relevant information.

---

## 3. Conformance Language Patterns

### 3.1 RFC 2119 Keywords

The specification uses standard RFC 2119 terminology, though often embedded in natural prose rather than capitalized:

**MUST (mandatory requirement):**
```
"must not be rendered"
"must be computed exclusive of"
"must enclose all portions"
```

**SHOULD (strong recommendation):**
```
"should be 1.2" (for version attribute)
"It is recommended that SVG files have the extension '.svg'"
```

**MAY (optional/permissive):**
```
"may run a separate program or plug-in"
```

### 3.2 Alternative Requirement Framing

Rather than relying on capitalized keywords, conformance is often expressed through:
- "are required to"
- "shall have"
- "must be computed"

### 3.3 Conformance Categories

**Distinct conformance classes defined separately (typically in Appendix D):**

1. **SVG Content Conformance**
   - Documents themselves
   - Well-formedness requirements
   - Validity constraints

2. **SVG Writer Conformance**
   - Generators, authoring tools, servers
   - Output requirements

3. **SVG Reader Conformance**
   - Interpreters, viewers, browsers
   - Rendering requirements
   - Feature support

4. **Extension and Encoding Conformance**
   - Custom elements and attributes
   - Character encoding requirements

### 3.4 Lacuna Values

**Unique conformance mechanism:**
Behaviors that apply when attributes remain unspecified, bridging XML parsing and application-layer interpretation.

### 3.5 Non-Conformance Description

**Two categories:**

1. **"in error"** — explicitly wrong, violates specification
2. **"unsupported value"** — non-conforming but not formally wrong

```
"An unsupported value is a value that does not conform to this
specification, but is not specifically listed as being in error"
```

This dual approach provides implementers nuance regarding problematic content.

### 3.6 Normative vs Informative Distinction

**Formatting conventions:**
- Normative definitions cluster in dedicated sections
- Informative chapters receive explicit labeling:
  ```
  This chapter is informative.
  ```
- Implementation Requirements and Conformance Criteria in appendices
- Error handling guidance typically in Appendix C

---

## 4. Example Presentation

### 4.1 Code Example Formatting

**Simple, unadorned code blocks:**
```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny"
     viewBox="0 0 30 30">
```

**Characteristics:**
- Plain text rendering (no syntax highlighting)
- Monospace font
- Delimited blocks
- Maintains accessibility across viewing contexts

### 4.2 Introduction and Labeling

**Formal labeling pattern:**
```
Example: [filename.svg]
```

**Examples:**
- `Example: [01_01.svg]`
- `Example: [bbox01.svg]`

**Pattern:**
1. Introductory prose (explains purpose)
2. Formal label with filename
3. Code block
4. Explanatory discussion (if needed)

### 4.3 Text-to-Code Ratio

**High ratio of explanatory prose to code:**
- Substantial paragraphs of normative text discuss concepts
- Brief code illustrations follow
- Priority on conceptual understanding over code-first presentation

### 4.4 Example Completeness

**Two patterns:**

1. **Complete, runnable documents**
   - Include XML declarations
   - Full namespace declarations
   - Can be executed as-is

2. **Focused fragments**
   - Show only relevant element snippets
   - Assume broader context
   - Used within larger discussions

### 4.5 Integration with Normative Content

**Examples serve as concrete illustrations:**
- Appear after formal definitions
- Demonstrate practical application of stated rules
- Bridge abstract specification to concrete implementation

```
Pattern:
1. Normative definition
2. Example code
3. Visual rendering (if applicable)
4. Discussion of what the example demonstrates
```

### 4.6 Visual Output Presentation

**When graphical output matters:**
- Include rendered PNG images alongside SVG source
- Reference format: `![Rendering](examples/bbox01.png)`
- Bridges abstract specification with visual result

### 4.7 Multiple Variations

**Sequential examples with distinct filenames:**
- `bbox01.svg` — correct bounding box
- `bbox02.svg` — incorrect bounding box (variant 1)
- `bbox03.svg` — incorrect bounding box (variant 2)

Allows comparison without cluttering single examples with conditional syntax.

---

## 5. References and Citations

### 5.1 Citation Format

**Bracketed notation with capitalized acronyms:**
```
[XML10]
[SMIL21]
[DOM3]
[CSS2]
```

### 5.2 Reference Categories

**Two distinct types in separate sections:**

#### 5.2.1 Normative References (Appendix S.1)
Standards that implementations must follow:
- XML specifications
- Unicode standards
- Core web standards (CSS, DOM, etc.)

#### 5.2.2 Informative References (Appendix S.2)
Supporting materials and background information:
- Related specifications
- Academic papers
- Explanatory resources

### 5.3 Citation Style Details

**W3C Specification Pattern:**
```
[ACRONYM] "Full Title in Quotation Marks",
Organization, Year Status.
URL: http://www.w3.org/TR/[specification-id]/
```

**Example:**
```
[SVG11] "Scalable Vector Graphics (SVG) 1.1 Specification",
W3C, 2003 Recommendation.
http://www.w3.org/TR/2003/REC-SVG11-20030114/
```

**External Standards:**
Similar formatting but may include RFC numbers or alternate repositories:
```
[RFC2119] "Key words for use in RFCs to Indicate Requirement Levels",
S. Bradner, March 1997.
http://www.ietf.org/rfc/rfc2119.txt
```

### 5.4 Draft vs Final Specification Distinction

**Working Draft:**
```
"W3C Working Draft 15 September 2008"
```

**Recommendation (final):**
```
"W3C Recommendation"
```

**Last Call Working Draft:**
```
"W3C Last Call Working Draft"
```

Citations include version dates and draft designations for work-in-progress materials.

### 5.5 Inline Reference Examples

**Combined URL and acronym pattern:**
```
Defined in the [XSL Area Model](link) ([XSL](#refs-ref-XSL), section 4.2.3)
```

Components:
1. Descriptive text with hyperlink
2. Bracketed acronym
3. Section reference (when applicable)

---

## 6. Diagrams and Visual Elements

### 6.1 Types of Diagrams

**Primary visual medium:** SVG examples (fitting for SVG specification)

**Diagram types used:**
- Geometric illustrations (bounding boxes, coordinate systems)
- Element relationship diagrams
- Rendering examples
- Conceptual visualizations

### 6.2 Integration into Text Flow

**Embedded directly within relevant sections:**
- Follow concept definitions
- SVG code provided inline
- Rendered as PNG preview for accessibility

Pattern:
```
1. Concept definition (prose)
2. SVG code block
3. Rendered output (PNG)
4. Discussion of what diagram shows
```

### 6.3 Figure Numbering and Captioning

**Example-based naming:**
```
bbox01.svg (source)
bbox01.png (rendered output)
```

**Captions include:**
- Descriptive titles
- `<desc>` elements within SVG source
- Explanatory labels ("Correct Bounding Box" vs "Incorrect Bounding Box")

### 6.4 Diagram-to-Text References

**Explicit reference patterns:**
```
"Example bbox01 shows one shape... with three possible bounding boxes."
```

Provides traceable linkage between prose and visual demonstrations.

### 6.5 Image Formats

**Dual approach:**
1. **SVG source code** — embedded directly in specification
2. **PNG renderings** — referenced as visual output

This showcases SVG's capabilities while accommodating readers needing raster previews.

### 6.6 Tables for Structured Information

**Extensive use in appendices:**
- Element Table (Appendix K)
- Attribute and Property Tables (Appendix L)
- Media Type Registration tables

**Purpose:** Organize normative reference material systematically

### 6.7 Visual Formatting of Definitions

**Structured formatting:**
- Terms in **bold**
- Followed by detailed explanations
- Embedded examples when helpful
- Cross-references to related terms

---

## 7. Abstract and Status Sections

### 7.1 Abstract Section

**Structure:** Single focused paragraph

**Content coverage:**
1. What the specification defines
2. Technical capabilities
3. Intended use cases
4. Target platforms (when applicable)

**Example from SVG Tiny 1.2:**
```
"This specification defines the features and syntax for
Scalable Vector Graphics (SVG) Tiny, Version 1.2, a language
for describing two-dimensional vector and mixed vector/raster
graphics in XML."
```

**Characteristics:**
- No metadata (that goes in Status section)
- Purely technical scope
- Self-contained
- Written for technical audience

### 7.2 Status of This Document Section

**Structure:** Multi-paragraph, multi-layered

**Required components:**

1. **Opening Disclaimer**
   ```
   "This section describes the status of this document at the
   time of its publication. Other documents may supersede this
   document."
   ```

2. **Detailed Status Statement**
   - Date of publication
   - Document maturity level (Working Draft, Last Call, etc.)
   - Working Group identification

3. **Process Timeline**
   - Advancement plans
   - Implementation requirements
   - Key milestones and dates

4. **Comment Procedures**
   - Email address for feedback
   - Subject line requirements
   - Comment deadline
   - Subscription instructions

5. **Change History Reference**
   - Points to appendix with detailed changes

6. **Working Group Identification**
   - Names the responsible W3C Working Group
   - Activity area

7. **Patent Policy Statement**
   - References W3C Patent Policy
   - Disclosure processes
   - Essential claims definitions

8. **Legal Disclaimer**
   - Draft material notice
   - Citation guidance

9. **Translations Note**
   - Points to translation resources

### 7.3 Language Patterns

**Boilerplate Elements:**
- "This section describes the status of this document..."
- Formal procedural language for comment submission
- Legal/standards compliance language
- Cross-references to W3C process documents

**Technical Specifications:**
- Version and date prominently stated
- Specific implementation milestones
- Clear differentiation of normative vs informative content

### 7.4 Abstract vs Status Distinction

| Abstract | Status |
|----------|--------|
| Purely technical scope | Document lifecycle |
| What the spec defines | Where in W3C process |
| Self-contained | Extensive cross-references |
| Stable across versions | Changes with each publication |
| For understanding content | For understanding process |

### 7.5 Document Self-Identification

**Key metadata:**
- **Version:** 1.2
- **Profile:** "tiny"
- **Date:** 15 September 2008
- **Status:** Last Call Working Draft
- **Editors:** Listed with affiliations (14 individuals for SVG Tiny 1.2)
- **Authors:** Multiple contributors noted
- **Working Group:** SVG Working Group
- **Activity:** Graphics Activity

---

## 8. Appendices Structure

### 8.1 Content Distribution

**Main Chapters (1-19):**
Core specification content
- Introduction and concepts
- Rendering models
- Document structure
- Features and capabilities

**Appendices (A-T):**
Supplementary material
- Formal definitions
- Implementation guidance
- Conformance requirements
- Technical bindings
- Historical documentation

This separation allows normative technical content to remain focused while supporting materials serve reference purposes.

### 8.2 Appendix Organization

**Letter-based system organized by function:**

#### Technical Specifications
- **Appendix A:** uDOM (SVG's Micro DOM)
- **Appendix B:** IDL Definitions

#### Implementation Guidance
- **Appendix C:** Implementation Requirements
- **Appendix D:** Conformance Criteria
- **Appendix E:** Detected Content Type
- **Appendix F:** Accessibility Support
- **Appendix G:** Internationalization Support

#### Format-Specific
- **Appendix H:** JPEG Support
- **Appendix I:** Portable Document Format (PDF)
- **Appendix J:** File Optimization Guidance

#### Reference Materials
- **Appendix K:** Element Table
- **Appendix L:** Attribute and Property Tables
- **Appendix M:** Media Type Registration
- **Appendix N:** RelaxNG Schema for SVG Tiny 1.2

#### Language Bindings
- **Appendix O:** ECMAScript Language Binding
- **Appendix P:** Java Language Binding
- **Appendix Q:** Perl Language Binding
- **Appendix R:** Python Language Binding

#### Documentary
- **Appendix S:** References (Normative and Informative)
- **Appendix T:** Change History

### 8.3 Normative vs Informative Appendices

**Normative (Implementation Required):**
- Implementation Requirements (C)
- Conformance Criteria (D)
- IDL Definitions (B)
- Schema (N)

**Informative (Guidance):**
- Accessibility Support (F)
- Internationalization (G)
- File Optimization (J)
- Change History (T)

**Distinction method:** Metadata rather than explicit labeling in most cases

### 8.4 Cross-Reference Strategy

**Main text to appendices:**
```
See [Appendix D](#chapter-conform) for conformance requirements.
Defined in [uDOM](#chapter-svgudom).
The RelaxNG schema is provided in [Appendix N](#schema).
```

**Enables:**
- Detail access without disrupting narrative flow
- Modular reading
- Reference lookup

### 8.5 Role in W3C Specifications

**Critical functions:**

1. **Formalize Interface Definitions**
   - IDL for programmatic accuracy
   - Language bindings for cross-platform implementation

2. **Document Conformance**
   - Validation criteria
   - Test requirements
   - Conformance classes

3. **Record Evolution**
   - Change histories
   - Version transparency
   - Backward compatibility notes

4. **Provide Implementation Guidance**
   - Best practices
   - Optimization strategies
   - Accessibility considerations

5. **Enable Validation**
   - Schemas for automated checking
   - Element/attribute tables for reference
   - Test suites

### 8.6 Typical Appendix Topics for W3C Specifications

**Standard patterns observed:**

1. **IDL Definitions** — Programmatic interfaces
2. **Schema Files** — Automated validation
3. **Change Histories** — Version transparency
4. **Language Bindings** — Cross-platform implementation
5. **Reference Tables** — Quick lookup (elements, attributes)
6. **Conformance Criteria** — Validation requirements
7. **Accessibility Guidance** — WAI compliance
8. **Implementation Notes** — Best practices
9. **Media Type Registration** — MIME types
10. **References** — Normative and informative citations

---

## 9. Formatting Conventions

### 9.1 Element Names

**Pattern:** Single quotes with monospace formatting

**Examples:**
```
'svg'
'path'
'rect'
'g'
```

**When used as link anchors:**
```
['svg'](#struct-SVGElement)
['path'](#PathElement)
```

### 9.2 Attribute Names

**Same convention as elements:**
```
'version'
'viewBox'
'fill'
'stroke'
'transform'
```

**With links:**
```
['version'](#VersionAttribute)
['viewBox'](#ViewBoxAttribute)
```

### 9.3 Hyperlink Conventions

**Internal cross-references:**
```
[descriptive text](#section-id)
```

**External references:**
```
[Organization](#refs-ref-CODE)
```

**Combined pattern:**
```
See the [coordinate system](#coords-units) for details.
Defined in [XSL](#refs-ref-XSL), section 4.2.3.
```

### 9.4 Notes and Callouts

**Pattern:** Bold prefix within prose

```
Note: Important clarification text follows.

Example: [filename.svg]

Warning: Deprecated feature notice.
```

### 9.5 Code and Data Types

**Inline code:** Monospace
```
"image/svg+xml"
application/svg+xml
xmlns="http://www.w3.org/2000/svg"
```

**Block code:** Indented with optional syntax context
```xml
<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg">
  <!-- content -->
</svg>
```

### 9.6 Definition Lists

**Pattern:**
```
**Term** — Description begins on same line or next line.
Multiple paragraphs may follow for complex definitions.
Cross-references and examples embedded as needed.
```

**Example:**
```
**bounding box** — A rectangle that encloses all portions of a
graphical element. The bounding box must enclose all portions of
the geometry, including control points for curves.
```

### 9.7 Property Values

**Single quotes for enumerated values:**
```
'none'
'onLoad'
'auto'
'inherit'
```

**Namespace URIs in monospace:**
```
http://www.w3.org/2000/svg
http://www.w3.org/1999/xlink
```

### 9.8 Keywords and Reserved Terms

**Defined in terminology section with consistent formatting:**
```
"in error" — explicitly violates specification
"unsupported value" — non-conforming but not formally wrong
"lacuna value" — default behavior when attribute unspecified
```

### 9.9 Structural Formatting

**Chapter headings:**
```
# 1 Introduction
## 1.1 About SVG
### 1.1.1 Subsection Topic
```

**Appendix headings:**
```
# Appendix A: uDOM
## A.1 Introduction
## A.2 Interface Definitions
```

### 9.10 Tables

**Standard HTML table formatting:**
- Header row with bold text
- Clear column labels
- Alignment appropriate to content type
- Borders for readability

### 9.11 Lists

**Unordered lists:**
- Used for feature enumerations
- Implementation requirements
- Non-sequential information

**Ordered lists:**
- Used for procedural steps
- Sequential requirements
- Numbered references

---

## 10. Recommendations for FBF.SVG

Based on the analysis of SVG Tiny 1.2, here are specific recommendations for the FBF.SVG proposal:

### 10.1 Document Structure

**Adopt the W3C standard structure:**

```
FBF.SVG Specification
├── Abstract
├── Status of This Document
├── Table of Contents (standard and expanded)
├── 1. Introduction
│   ├── 1.1 About FBF.SVG
│   ├── 1.2 Motivation and Goals
│   ├── 1.3 Relationship to SVG
│   ├── 1.4 Defining Documents
│   ├── 1.5 MIME Types
│   └── 1.6 Definitions
├── 2. Concepts
│   ├── 2.1 Frame-by-Frame Animation Principles
│   ├── 2.2 Binary Format Rationale
│   └── 2.3 Use Cases
├── 3. FBF Document Structure
├── 4. Data Types and Encoding
├── 5. Frame Sequences
├── 6. Compression and Optimization
├── 7. SVG Compatibility
├── 8. Rendering Model
├── 9. Conformance
└── Appendices
    ├── A. Binary Format Specification
    ├── B. File Format Schema
    ├── C. Conformance Criteria
    ├── D. Implementation Requirements
    ├── E. SVG Feature Subset
    ├── F. Example Conversions
    ├── G. Performance Benchmarks
    ├── H. Accessibility Considerations
    ├── I. Change History
    └── J. References (Normative and Informative)
```

### 10.2 Writing Style Guidelines

**Apply these patterns:**

1. **Use passive voice for specifications**
   - "must be encoded as..."
   - "shall be computed..."
   - "are required to support..."

2. **Use present tense consistently**
   - "The frame data contains..."
   - "The compression algorithm operates..."

3. **Use imperative for implementer instructions**
   - "Encode all frame data using..."
   - "Compute the delta between frames..."

4. **Layer complexity progressively**
   - Start with accessible explanations
   - Add technical precision
   - Provide edge cases
   - Detail implementation requirements

5. **Use formal transitions**
   - "See [section] for details"
   - "Note that [clarification]"
   - "For example, [illustration]"
   - "The following describes [preview]"

### 10.3 Conformance Language

**Follow RFC 2119 style:**

1. **Use MUST for mandatory requirements:**
   ```
   "FBF readers MUST support DEFLATE compression."
   "Frame timing information MUST be encoded as 32-bit integers."
   ```

2. **Use SHOULD for strong recommendations:**
   ```
   "FBF writers SHOULD optimize frame deltas to minimize file size."
   "It is recommended that FBF files use the extension '.fbf'"
   ```

3. **Use MAY for optional features:**
   ```
   "FBF readers MAY support additional compression algorithms."
   "Implementations MAY provide conversion tools to SVG."
   ```

4. **Define conformance classes clearly:**
   - FBF Content Conformance
   - FBF Writer Conformance
   - FBF Reader Conformance
   - FBF to SVG Converter Conformance

5. **Distinguish error types:**
   - "in error" — explicitly violates specification
   - "unsupported value" — non-conforming but processable

### 10.4 Example Presentation

**Follow these patterns:**

1. **Label examples formally:**
   ```
   Example: [simple_animation.fbf]
   ```

2. **Provide complete examples when possible:**
   ```
   Include full file structure
   Show binary encoding details
   Provide equivalent SVG representation
   ```

3. **Show rendered output:**
   - Include PNG sequence showing frames
   - Reference format: `![Frame 1](examples/frame01.png)`

4. **Use multiple variations:**
   - `example01.fbf` — simple case
   - `example02.fbf` — with compression
   - `example03.fbf` — complex paths

5. **Maintain high prose-to-code ratio:**
   - Explain concept before showing code
   - Discuss what example demonstrates
   - Highlight key aspects

### 10.5 References

**Structure the references section:**

**Normative References:**
```
[SVG2] "Scalable Vector Graphics (SVG) 2", W3C, 2018 Recommendation.
       https://www.w3.org/TR/SVG2/

[DEFLATE] "DEFLATE Compressed Data Format Specification version 1.3",
          RFC 1951, May 1996.
          https://www.ietf.org/rfc/rfc1951.txt

[RFC2119] "Key words for use in RFCs to Indicate Requirement Levels",
          S. Bradner, March 1997.
          https://www.ietf.org/rfc/rfc2119.txt
```

**Informative References:**
```
[SMIL] "Synchronized Multimedia Integration Language (SMIL 3.0)",
       W3C, 2008 Recommendation.
       https://www.w3.org/TR/SMIL3/
```

**Use inline citations:**
```
The binary format follows DEFLATE compression [DEFLATE].
Timing is based on SMIL principles ([SMIL], section 3.2).
```

### 10.6 Diagrams

**Create these visual aids:**

1. **File format structure diagram**
   - Show header, frame data, footer sections
   - Use boxes and arrows
   - Label byte offsets

2. **Frame delta encoding visualization**
   - Show original frame, next frame, delta
   - Illustrate compression benefit

3. **Conversion flow diagrams**
   - SVG to FBF process
   - FBF to SVG process

4. **Integration patterns:**
   - Embed SVG code and rendered output
   - Use both SVG and PNG formats
   - Reference explicitly in text

### 10.7 Abstract Section

**Write concise abstract:**

```
Abstract

This specification defines the features and binary format for
FBF.SVG (Frame-by-Frame Binary Format for SVG), an optimized
format for encoding frame-by-frame SVG animations. FBF.SVG
provides significant file size reduction and improved performance
for sequential SVG animations while maintaining full compatibility
with SVG rendering engines.
```

### 10.8 Status Section

**Include required components:**

```
Status of This Document

This section describes the status of this document at the time
of its publication. Other documents may supersede this document.

This document is a [Working Draft/Proposal] and has not been
officially submitted to W3C. It is published for examination,
experimental implementation, and evaluation.

Comments on this document should be sent to [email address]
with "[FBF.SVG]" in the subject line.

This document was developed independently and represents a
proposed extension to the SVG specification. Implementation
and deployment are encouraged for evaluation purposes.

[Additional standard W3C boilerplate as appropriate]
```

### 10.9 Appendices to Include

**Essential appendices for FBF.SVG:**

1. **Appendix A: Binary Format Specification**
   - Complete byte-level format
   - Field definitions
   - Encoding rules

2. **Appendix B: Conformance Criteria**
   - Conformance classes
   - Test requirements
   - Validation procedures

3. **Appendix C: SVG Feature Subset**
   - Supported SVG elements
   - Supported attributes
   - Unsupported features

4. **Appendix D: Implementation Requirements**
   - Reader requirements
   - Writer requirements
   - Converter requirements

5. **Appendix E: Example Files**
   - Complete example FBF files
   - Equivalent SVG versions
   - Performance comparisons

6. **Appendix F: Compression Algorithms**
   - DEFLATE details
   - Delta encoding strategies
   - Optimization techniques

7. **Appendix G: MIME Type Registration**
   - Proposed MIME type
   - File extension registration
   - Media type parameters

8. **Appendix H: Accessibility Considerations**
   - How accessibility is preserved
   - Alternative content provision
   - Screen reader support

9. **Appendix I: Security Considerations**
   - Potential security issues
   - Mitigation strategies
   - Safe implementation practices

10. **Appendix J: References**
    - Normative references
    - Informative references

### 10.10 Formatting Conventions

**Establish consistent formatting:**

1. **Element names:** `'fbf'`, `'frame'`, `'sequence'`
2. **Attribute names:** `'duration'`, `'compression'`, `'format'`
3. **Data types:** `<integer>`, `<float>`, `<binary>`
4. **File extensions:** `.fbf` (monospace)
5. **MIME types:** `application/fbf+svg` (monospace)
6. **Keywords:** **bold** for first definition
7. **Code blocks:** Indented, monospace, with clear language labels
8. **Cross-references:** `[descriptive text](#section-id)`

### 10.11 Progressive Complexity

**Structure each major section:**

1. **High-level overview** (accessible)
   - Plain language explanation
   - Why this feature exists
   - What problem it solves

2. **Formal definition** (technical)
   - Precise specification
   - Data types and structures
   - Mandatory requirements

3. **Examples** (concrete)
   - Code samples
   - Visual diagrams
   - Step-by-step illustrations

4. **Implementation guidance** (practical)
   - How to implement correctly
   - Common pitfalls
   - Best practices

5. **Edge cases** (comprehensive)
   - Boundary conditions
   - Error handling
   - Special cases

### 10.12 Consistency Checklist

**Before finalizing, verify:**

- [ ] All elements use consistent formatting (`'element'`)
- [ ] All attributes use consistent formatting (`'attribute'`)
- [ ] All code examples are labeled (`Example: [filename]`)
- [ ] All diagrams are referenced explicitly in text
- [ ] All conformance requirements use RFC 2119 keywords
- [ ] All chapters have clear introductions
- [ ] All technical terms are defined on first use
- [ ] All cross-references link correctly
- [ ] All examples include explanatory text
- [ ] All appendices serve clear purposes
- [ ] Normative vs informative distinction is clear
- [ ] Table of contents is complete and accurate
- [ ] References section includes all citations
- [ ] Status section is accurate and complete
- [ ] Abstract clearly summarizes the specification

---

## Conclusion

The W3C SVG Tiny 1.2 specification demonstrates a mature, well-structured approach to technical documentation that balances formal precision with accessibility. The FBF.SVG proposal should adopt these patterns to ensure professional quality and compatibility with W3C standards expectations.

**Key principles to maintain:**

1. **Progressive complexity** — accessible introduction, technical depth, implementation details
2. **Formal structure** — consistent organization, clear hierarchy, comprehensive appendices
3. **Precise conformance language** — RFC 2119 keywords, clear requirements, defined error handling
4. **Rich examples** — complete code, visual output, explanatory text
5. **Comprehensive cross-referencing** — seamless navigation, modular reading, reference lookup
6. **Professional formatting** — consistent conventions, clear typography, accessible presentation

By following these patterns, the FBF.SVG specification will meet W3C expectations and serve as a valuable reference for implementers, while remaining accessible to developers evaluating the format.

---

**Document Information:**
- **Analysis Date:** 2025-11-10
- **Source:** W3C SVG Tiny 1.2 Specification (Working Draft, 15 September 2008)
- **Analysis Tool:** WebFetch with targeted prompts
- **Analyst:** Claude Code (Anthropic)
- **Purpose:** Style guide for FBF.SVG proposal documentation
