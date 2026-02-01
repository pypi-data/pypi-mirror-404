# Developing the FBF.SVG Standard

**Purpose**: Practical guide for contributing to the FBF.SVG specification

> **🎯 For understanding the vision and goals, see [CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md)**

---

## Quick Start

1. **Read the specification**: Start with [FBF_SVG_SPECIFICATION.md](FBF_SVG_SPECIFICATION.md)
2. **Understand the process**: Review [CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md)
3. **Follow this guide**: Learn the practical procedures below
4. **Ask questions**: Use [GitHub Discussions](https://github.com/Emasoft/svg2fbf/discussions)

---

## How to Contribute to the Standard

### Step 1: Research and Discuss

Before making changes to the specification:

1. **Check existing discussions**:
   - Search [GitHub Issues](https://github.com/Emasoft/svg2fbf/issues)
   - Browse [GitHub Discussions](https://github.com/Emasoft/svg2fbf/discussions)
   - Review [ROADMAP.md](../docs/ROADMAP.md) for planned work
   - Look for related proposals or RFCs

2. **Open a discussion** (for non-trivial changes):
   - Use GitHub Discussions → **💡 Ideas** category
   - Describe the problem or gap you've identified
   - Propose your approach
   - Get feedback from maintainers and community

**Example Discussion**:
```markdown
**Title**: Add metadata for frame-level accessibility labels

**Problem**: Current spec doesn't support per-frame ARIA labels,
making it hard to describe what happens in each frame for screen readers.

**Proposal**: Add optional `fbf:frameLabel` metadata to each FRAME group:
<g id="FRAME00001" fbf:frameLabel="Ball bounces upward">

**Use Case**: Educational animations for visually impaired students

**Backward Compatibility**: Fully backward compatible - attribute is optional

**Conformance Impact**: Optional for Basic, Recommended for Full
```

### Step 2: Read the Required Documentation

**Essential Reading**:
- [ ] **[FBF_SVG_SPECIFICATION.md](FBF_SVG_SPECIFICATION.md)** - Complete technical specification
- [ ] **[KEY_INNOVATIONS.md](../docs/KEY_INNOVATIONS.md)** - Three revolutionary capabilities
- [ ] **[GETTING_STARTED.md](../docs/GETTING_STARTED.md)** - Tutorial and examples

**Recommended Reading**:
- [ ] **[ROADMAP.md](../docs/ROADMAP.md)** - Project timeline and milestones
- [ ] **[COMPARATIVE_ANALYSIS.md](../docs/COMPARATIVE_ANALYSIS.md)** - vs. competing formats
- [ ] **[FBF_SVG_PROPOSAL.md](FBF_SVG_PROPOSAL.md)** - Formal W3C proposal

**W3C Reference Documents**:
- [ ] **[SVG 1.0 Specification (2001)](https://www.w3.org/TR/2001/PR-SVG-20010719/intro.html)** - Introduction structure and design principles
- [ ] **[SVG Tiny 1.1 Specification (2008)](https://www.w3.org/TR/2008/WD-SVGMobile12-20080915/single-page.html)** - SVG profile patterns and conventions
- [ ] **[REX Requirements (2006)](https://www.w3.org/TR/rex-reqs/)** - Streaming SVG over networks
- [ ] **[SVG Integration Working Draft (2014)](https://www.w3.org/TR/2014/WD-svg-integration-20140417/)** - W3C drafting conventions

### Step 3: Make Your Changes

1. **Fork the repository**:
   ```bash
   gh repo fork Emasoft/svg2fbf --clone
   cd svg2fbf
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b spec/add-frame-accessibility-labels
   ```

   Branch naming conventions:
   - `spec/` - Specification changes
   - `test/` - Test case additions
   - `doc/` - Documentation improvements
   - `meta/` - Metadata vocabulary additions

3. **Make your changes** to specification documents:
   - Edit relevant `.md` files in `FBF.SVG/` or `docs/`
   - Update related documents (GETTING_STARTED, KEY_INNOVATIONS, etc.)
   - Add examples demonstrating the change
   - Update validation rules if needed (fbf-svg.xsd)

4. **Follow specification style** (see Style Guide section below)

**Example commit**:
```
spec: Add frame-level accessibility metadata

- Define optional fbf:frameLabel attribute for frame groups
- Add example showing screen reader narration use case
- Update conformance section (remains optional for Basic level)
- Reference WCAG 2.1 success criteria 1.1.1

Closes #234
```

### Step 4: Submit for Review

1. **Self-review checklist**:
   - [ ] Specification language is clear and unambiguous
   - [ ] Examples are correct and tested
   - [ ] No conflicts with existing requirements
   - [ ] Backward compatible (or migration path documented)
   - [ ] References to W3C standards are accurate
   - [ ] Impacts on conformance levels identified
   - [ ] Related test cases created or updated

2. **Create pull request**:
   ```bash
   git push origin spec/add-frame-accessibility-labels
   gh pr create --title "spec: Add frame-level accessibility metadata" \
                --body "See #234 for discussion"
   ```

3. **PR template** (will be provided automatically):
   ```markdown
   ## Type of Change
   - [ ] Specification refinement
   - [x] New feature addition
   - [ ] Clarification/editorial
   - [ ] Test case addition

   ## Description
   Adds optional `fbf:frameLabel` attribute to enable per-frame
   accessibility descriptions for screen readers.

   ## Motivation
   Without this, screen readers cannot describe what's happening
   in each frame, limiting accessibility for vision-impaired users.

   ## Backward Compatibility
   ✅ Fully backward compatible - attribute is optional

   ## Conformance Impact
   - Basic Conformance: Optional
   - Full Conformance: Recommended

   ## Related Issues
   Closes #234
   ```

### Step 5: Iterate Based on Feedback

Expect review from:
- **Maintainers**: Technical accuracy and alignment with goals
- **Community**: Real-world applicability and use cases
- **W3C liaisons** (when formed): Standards compliance

Address feedback by:
- Responding to comments with clarifications
- Making requested changes with additional commits
- Providing additional examples or rationale
- Updating documentation based on discussion

---

## Specification Style Guide

### RFC 2119 Keywords

Use these keywords with **precise meaning** per [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt):

| Keyword | Meaning | When to Use |
|---------|---------|-------------|
| **MUST** / **REQUIRED** | Absolute requirement | Mandatory for conformance |
| **MUST NOT** / **SHALL NOT** | Absolute prohibition | Never allowed |
| **SHOULD** / **RECOMMENDED** | Best practice | Valid reasons may exist to ignore |
| **SHOULD NOT** / **NOT RECOMMENDED** | Generally avoid | Valid reasons may exist in special circumstances |
| **MAY** / **OPTIONAL** | Truly optional | Implementer's choice |

**Good Examples**:
```markdown
✅ The root `<svg>` element MUST include the `fbf` namespace declaration.

✅ Authors SHOULD provide `<title>` metadata for accessibility.

✅ Implementations MAY optimize duplicate elements through deduplication.
```

**Bad Examples**:
```markdown
❌ You need to add the fbf namespace.  (ambiguous - use MUST)
❌ It's recommended to include a title.  (informal - use SHOULD)
❌ Deduplication is possible.  (vague - use MAY)
❌ Don't use external resources.  (informal - use MUST NOT)
```

### Normative vs. Informative

**Normative**: Requirements for conformance (validators check these)
**Informative**: Explanations, examples, best practices (helpful but not required)

Mark sections clearly:

```markdown
## 5.2 Frame Sequencing (Normative)

Frame IDs MUST follow the pattern `FRAME` + 5 digits (00001-99999).

## 5.3 Example Frame Structure (Informative)

This non-normative example shows a valid frame definition:

<g id="FRAME00001">
  <rect width="100" height="100" fill="red"/>
</g>
```

Use these markers:
- `(Normative)` - Requirements that affect conformance
- `(Informative)` - Non-normative explanations
- `Note: ` - Informative remarks within normative sections

### Code Examples

**Every feature MUST have a code example**. Examples should be:
- Complete and valid
- Minimal (show only relevant parts)
- Well-commented
- Tested (actually works)

**Example Template**:
```markdown
### 6.4 Shared Element Deduplication

Elements identical across frames SHOULD be moved to `SHARED_DEFINITIONS`
to reduce file size and improve rendering performance.

**Example**:
\`\`\`xml
<defs>
  <g id="SHARED_DEFINITIONS">
    <!-- Background appears in all frames -->
    <rect id="shared_bg" width="800" height="600" fill="#f0f0f0"/>
  </g>

  <g id="FRAME00001">
    <use xlink:href="#shared_bg"/>
    <!-- Frame-specific content -->
    <circle cx="100" cy="100" r="20" fill="red"/>
  </g>

  <g id="FRAME00002">
    <use xlink:href="#shared_bg"/>
    <!-- Different content, same background -->
    <circle cx="200" cy="150" r="20" fill="blue"/>
  </g>
</defs>
\`\`\`

In this example, the background rectangle is defined once and reused,
reducing file size by approximately 40% compared to duplicating the
background in each frame.
```

### References

Reference W3C and other standards correctly using dual-URL pattern:

**Normative references** (required to understand the spec):
```markdown
### Normative References

**[SVG11]**
*Scalable Vector Graphics (SVG) 1.1 (Second Edition)*
Erik Dahlström et al., editors. W3C Recommendation, 16 August 2011.
Latest version: https://www.w3.org/TR/SVG11/
Referenced version: https://www.w3.org/TR/2011/REC-SVG11-20110816/

**[RFC2119]**
*Key words for use in RFCs to Indicate Requirement Levels*
S. Bradner. IETF RFC 2119, March 1997.
https://www.ietf.org/rfc/rfc2119.txt
```

**Informative references** (helpful but not required):
```markdown
### Informative References

**[CSS3-ANIMATIONS]**
*CSS Animations Level 1*
Dean Jackson et al., editors. W3C Working Draft, 11 February 2014.
https://www.w3.org/TR/css3-animations/

**[OPENTOONZ-5346]**
*Issue #5346: Standard SVG format for frame-by-frame animations*
OpenToonz GitHub Repository, June 2022.
https://github.com/opentoonz/opentoonz/issues/5346
```

**Citing in text**:
```markdown
The `<animate>` element is defined in [SMIL-ANIMATION] and
incorporated into SVG per [SVG11] section 19.2.

For rationale and use cases, see [OPENTOONZ-5346].
```

---

## Creating Test Cases

Test cases validate that implementations conform to the specification.

### Valid Document Tests

Create FBF.SVG files that **MUST pass validation**.

**Location**: `tests/valid/`

**Example**: `tests/valid/basic_two_frame_loop.fbf.svg`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     xmlns:fbf="http://opentoonz.github.io/fbf/1.0#"
     viewBox="0 0 400 300">

  <metadata>
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
             xmlns:dc="http://purl.org/dc/elements/1.1/">
      <rdf:Description>
        <dc:title>Basic Two-Frame Test</dc:title>
        <fbf:frameCount>2</fbf:frameCount>
        <fbf:fps>2</fbf:fps>
      </rdf:Description>
    </rdf:RDF>
  </metadata>

  <g id="ANIMATION_BACKDROP">
    <g id="STAGE_BACKGROUND"></g>
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" xlink:href="#FRAME00001">
          <animate attributeName="xlink:href"
                   values="#FRAME00001;#FRAME00002"
                   dur="1s"
                   repeatCount="indefinite"
                   calcMode="discrete"/>
        </use>
      </g>
    </g>
    <g id="STAGE_FOREGROUND"></g>
  </g>

  <g id="OVERLAY_LAYER"></g>

  <defs>
    <g id="FRAME00001">
      <rect width="400" height="300" fill="red"/>
    </g>
    <g id="FRAME00002">
      <rect width="400" height="300" fill="blue"/>
    </g>
  </defs>
</svg>
```

**Test description** in `tests/valid/README.md`:
```markdown
### basic_two_frame_loop.fbf.svg

**Purpose**: Validate minimal conforming FBF.SVG document

**Conformance Level**: Basic

**Expected Result**: PASS

**Tests**:
- ✅ Required structural elements present (ANIMATION_BACKDROP, ANIMATION_STAGE, etc.)
- ✅ Correct frame ID sequence (FRAME00001, FRAME00002)
- ✅ Valid SMIL animation with discrete calcMode
- ✅ Metadata includes required RDF/Dublin Core fields
- ✅ Proper namespace declarations

**Validation Command**:
```bash
uv run python scripts/validate_fbf.py tests/valid/basic_two_frame_loop.fbf.svg
```
```

### Invalid Document Tests

Create FBF.SVG files that **MUST fail validation** to test error detection.

**Location**: `tests/invalid/`

**Example**: `tests/invalid/missing_animation_backdrop.fbf.svg`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <!-- Missing ANIMATION_BACKDROP - MUST fail validation -->
  <defs>
    <g id="FRAME00001">
      <rect width="400" height="300" fill="red"/>
    </g>
  </defs>
</svg>
```

**Test description** in `tests/invalid/README.md`:
```markdown
### missing_animation_backdrop.fbf.svg

**Purpose**: Verify validator detects missing required element

**Expected Result**: FAIL

**Expected Error**: Missing required element: ANIMATION_BACKDROP

**Specification Reference**: Section 4.2 - Structural Requirements

**Error Message Should Contain**:
- "ANIMATION_BACKDROP"
- "required element"
- "conformance violation"
```

### Rendering Tests

Visual tests to verify correct rendering behavior.

**Location**: `tests/rendering/`

**Example**: `tests/rendering/gradient_deduplication/`
```
gradient_deduplication/
├── test.fbf.svg           # Test document
├── expected_frame_001.png # Expected rendering frame 1
├── expected_frame_010.png # Expected rendering frame 10
├── metadata.yaml          # Test configuration
└── README.md              # Test description
```

**Metadata** (`metadata.yaml`):
```yaml
test_name: gradient_deduplication
description: Verify deduplicated gradients render identically to non-deduplicated
frames: 10
fps: 10
expected_file_size_reduction: ">30%"
visual_regression_threshold: 0.001  # Max pixel difference
browser_compatibility:
  - chrome: ">=90"
  - firefox: ">=88"
  - safari: ">=14"
```

---

## Documentation Standards

### Document Structure

All specification documents should follow this structure:

```markdown
# Document Title

## Abstract
Brief summary (2-3 sentences) of document purpose and scope.

## Status of This Document
Current standardization status (Draft, Community Review, etc.)

## Table of Contents
(Auto-generated by GitHub or tool)

## 1. Introduction
### 1.1 Background
### 1.2 Goals
### 1.3 Non-Goals
### 1.4 Terminology

## 2. Conformance Requirements
### 2.1 Conformance Levels
### 2.2 Requirements Notation (RFC 2119)

## 3. Technical Specification
(Normative sections with subsections)

## 4. Examples (Informative)

## Appendix A: References
### A.1 Normative References
### A.2 Informative References

## Appendix B: Acknowledgments

## Appendix C: Change History
```

### Diagrams and Visual Aids

Use SVG diagrams (not ASCII art) for technical illustrations.

**Creating Diagrams**:
1. Create in `FBF.SVG/diagrams/` or `docs/diagrams/`
2. Use Inkscape, draw.io, or Mermaid
3. Export as SVG with embedded fonts
4. Optimize with SVGO if needed

**Embedding Diagrams**:
```markdown
![Frame Streaming Architecture](diagrams/streaming_architecture.svg)

*Figure 1: Progressive frame appending during playback. The structure
(ANIMATION_BACKDROP, ANIMATION_STAGE, PROSKENION) is transmitted first,
followed by frame definitions appended to `<defs>` as needed.*
```

**Diagram Tools**:
- **Inkscape**: Architecture and technical diagrams
- **draw.io** (diagrams.net): Flowcharts and process diagrams
- **Mermaid**: Simple diagrams, then export to SVG
- **D3.js**: Data visualization diagrams

### Version History

Document significant changes in a revision history table:

```markdown
## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.3.0 | 2024-11-07 | A. Johnson | Added frame-level accessibility metadata |
| 0.2.1 | 2024-10-20 | B. Smith | Clarified streaming protocol error handling |
| 0.2.0 | 2024-10-15 | E. Sabetta | Defined streaming protocol (WebSocket) |
| 0.1.0 | 2024-09-01 | E. Sabetta | Initial specification draft |
```

---

## Communication Channels

### GitHub Discussions

**Use for**:
- Questions about specification
- Use case sharing
- Feature proposals (RFCs)
- General discussion

**Categories**:
- **💡 Ideas**: Propose new features or changes to the specification
- **🙏 Q&A**: Ask questions about the specification or contribution process
- **📣 Show and Tell**: Share FBF.SVG creations or implementations
- **📖 Specification**: Discuss specific sections, ambiguities, or clarifications

**Discussion Template**:
```markdown
**Category**: Ideas

**Title**: Support for audio synchronization metadata

**Description**:
Add optional metadata to synchronize frame timing with audio tracks.

**Use Case**:
Creating music videos or educational content where visual frames
must align precisely with audio events.

**Proposed Solution**:
Add `fbf:audioSync` metadata with timecodes and frame references.

**Example**:
<g id="FRAME00042" fbf:audioSync="2.5s" fbf:audioEvent="beat-drop">

**Questions for Community**:
1. Should this be in FBF.SVG Basic or Full?
2. What audio formats should be referenced?
3. How to handle audio track metadata?
```

### GitHub Issues

**Use for**:
- Specification bugs (ambiguities, contradictions, errors)
- Test case requests
- Documentation improvements
- Tracking formal change proposals

**Issue Labels**:
- `spec-bug`: Errors or ambiguities in specification
- `spec-enhancement`: Proposed new features
- `test-case`: Test case additions or modifications
- `documentation`: Documentation improvements
- `question`: Clarification requests
- `good-first-issue`: Good for new contributors

**Issue Template**:
```markdown
**Type**: Specification Bug

**Section**: 4.2 Structural Requirements

**Issue**: Ambiguous language about ANIMATION_BACKDROP positioning

**Current Text**:
"The ANIMATION_BACKDROP element should contain the animation structure."

**Problem**:
Uses "should" (RFC 2119 SHOULD) but later sections imply it's required
(MUST). This creates ambiguity about conformance requirements.

**Proposed Fix**:
Change to:
"The ANIMATION_BACKDROP element MUST be a direct child of the root
<svg> element and MUST contain exactly one ANIMATION_STAGE element."

**Impact**:
- Conformance: Clarifies mandatory requirement
- Backward compatibility: No breaking changes (was already required in practice)
- Validation: Validators can now check unambiguously
```

### Opening a Formal Discussion on GitHub

1. Go to [Discussions](https://github.com/Emasoft/svg2fbf/discussions)
2. Click "New Discussion"
3. Select appropriate category
4. Use clear, descriptive title
5. Provide context and details
6. Tag relevant maintainers if needed
7. Be patient - community review takes time

---

## Getting Help

### Questions About Contributing

**Quick questions**:
- Open a [GitHub Discussion](https://github.com/Emasoft/svg2fbf/discussions) (🙏 Q&A category)
- Check [CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md) FAQ section
- Review existing discussions for similar questions

**Specification clarifications**:
- Comment on relevant section in specification document
- Open an issue with `spec-bug` or `question` label
- Reference specific section numbers and line numbers

**Contribution process questions**:
- Read this document and [CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md)
- Ask in GitHub Discussions (🙏 Q&A category)
- Request maintainer guidance in your PR

### Mentorship for New Contributors

If you're new to standards work, we can help!

**Request mentorship** by:
1. Opening a Discussion with **💡 Ideas** or **🙏 Q&A** category
2. Title: "Mentorship Request: [Your Interest Area]"
3. Describe your background and skills
4. Indicate what you'd like to contribute
5. Ask for guidance on getting started

**A maintainer will**:
- Suggest a good first task
- Provide guidance on standards processes
- Review your early contributions with detailed feedback
- Answer questions along the way
- Connect you with relevant experts

**Good first tasks** (labeled `good-first-issue`):
- Add examples to existing specification sections
- Write use case documentation (1-2 pages)
- Create simple valid/invalid test cases
- Fix typos or improve clarity in documentation
- Translate documentation to other languages

---

## Examples of Standard Contributions

### Example 1: Adding Frame Metadata

**Goal**: Define per-frame metadata schema

**Files to modify**:
1. `FBF.SVG/FBF_SVG_SPECIFICATION.md` - Add section 7.3
2. `docs/GETTING_STARTED.md` - Add usage example
3. `tests/valid/frame_metadata.fbf.svg` - Create test case
4. `FBF.SVG/fbf-svg.xsd` - Update XML Schema

**Specification text to add**:
```markdown
### 7.3 Frame-Level Metadata (Optional)

Individual frames MAY include metadata attributes from the `fbf` namespace
to provide additional information about the frame's content.

**Defined attributes**:
- `fbf:label` (string) - Human-readable label for the frame
- `fbf:duration` (number) - Override default frame duration in seconds
- `fbf:keyframe` (boolean) - Indicates a key frame suitable for seeking

**Example**:
\`\`\`xml
<g id="FRAME00042"
   fbf:label="Ball reaches peak"
   fbf:duration="0.2"
   fbf:keyframe="true">
  <circle cx="400" cy="100" r="20" fill="red"/>
</g>
\`\`\`

**Conformance**: Frame-level metadata is OPTIONAL for both Basic and
Full conformance levels. Implementations MAY ignore unrecognized metadata.

**Processing Model**: User agents SHOULD expose frame metadata through
the DOM interface (see WebIDL definition in Appendix D).
```

### Example 2: Security Considerations Document

**Goal**: Document security best practices

**Files to create**:
1. `FBF.SVG/SECURITY_CONSIDERATIONS.md` - New document
2. Update `FBF.SVG/README.md` - Add reference

**Content structure**:
```markdown
# FBF.SVG Security Considerations

## Abstract
This document specifies security considerations for FBF.SVG implementations
and authors.

## 1. External Resource Loading

FBF.SVG documents MUST NOT load external resources (images, fonts, scripts)
from untrusted origins without explicit user consent.

**Rationale**: Prevents tracking, CSRF attacks, and information disclosure.

**Mitigation for Authors**:
- Embed images as base64 data URIs
- Subset and embed fonts within the document
- Avoid external stylesheet references

**Mitigation for User Agents**:
- Implement Content Security Policy (CSP) enforcement
- Block or prompt for external resource loads
- Sanitize data URIs

## 2. Denial of Service Attacks

Extremely large FBF.SVG documents (millions of frames, deeply nested
structures, or complex paths) can cause browser rendering DoS.

**Mitigation for Authors**:
- Implement memory-based fragmentation (streaming)
- Limit frame count in production documents
- Optimize path complexity

**Mitigation for User Agents**:
- Implement resource limits (max frames, max file size)
- Use progressive rendering with timeouts
- Refuse to render documents exceeding limits

## 3. Content Security Policy

Authors deploying FBF.SVG SHOULD use Content Security Policy headers:

\`\`\`http
Content-Security-Policy: default-src 'none';
                         img-src 'self' data:;
                         style-src 'unsafe-inline';
                         script-src 'none'
\`\`\`

**Rationale**: Prevents script injection and ensures declarative-only content.
```

### Example 3: Use Case Documentation

**Goal**: Document real-world use case for LLM visual interfaces

**Files to create**:
1. `docs/use_cases/llm_visual_interfaces.md`
2. Update `docs/USE_CASES_INDEX.md`

**Content template**:
```markdown
# Use Case: LLM Visual Interfaces

## Problem Statement

Large Language Models (LLMs) need to provide visual feedback and interactive
interfaces to users, but current approaches require:
- Generating imperative JavaScript code (security risk)
- Using proprietary graphics APIs (vendor lock-in)
- Complex state management (fragile, hard to debug)

## FBF.SVG Solution

FBF.SVG enables declarative, secure visual interfaces that LLMs can generate
without scripting:

1. **Generate interactive SVG**: LLM creates FBF.SVG with click handlers
2. **Stream progressive updates**: Add frames in real-time as user interacts
3. **Coordinate-based input**: User provides click coordinates, LLM responds visually

## Example Scenario: Interactive Chart

**Step 1**: LLM generates initial chart

\`\`\`xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
  <g id="ANIMATION_BACKDROP">
    <g id="ANIMATION_STAGE">
      <g id="ANIMATED_GROUP">
        <use id="PROSKENION" xlink:href="#FRAME00001"/>
      </g>
    </g>
  </g>

  <defs>
    <g id="FRAME00001">
      <text x="400" y="50" text-anchor="middle">
        Sales Data (Click bars for details)
      </text>
      <rect id="bar-jan" x="100" y="200" width="80" height="150" fill="blue"/>
      <rect id="bar-feb" x="200" y="150" width="80" height="200" fill="blue"/>
    </g>
  </defs>
</svg>
\`\`\`

**Step 2**: User clicks bar at coordinates (140, 250)

**Step 3**: LLM detects click on "bar-jan", streams updated frame:

\`\`\`xml
<g id="FRAME00002">
  <!-- Original bars -->
  <rect id="bar-jan" x="100" y="200" width="80" height="150" fill="orange"/>
  <rect id="bar-feb" x="200" y="150" width="80" height="200" fill="blue"/>

  <!-- Detail popup -->
  <rect x="300" y="100" width="200" height="100" fill="white" stroke="black"/>
  <text x="400" y="130" text-anchor="middle">January Sales</text>
  <text x="400" y="160" text-anchor="middle">$45,000</text>
</g>
\`\`\`

## Benefits

- ✅ **Secure**: No JavaScript execution required
- ✅ **Simple**: LLM generates declarative markup only
- ✅ **Streamable**: Progressive enhancement without page reload
- ✅ **Accessible**: Native SVG semantics and ARIA support

## Implementation Notes

See [KEY_INNOVATIONS.md](../KEY_INNOVATIONS.md) for technical details on
bidirectional visual communication protocol.

## Demo

[Live demo on CodePen](https://codepen.io/example)
```

---

## Summary: Quick Contribution Checklist

Before submitting a contribution:

- [ ] Read core specification documents
- [ ] Discuss proposed changes in GitHub Discussions (for non-trivial changes)
- [ ] Create feature branch from `main` with proper naming (`spec/`, `test/`, `doc/`)
- [ ] Make changes using RFC 2119 keywords correctly
- [ ] Add complete, tested code examples for all features
- [ ] Create or update test cases (valid/invalid documents)
- [ ] Update related documentation (GETTING_STARTED, KEY_INNOVATIONS, etc.)
- [ ] Check backward compatibility
- [ ] Document impacts on conformance levels
- [ ] Submit PR with clear description and issue references
- [ ] Respond to review feedback promptly
- [ ] Update PR based on community discussion
- [ ] Celebrate when merged! 🎉

---

## Additional Resources

### Style and Convention References
- [W3C Manual of Style](https://www.w3.org/2001/06/manual/)
- [RFC 2119 - Requirement Levels](https://www.ietf.org/rfc/rfc2119.txt)
- [W3C QA Framework](https://www.w3.org/QA/)

### Tools
- **xmllint**: XML validation (`xmllint --schema fbf-svg.xsd file.fbf.svg`)
- **validate_fbf.py**: FBF.SVG-specific validator
- **SVGO**: SVG optimization tool
- **Inkscape**: SVG diagram creation

### Learning Resources
- [How to Write a Technical Specification](https://stackoverflow.blog/2020/04/06/how-to-write-a-technical-specification/)
- [W3C Process Document](https://www.w3.org/Consortium/Process/)
- [SVG Specification Guide](https://www.w3.org/TR/SVG11/howto.html)

---

## Thank You!

Your contributions help make FBF.SVG a robust, implementable standard for the entire web community.

**Questions?** Open a [GitHub Discussion](https://github.com/Emasoft/svg2fbf/discussions)

---

**For understanding the vision, see [CONTRIBUTING_FORMAT.md](CONTRIBUTING_FORMAT.md)**
**For tool/code contributions, see [../CONTRIBUTING.md](../CONTRIBUTING.md)**
