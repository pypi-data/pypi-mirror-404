# FBF.SVG Proposal Planning Document

**Purpose**: This document outlines the structure, required evidence, references, and documentation needed to support the FBF.SVG standards proposal.

**Status**: Planning and Requirements Document
**Date**: 2025-11-08
**Related**: FBF_SVG_PROPOSAL.md (main proposal document)

---

## Document Structure and Organization

### Part I: Foundation and Context

#### 1. Executive Materials
- [ ] **Abstract** (200-300 words)
  - Problem statement in one sentence
  - Proposed solution in one sentence
  - Key innovations (3-4 bullet points)
  - Expected impact

- [ ] **Executive Summary** (1-2 pages)
  - Business case for FBF.SVG
  - Market need and opportunity
  - Technical feasibility evidence
  - Adoption strategy
  - Success metrics

#### 2. Introduction and Background
- [ ] **Section 1.1: Historical Context**
  - Evolution of web animation (GIF → Flash → HTML5 → SVG)
  - Current state of SVG animation ecosystem
  - Gap analysis: what's missing?

- [ ] **Section 1.2: Motivation**
  - Traditional animation workflows
  - AI/LLM visual communication needs
  - Real-time streaming requirements
  - Technical documentation use cases

- [ ] **Section 1.3: Goals and Non-Goals**
  - Primary objectives (ranked by priority)
  - Secondary objectives
  - Explicitly stated non-goals (to prevent scope creep)

- [ ] **Section 1.4: Scope and Boundaries**
  - What the specification covers
  - What it delegates to other specs
  - Relationship to SVG 1.1, SVG 2.0, SMIL

### Part II: Technical Specification

#### 3. Format Definition
- [ ] **Section 3.1: Document Structure**
  - Required elements and ordering
  - Optional elements
  - Namespace declarations
  - Root element attributes

- [ ] **Section 3.2: Animation Mechanism**
  - SMIL-based frame sequencing
  - Alternative mechanisms (CSS fallback)
  - Timing model
  - Frame reference system

- [ ] **Section 3.3: Metadata Requirements**
  - RDF/XML structure
  - Dublin Core fields (required vs. optional)
  - FBF-specific fields
  - Extensibility points

- [ ] **Section 3.4: Security Model**
  - No external resources policy
  - Content Security Policy requirements
  - Script validation (hash-based)
  - Sanitization requirements

#### 4. Conformance Levels
- [ ] **Section 4.1: FBF.SVG Basic**
  - Minimal requirements
  - Validation criteria
  - Use cases appropriate for Basic

- [ ] **Section 4.2: FBF.SVG Full**
  - Additional requirements beyond Basic
  - Metadata completeness
  - Use cases requiring Full conformance

- [ ] **Section 4.3: Validation and Testing**
  - Validation tools
  - Test suites
  - Conformance certification process

### Part III: Advanced Capabilities

#### 5. Streaming Architecture
- [ ] **Section 5.1: Design Rationale**
  - Why frames-at-end?
  - Progressive rendering benefits
  - Memory management approach

- [ ] **Section 5.2: Streaming Protocol**
  - Frame transmission format
  - Client-server communication
  - Synchronization mechanisms
  - Error handling

- [ ] **Section 5.3: Memory Management**
  - Timed fragmentation technique
  - Sliding window buffers
  - Frame eviction policies
  - Performance trade-offs

#### 6. Interactive Visual Communication
- [ ] **Section 6.1: Conceptual Model**
  - LLM visual output (frame generation)
  - User visual input (coordinate capture)
  - Bidirectional flow
  - State management

- [ ] **Section 6.2: DOM Interfaces**
  - FBFBackdropElement interface
  - FBFStreamingElement interface
  - Event handling
  - Error conditions

- [ ] **Section 6.3: Protocol Specification**
  - Frame generation messages
  - User input messages
  - Session management
  - Security considerations

### Part IV: Implementation and Ecosystem

#### 7. Reference Implementation
- [ ] **Section 7.1: svg2fbf Converter**
  - Architecture overview
  - Optimization algorithms
  - Configuration options
  - Usage examples

- [ ] **Section 7.2: Validator**
  - Validation levels
  - Error reporting
  - Performance characteristics

- [ ] **Section 7.3: Example Implementations**
  - Browser player (planned)
  - Streaming server (planned)
  - Authoring tools (planned)

#### 8. Standardization Path
- [ ] **Section 8.1: Community Phase**
  - Feedback collection
  - Implementation reports
  - Issue resolution

- [ ] **Section 8.2: W3C Process**
  - Community Group formation
  - Working Draft progression
  - Candidate Recommendation criteria
  - Recommendation requirements

- [ ] **Section 8.3: Governance**
  - Decision-making process
  - Intellectual property policy
  - Contribution guidelines

### Part V: Analysis and Evidence

#### 9. Use Cases and Requirements
- [ ] **Section 9.1: Traditional Animation**
  - Workflow analysis
  - Tool integration requirements
  - Performance requirements

- [ ] **Section 9.2: AI Visual Interfaces**
  - LLM integration patterns
  - Interaction latency requirements
  - Context management

- [ ] **Section 9.3: Real-Time Streaming**
  - Bandwidth requirements
  - Latency tolerance
  - Scalability considerations

#### 10. Comparative Analysis
- [ ] **Section 10.1: vs. Existing Formats**
  - Lottie comparison
  - CSS Animation comparison
  - Video formats comparison
  - Static image sequences comparison

- [ ] **Section 10.2: vs. Web Artifacts**
  - Complexity comparison
  - Security comparison
  - Performance comparison

#### 11. Impact and Benefits
- [ ] **Section 11.1: For Content Creators**
  - Workflow improvements
  - Quality benefits
  - Distribution advantages

- [ ] **Section 11.2: For Developers**
  - Implementation simplicity
  - Integration opportunities
  - Ecosystem growth

- [ ] **Section 11.3: For End Users**
  - Experience improvements
  - Accessibility benefits
  - Privacy advantages

### Part VI: Supporting Materials

#### 12. Appendices
- [ ] **Appendix A: Complete XSD Schema**
- [ ] **Appendix B: Example Documents**
- [ ] **Appendix C: Test Suite**
- [ ] **Appendix D: Glossary**
- [ ] **Appendix E: FAQ**

---

## Arguments to Prove

### Core Technical Arguments

#### Argument 1: FBF.SVG is Necessary (Gap Analysis)
**Claim**: Existing SVG animation methods are insufficient for frame-based animation use cases.

**Evidence Required**:
- [ ] Survey of current SVG animation approaches
  - SMIL property animation (what it can/cannot do)
  - CSS animation limitations
  - JavaScript-based animation drawbacks
  - Manual frame switching techniques (inefficiency)

- [ ] Use case analysis
  - Traditional cel animation workflows
  - Frame-by-frame technical documentation
  - Scientific visualization requiring discrete states
  - Cases where interpolation is inappropriate

- [ ] Comparative workflow analysis
  - Current workflow: Export to video (steps, file sizes, limitations)
  - FBF.SVG workflow: Direct SVG export (advantages)
  - Quantitative comparison (time, file size, quality)

**Documentation Needed**:
- Case studies from animators (current pain points)
- File size comparisons (PNG sequence vs. video vs. FBF.SVG)
- Quality comparisons (resolution independence demonstration)

#### Argument 2: FBF.SVG is Feasible (Technical Viability)
**Claim**: FBF.SVG can be efficiently implemented in browsers and tools.

**Evidence Required**:
- [ ] Reference implementation exists and works
  - svg2fbf tool (link, documentation)
  - Example FBF.SVG files (playable in browsers)
  - Validator (demonstrates mechanical validation)

- [ ] Performance analysis
  - Parsing performance (document size vs. parse time)
  - Rendering performance (frame rate vs. frame complexity)
  - Memory usage (static vs. streaming scenarios)
  - Comparison to video playback performance

- [ ] Browser compatibility
  - SMIL support matrix (Chrome, Firefox, Safari, Edge)
  - Fallback behavior (browsers without SMIL)
  - Progressive enhancement strategy

**Documentation Needed**:
- Performance benchmarks (specific numbers)
- Browser compatibility test results
- Reference implementation source code and documentation
- Example files of varying complexity

#### Argument 3: FBF.SVG Provides Unique Value (Competitive Advantage)
**Claim**: FBF.SVG offers capabilities unavailable in competing formats.

**Evidence Required**:
- [ ] Feature comparison matrix
  - FBF.SVG vs. Lottie (features, file size, compatibility)
  - FBF.SVG vs. APNG/WebP (vector vs. raster, interactivity)
  - FBF.SVG vs. CSS Animation (frame-based vs. interpolation)
  - FBF.SVG vs. video (streaming, interaction, editability)

- [ ] Unique capabilities demonstration
  - Streaming: Unlimited duration proof-of-concept
  - Interactive communication: LLM visual interface demo
  - Controlled extensibility: Custom backdrop injection example
  - Optimization: File size reduction metrics

**Documentation Needed**:
- Side-by-side comparison table
- Feature matrix with checkmarks
- File size comparison charts
- Interactive demos showcasing unique features

#### Argument 4: Streaming Architecture is Sound (Technical Innovation)
**Claim**: Frames-at-end architecture enables efficient real-time streaming.

**Evidence Required**:
- [ ] Architectural analysis
  - Why frames-at-end? (progressive rendering explanation)
  - Memory management strategy (timed fragmentation)
  - Comparison to alternative architectures (frames-at-beginning, interleaved)

- [ ] Performance validation
  - Streaming latency measurements
  - Memory usage with/without fragmentation
  - Scalability testing (100, 1000, 10000 frames)

- [ ] Academic foundation
  - Concolato et al. (2007) timed fragmentation research
  - SVG document fragmentation techniques
  - Memory control for animation playback

**Documentation Needed**:
- Architecture diagrams (frame flow, memory management)
- Performance graphs (latency, memory, scalability)
- Academic citations and summaries
- Proof-of-concept streaming demo

#### Argument 5: Interactive Communication is Practical (Novel Use Case)
**Claim**: LLMs can effectively communicate visually using FBF.SVG without programming.

**Evidence Required**:
- [ ] Conceptual validation
  - Why declarative SVG vs. imperative JavaScript?
  - Security advantages (no code execution)
  - Reliability advantages (no runtime errors)
  - Performance advantages (instant rendering)

- [ ] Comparison to web artifacts
  - Complexity comparison (SVG generation vs. JavaScript generation)
  - Error rate comparison (declarative vs. imperative)
  - Latency comparison (native rendering vs. JS execution)

- [ ] Use case demonstrations
  - Equipment repair scenario (visual step-by-step)
  - Interactive menu scenario (visual selection)
  - Technical analysis scenario (color-coded diagrams)

**Documentation Needed**:
- Conceptual diagrams (LLM → SVG → User → LLM flow)
- Code comparison (SVG vs. JavaScript for same UI)
- User interaction protocol specification
- Proof-of-concept LLM visual interface

#### Argument 6: Format is Secure (Security Model)
**Claim**: FBF.SVG's security model prevents common web vulnerabilities.

**Evidence Required**:
- [ ] Threat model analysis
  - No external resources → prevents tracking, phishing
  - No scripts (except validated polyfill) → prevents XSS
  - Strict structure validation → prevents injection attacks
  - CSP compliance → defense in depth

- [ ] Security comparison
  - FBF.SVG vs. user-generated JavaScript (attack surface)
  - FBF.SVG vs. external resource loading (privacy)
  - FBF.SVG vs. unvalidated SVG (injection risks)

**Documentation Needed**:
- Threat model document
- Security analysis report
- CSP policy specification
- Script hash validation procedure

#### Argument 7: Format is Accessible (Inclusivity)
**Claim**: FBF.SVG maintains and enhances SVG's accessibility features.

**Evidence Required**:
- [ ] Accessibility feature preservation
  - ARIA labels in SVG elements
  - Screen reader compatibility
  - Keyboard navigation support
  - Text alternatives for visual content

- [ ] WCAG compliance analysis
  - Level A requirements
  - Level AA requirements
  - Specific guidelines addressed

**Documentation Needed**:
- Accessibility guidelines for FBF.SVG authors
- Screen reader testing results
- WCAG compliance checklist
- Accessible example files

#### Argument 8: Optimization is Effective (File Size Claims)
**Claim**: Element deduplication yields 40-70% file size reduction.

**Evidence Required**:
- [ ] Test cases with metrics
  - Simple animation (10 frames, minimal changes)
  - Complex animation (100+ frames, many elements)
  - Real-world animation (actual production content)

- [ ] Optimization breakdown
  - Deduplication contribution (% reduction)
  - Path optimization contribution (% reduction)
  - Gradient merging contribution (% reduction)
  - Compression contribution (gzip/brotli)

**Documentation Needed**:
- File size comparison tables
- Before/after optimization examples
- Optimization algorithm documentation
- Compression benchmarks

---

## Literature and References to Collect

### Normative References (Required by Specification)

#### Core Web Standards
- [ ] **SVG 1.1 (Second Edition)**
  - Citation: W3C Recommendation, 16 August 2011
  - URL: https://www.w3.org/TR/SVG11/
  - Relevance: Base specification FBF.SVG extends
  - Key sections: Basic shapes, text, paths, gradients, SMIL animation

- [ ] **SVG 2.0**
  - Citation: W3C Candidate Recommendation
  - URL: https://www.w3.org/TR/SVG2/
  - Relevance: Mesh gradients, modern features
  - Key sections: Mesh gradient specification, updated animation model

- [ ] **SMIL Animation**
  - Citation: W3C Recommendation, 1 December 2008
  - URL: https://www.w3.org/TR/SMIL3/
  - Relevance: Animation timing model
  - Key sections: Timing model, animation elements, discrete animation

- [ ] **XML 1.0**
  - Citation: W3C Recommendation, Fifth Edition
  - URL: https://www.w3.org/TR/xml/
  - Relevance: Base syntax
  - Key sections: Document structure, well-formedness

- [ ] **XML Schema Part 1: Structures**
  - Citation: W3C Recommendation, 28 October 2004
  - URL: https://www.w3.org/TR/xmlschema-1/
  - Relevance: XSD validation
  - Key sections: Schema composition, element declarations

#### Metadata Standards
- [ ] **RDF (Resource Description Framework)**
  - Citation: W3C Recommendation, 10 February 2004
  - URL: https://www.w3.org/TR/rdf-concepts/
  - Relevance: Metadata structure
  - Key sections: RDF/XML syntax, triple model

- [ ] **Dublin Core Metadata Element Set**
  - Citation: ISO Standard 15836:2009
  - URL: https://www.dublincore.org/specifications/dublin-core/dces/
  - Relevance: Standard metadata fields
  - Key sections: Core elements (creator, title, date, etc.)

#### Security Standards
- [ ] **Content Security Policy Level 3**
  - Citation: W3C Working Draft
  - URL: https://www.w3.org/TR/CSP3/
  - Relevance: Security policy
  - Key sections: Directive syntax, unsafe-inline, data: URIs

### Informative References (Supporting Evidence)

#### SVG Profile Precedents
- [ ] **SVG Tiny 1.2**
  - Citation: W3C Recommendation, 22 December 2008
  - URL: https://www.w3.org/TR/SVGTiny12/
  - Relevance: Profile precedent (mobile/embedded devices)
  - Analysis: How it constrains SVG, conformance levels

- [ ] **SVG Basic**
  - Citation: W3C Recommendation, 14 January 2003
  - URL: https://www.w3.org/TR/SVGMobile/
  - Relevance: Profile precedent (web publishing)
  - Analysis: Feature subsetting approach

#### Animation Research
- [ ] **Concolato et al. (2007) - Timed Fragmentation**
  - Citation: Proceedings of the 2007 ACM symposium on Document engineering (pp. 121-124)
  - URL: https://dl.acm.org/doi/abs/10.1145/1284420.1284453
  - Relevance: Memory management for SVG animation
  - Key concepts: Document fragmentation, playback memory control, timed eviction
  - **Action**: Obtain PDF, summarize key techniques, cite specific page numbers

- [ ] **SVG Animation Survey Papers**
  - Search: "SVG animation performance" (IEEE, ACM databases)
  - Search: "SVG streaming" (web technology conferences)
  - Search: "Declarative animation web" (W3C workshop proceedings)

#### Vector Animation Formats (Competitive Analysis)
- [ ] **Lottie Format Specification**
  - URL: https://lottiefiles.github.io/lottie-docs/
  - Relevance: Competitor analysis
  - Analysis: JSON-based, After Effects integration, limitations vs. FBF.SVG

- [ ] **WebP Animation**
  - URL: https://developers.google.com/speed/webp
  - Relevance: Raster animation alternative
  - Analysis: Compression, file sizes, lack of vector benefits

- [ ] **APNG Specification**
  - URL: https://wiki.mozilla.org/APNG_Specification
  - Relevance: Raster animation alternative
  - Analysis: Browser support, use cases, limitations

#### AI and Human-Computer Interaction
- [ ] **LLM Visual Interface Research**
  - Search: "Large language model visual output" (recent papers)
  - Search: "AI generated user interfaces" (HCI conferences)
  - Search: "Multimodal AI interaction" (CHI, UIST proceedings)
  - **Goal**: Establish context for LLM visual communication use case

- [ ] **Anthropic Artifacts Documentation**
  - URL: Check Anthropic documentation/blog posts
  - Relevance: Current web artifact approach comparison
  - Analysis: Code generation complexity, error rates, security concerns

#### Accessibility Standards
- [ ] **WCAG 2.1**
  - Citation: W3C Recommendation, 5 June 2018
  - URL: https://www.w3.org/TR/WCAG21/
  - Relevance: Accessibility compliance
  - Key sections: Animation guidelines, keyboard access, screen reader support

- [ ] **ARIA (Accessible Rich Internet Applications)**
  - Citation: W3C Recommendation
  - URL: https://www.w3.org/TR/wai-aria/
  - Relevance: SVG accessibility
  - Key sections: ARIA in SVG, roles, properties

#### Performance and Optimization
- [ ] **SVG Optimization Tools Analysis**
  - SVGO (https://github.com/svg/svgo)
  - Scour (https://github.com/scour-project/scour)
  - Analysis: Techniques used, effectiveness, comparison to FBF.SVG deduplication

- [ ] **Web Performance Research**
  - Search: "SVG rendering performance" (web performance conferences)
  - Search: "DOM manipulation performance" (browser engineering blogs)

---

## Documentation to Provide

### Technical Documentation

#### 1. Complete Format Specification
**Status**: ✅ Complete (FBF_SVG_SPECIFICATION.md)

**Sections**:
- [x] Design principles
- [x] Document structure
- [x] Conformance levels
- [x] Forbidden elements
- [x] Naming conventions
- [x] SMIL animation
- [x] Metadata requirements
- [x] Security model
- [x] Validation
- [x] DOM interfaces
- [x] Streaming capabilities
- [x] Interactive communication protocol
- [x] References

**Enhancements Needed**:
- [ ] Add more code examples for each section
- [ ] Include SVG diagrams (not ASCII art)
- [ ] Expand validation section with specific error messages
- [ ] Add timing diagrams for animation sequences

#### 2. XML Schema Definition (XSD)
**Status**: ✅ Complete (fbf-svg.xsd)

**Contents**:
- [x] Namespace declarations
- [x] Element definitions
- [x] Attribute constraints
- [x] Sequence ordering requirements
- [x] Metadata structure

**Enhancements Needed**:
- [ ] Add more detailed documentation comments
- [ ] Include examples in XSD comments
- [ ] Validate schema against W3C XSD validator
- [ ] Create schema documentation (xsddoc or similar)

#### 3. Validator Implementation
**Status**: ✅ Complete (validate_fbf.py)

**Features**:
- [x] XML well-formedness checking
- [x] XSD validation
- [x] Structural validation
- [x] Security checking
- [x] Metadata validation
- [x] Animation validation

**Enhancements Needed**:
- [ ] Improve error messages (more specific guidance)
- [ ] Add warning levels (error vs. warning vs. info)
- [ ] Performance optimization for large files
- [ ] JSON output format (for tool integration)
- [ ] Web-based validator (online validation service)

#### 4. Reference Implementation Documentation
**Status**: ✅ Exists (svg2fbf README.md)

**Contents**:
- [x] Installation instructions
- [x] Basic usage examples
- [x] Advanced usage (CLI parameters)
- [x] YAML configuration
- [x] Optimization options

**Enhancements Needed**:
- [ ] API documentation (if used as library)
- [ ] Detailed optimization algorithm explanation
- [ ] Troubleshooting guide
- [ ] Performance tuning guide
- [ ] Integration examples (build systems, automation)

### Test Suite and Examples

#### 5. Conformance Test Suite
**Status**: ⏳ Needed

**Test Categories**:
- [ ] **Valid Documents** (should pass validation)
  - Basic conformance minimal example
  - Full conformance complete example
  - Optional features (mesh gradients, etc.)
  - Edge cases (single frame, maximum frames, etc.)

- [ ] **Invalid Documents** (should fail validation)
  - Missing required elements
  - Incorrect element ordering
  - Invalid metadata
  - External resource references
  - Incorrect namespace declarations
  - Invalid frame ID sequences

- [ ] **Rendering Tests**
  - Frame timing accuracy
  - Animation mode behaviors (loop, once, pingpong)
  - Gradient rendering
  - Transform handling
  - ViewBox scaling

- [ ] **Streaming Tests**
  - Progressive frame addition
  - Memory management (fragmentation)
  - Concurrent frame appending
  - Error recovery

- [ ] **Interaction Tests**
  - Element selection
  - Coordinate capture
  - Event serialization
  - State management

**Format**:
- [ ] Test files (valid/invalid FBF.SVG)
- [ ] Expected outcomes (pass/fail, error messages)
- [ ] Rendering references (screenshots or checksums)
- [ ] Test harness (automated testing tool)

#### 6. Example Animations
**Status**: ⏳ Needed (more examples)

**Categories**:
- [ ] **Simple Examples** (learning/teaching)
  - "Hello World" (3-frame animation)
  - Bouncing ball (10-frame loop)
  - Color transition (5-frame sequence)

- [ ] **Intermediate Examples**
  - Character walk cycle (12-frame loop)
  - Logo animation (30 frames)
  - Loading spinner (8-frame loop)

- [ ] **Complex Examples**
  - Full character animation (100+ frames)
  - Technical diagram sequence
  - Scientific visualization

- [ ] **Streaming Examples**
  - Live frame addition demo
  - Real-time chart update
  - Collaborative diagram

- [ ] **Interactive Examples**
  - Visual menu selection
  - Equipment manual (clickable components)
  - Educational quiz (visual feedback)

**For Each Example**:
- [ ] Source SVG frames
- [ ] Generated FBF.SVG
- [ ] HTML demo page
- [ ] Documentation explaining technique

### Tutorial and Educational Materials

#### 7. Getting Started Guide
**Status**: ⏳ Needed

**Sections**:
- [ ] What is FBF.SVG? (concept introduction)
- [ ] Creating your first animation
  - Drawing frames in Inkscape
  - Exporting frame sequence
  - Converting with svg2fbf
  - Viewing the result
- [ ] Understanding the FBF.SVG structure
- [ ] Customizing animations (fps, loop mode, etc.)
- [ ] Troubleshooting common issues

#### 8. Best Practices Guide
**Status**: ⏳ Needed

**Topics**:
- [ ] Designing for deduplication
  - Reusing elements across frames
  - Gradient consistency
  - Symbol usage

- [ ] Optimizing file size
  - Path precision selection
  - Gradient simplification
  - Minimizing unique elements

- [ ] Performance considerations
  - Frame count limits
  - Element complexity
  - Filter usage

- [ ] Accessibility guidelines
  - Adding ARIA labels
  - Providing text alternatives
  - Ensuring keyboard navigation

- [ ] Security best practices
  - Avoiding external references
  - Sanitizing user-generated content
  - CSP policy implementation

#### 9. Advanced Topics Guide
**Status**: ⏳ Needed

**Topics**:
- [ ] Streaming implementation
  - Server architecture
  - Client player implementation
  - State synchronization
  - Error handling

- [ ] Interactive communication
  - Protocol implementation
  - LLM integration
  - Event handling
  - Security considerations

- [ ] Custom players
  - DOM interface implementation
  - Memory management
  - Performance optimization
  - Browser compatibility

### Use Case Documentation

#### 10. Case Studies
**Status**: ⏳ Needed

**Categories**:
- [ ] **Traditional Animation**
  - Animation studio workflow
  - Before/after comparison
  - File size metrics
  - Quality assessment

- [ ] **AI Visual Interface**
  - LLM integration example
  - User interaction flow
  - Latency measurements
  - Security analysis

- [ ] **Technical Documentation**
  - Equipment manual conversion
  - User feedback
  - Effectiveness metrics

- [ ] **Educational Content**
  - Interactive lesson creation
  - Accessibility compliance
  - Student engagement data

**For Each Case Study**:
- [ ] Background and problem statement
- [ ] FBF.SVG solution implementation
- [ ] Quantitative results (metrics)
- [ ] Qualitative feedback (user testimonials)
- [ ] Lessons learned

#### 11. Integration Guides
**Status**: ⏳ Needed

**For Different Tools**:
- [ ] **Inkscape Plugin** (planned)
  - Installation guide
  - Export workflow
  - Configuration options
  - Troubleshooting

- [ ] **Blender Integration** (planned)
  - Setup instructions
  - Animation export
  - Best practices

- [ ] **Web Framework Integration**
  - React component usage
  - Vue.js integration
  - Angular integration

- [ ] **Build System Integration**
  - Webpack loader
  - Gulp/Grunt task
  - npm scripts

---

## Functionalities and Procedures to Define

### Core Format Functionalities

#### 1. Frame Definition and Sequencing
**Specification Needed**:
- [ ] **Frame ID Format**
  - Pattern: FRAME + 5-digit zero-padded number
  - Valid range: FRAME00001 to FRAME99999
  - Sequencing requirements (no gaps allowed)
  - Error handling for invalid IDs

- [ ] **Frame Content Rules**
  - Allowed elements within frame group
  - Forbidden elements
  - Nesting restrictions
  - Transform inheritance

- [ ] **Frame Ordering**
  - Sequential ID requirement
  - Validation algorithm
  - Error messages for misordering

**Formal Definition**:
```
frame_id ::= "FRAME" digit{5}
digit ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"

Constraint: For all frame IDs id_n and id_{n+1} in document order,
            id_{n+1} = id_n + 1

Example:
  Valid:   FRAME00001, FRAME00002, FRAME00003
  Invalid: FRAME00001, FRAME00003 (gap at 00002)
  Invalid: FRAME00001, FRAME00002, FRAME00002 (duplicate)
```

#### 2. Animation Timing Model
**Specification Needed**:
- [ ] **Duration Calculation**
  - Formula: duration = frameCount / fps
  - Precision: Decimal places supported
  - Minimum/maximum duration

- [ ] **Frame Display Duration**
  - Formula: frameTime = duration / frameCount
  - Discrete timing (no interpolation)
  - Timing precision limits

- [ ] **Animation Modes**
  - Loop (indefinite repeat)
  - Once (single playthrough)
  - Count (N repeats)
  - Ping-pong (forward then reverse)

**Formal Definition**:
```
Animation Timing:
  Given: N frames, fps rate

  Total duration:
    duration = N / fps (seconds)

  Per-frame duration:
    frameTime = duration / N = 1 / fps (seconds)

  SMIL values attribute:
    values = "#FRAME00001;#FRAME00002;...;#FRAME{N}"

  SMIL dur attribute:
    dur = duration + "s"

  SMIL calcMode:
    calcMode = "discrete" (no interpolation)
```

#### 3. Element Deduplication Algorithm
**Specification Needed**:
- [ ] **Hash Computation**
  - Canonicalization process (normalize whitespace, attribute order)
  - Hash algorithm (SHA-256)
  - Collision handling (should never occur with SHA-256)

- [ ] **Duplicate Detection**
  - Hash comparison
  - Handling of near-duplicates (different precision)
  - Transform-aware comparison (same element, different position)

- [ ] **Reference Replacement**
  - When to use <use> vs. inline
  - ID assignment for shared elements
  - Reference updating

**Formal Definition**:
```
Deduplication Algorithm:

1. Canonicalize each element:
   - Normalize whitespace
   - Sort attributes alphabetically
   - Serialize to string

2. Compute hash:
   hash = SHA256(canonicalized_element)

3. Build hash map:
   For each element e in all frames:
     h = hash(e)
     If h not in hashMap:
       hashMap[h] = e
       assign unique ID to e
       add e to SHARED_DEFINITIONS
     Else:
       shared_e = hashMap[h]
       replace e with <use xlink:href="#shared_e.id"/>

4. Cleanup:
   Remove empty frame groups
   Renumber shared element IDs sequentially
```

#### 4. Gradient Optimization Algorithm
**Specification Needed**:
- [ ] **Stop Comparison**
  - Exact stop matching (color, offset, opacity)
  - Tolerance for floating-point offset comparison
  - Gradient attribute comparison (spreadMethod, gradientUnits)

- [ ] **Gradient Merging**
  - Conditions for mergeability
  - ID reassignment
  - Reference updating in all frames

**Formal Definition**:
```
Gradient Merging Algorithm:

1. Extract all gradient elements
2. For each pair (g1, g2) of gradients:
   If equivalent(g1, g2):
     Merge g2 into g1
     Update all references to g2 → g1
     Remove g2

equivalent(g1, g2):
  - Same type (linearGradient vs. radialGradient)
  - Same spreadMethod
  - Same gradientUnits
  - Same number of stops
  - For all stops: same offset, color, opacity
```

#### 5. Path Optimization Algorithm
**Specification Needed**:
- [ ] **Precision Reduction**
  - Rounding algorithm
  - Precision level (decimal places: 1-28)
  - Handling of different path commands (M, L, C, Q, A)

- [ ] **Command Simplification**
  - Consecutive identical commands
  - Absolute to relative conversion
  - Redundant command removal

**Formal Definition**:
```
Path Precision Reduction:

Given: Path data, precision P (decimal places)

For each coordinate value v in path:
  v_rounded = round(v, P)

Example (P=3):
  Original: M 123.456789 456.789123 L 789.123456 ...
  Rounded:  M 123.457 456.789 L 789.123 ...

Command Simplification:
  L 10 10 L 20 20 → L 10 10 20 20 (merge consecutive L)
  M 10 10 L 10 20 → M 10 10 V 20 (use vertical line)
```

### Streaming Functionalities

#### 6. Frame Appending Protocol
**Specification Needed**:
- [ ] **Client-Server Communication**
  - Transport: WebSocket vs. Server-Sent Events vs. HTTP Long Polling
  - Message format: XML fragment vs. JSON metadata + XML
  - Error handling: Retry policy, timeout handling

- [ ] **Frame Validation**
  - Sequential ID checking
  - Structure validation
  - Security validation (no external resources)

- [ ] **DOM Manipulation**
  - Append to <defs>
  - Update <animate values="...">
  - Trigger re-render

**Formal Definition**:
```
Frame Streaming Protocol:

1. Client → Server: Subscribe request
   {
     "action": "subscribe",
     "sessionId": "...",
     "capabilities": {...}
   }

2. Server → Client: Initial document
   <svg>...</svg> (complete FBF.SVG header + initial frames)

3. Client: Begin playback with initial frames

4. Server → Client: Additional frames (streaming)
   {
     "action": "append_frame",
     "frameId": "FRAME00042",
     "frameData": "<g id=\"FRAME00042\">...</g>"
   }

5. Client: Validate and append
   - Verify frameId is sequential (prev + 1)
   - Parse and validate frameData XML
   - Append to <defs>
   - Update animation values
   - Continue playback

6. Error handling:
   If validation fails:
     Client → Server: Error report
     Server: Retry or abort
```

#### 7. Memory Management (Timed Fragmentation)
**Specification Needed**:
- [ ] **Buffer Size Determination**
  - Default: 100 frames
  - Minimum: 10 frames
  - Maximum: 1000 frames
  - Device-based adaptation

- [ ] **Frame Eviction Policy**
  - FIFO (First In, First Out)
  - Sliding window
  - Key frame retention (optional)

- [ ] **Seek Behavior**
  - Within buffer: Instant seek
  - Outside buffer: Re-fetch from server

**Formal Definition**:
```
Timed Fragmentation Algorithm:

Initialize:
  buffer = CircularBuffer(maxSize = 100)
  currentFrameIndex = 0

OnFrameArrive(frame):
  buffer.append(frame)
  If buffer.size() > maxSize:
    oldestFrame = buffer.removeFirst()
    DOM.removeChild(oldestFrame)

OnSeek(targetFrameIndex):
  If targetFrameIndex in buffer:
    currentFrameIndex = targetFrameIndex
    Instant seek
  Else:
    Request frames from server
    Wait for frames
    Populate buffer
    Seek when ready
```

### Interactive Communication Functionalities

#### 8. User Input Capture
**Specification Needed**:
- [ ] **Coordinate Translation**
  - Screen coordinates → SVG viewport coordinates
  - Accounting for zoom, pan, transforms
  - Multi-touch handling

- [ ] **Element Hit Detection**
  - Point-in-polygon algorithm
  - Z-order consideration
  - Class/ID filtering (only selectable elements)

- [ ] **Event Serialization**
  - Click/touch → JSON message
  - Gesture recognition (swipe, pinch, long press)
  - Timestamp, viewport state inclusion

**Formal Definition**:
```
Coordinate Translation:

Given:
  - Screen point (sx, sy)
  - Viewport dimensions (vw, vh)
  - SVG viewBox (x, y, width, height)
  - Transform matrix M

Calculate SVG coordinates:
  svg_x = (sx / vw) * width + x
  svg_y = (sy / vh) * height + y

  If transforms applied:
    (svg_x, svg_y) = M^-1 * (svg_x, svg_y)

Element Hit Detection:
  For each element e in document (reverse z-order):
    If point(svg_x, svg_y) inside e.boundingBox:
      If e.class contains "selectable":
        Return e
  Return null

Event Serialization:
  {
    "type": "element_select" | "coordinate_select",
    "elementId": e.id (if found) | null,
    "coordinates": {"x": svg_x, "y": svg_y},
    "screenCoordinates": {"x": sx, "y": sy},
    "timestamp": ISO8601,
    "viewport": {
      "width": vw,
      "height": vh,
      "scale": currentZoom,
      "pan": {"x": panX, "y": panY}
    }
  }
```

#### 9. Server-Side Frame Generation
**Specification Needed**:
- [ ] **LLM Integration**
  - Input: User interaction event + conversation context
  - Processing: LLM generates SVG frame content
  - Output: Frame XML fragment

- [ ] **SVG Validation**
  - Structure checking
  - Security validation (no external resources)
  - ID uniqueness verification

- [ ] **Response Timing**
  - Target latency: <200ms for interactive feel
  - Timeout handling
  - Progressive generation (quick placeholder → detailed frame)

**Formal Definition**:
```
Server-Side Frame Generation:

OnUserInteraction(event):
  1. Parse interaction event
     - Extract elementId, coordinates, action, context

  2. Build LLM prompt
     prompt = buildPrompt(
       conversationHistory,
       currentFrame,
       event.elementId,
       event.action,
       event.context
     )

  3. Generate SVG content
     svgContent = LLM.generate(prompt, constraints={
       "format": "SVG",
       "noExternalResources": true,
       "maxElements": 100
     })

  4. Validate generated SVG
     If not valid:
       Retry with stricter prompt
       Or fallback to template-based generation

  5. Assign frame ID
     nextFrameId = getCurrentMaxFrameId() + 1

  6. Wrap in frame group
     frame = f"<g id='FRAME{nextFrameId:05d}'>{svgContent}</g>"

  7. Send to client
     sendMessage({
       "action": "append_frame",
       "frameId": f"FRAME{nextFrameId:05d}",
       "frameData": frame
     })
```

#### 10. State Management
**Specification Needed**:
- [ ] **Client State**
  - Current frame index
  - Buffered frame IDs
  - Viewport state (zoom, pan)
  - Selection state

- [ ] **Server State**
  - Conversation history
  - Generated frame IDs
  - User interaction log
  - Session metadata

- [ ] **Synchronization**
  - State update frequency
  - Conflict resolution
  - Recovery from desynchronization

**Formal Definition**:
```
State Management:

Client State:
  {
    "sessionId": "...",
    "currentFrameIndex": 42,
    "bufferedFrames": ["FRAME00038", ..., "FRAME00137"],
    "viewport": {
      "zoom": 1.5,
      "panX": -100,
      "panY": -50
    },
    "selectedElements": ["option_3"]
  }

Server State:
  {
    "sessionId": "...",
    "conversationHistory": [
      {"role": "user", "content": "..."},
      {"role": "assistant", "frame": "FRAME00001"}
    ],
    "generatedFrameIds": ["FRAME00001", ..., "FRAME00042"],
    "userModel": {
      "expertiseLevel": "beginner",
      "preferredDetailLevel": "verbose"
    }
  }

Synchronization:
  - Client sends state update with each interaction
  - Server incorporates client state into generation
  - Periodic heartbeat (every 30s) for connection health
  - On reconnect: Client sends full state for recovery
```

### Security Functionalities

#### 11. Content Validation
**Specification Needed**:
- [ ] **External Resource Detection**
  - Scan for xlink:href, href not starting with #
  - Scan for src attributes
  - Scan for @import in <style>
  - Rejection policy

- [ ] **Script Validation**
  - Allow only if mesh gradient polyfill
  - Hash-based verification
  - Rejection of non-matching scripts

- [ ] **Element Sanitization**
  - Forbidden elements: <foreignObject>, <script> (unless polyfill)
  - Attribute whitelist/blacklist
  - Event handler removal (onclick, etc.)

**Formal Definition**:
```
Content Validation:

validateFBFSVG(document):
  errors = []

  # Check external resources
  For each element e in document:
    If e has xlink:href attribute:
      If not xlink:href.startsWith("#"):
        errors.append("External resource: " + e.id)
    If e has href attribute:
      If not href.startsWith("#") and not href.startsWith("data:"):
        errors.append("External resource: " + e.id)

  # Check scripts
  scripts = document.findAll("script")
  If scripts.length > 1:
    errors.append("Multiple scripts not allowed")
  Else if scripts.length == 1:
    scriptHash = SHA256(scripts[0].textContent)
    If scriptHash != CANONICAL_POLYFILL_HASH:
      errors.append("Unauthorized script")

  # Check forbidden elements
  If document.findAll("foreignObject").length > 0:
    errors.append("foreignObject not allowed")

  Return errors
```

#### 12. CSP Policy Enforcement
**Specification Needed**:
- [ ] **Policy Definition**
  - Required directives
  - Optional directives
  - Fallback behavior

- [ ] **Validation**
  - Server-side CSP header verification
  - Client-side policy checking
  - Violation reporting

**Formal Definition**:
```
Content Security Policy:

Required directives:
  default-src 'none';
  img-src data:;
  style-src 'unsafe-inline';

Optional directive (if mesh gradients present):
  script-src 'unsafe-inline';

Recommended additional:
  frame-ancestors 'none';
  base-uri 'none';

Server configuration:
  Content-Security-Policy: default-src 'none'; img-src data:; style-src 'unsafe-inline'

Validation:
  - Check response headers for CSP
  - Warn if missing or too permissive
  - Reject if violates minimum requirements
```

---

## Implementation Roadmap

### Phase 1: Specification Completion (Months 1-3)
- [ ] Finalize all formal definitions
- [ ] Complete test suite (100+ test cases)
- [ ] Enhance validator (better error messages)
- [ ] Write tutorials and guides
- [ ] Create comprehensive examples

### Phase 2: Reference Implementation (Months 4-6)
- [ ] Browser player implementation
  - Basic playback
  - Streaming support
  - Interactive communication
- [ ] Streaming server implementation
  - WebSocket support
  - LLM integration example
  - State management
- [ ] Performance optimization
  - Benchmarking
  - Profiling
  - Optimization

### Phase 3: Tool Ecosystem (Months 7-12)
- [ ] Authoring tool plugin (Inkscape priority)
- [ ] Build system integrations
- [ ] Web framework components
- [ ] Documentation site
- [ ] Tutorial videos

### Phase 4: Community and Standardization (Months 13-24)
- [ ] W3C Community Group formation
- [ ] Public feedback collection
- [ ] Specification refinement
- [ ] Implementation reports
- [ ] Move toward W3C Recommendation

---

## Success Metrics

### Technical Metrics
- [ ] File size reduction: 40-70% vs. naive SVG
- [ ] Rendering performance: 60fps for typical animations
- [ ] Streaming latency: <100ms frame appending
- [ ] Validation accuracy: 100% (no false positives/negatives)
- [ ] Test suite coverage: >90%

### Adoption Metrics
- [ ] Reference implementation downloads: >10,000
- [ ] Authoring tool plugins: 2+ major tools
- [ ] Public examples: >100 FBF.SVG files
- [ ] Tutorial views: >50,000
- [ ] Community size: >1,000 active users

### Ecosystem Metrics
- [ ] Independent implementations: 2+
- [ ] Commercial adoption: 5+ companies
- [ ] Educational use: 10+ institutions
- [ ] Standards progress: W3C Community Group formed
- [ ] Media coverage: Featured in web dev publications

---

## Risk Assessment and Mitigation

### Risk 1: SMIL Deprecation
**Likelihood**: Low (reversed in 2016, stable since)
**Impact**: High (core animation mechanism)
**Mitigation**: CSS Animation fallback specified, polyfill possible

### Risk 2: Low Adoption (Chicken-Egg)
**Likelihood**: Medium
**Impact**: High (format needs ecosystem)
**Mitigation**: Focus on one tool (Inkscape), create compelling demos

### Risk 3: Competing Formats
**Likelihood**: High (Lottie, APNG, WebP)
**Impact**: Medium
**Mitigation**: Emphasize unique features (streaming, LLM communication)

### Risk 4: Performance Issues
**Likelihood**: Medium (complex animations on low-end devices)
**Impact**: Medium
**Mitigation**: Adaptive frame rate, graceful degradation

### Risk 5: Security Vulnerabilities
**Likelihood**: Low (strict validation)
**Impact**: High (trust damage)
**Mitigation**: Security audit, bug bounty program, rapid response

### Risk 6: Standardization Delays
**Likelihood**: High (W3C process is slow)
**Impact**: Low (can proceed without formal standard)
**Mitigation**: Community adoption in parallel with standardization

---

## Next Steps (Priority Order)

### Immediate (This Week)
1. [ ] Review and refine main proposal document
2. [ ] Create 5-10 compelling example animations
3. [ ] Write "Getting Started" tutorial
4. [ ] Set up GitHub Discussions for community feedback

### Short-term (This Month)
1. [ ] Enhance validator (better error messages)
2. [ ] Create test suite (50+ test cases)
3. [ ] Write comparative analysis document (FBF.SVG vs. alternatives)
4. [ ] Implement basic browser player (HTML/JS)

### Medium-term (Next 3 Months)
1. [ ] Develop Inkscape plugin (MVP)
2. [ ] Create streaming server example
3. [ ] Write LLM integration guide
4. [ ] Present at web dev conference or W3C meeting

### Long-term (Next Year)
1. [ ] Form W3C Community Group
2. [ ] Achieve 2+ independent implementations
3. [ ] Publish case studies from real-world usage
4. [ ] Begin W3C Recommendation track

---

*This planning document will be updated as the proposal progresses and community feedback is incorporated.*
