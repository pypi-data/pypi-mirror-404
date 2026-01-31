# Contributing to the FBF.SVG Standard

**Purpose**: Understanding the vision, goals, and principles of FBF.SVG standard development

> **🛠️ For practical contribution procedures, see [DEVELOPING_FORMAT.md](DEVELOPING_FORMAT.md)**

---

## Understanding the Distinction

This project maintains **two distinct contribution tracks**:

### 🔧 Tool Development ([../CONTRIBUTING.md](../CONTRIBUTING.md))
Implementation of conformant tools:
- `svg2fbf` converter (Python)
- Streaming server/client
- FBF.SVG player implementations
- Testing frameworks

**Scope**: Software implementation - code, tests, bug fixes.

### 📐 Standard Development (This Document)
Evolution of the FBF.SVG format specification:
- Format structure and semantics
- Validation rules and conformance levels
- Metadata schemas
- Extensibility mechanisms
- W3C standardization process

**Scope**: Standards development - specifications, documentation, use cases, formal definitions.

**Architectural Parallel**: Tool development implements conformant renderers (analogous to browser development). Standard development defines the specification (analogous to W3C standards work on HTML/CSS).

---

## What is FBF.SVG?

**FBF.SVG (Frame-by-Frame SVG)** is a proposed **SVG profile** for creating vector-based frame-by-frame animations. It's designed to be:

- **Standards-compliant**: Built on SVG 1.1/2.0 and SMIL Animation
- **Streamable**: Progressive rendering with unlimited frame streaming
- **Interactive**: Bidirectional LLM-to-user visual communication
- **Extensible**: Controlled extension points with validation guarantees
- **Web-native**: Works in browsers without plugins

The standard defines:
- Structural requirements (mandatory elements)
- Metadata schemas (RDF/Dublin Core)
- Animation semantics (SMIL-based frame sequencing)
- Conformance levels (Basic vs. Full)
- Validation rules and test suite

**Current Status**: Community review phase, preparing for W3C Community Group formation

**Origin**: The FBF.SVG format originated from [OpenToonz Issue #5346](https://github.com/opentoonz/opentoonz/issues/5346), addressing the need for an open vector animation format for the OpenToonz professional 2D animation software.

---

## Why FBF.SVG Matters

### The Problem: Format Fragmentation

> "An officially recommended standard for frame-by-frame vector animations will guarantee that artists and consumers will be able to have a common media format to share and exchange vector-based video animations, instead of being forcefully limited to the jungle of incompatible proprietary or open source formats..."
>
> — **Emanuele Sabetta**, FBF.SVG Project Lead

Without a standard, the ecosystem suffers from:
- **Vendor lock-in**: Artists forced into proprietary toolchains
- **Fragmentation**: Competing formats with incompatible implementations
- **Limited interoperability**: Content that doesn't work across platforms
- **Barrier to innovation**: High cost to support multiple formats

### The Solution: An Open Standard

FBF.SVG aims to be the **MP4 of vector animations** — a standardized, open, widely compatible format that:
- Provides platform-independent format with tool choice freedom
- Enables single standard API, reducing JavaScript library fragmentation
- Guarantees universal playback without plugin/library dependencies
- Reduces vendor lock-in, increasing competition and innovation

**For detailed arguments and discussion, see [FBF_PROS_AND_CONS.md](FBF_PROS_AND_CONS.md)**

---

## Standards Development Complexity

While FBF.SVG builds upon the established SVG specification foundation, creating a robust, standardized **profile** for frame-by-frame animation presents significant technical challenges:

### Specification Design Challenges
- **Multi-standard integration**: Complex interactions between SVG, SMIL, RDF, and custom metadata vocabularies
- **Novel streaming semantics**: Extension of SVG usage patterns beyond conventional document rendering
- **Precision requirements**: Specification language must ensure deterministic interoperability across independent implementations
- **Backward compatibility**: Constraints imposed by existing SVG tooling ecosystems
- **Formal validation**: Unambiguous, mechanically-testable conformance rules
- **Real-world constraints**: Use cases that stress SVG architectural assumptions

### Inherent Standards Work Characteristics
- **Linguistic precision**: Specification ambiguity causes implementation divergence
- **Edge case proliferation**: Comprehensive coverage of interaction scenarios
- **Compatibility constraints**: Design space limited by backward compatibility requirements
- **Multi-stakeholder requirements**: Reconciliation of diverse implementation needs
- **Consensus processes**: Changes subject to rigorous review and approval

**Impact**: Contributions to the specification—clarifications, test cases, use case documentation—directly improve FBF.SVG robustness and implementability. Standards development demands precision, patience, and collaborative iteration. Contributors uncertain about processes should request guidance from maintainers.

---

## Standardization Process

FBF.SVG is on a path toward **W3C Recommendation**. Understanding the process helps you contribute effectively.

### Current Phase: Community Review (Months 1-6)

**Goals**:
- Gather feedback on specification
- Build community of contributors
- Create comprehensive test suite
- Develop reference implementations

**How to contribute**:
- Review specification for clarity and completeness
- Submit use cases and examples
- Identify gaps or ambiguities
- Create test cases

### Next Phase: W3C Community Group (Months 7-12)

**Goals**:
- Form official W3C Community Group
- Publish First Public Working Draft (FPWD)
- Gather wider W3C community feedback
- Refine specification based on implementation experience

**How to contribute**:
- Join W3C Community Group (when formed)
- Participate in working group calls/discussions
- Review and comment on drafts
- Implement the specification and report feedback

### Future Phase: W3C Recommendation Track (Months 13-24+)

**Goals**:
- Transition to W3C Working Group
- Progress through: WD → CR → PR → REC
- Demonstrate interoperability (≥2 implementations)
- Pass W3C Formal Objection review

**Requirements**:
- **Candidate Recommendation (CR)**: Feature-complete spec, test suite, 2+ implementations
- **Proposed Recommendation (PR)**: Demonstrated interoperability, implementation reports
- **Recommendation (REC)**: Final approval, official W3C standard

**How to contribute**:
- Implement specification in browsers/tools
- Submit implementation reports
- Respond to formal reviews
- Participate in interoperability testing

---

## Areas Needing Contributions

Understanding where help is needed most helps you choose the right contribution area.

### High Priority (Help Needed Now!)

#### 1. Use Case Documentation
**Status**: Minimal examples exist
**Need**: 20+ real-world use cases across domains

**Examples needed**:
- Educational animations (math, science)
- Data visualization streaming
- LLM visual interfaces
- Accessibility scenarios
- Gaming/interactive art

**Impact**: Use cases validate requirements, guide feature prioritization, and demonstrate value to W3C and implementers.

#### 2. Test Suite Expansion
**Status**: ~10 test cases exist
**Need**: 100+ tests covering all features

**Current gaps**:
- Edge cases (malformed documents)
- Conformance level tests (Basic vs. Full)
- Rendering tests (visual regression)
- Streaming behavior tests
- Interactive features tests

**Impact**: Comprehensive test suites are required for W3C Candidate Recommendation status. Tests ensure interoperability between implementations.

#### 3. Formal Grammar Definition
**Status**: Prose description only
**Need**: BNF/EBNF formal grammar

**Impact**: Formal grammars eliminate ambiguity, enable parser generators, and are expected in W3C specifications.

#### 4. Accessibility Guidelines
**Status**: Minimal coverage
**Need**: Comprehensive WCAG 2.1 AA compliance guide

**Specific needs**:
- Screen reader best practices
- Keyboard navigation for interactive FBF.SVG
- Color contrast requirements
- Alternative text for frames
- Timing and motion safety (seizure prevention)

**Impact**: Accessibility is a core W3C value and requirement for Recommendation status.

#### 5. WebIDL Interface Definitions
**Status**: Conceptual only
**Need**: Complete WebIDL for JavaScript DOM API

**Impact**: Browser implementers need formal API definitions. WebIDL ensures consistent JavaScript interfaces across implementations.

### Medium Priority

- Internationalization (i18n) guidelines
- Security considerations (CSP, XSS prevention)
- Performance optimization best practices
- Streaming protocol specification (HTTP/WebSocket)
- Compression format recommendations

### Lower Priority (Future Work)

- FBF.SVG 2.0 features (scripting support?)
- Alternative animation models (CSS Animations)
- Binary FBF format (compressed variant)
- 3D frame support (SVG + WebGL?)

---

## Why W3C Reference Documents Matter

Contributors should study these W3C documents to understand specification structure, technical language conventions, and standardization best practices:

### Essential References

**[SVG 1.0 Specification (2001)](https://www.w3.org/TR/2001/PR-SVG-20010719/intro.html)**
Original SVG proposal showing introduction structure, design principles, and rationale for SVG as a standard. Essential for understanding how to position FBF.SVG within the SVG family.

**[SVG Tiny 1.1 Specification (2008)](https://www.w3.org/TR/2008/WD-SVGMobile12-20080915/single-page.html)**
Primary reference for SVG profile structure. Demonstrates element documentation patterns, conformance requirements, BNF grammar notation, and profile-specific constraints. FBF.SVG follows similar profile design patterns.

**[REX Requirements (2006)](https://www.w3.org/TR/rex-reqs/)**
Remote Events for XML protocol requirements. Relevant for understanding W3C thinking on streaming SVG content over networks, which informs FBF.SVG's streaming architecture design.

**[SVG Integration Working Draft (2014)](https://www.w3.org/TR/2014/WD-svg-integration-20140417/)**
Demonstrates formal W3C Working Draft conventions including editorial annotations, issue tracking, change proposals, and collaborative drafting methods. Essential for understanding how to maintain specification documents through iterative community review.

### Why These Documents Matter

- **Language & Style**: W3C specifications use precise technical language with RFC 2119 keywords (MUST, SHOULD, MAY)
- **Structure & Organization**: Standard section ordering, normative vs. informative content, conformance classes
- **Formal Definitions**: BNF grammars, processing models, algorithm specifications
- **Change Management**: How to annotate proposals, track issues, and maintain editorial coherence during multi-contributor drafting

Contributors proposing specification changes should reference these documents to ensure FBF.SVG follows established W3C conventions and has maximum compatibility with the broader SVG ecosystem.

---

## Recognition and Attribution

Contributors to the FBF.SVG standard will be recognized in:

### Specification Authors
Listed as editors/authors in specification documents:
```markdown
**Editors**:
- Emanuele Sabetta (Original Author)
- [Your Name] (Accessibility Lead)
- [Other Name] (Test Suite Lead)
```

### Acknowledgments Section
All contributors listed:
```markdown
## Acknowledgments

The editors would like to thank the following people for their
contributions to this specification:

- Alice Johnson - Use case documentation
- Bob Smith - Formal grammar definition
- Carol Williams - WCAG compliance guidelines
- [Your Name] - [Your contribution]
```

### GitHub Contributors Page
Automatically tracks all code and documentation contributions

### W3C Specification Credits
When published as W3C document, all contributors acknowledged

---

## Legal and Licensing

### Specification License

The FBF.SVG specification documents are licensed under:
- **[W3C Document License](https://www.w3.org/Consortium/Legal/2015/doc-license)** (when published by W3C)
- **[Creative Commons CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/)** (community drafts)

This allows:
- ✅ Free distribution
- ✅ Derivative works (translations, summaries)
- ✅ Commercial use
- ✅ Implementation in products

Requirements:
- Attribution to original authors
- Indication of changes made

### Patent Policy

When the W3C Community Group forms, all contributors must agree to:
- **[W3C Community Contributor License Agreement (CLA)](https://www.w3.org/community/about/process/cla/)**

This ensures:
- **Royalty-free** implementations (no patent licensing fees)
- **Non-discriminatory** access to the standard
- **Defensive termination** (protection against patent trolls)

**What this means**: If you contribute to the specification, you agree not to assert any patents you hold against implementations of FBF.SVG.

### Copyright

By contributing, you agree:
- Your contributions are your original work or properly licensed
- You have the right to submit the contribution
- Your contribution will be licensed under the specification license

---

## Code of Conduct

### Our Commitment

The FBF.SVG community is committed to providing a welcoming, inclusive, and harassment-free environment for all participants, regardless of:

- Age, body size, disability
- Ethnicity, gender identity/expression
- Experience level, education
- Nationality, race, religion
- Sexual identity/orientation

### Expected Behavior

- **Be respectful** of differing viewpoints and experiences
- **Be collaborative** - specifications are consensus-driven
- **Accept constructive criticism** gracefully
- **Focus on technical merit** - what's best for the standard
- **Show empathy** toward other community members
- **Assume good faith** - most disagreements are honest differences

### Unacceptable Behavior

- Harassment, intimidation, or discrimination
- Trolling, insulting/derogatory comments
- Publishing others' private information without consent
- Sustained disruption of discussions
- Other conduct inappropriate for a professional setting

### Enforcement

Violations may be reported to:
- **Email**: 713559+Emasoft@users.noreply.github.com
- **GitHub**: Use "Report abuse" feature

Maintainers will:
1. Investigate reports promptly
2. Take appropriate action (warning, temporary ban, permanent ban)
3. Maintain confidentiality of reporters

### W3C Code of Conduct

When participating in W3C activities (Community Group, Working Group), you must also follow the **[W3C Code of Ethics and Professional Conduct](https://www.w3.org/Consortium/cepc/)**.

---

## Frequently Asked Questions

### Q: How is this different from contributing code to svg2fbf?

**A**: Tool development ([../CONTRIBUTING.md](../CONTRIBUTING.md)) involves writing Python code, tests, and bug fixes for the `svg2fbf` converter and related tools. Standard development (this document) involves writing **specification text**, defining requirements, creating test cases, and working toward W3C standardization. Think of it as the difference between building a web browser (tool) vs. writing the HTML specification (standard).

### Q: Do I need to be a W3C member to contribute?

**A**: No! Community review and GitHub contributions are open to everyone. W3C membership will only be required for voting privileges when we form a W3C Community Group or Working Group. Even then, individual participation is free.

### Q: Can I create my own FBF.SVG-based format?

**A**: Yes! FBF.SVG is designed to be extensible. You can add custom elements/attributes in your own namespace. However:
- Custom extensions must use designated extension points (ANIMATION_BACKDROP)
- Must not break Basic Conformance validation
- Should be documented if you want others to adopt them

See [DEVELOPING_FORMAT.md](DEVELOPING_FORMAT.md) for extensibility guidelines.

### Q: What if my use case isn't supported by FBF.SVG?

**A**: Perfect! That's valuable feedback:
1. Document the use case in detail
2. Explain what's missing or limiting
3. Propose how FBF.SVG could be extended
4. Or, help us understand if it's out of scope

We want to know about both supported AND unsupported use cases.

### Q: What makes a good specification contribution?

**A**:
- ✅ Solves a real problem (not hypothetical)
- ✅ Clear, unambiguous language
- ✅ Includes code examples
- ✅ Backward compatible or migration path provided
- ✅ Tested with real FBF.SVG documents
- ✅ Documented impacts on conformance

---

## Contributing Expertise Areas

Different areas require different expertise:

### A. Specification Writing
**Skills**: Technical writing, formal specifications, W3C experience
**Value**: Ensures clarity, precision, and implementability

### B. Use Case Development
**Skills**: Domain expertise (animation, streaming, AI, accessibility)
**Value**: Validates requirements, demonstrates real-world applicability

### C. Metadata and Semantics
**Skills**: RDF, Dublin Core, semantic web, ontologies
**Value**: Enables rich metadata, interoperability with semantic web

### D. Accessibility and Internationalization
**Skills**: WCAG, ARIA, i18n, screen reader expertise
**Value**: Makes FBF.SVG inclusive and globally usable

### E. Validation and Conformance
**Skills**: Formal testing, XML Schema, Schematron, logic
**Value**: Ensures interoperability, required for W3C Recommendation

### F. Ecosystem Integration
**Skills**: Web standards (CSS, HTML, WebIDL), browser internals
**Value**: Enables seamless integration with web platform

---

## Next Steps

**Ready to contribute?**

1. Read the core specification: [FBF_SVG_SPECIFICATION.md](FBF_SVG_SPECIFICATION.md)
2. Review the standardization arguments: [FBF_PROS_AND_CONS.md](FBF_PROS_AND_CONS.md)
3. Learn the practical procedures: [DEVELOPING_FORMAT.md](DEVELOPING_FORMAT.md)
4. Join the discussion: [GitHub Discussions](https://github.com/Emasoft/svg2fbf/discussions)

**Questions or need help?**
Open a [GitHub Discussion](https://github.com/Emasoft/svg2fbf/discussions) - we're here to help!

---

## Thank You!

Contributing to a web standard is impactful work that benefits the entire web community. Your contributions to FBF.SVG help create a better future for vector animation on the web.

**Made with ❤️ for the OpenToonz community**

---

**For practical contribution procedures, see [DEVELOPING_FORMAT.md](DEVELOPING_FORMAT.md)**
**For tool/code contributions, see [../CONTRIBUTING.md](../CONTRIBUTING.md)**
