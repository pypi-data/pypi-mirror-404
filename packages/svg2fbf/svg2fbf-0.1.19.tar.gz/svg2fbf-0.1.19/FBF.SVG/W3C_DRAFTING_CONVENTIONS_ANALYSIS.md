# W3C Working Draft Conventions Analysis
## Based on SVG Integration Working Draft (2014-04-17)

**Source Document:** https://www.w3.org/TR/2014/WD-svg-integration-20140417/
**Analysis Date:** 2025-11-10
**Purpose:** Extract formal drafting conventions for application to FBF.SVG proposal

---

## Executive Summary

The W3C SVG Integration Working Draft demonstrates a pragmatic, transparency-first approach to collaborative specification development. Rather than hiding uncertainty, the document explicitly marks incomplete sections with "TODO" markers, poses open questions directly in the text, and uses "Should we remove this?" annotations to flag features under consideration for removal. This candid approach creates a living document that invites stakeholder feedback while maintaining formal structure through RFC 2119 conformance keywords, structured normative references, and explicit status declarations.

The document employs a minimalist editorial annotation system—no complex XML markup or color-coded change tracking. Instead, it relies on plain-text markers ("TODO", inline questions) and section-level incompleteness indicators. This lightweight approach prioritizes readability and git-based version control over heavyweight change management systems. Processing modes and feature matrices are presented in simple binary tables (yes/no columns), making security boundaries and implementation requirements immediately clear.

For multi-editor collaboration, the draft uses institutional attribution (editor affiliations prominently listed), public mailing list governance, and working group consensus processes. Individual contributions are acknowledged in a dedicated section, while the document itself asserts collective authorship by the SVG Working Group. This model balances individual accountability with community ownership—a critical pattern for open standards development.

---

## 1. Editorial Annotation System

### 1.1 Inline Change Markers

The document uses **plain-text TODO markers** embedded directly in section headings and body text:

**Section-Level TODOs:**
```markdown
### 4.2. Using SVG in 'foreignObject' TODO
```

This signals that an entire section requires completion or review. The TODO marker appears **after the section title**, making it immediately visible in navigation/TOC.

**Inline Questions as Editorial Notes:**
Rather than formal "Note:" or "Ed:" prefixes, the document poses questions directly:

> "Should animations run in the resource document?"

> "What should we say about when to rasterize the foreign content?"

> "Should we remove this processing mode?" (appears twice for Animated and Static modes)

**Acknowledgment of Incompleteness:**
The document explicitly admits uncertainty:

> "This is all too handwavy. And we perhaps shouldn't try to make an exhaustive list."

This transparent acknowledgment invites feedback rather than pretending completeness.

**Action Items Embedded in Text:**
> "Add examples of HTML in foreignObject, by reference and inline."

These are not hidden in comments but visible to all readers, creating public accountability.

### 1.2 Status Indicators

**Document-Level Status Declaration:**

The document header includes:
- **Status Label:** "W3C First Public Working Draft"
- **Publication Date:** "17 April 2014"
- **Version URL:** `http://www.w3.org/TR/2014/WD-svg-integration-20140417/`
- **Latest Draft URL:** `https://dvcs.w3.org/hg/svg2/specs/integration`

**Status Boilerplate:**
> "This is a draft document and may be updated, replaced or obsoleted by other documents at any time. It is inappropriate to cite this document as other than work in progress."

This standard W3C disclaimer appears prominently near the top of the document.

**No Section-Level Status Markers:**
Unlike some specs, this draft does not use section-level maturity indicators (e.g., "At Risk", "Stable"). Status is document-wide.

### 1.3 Change Markup Absence

**No Explicit Diff Markup:**
The document does **not** use formal change markup like:
- `<ins>` or `<del>` HTML tags
- Green/red highlighting for additions/removals
- "NEW" or "CHANGED" badges

Instead, changes are tracked through:
- Version control (referenced editor's draft at `dvcs.w3.org/hg/svg2`)
- TODO markers for incomplete sections
- Inline questions for disputed/uncertain content

This suggests reliance on **git-based diff viewing** rather than inline change presentation.

---

## 2. Issue Tracking Conventions

### 2.1 Issue Documentation Format

**No Formal Issue Numbers:**
The document does **not** use patterns like:
- "ISSUE-123: Description"
- "[OPEN] Issue: ..."
- Numbered issue lists

Instead, issues are embedded as **plain-text questions or removal candidates**.

**Inline Issue Patterns:**

1. **Open Questions:**
   > "Should animations run in the resource document?"

   These function as **unnamed issues** awaiting working group resolution.

2. **Removal Candidates:**
   > "Should we remove this processing mode?"

   This signals a feature "at risk" of being cut from the spec.

3. **Handwaving Acknowledgment:**
   > "This is all too handwavy."

   This marks sections needing complete rewrite.

### 2.2 Issue Resolution Tracking

**No Inline Resolution Markers:**
The document does not show resolved issues with:
- "RESOLVED: ..." markers
- Struck-through text with resolution notes
- Change logs within sections

**External Issue Tracker:**
The document references:
- **Public mailing list:** `www-svg@w3.org` (with public archives)
- **Working Group Charter:** References governance process

This suggests issues are tracked in:
1. Email threads on `www-svg@w3.org`
2. Meeting minutes (not linked in this draft)
3. Potentially a bug tracker (not explicitly referenced)

**Implication for FBF.SVG:**
- Use inline questions for open issues during drafting
- Track formal issue resolution in GitHub Issues
- Link to issue discussions from the spec text

---

## 3. Change Proposal Templates

### 3.1 Modification Proposals

**No Explicit Change Proposal Markup:**
The draft does not include formal change proposal sections like:
```markdown
### Proposal: Change X to Y
**Rationale:** ...
**Before:** ...
**After:** ...
```

Instead, proposals are implicit in:
- TODO markers (section needs work)
- Inline questions (decision needed)
- Draft text presented as tentative

### 3.2 Addition Proposals

**Marked Incomplete Sections:**
> "Add examples of HTML in foreignObject, by reference and inline."

This is an **addition proposal** framed as an action item, not a formal proposal template.

### 3.3 Removal Proposals

**Explicit Removal Questions:**
> "Should we remove this processing mode?"

This is the **most explicit change proposal pattern** in the document. It:
- Identifies a feature (Animated/Static mode)
- Poses a yes/no decision
- Leaves the content in place until resolution

**Template for FBF.SVG:**
When considering removing a feature from the spec:
```markdown
> **Removal Under Consideration:** Should we remove [feature name]?
>
> [Brief rationale for potential removal]
```

---

## 4. Multi-Contributor Protocols

### 4.1 Editor Attribution

**Institutional Affiliation Model:**
The document lists three editors with their organizations:

```
Editors:
    Cameron McCormack, Mozilla Corporation
    Doug Schepers, W3C
    Dirk Schulze, Adobe Systems Inc.
```

This serves multiple purposes:
1. **Individual accountability** (named editors responsible)
2. **Institutional legitimacy** (major browser vendors/W3C involved)
3. **Conflict of interest transparency** (affiliations visible)

### 4.2 Collective Authorship

**Working Group Attribution:**
> "The authors of this document are the SVG Working Group participants."

This distributes authorship across the entire working group, not just editors.

**Distinction:**
- **Editors:** Maintain document, integrate feedback
- **Authors:** SVG WG members who contribute content/decisions

### 4.3 Acknowledgments Section

**Individual Contributor Recognition:**
The document includes an "Acknowledgments" section crediting:
> "Erik Dahlström" for substantive contributions

This recognizes contributions beyond editorial work (e.g., technical proposals, reviews).

### 4.4 Public Feedback Mechanism

**Mailing List Governance:**
> "Comments on this document are welcome. Please send them to www-svg@w3.org with a subject line starting with [svg-integration] (with public archives)."

This establishes:
- **Public discussion venue** (mailing list)
- **Subject line convention** (`[svg-integration]`)
- **Archival transparency** (public archives)

### 4.5 Consensus Process

**Implicit Consensus Model:**
The document does not explicitly describe how decisions are made, but references:
- **Working Group Charter** (governance rules)
- **W3C Patent Policy** (patent disclosure process)

This implies standard W3C consensus-based decision-making.

---

## 5. Reference Standards

### 5.1 Normative References Format

**Structure:**
Each reference includes:
1. **Label:** `[ACRONYM]` in square brackets
2. **Title:** Full specification title
3. **Authors/Editors:** Credited individuals
4. **Publication Date:** Month/Year
5. **Version URL:** Link to specific dated version
6. **Latest URL:** Link to living standard/latest draft

**Example from Document:**
```
[SVG2]
SVG 2.0 Specification. Nikos Andronikos; Rossen Atanassov; Tavmjong Bah;
Amelia Bellamy-Royds; Brian Birtles; Cyril Concolato; Erik Dahlström;
Chris Lilley; Cameron McCormack; Doug Schepers; Dirk Schulze;
Richard Schwerdtfeger; Satoru Takagi; Jonathan Watt.
25 February 2014. W3C Working Draft.
URL: http://www.w3.org/TR/2014/WD-SVG2-20140211/ (or later)
URL: http://www.w3.org/TR/SVG2/
```

**Key Pattern:** Dual URLs
- **Specific edition URL:** Points to exact version cited
- **Latest version URL:** Points to current draft (may be newer)

This allows readers to see both:
- What version the spec authors referenced
- What the current state of that spec is

### 5.2 Informative References

**No Explicit Informative Section in This Draft:**
The SVG Integration draft does not separate normative and informative references, suggesting all listed references are normative.

**Standard W3C Practice:**
Typically, W3C specs use:
- **Normative References:** Required for implementation
- **Informative References:** Helpful context, not binding

### 5.3 Internal Cross-References

**Link Format:**
The document uses **fragment identifiers** for internal links:
- `[dynamic interactive](#dynamic-interactive-mode)`
- `[processing mode](#processing-mode)`
- `[referencing mode](#referencing-mode)`

**Pattern:**
```markdown
[visible text](#fragment-id)
```

This creates hyperlinked cross-references within the document.

### 5.4 RFC 2119 Keyword Usage

**Conformance Keywords:**
The document uses RFC 2119 keywords to create binding requirements:

> "must use the [dynamic interactive](#dynamic-interactive-mode) [processing mode](#processing-mode)"

> "must not be applied or run"

> "must instead be treated as if a network error occurred"

**Pattern:**
- **"must"** = absolute requirement (REQUIRED)
- **"must not"** = absolute prohibition (SHALL NOT)
- **"should"** = recommended but not required (SHOULD)

**Implication:**
RFC 2119 keywords create **testable conformance criteria**. Implementations either comply or don't.

---

## 6. Quick Reference Guide

### 6.1 Editorial Markers Cheat Sheet

| Marker | Usage | Example |
|--------|-------|---------|
| **TODO** | Section needs completion | `### 4.2. Using SVG in 'foreignObject' TODO` |
| **Inline Question** | Decision needed | `Should animations run in the resource document?` |
| **Removal Question** | Feature at risk | `Should we remove this processing mode?` |
| **Action Item** | Content to add | `Add examples of HTML in foreignObject` |
| **Handwaving** | Section too vague | `This is all too handwavy.` |

### 6.2 Status Declaration Template

```markdown
**W3C [Status Level] [Date]**

This version: [dated URL]
Latest published version: [latest URL]
Editor's Draft: [git-tracked URL]

This is a draft document and may be updated, replaced or obsoleted by
other documents at any time. It is inappropriate to cite this document
as other than work in progress.
```

### 6.3 Reference Entry Template

```markdown
[ACRONYM]
Full Title. Author 1; Author 2; Author 3. Publication Date. Status.
URL: [specific version URL]
URL: [latest version URL]
```

### 6.4 RFC 2119 Keyword Quick Reference

| Keyword | Meaning | Testable? |
|---------|---------|-----------|
| **MUST** | Absolute requirement | Yes |
| **MUST NOT** | Absolute prohibition | Yes |
| **SHOULD** | Recommended | No (but justify deviation) |
| **SHOULD NOT** | Not recommended | No (but justify use) |
| **MAY** | Optional | No |

### 6.5 Processing Mode Table Format

**Binary Feature Matrix:**

```markdown
| Feature | Enabled |
|---------|---------|
| script execution | no |
| external references | no |
| animations | yes |
```

This creates **clear security boundaries** and **implementation requirements**.

---

## 7. Application to FBF.SVG

### 7.1 Document Structure Recommendations

**For FBF.SVG Working Draft, adopt:**

1. **Prominent Status Declaration**
   ```markdown
   **W3C Community Group Draft Report [Date]**

   This is a draft proposal for extending SVG 2.0. It has not been
   adopted by any W3C Working Group. It is inappropriate to cite this
   document except as "work in progress."

   Latest version: https://github.com/[org]/fbf-svg/blob/main/FBF_SVG.md
   Issue tracker: https://github.com/[org]/fbf-svg/issues
   ```

2. **Editor Attribution with Affiliations**
   ```markdown
   Editors:
       [Your Name], [Affiliation if applicable]
       [Contributor 2], [Their Affiliation]
   ```

3. **Public Feedback Mechanism**
   ```markdown
   Comments on this proposal are welcome. Please file issues at:
   https://github.com/[org]/fbf-svg/issues

   Or join discussions in:
   [Community forum/mailing list if applicable]
   ```

### 7.2 Editorial Annotation Strategy

**For initial drafting:**

- **Use TODO markers** for incomplete sections:
  ```markdown
  ### 3.2. Frame Timing Model TODO
  ```

- **Pose inline questions** for disputed/uncertain content:
  ```markdown
  > Should frame transitions be instantaneous or gradual?
  ```

- **Mark removal candidates** explicitly:
  ```markdown
  > **Removal Under Consideration:** Should we support non-integer frame IDs?
  ```

- **Acknowledge incompleteness** transparently:
  ```markdown
  > This section needs concrete examples of complex frame sequences.
  ```

### 7.3 Issue Tracking Integration

**Hybrid approach:**

1. **Inline markers** for draft-stage issues (during writing)
2. **GitHub Issues** for formal tracking (once published)
3. **Link from spec to issues:**
   ```markdown
   > **Open Issue:** Frame inheritance semantics unclear.
   > See [Issue #42](https://github.com/org/fbf-svg/issues/42)
   ```

### 7.4 Change Proposal Format

**For proposing modifications to existing SVG features:**

```markdown
### Proposal: Extend `<use>` Element for Frame Selection

**Current SVG 2.0 Behavior:**
The `<use>` element references a single target element.

**Proposed Extension:**
Add `frame` attribute to select frame from multi-frame target:
```xml
<use href="#animated-sprite" frame="5"/>
```

**Rationale:**
Enables static frame selection from FBF sources without scripting.

**Compatibility:**
Backward compatible—`frame` attribute ignored by legacy renderers.

**Open Questions:**
- Should `frame` accept frame IDs or only indices?
- How to handle out-of-range frame values?
```

### 7.5 Conformance Requirements Strategy

**Use RFC 2119 keywords consistently:**

- **MUST/MUST NOT** for absolute requirements:
  > "A conforming FBF renderer MUST render only the current frame."

- **SHOULD/SHOULD NOT** for recommendations:
  > "Authoring tools SHOULD validate frame ID uniqueness."

- **MAY** for optional features:
  > "Renderers MAY pre-cache upcoming frames for performance."

**Create testable criteria:**
Every MUST/MUST NOT should be verifiable through:
- Automated testing (rendering output comparison)
- Manual inspection (visual verification)
- Reference implementation behavior

### 7.6 Feature Matrix for FBF

**Adopt binary table format for processing modes:**

```markdown
### 5.3. FBF Processing Modes

| Feature | Static Mode | Animated Mode |
|---------|-------------|---------------|
| Frame selection | first frame | script-controlled |
| Timeline evaluation | no | yes |
| Frame transitions | n/a | instantaneous |
| External frame references | yes | yes |
```

This creates **immediately scannable implementation requirements**.

### 7.7 Reference Section Structure

**For FBF.SVG, include:**

```markdown
## Normative References

[SVG2]
SVG 2.0 Specification. [editors]. W3C Working Draft/Candidate Recommendation.
URL: https://www.w3.org/TR/SVG2/

[RFC2119]
Key words for use in RFCs to Indicate Requirement Levels. S. Bradner.
IETF RFC 2119. March 1997.
URL: https://www.ietf.org/rfc/rfc2119.txt

[SMIL]
Synchronized Multimedia Integration Language (SMIL 3.0). [editors].
W3C Recommendation. December 2008.
URL: https://www.w3.org/TR/SMIL3/

## Informative References

[GIF89a]
Graphics Interchange Format Version 89a. CompuServe Incorporated. July 1990.
URL: https://www.w3.org/Graphics/GIF/spec-gif89a.txt

[APNG]
APNG Specification. Mozilla Corporation.
URL: https://wiki.mozilla.org/APNG_Specification
```

### 7.8 Top 3 Critical Conventions for FBF.SVG

#### 1. **Transparent Incompleteness Marking**

**Why Critical:**
The SVG Integration draft's most valuable pattern is its **candid acknowledgment of uncertainty**. Rather than presenting incomplete sections as polished, it explicitly marks them with TODO and inline questions. This:
- **Invites stakeholder feedback** on uncertain areas
- **Sets realistic expectations** (draft status is obvious)
- **Prevents premature standardization** of flawed content

**For FBF.SVG:**
- Mark all incomplete sections with TODO
- Pose design alternatives as inline questions
- Acknowledge handwaving explicitly ("This needs concrete examples")
- Use GitHub Issues to track resolution of inline questions

**Example:**
```markdown
### 4.2. Frame Inheritance Model TODO

> Should child frames inherit styles from parent frames, or are frames isolated?

This section requires concrete examples and implementer feedback.
```

#### 2. **RFC 2119 Conformance Keywords**

**Why Critical:**
The draft uses **"must", "must not", "should"** to create **testable conformance criteria**. This is essential for:
- **Interoperability** (all implementations behave consistently)
- **Validation** (automated testing can verify compliance)
- **Legal clarity** (patent licensing tied to conformance)

**For FBF.SVG:**
- Use MUST/MUST NOT for security-critical requirements
- Use SHOULD for best practices (but allow justified deviation)
- Every MUST creates a test case obligation

**Example:**
```markdown
A conforming FBF renderer MUST render only the frame specified by
the current frame selector. It MUST NOT render multiple frames
simultaneously unless explicitly composited via FBF composition operators.
```

#### 3. **Dual-URL Reference Pattern**

**Why Critical:**
The draft's reference format provides **both specific and latest URLs**:
```
URL: http://www.w3.org/TR/2014/WD-SVG2-20140211/ (specific)
URL: http://www.w3.org/TR/SVG2/ (latest)
```

This serves two audiences:
- **Implementers:** Need to know exactly which version was referenced
- **Future readers:** Need to see current state of referenced specs

**For FBF.SVG:**
- Always cite specific dated versions of SVG 2.0, SMIL, etc.
- Also link to "latest" URLs so readers see current status
- If referencing GitHub-tracked specs, use commit SHAs + latest branch

**Example:**
```markdown
[SVG2]
SVG 2.0 Specification. W3C.
URL: https://www.w3.org/TR/2024/CR-SVG2-20241015/ (cited version)
URL: https://www.w3.org/TR/SVG2/ (latest)
```

---

## 8. Additional Observations

### 8.1 No Heavy Change Markup

**Key Finding:**
The SVG Integration draft does **not** use:
- `<ins>`/`<del>` HTML tags
- Red/green diff highlighting
- "NEW in version X" badges

**Implication:**
W3C working drafts rely on **external version control** (git) for change tracking, not inline markup. This keeps the document source clean and readable.

**For FBF.SVG:**
- Use git commits to track changes
- Reference commit history in status updates
- Don't pollute the spec source with change markup

### 8.2 Security-First Feature Tables

**Key Finding:**
The processing mode tables use **binary yes/no columns** for features like:
- Script execution
- External references
- Animations

**Implication:**
This creates **immediately visible security boundaries**. Readers can instantly see which modes are sandboxed.

**For FBF.SVG:**
Create a processing mode table showing:
```markdown
| Feature | Static Rendering | Dynamic (Scripted) |
|---------|------------------|--------------------|
| Frame selection | first frame only | script-controlled |
| JavaScript execution | no | yes |
| External frame URLs | resolved at load | resolved per-frame |
```

### 8.3 Minimal Boilerplate

**Key Finding:**
The draft includes **only essential boilerplate**:
- Status declaration
- Editor list
- Patent policy link
- Mailing list for comments

It does **not** include:
- Lengthy legal disclaimers
- Excessive W3C process documentation
- Redundant copyright notices

**Implication:**
Keep boilerplate minimal to maximize signal-to-noise ratio.

**For FBF.SVG:**
- Status declaration (1 paragraph)
- Editor list with affiliations
- Link to issue tracker
- License/copyright (1 line)

---

## 9. Implementation Checklist for FBF.SVG

### Phase 1: Initial Draft Structure

- [ ] Add W3C-style status declaration at top
- [ ] List editors with affiliations
- [ ] Add "Comments welcome" section with GitHub Issues link
- [ ] Structure references section (Normative + Informative)
- [ ] Add RFC 2119 keyword definitions section

### Phase 2: Content Drafting

- [ ] Mark incomplete sections with TODO
- [ ] Pose design alternatives as inline questions
- [ ] Use MUST/MUST NOT for conformance requirements
- [ ] Create feature matrix table for processing modes
- [ ] Add concrete examples for each major feature

### Phase 3: Issue Tracking Integration

- [ ] File GitHub issues for each inline question
- [ ] Link from spec text to relevant issues
- [ ] Update inline questions with issue numbers
- [ ] Resolve issues in working group discussions

### Phase 4: Reference Completion

- [ ] Cite specific dated versions of SVG 2.0, SMIL
- [ ] Add dual URLs (specific + latest) for all references
- [ ] Verify all external specs still exist at cited URLs
- [ ] Add informative references for GIF, APNG, FLIF

### Phase 5: Pre-Publication Cleanup

- [ ] Resolve or document all TODO markers
- [ ] Ensure every MUST has a corresponding test case
- [ ] Add acknowledgments section for contributors
- [ ] Verify RFC 2119 keyword usage consistency
- [ ] Update status date and version URL

---

## 10. Conclusion

The W3C SVG Integration Working Draft demonstrates that **transparency and simplicity** are more valuable than elaborate change management systems. Its key strengths:

1. **Honest incompleteness marking** (TODO, inline questions)
2. **Testable conformance** (RFC 2119 keywords)
3. **Clear security boundaries** (binary feature tables)
4. **Git-based change tracking** (no inline diff markup)
5. **Public, archived feedback** (mailing list with archives)

For FBF.SVG, adopt these patterns to create a **readable, collaborative, and implementable** specification that invites feedback while maintaining formal rigor.

---

## Appendix: Example FBF.SVG Section Using These Conventions

```markdown
# Frame-Based Format Extension to SVG 2.0

**W3C Community Group Draft Report — 2025-11-10**

This version: https://github.com/[org]/fbf-svg/blob/main/FBF_SVG.md
Latest version: https://github.com/[org]/fbf-svg/blob/main/FBF_SVG.md
Issue tracker: https://github.com/[org]/fbf-svg/issues

**Editors:**
- [Editor 1], [Affiliation]
- [Editor 2], [Affiliation]

**Status of This Document:**

This is a draft proposal for extending SVG 2.0 with frame-based animation
capabilities. It has not been adopted by any W3C Working Group. This document
is being developed by the [Community Group Name] and may be updated, replaced,
or obsoleted at any time.

Comments on this proposal are welcome. Please file issues at:
https://github.com/[org]/fbf-svg/issues

---

## 1. Introduction

This specification defines extensions to SVG 2.0 [SVG2] that enable frame-based
animation, inspired by formats such as GIF [GIF89a] and APNG [APNG].

### 1.1. Conformance Keywords

The key words "MUST", "MUST NOT", "SHOULD", "SHOULD NOT", and "MAY" in this
document are to be interpreted as described in RFC 2119 [RFC2119].

---

## 2. Frame Definition and Selection

### 2.1. The `<frame>` Element

A frame represents a discrete animation state. Frames MUST be children of a
`<defs>` element or frame container.

**Attributes:**
- `id`: Unique frame identifier (REQUIRED)
- `duration`: Display duration in milliseconds (OPTIONAL)

**Example:**
```xml
<defs>
  <frame id="frame1" duration="100">
    <rect x="0" y="0" width="100" height="100" fill="red"/>
  </frame>
  <frame id="frame2" duration="100">
    <rect x="0" y="0" width="100" height="100" fill="blue"/>
  </frame>
</defs>
```

> **Open Issue:** Should `duration` be optional or required?
> See [Issue #7](https://github.com/org/fbf-svg/issues/7)

### 2.2. Frame Selection TODO

> Should frame selection be index-based, ID-based, or both?

This section requires concrete examples of frame selection via scripting
and declarative attributes.

---

## 3. Processing Modes

### 3.1. Feature Matrix

| Feature | Static Mode | Animated Mode |
|---------|-------------|---------------|
| Frame selection | first frame | script-controlled |
| Timeline evaluation | no | yes |
| JavaScript execution | no | yes |
| External references | yes | yes |

A conforming FBF renderer in **static mode** MUST render only the first frame.
It MUST NOT evaluate timelines or execute scripts.

A conforming FBF renderer in **animated mode** MUST support script-based frame
selection and timeline evaluation.

---

## Normative References

[SVG2]
SVG 2.0 Specification. W3C.
URL: https://www.w3.org/TR/2024/CR-SVG2-20241015/ (cited version)
URL: https://www.w3.org/TR/SVG2/ (latest)

[RFC2119]
Key words for use in RFCs to Indicate Requirement Levels. S. Bradner. IETF.
March 1997.
URL: https://www.ietf.org/rfc/rfc2119.txt

## Informative References

[GIF89a]
Graphics Interchange Format Version 89a. CompuServe. July 1990.
URL: https://www.w3.org/Graphics/GIF/spec-gif89a.txt

[APNG]
APNG Specification. Mozilla Corporation.
URL: https://wiki.mozilla.org/APNG_Specification

---

## Acknowledgments

Thanks to [contributors] for feedback on early drafts.
```

---

**End of Analysis Document**
