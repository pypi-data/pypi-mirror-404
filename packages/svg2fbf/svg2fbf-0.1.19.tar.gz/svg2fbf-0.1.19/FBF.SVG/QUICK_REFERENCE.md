# FBF.SVG Specification Quick Reference

**Fast lookup guide for W3C specification patterns**

---

## Document Sections Checklist

- [ ] Header (title, version, status, date, editors)
- [ ] Abstract (1-2 sentences)
- [ ] Status of this Document
- [ ] Table of Contents
- [ ] 1. Introduction
  - [ ] 1.1 About FBF.SVG
  - [ ] 1.2 MIME Type and File Extensions
  - [ ] 1.3 Namespace and Identifiers
  - [ ] 1.4 W3C Compatibility
  - [ ] 1.5 Terminology
  - [ ] 1.6 Definitions (Glossary)
- [ ] 2-11. Core Content Chapters
- [ ] 12. Conformance
- [ ] Appendices (A-O)

---

## Element Documentation Template (7 Parts)

```markdown
## X.Y The '<element-name>' Element

[Introductory paragraph explaining purpose and use cases]

**DTD:**

```xml
<!ELEMENT element-name (child-elements) >
<!ATTLIST element-name
  %stdAttrs;
  attribute1 CDATA #IMPLIED
  attribute2 CDATA #REQUIRED
>
```

**Attributes:**

- **attribute1** = "[type](#type)"

  [Description]

  Default: [value]
  Animatable: [yes/no]

**Example:**

```xml
<element-name attribute1="value">
  <!-- content -->
</element-name>
```

**DOM Interface:**

```idl
interface FBFElementName : FBFElement {
  readonly attribute FBFType property;
};
```

**See also:** [Related sections]
```

---

## Quick BNF Syntax

| Notation | Meaning | Example |
|----------|---------|---------|
| `::=` | Defines | `number ::= integer \| float` |
| `\|` | Or (alternative) | `"yes" \| "no"` |
| `?` | Optional (0 or 1) | `sign?` |
| `*` | Zero or more | `[0-9]*` |
| `+` | One or more | `[0-9]+` |
| `[...]` | Character class | `[a-zA-Z]` |
| `(...)` | Grouping | `("+" \| "-")` |
| `"..."` | Terminal string | `"true"` |
| `#xHHHH` | Unicode char | `#x20` (space) |

---

## RFC 2119 Keywords

| Keyword | Meaning | Use for |
|---------|---------|---------|
| **MUST** | Absolute requirement | Critical requirements |
| **MUST NOT** | Absolute prohibition | Forbidden behaviors |
| **REQUIRED** | Synonym for MUST | Mandatory features |
| **SHALL** | Synonym for MUST | Legal/contractual contexts |
| **SHALL NOT** | Synonym for MUST NOT | Legal prohibitions |
| **SHOULD** | Strong recommendation | Best practices |
| **SHOULD NOT** | Strong recommendation against | Discouraged practices |
| **RECOMMENDED** | Synonym for SHOULD | Suggested approaches |
| **MAY** | Optional/permitted | Optional features |
| **OPTIONAL** | Synonym for MAY | Explicit optionality |

---

## Example Documentation Pattern

```markdown
**Example [element][number]: [title]**

[Brief description - 1-2 sentences]

```xml
<?xml version="1.0" standalone="no"?>
<root-element xmlns="...">
  <desc>Example description</desc>
  <!-- Example content -->
</root-element>
```

[View example](link)

**Demonstrated feature:**

[Explanation]

**Expected result:**

[What the viewer should see]
```

---

## Definition Entry Pattern

```markdown
**term-name**

[Primary definition paragraph]

[Additional context]

[References: '['element']', '['other-element']']

(See [Section Name](link))
```

---

## Attribute Documentation Pattern

```markdown
- **attribute-name** = "[data-type](#data-type)"

  [Semantic description]

  [Constraints or special behaviors]

  Default: [value or "none"]

  Animatable: [yes/no]
```

---

## DTD Cardinality

| Symbol | Meaning | Example |
|--------|---------|---------|
| (none) | Exactly one | `title` |
| `?` | Zero or one | `desc?` |
| `*` | Zero or more | `frame*` |
| `+` | One or more | `layer+` |

---

## Common Data Types

```bnf
/* Numbers */
integer ::= [+-]? [0-9]+
number ::= integer | ([+-]? [0-9]* "." [0-9]+)
percentage ::= number "%"

/* Lengths */
length ::= number unit?
unit ::= "em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%"

/* Time */
time ::= number ("s" | "ms" | "min" | "h")?

/* Lists */
number-list ::= number (comma-wsp number)*
comma-wsp ::= (wsp+ ","? wsp*) | ("," wsp*)
wsp ::= #x20 | #x9 | #xD | #xA

/* References */
iri-reference ::= uri
funciri ::= "url(" wsp* iri-reference wsp* ")"
```

---

## Conformance Class Template

```markdown
### X.Y Conforming [Class Name]

A conforming [class name] is a [description] that:

1. [Requirement 1 - use MUST/SHOULD/MAY]
2. [Requirement 2]
3. [Requirement 3]

[Additional subcategories if needed]
```

---

## Error Handling Template

```markdown
**Error Handling:**

- **Invalid [attribute] value:** [recovery behavior]
- **Negative [attribute] value:** An error. [effect]
- **Zero [attribute] value:** [effect]
- **Missing [attribute]:** [default behavior]

(See [Error Processing](link))
```

---

## Accessibility Checklist

- [ ] All visual elements have `<title>` or `<desc>`
- [ ] Event descriptions for screen readers
- [ ] ARIA attributes where appropriate
- [ ] Keyboard navigation support documented
- [ ] WCAG compliance statements
- [ ] Alternative text for all graphics

---

## Example File Naming

**Format:** `[category][number].[extension]`

**Examples:**
- `rect01.svg` - First rectangle example
- `timeline01.fbf.svg` - First timeline example
- `collision-error01.fbf.svg` - First collision error demonstration

**Categories:**
- Element names: `rect`, `circle`, `path`, `frame`, `layer`
- Feature names: `gradient`, `filter`, `collision`, `timeline`
- Concept names: `coords`, `transform`, `style`
- Special: `error`, `perf`, `a11y`, `tutorial`

---

## Status Section Template

```markdown
## Status of this Document

This section describes the status of this document at the time of its publication.
Other documents may supersede this document.

This document is a [status] published on [date]. [Review period statement if applicable]

[Discussion and feedback information]

[Implementation status]

**Publication as a [status] does not imply endorsement by the W3C Membership.**
This is still a draft document and may be updated, replaced or obsoleted.

[Patent policy statement]

[Organizational context]
```

---

## Copyright Notice Template

```markdown
Copyright © [years] [Organization], All Rights Reserved.

[License/usage terms]
```

---

## Cross-Reference Formats

**To element:** `'['element-name']'` → links to element definition

**To attribute:** `'attribute-name'` → links to attribute definition

**To section:** `[Section Title](link#anchor)` → links to section

**To definition:** `[term-name](#term-name)` → links to glossary entry

**To type:** `[<type-name>](#type-name)` → links to type definition

---

## Processing Model Language

**Procedural:**
> "The processing occurs in the following order: first [step 1], then [step 2], finally [step 3]."

**Conditional:**
> "If [condition], then [action]. Otherwise, [alternative]."

**Conceptual:**
> "[Technology] uses a '[model name]' model, where [analogy]."

**Mathematical:**
> "[Operation] follows the mathematical rules for [concept] as described in [reference]."

**Implementation:**
> "A conforming implementation is not required to implement the model in exactly this way, but the result SHALL match this description."

---

## IDL Interface Pattern

```idl
interface InterfaceName : ParentInterface {
  // Constants
  const unsigned short CONSTANT_NAME = value;

  // Readonly attributes
  readonly attribute Type attributeName;

  // Mutable attributes
  attribute Type mutableAttribute;

  // Methods
  ReturnType methodName(ParamType param) raises(ExceptionName);
};
```

---

## Quick File Locations

**In this repository:**

- `W3C_SPECIFICATION_PATTERNS.md` - Full specification patterns
- `W3C_SYNTAX_PATTERNS.md` - Grammar and syntax
- `W3C_EXAMPLE_TEMPLATES.md` - Example documentation
- `SVG_SPEC_ANALYSIS_SUMMARY.md` - Complete analysis overview
- `QUICK_REFERENCE.md` - This file

**External:**

- SVG 1.0 Spec: https://www.w3.org/TR/2001/PR-SVG-20010719/
- ReSpec Tool: https://respec.org/
- RFC 2119: https://www.ietf.org/rfc/rfc2119.txt
- WCAG 2.1: https://www.w3.org/TR/WCAG21/

---

## Common Mistakes to Avoid

❌ **DON'T:**
- Use vague language ("might", "possibly", "sometimes")
- Mix MUST/SHOULD/MAY inconsistently
- Leave attributes undocumented
- Omit default values
- Skip examples for complex features
- Use implementation-specific details in normative sections
- Forget cross-references
- Mix normative and informative content without marking

✅ **DO:**
- Use precise, unambiguous language
- Apply RFC 2119 keywords consistently
- Document every attribute completely
- Specify defaults explicitly
- Provide working examples
- Describe behavior, not implementation
- Cross-reference extensively
- Mark informative sections clearly

---

**Version:** 1.0
**Last Updated:** 2025-11-10
