# W3C Syntax and Formal Grammar Patterns

**Companion to W3C Specification Patterns for FBF.SVG**

This document provides detailed syntax patterns, formal grammar notation, and validation rules extracted from the SVG 1.0 specification.

---

## Table of Contents

1. [BNF Grammar Notation](#1-bnf-grammar-notation)
2. [DTD Patterns](#2-dtd-patterns)
3. [Attribute Syntax Patterns](#3-attribute-syntax-patterns)
4. [Value Type Syntax](#4-value-type-syntax)
5. [Path Data Grammar](#5-path-data-grammar)
6. [List and Sequence Syntax](#6-list-and-sequence-syntax)
7. [Error Handling Patterns](#7-error-handling-patterns)
8. [Validation Rules](#8-validation-rules)

---

## 1. BNF Grammar Notation

### 1.1 Basic BNF Conventions

The SVG specification uses **Backus-Naur Form (BNF)** extended with regular expression syntax.

#### **Terminal Symbols**

Terminals are enclosed in quotes:

```bnf
comma ::= ","
dot ::= "."
sign ::= "+" | "-"
```

#### **Non-Terminal Symbols**

Non-terminals are lowercase identifiers:

```bnf
number
integer
length
coordinate
```

#### **Production Rules**

Format: `symbol ::= definition`

```bnf
integer ::= [+-]? [0-9]+
```

#### **Alternatives**

Use pipe symbol `|` for alternatives:

```bnf
unit ::= "em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc"
```

#### **Grouping**

Use parentheses for grouping:

```bnf
number ::= integer | ([+-]? [0-9]* "." [0-9]+)
```

#### **Optional Elements**

Use `?` for zero or one occurrence:

```bnf
sign? [0-9]+
```

#### **Repetition**

- `*` = zero or more occurrences
- `+` = one or more occurrences

```bnf
digits ::= [0-9]+
wsp* ::= (#x20 | #x9 | #xD | #xA)*
```

#### **Character Ranges**

Use square brackets for character classes:

```bnf
[0-9]      ::= any digit from 0 to 9
[a-zA-Z]   ::= any ASCII letter
[+-]       ::= plus or minus sign
```

#### **Unicode Character References**

Format: `#xHHHH` where HHHH is hexadecimal

```bnf
wsp ::= #x20 | #x9 | #xD | #xA
```

Meanings:
- `#x20` = space (U+0020)
- `#x9` = tab (U+0009)
- `#xD` = carriage return (U+000D)
- `#xA` = line feed (U+000A)

### 1.2 Complete BNF Example: Numbers

```bnf
number ::= integer
         | [+-]? [0-9]* "." [0-9]+

integer ::= [+-]? [0-9]+

digit-sequence ::= [0-9]+

sign ::= "+" | "-"

exponent ::= ("e" | "E") sign? digit-sequence

fractional-constant ::= digit-sequence? "." digit-sequence
                      | digit-sequence "."

floating-point-constant ::= fractional-constant exponent?
                          | digit-sequence exponent
```

**Valid Examples:**
- `0`
- `123`
- `-456`
- `3.14159`
- `-.5`
- `1.23e-4`
- `6.022E+23`

### 1.3 Whitespace Handling

```bnf
wsp ::= (#x20 | #x9 | #xD | #xA)

comma-wsp ::= (wsp+ comma? wsp*) | (comma wsp*)

comma ::= ","
```

**Processing Rule:**

> "The processing of the BNF must consume as much of a given BNF production as
> possible, stopping at the point when a character is encountered which no longer
> satisfies the production."

This is **greedy matching**: parsers should consume as many characters as possible
for each production.

---

## 2. DTD Patterns

### 2.1 Element Declaration

```xml
<!ELEMENT element-name content-model >
```

### 2.2 Content Models

#### **Empty Content**

```xml
<!ELEMENT line EMPTY >
```

#### **Element Content (Sequence)**

```xml
<!ELEMENT svg (desc?, title?, defs?, ...)>
```

Children must appear in order.

#### **Element Content (Choice)**

```xml
<!ELEMENT switch (desc | title | rect | circle | ...)>
```

Any one child from the list.

#### **Mixed Content**

```xml
<!ELEMENT text (#PCDATA | tspan | tref | textPath)*>
```

Text and elements can be interleaved.

### 2.3 Cardinality Indicators

| Symbol | Meaning | Example |
|--------|---------|---------|
| (none) | Exactly one | `desc` |
| `?` | Zero or one (optional) | `desc?` |
| `*` | Zero or more | `g*` |
| `+` | One or more | `stop+` |

**Examples:**

```xml
<!-- Must have exactly one 'title' -->
<!ELEMENT metadata (title) >

<!-- Optional 'desc' and 'title' -->
<!ELEMENT svg (desc?, title?, ...) >

<!-- Zero or more 'stop' elements -->
<!ELEMENT linearGradient (stop*) >

<!-- One or more 'tspan' elements -->
<!ELEMENT text (tspan+) >
```

### 2.4 Attribute List Declaration

```xml
<!ATTLIST element-name
  attribute-name attribute-type default-value
  ...
>
```

#### **Attribute Types**

| Type | Description | Example |
|------|-------------|---------|
| `CDATA` | Character data | `width CDATA #IMPLIED` |
| `ID` | Unique identifier | `id ID #IMPLIED` |
| `IDREF` | Reference to ID | `href IDREF #IMPLIED` |
| `NMTOKEN` | Name token | `type NMTOKEN #IMPLIED` |
| Enumeration | List of values | `(yes\|no) "no"` |

#### **Default Value Indicators**

| Indicator | Meaning | Example |
|-----------|---------|---------|
| `#REQUIRED` | Attribute is mandatory | `width CDATA #REQUIRED` |
| `#IMPLIED` | Attribute is optional | `x CDATA #IMPLIED` |
| `"value"` | Default value | `fill CDATA "black"` |
| `#FIXED "value"` | Fixed value only | `version CDATA #FIXED "1.0"` |

### 2.5 Parameter Entities

Define reusable attribute groups:

```xml
<!-- Define entity -->
<!ENTITY % stdAttrs "
  id ID #IMPLIED
  xml:base CDATA #IMPLIED
  xml:lang NMTOKEN #IMPLIED
  xml:space (default|preserve) #IMPLIED
">

<!-- Use entity -->
<!ATTLIST rect
  %stdAttrs;
  x CDATA #IMPLIED
  y CDATA #IMPLIED
  width CDATA #REQUIRED
  height CDATA #REQUIRED
>
```

### 2.6 Complete DTD Example

```xml
<!-- Element declarations -->
<!ELEMENT svg (desc?, title?, defs?, g*, rect*, circle*, ...)>
<!ELEMENT rect EMPTY>
<!ELEMENT g (desc?, title?, g*, rect*, circle*, ...)>

<!-- Parameter entities -->
<!ENTITY % stdAttrs "
  id ID #IMPLIED
  xml:lang NMTOKEN #IMPLIED
">

<!ENTITY % PresentationAttributes-All "
  fill CDATA #IMPLIED
  stroke CDATA #IMPLIED
  stroke-width CDATA #IMPLIED
  opacity CDATA #IMPLIED
">

<!-- Attribute lists -->
<!ATTLIST svg
  %stdAttrs;
  width CDATA #IMPLIED
  height CDATA #IMPLIED
  viewBox CDATA #IMPLIED
  xmlns CDATA #FIXED "http://www.w3.org/2000/svg"
  version CDATA #FIXED "1.0"
>

<!ATTLIST rect
  %stdAttrs;
  %PresentationAttributes-All;
  x CDATA #IMPLIED
  y CDATA #IMPLIED
  width CDATA #REQUIRED
  height CDATA #REQUIRED
  rx CDATA #IMPLIED
  ry CDATA #IMPLIED
>

<!ATTLIST g
  %stdAttrs;
  %PresentationAttributes-All;
  transform CDATA #IMPLIED
>
```

---

## 3. Attribute Syntax Patterns

### 3.1 Numeric Attributes

#### **Integer**

```bnf
integer ::= [+-]? [0-9]+
```

**Examples:**
```xml
<rect x="0" y="100" width="200" height="50"/>
```

#### **Number (Floating Point)**

```bnf
number ::= integer | ([+-]? [0-9]* "." [0-9]+)
```

**Examples:**
```xml
<circle cx="50.5" cy="75.25" r="20.0"/>
```

#### **Percentage**

```bnf
percentage ::= number "%"
```

**Examples:**
```xml
<rect width="50%" height="100%"/>
```

### 3.2 Length Attributes

```bnf
length ::= number ("em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%")?
```

**Unit Definitions:**

| Unit | Definition | Example |
|------|------------|---------|
| (none) | User units | `width="100"` |
| `em` | Font size | `width="5em"` |
| `ex` | x-height of font | `width="10ex"` |
| `px` | Pixels (user units) | `width="100px"` |
| `in` | Inches (1in = 2.54cm = 96px) | `width="2in"` |
| `cm` | Centimeters | `width="5cm"` |
| `mm` | Millimeters (1mm = 0.1cm) | `width="50mm"` |
| `pt` | Points (1pt = 1/72in) | `width="72pt"` |
| `pc` | Picas (1pc = 12pt) | `width="6pc"` |
| `%` | Percentage of viewport/parent | `width="50%"` |

**Examples:**
```xml
<rect x="10mm" y="2cm" width="5in" height="100pt"/>
<circle cx="50%" cy="50%" r="10em"/>
```

### 3.3 Coordinate Attributes

```bnf
coordinate ::= length
```

**Examples:**
```xml
<line x1="0" y1="0" x2="100" y2="100"/>
<path d="M 10,20 L 30,40"/>
```

### 3.4 Color Attributes

```bnf
color ::= "#" hexdigit hexdigit hexdigit
        | "#" hexdigit hexdigit hexdigit hexdigit hexdigit hexdigit
        | "rgb(" wsp* integer comma integer comma integer wsp* ")"
        | "rgb(" wsp* percentage comma percentage comma percentage wsp* ")"
        | color-keyword

hexdigit ::= [0-9a-fA-F]

comma ::= wsp* "," wsp*
```

**Color Keywords (subset):**
`black`, `white`, `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `gray`, etc.

**Examples:**
```xml
<rect fill="#FF0000"/>                    <!-- Hex 6-digit -->
<rect fill="#F00"/>                        <!-- Hex 3-digit -->
<rect fill="rgb(255, 0, 0)"/>              <!-- RGB integer -->
<rect fill="rgb(100%, 0%, 0%)"/>           <!-- RGB percentage -->
<rect fill="red"/>                         <!-- Keyword -->
```

### 3.5 Paint Attributes

```bnf
paint ::= "none"
        | "currentColor"
        | color
        | funciri
        | "inherit"

funciri ::= "url(" wsp* iri-reference wsp* ")" (wsp+ fallback)?

fallback ::= "none" | color
```

**Examples:**
```xml
<rect fill="none"/>
<rect fill="currentColor"/>
<rect fill="blue"/>
<rect fill="url(#gradient1)"/>
<rect fill="url(#gradient1) red"/>        <!-- With fallback -->
<rect fill="inherit"/>
```

### 3.6 Transform Attributes

```bnf
transform-list ::= wsp* transforms? wsp*

transforms ::= transform (comma-wsp+ transform)*

transform ::= matrix | translate | scale | rotate | skewX | skewY

matrix ::= "matrix" wsp* "(" wsp*
           number comma-wsp
           number comma-wsp
           number comma-wsp
           number comma-wsp
           number comma-wsp
           number wsp* ")"

translate ::= "translate" wsp* "(" wsp* number (comma-wsp number)? wsp* ")"

scale ::= "scale" wsp* "(" wsp* number (comma-wsp number)? wsp* ")"

rotate ::= "rotate" wsp* "(" wsp* number (comma-wsp number comma-wsp number)? wsp* ")"

skewX ::= "skewX" wsp* "(" wsp* number wsp* ")"

skewY ::= "skewY" wsp* "(" wsp* number wsp* ")"
```

**Examples:**
```xml
<g transform="translate(50,50)"/>
<g transform="rotate(45)"/>
<g transform="scale(2)"/>
<g transform="scale(2, 3)"/>
<g transform="rotate(45, 100, 100)"/>
<g transform="matrix(1, 0, 0, 1, 50, 50)"/>
<g transform="translate(50,50) rotate(45) scale(2)"/>
```

### 3.7 ViewBox Attribute

```bnf
viewBox ::= wsp* number comma-wsp number comma-wsp number comma-wsp number wsp*
```

Format: `min-x min-y width height`

**Examples:**
```xml
<svg viewBox="0 0 100 100"/>
<svg viewBox="-50 -50 100 100"/>
<svg viewBox="0, 0, 1200, 800"/>
```

### 3.8 PreserveAspectRatio Attribute

```bnf
preserveAspectRatio ::= defer? align meetOrSlice?

defer ::= "defer" wsp+

align ::= "none"
        | "xMinYMin" | "xMidYMin" | "xMaxYMin"
        | "xMinYMid" | "xMidYMid" | "xMaxYMid"
        | "xMinYMax" | "xMidYMax" | "xMaxYMax"

meetOrSlice ::= "meet" | "slice"
```

**Examples:**
```xml
<svg preserveAspectRatio="none"/>
<svg preserveAspectRatio="xMidYMid meet"/>
<svg preserveAspectRatio="xMinYMin slice"/>
<svg preserveAspectRatio="defer xMidYMid"/>
```

---

## 4. Value Type Syntax

### 4.1 Basic Data Types

#### **Boolean**

Not a native SVG type, but used in DOM:

**XML Attribute Representation:**
```xml
<!-- Use enumeration -->
<!ATTLIST element
  attribute (true|false) "false"
>
```

**Examples:**
```xml
<feConvolveMatrix preserveAlpha="true"/>
```

#### **String**

```bnf
string ::= [any characters]*
```

**Examples:**
```xml
<title>My SVG Document</title>
<text>Hello, World!</text>
```

### 4.2 List Types

#### **Number List**

```bnf
number-list ::= number (comma-wsp number)*
```

**Examples:**
```xml
<polygon points="0,0 100,0 100,100 0,100"/>
<feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 1 0"/>
```

#### **Length List**

```bnf
length-list ::= length (comma-wsp length)*
```

**Examples:**
```xml
<text x="10 20 30 40 50">ABCDE</text>
<text y="10, 20, 30, 40, 50">ABCDE</text>
```

### 4.3 Time Values (for Animation)

```bnf
clock-value ::= timecount-value
              | wallclock-sync-value

timecount-value ::= clock-val ("." fractional-seconds)? metric?

metric ::= "h" | "min" | "s" | "ms"

clock-val ::= [0-9]+

fractional-seconds ::= [0-9]+

wallclock-sync-value ::= "wallclock(" wallclock-val ")"

wallclock-val ::= datetime    <!-- ISO 8601 format -->
```

**Examples:**
```xml
<animate begin="0s" dur="5s"/>
<animate begin="2.5s" dur="1.5s"/>
<animate begin="00:00:30" dur="00:00:05"/>
<animate begin="3min" dur="45s"/>
<animate begin="wallclock(2001-07-19T09:00:00)"/>
```

### 4.4 IRI References

```bnf
iri-reference ::= uri

funciri ::= "url(" wsp* iri-reference wsp* ")"
```

**Examples:**
```xml
<use href="#mySymbol"/>
<use xlink:href="#mySymbol"/>        <!-- SVG 1.0/1.1 -->
<rect fill="url(#gradient1)"/>
<image href="image.png"/>
<script href="script.js"/>
```

---

## 5. Path Data Grammar

### 5.1 Complete Path Data BNF

```bnf
path-data ::= wsp* moveto-drawto-command-groups? wsp*

moveto-drawto-command-groups ::= moveto-drawto-command-group (wsp* moveto-drawto-command-group)*

moveto-drawto-command-group ::= moveto (wsp* drawto-commands)?

drawto-commands ::= drawto-command (wsp* drawto-command)*

drawto-command ::= closepath
                 | lineto
                 | horizontal-lineto
                 | vertical-lineto
                 | curveto
                 | smooth-curveto
                 | quadratic-bezier-curveto
                 | smooth-quadratic-bezier-curveto
                 | elliptical-arc

moveto ::= ("M" | "m") wsp* moveto-argument-sequence

moveto-argument-sequence ::= coordinate-pair (comma-wsp lineto-argument-sequence)?

closepath ::= ("Z" | "z")

lineto ::= ("L" | "l") wsp* lineto-argument-sequence

lineto-argument-sequence ::= coordinate-pair (comma-wsp coordinate-pair)*

horizontal-lineto ::= ("H" | "h") wsp* coordinate-sequence

vertical-lineto ::= ("V" | "v") wsp* coordinate-sequence

coordinate-sequence ::= coordinate (comma-wsp coordinate)*

curveto ::= ("C" | "c") wsp* curveto-argument-sequence

curveto-argument-sequence ::= curveto-argument (comma-wsp curveto-argument)*

curveto-argument ::= coordinate-pair comma-wsp coordinate-pair comma-wsp coordinate-pair

smooth-curveto ::= ("S" | "s") wsp* smooth-curveto-argument-sequence

smooth-curveto-argument-sequence ::= smooth-curveto-argument (comma-wsp smooth-curveto-argument)*

smooth-curveto-argument ::= coordinate-pair comma-wsp coordinate-pair

quadratic-bezier-curveto ::= ("Q" | "q") wsp* quadratic-bezier-curveto-argument-sequence

quadratic-bezier-curveto-argument-sequence ::= quadratic-bezier-curveto-argument (comma-wsp quadratic-bezier-curveto-argument)*

quadratic-bezier-curveto-argument ::= coordinate-pair comma-wsp coordinate-pair

smooth-quadratic-bezier-curveto ::= ("T" | "t") wsp* smooth-quadratic-bezier-curveto-argument-sequence

smooth-quadratic-bezier-curveto-argument-sequence ::= coordinate-pair (comma-wsp coordinate-pair)*

elliptical-arc ::= ("A" | "a") wsp* elliptical-arc-argument-sequence

elliptical-arc-argument-sequence ::= elliptical-arc-argument (comma-wsp elliptical-arc-argument)*

elliptical-arc-argument ::= nonnegative-number comma-wsp nonnegative-number comma-wsp
                            number comma-wsp flag comma-wsp flag comma-wsp coordinate-pair

coordinate-pair ::= coordinate comma-wsp coordinate

coordinate ::= number

nonnegative-number ::= integer | ([0-9]* "." [0-9]+)

flag ::= "0" | "1"

comma-wsp ::= (wsp+ comma? wsp*) | (comma wsp*)

comma ::= ","

wsp ::= (#x20 | #x9 | #xD | #xA)
```

### 5.2 Path Command Reference

| Command | Name | Parameters | Description |
|---------|------|------------|-------------|
| `M x y` | moveto (abs) | x, y | Move to absolute position |
| `m dx dy` | moveto (rel) | dx, dy | Move relative |
| `L x y` | lineto (abs) | x, y | Line to absolute position |
| `l dx dy` | lineto (rel) | dx, dy | Line relative |
| `H x` | horizontal lineto (abs) | x | Horizontal line to x |
| `h dx` | horizontal lineto (rel) | dx | Horizontal line relative |
| `V y` | vertical lineto (abs) | y | Vertical line to y |
| `v dy` | vertical lineto (rel) | dy | Vertical line relative |
| `C x1 y1 x2 y2 x y` | curveto (abs) | x1, y1, x2, y2, x, y | Cubic Bézier |
| `c dx1 dy1 dx2 dy2 dx dy` | curveto (rel) | dx1, dy1, dx2, dy2, dx, dy | Cubic Bézier relative |
| `S x2 y2 x y` | smooth curveto (abs) | x2, y2, x, y | Smooth cubic Bézier |
| `s dx2 dy2 dx dy` | smooth curveto (rel) | dx2, dy2, dx, dy | Smooth cubic relative |
| `Q x1 y1 x y` | quadratic Bézier (abs) | x1, y1, x, y | Quadratic Bézier |
| `q dx1 dy1 dx dy` | quadratic Bézier (rel) | dx1, dy1, dx, dy | Quadratic Bézier relative |
| `T x y` | smooth quadratic (abs) | x, y | Smooth quadratic Bézier |
| `t dx dy` | smooth quadratic (rel) | dx, dy | Smooth quadratic relative |
| `A rx ry φ fA fS x y` | elliptical arc (abs) | rx, ry, φ, fA, fS, x, y | Arc to absolute |
| `a rx ry φ fA fS dx dy` | elliptical arc (rel) | rx, ry, φ, fA, fS, dx, dy | Arc relative |
| `Z` or `z` | closepath | (none) | Close current subpath |

**Arc Parameters:**
- `rx`, `ry` = radii of ellipse
- `φ` = rotation angle in degrees
- `fA` = large-arc-flag (0 or 1)
- `fS` = sweep-flag (0 or 1)
- `x`, `y` = endpoint

### 5.3 Path Data Examples

**Simple shapes:**
```xml
<!-- Triangle -->
<path d="M 100 100 L 300 100 L 200 300 Z"/>

<!-- Rectangle -->
<path d="M 10 10 H 90 V 90 H 10 Z"/>

<!-- Bezier curve -->
<path d="M 10 80 C 40 10, 65 10, 95 80 S 150 150, 180 80"/>

<!-- Arc -->
<path d="M 10 315 A 30 50 0 0 1 162.55 162.45"/>
```

**Whitespace variations (all equivalent):**
```xml
<path d="M100,100L200,200"/>
<path d="M 100 100 L 200 200"/>
<path d="M100 100L200 200"/>
<path d="M100,100 L200,200"/>
```

**Implicit commands:**
```xml
<!-- Multiple lineto after moveto -->
<path d="M 10 10 20 20 30 30"/>
<!-- Equivalent to: M 10 10 L 20 20 L 30 30 -->

<!-- Multiple moveto -->
<path d="M 10 10 20 20"/>
<!-- Equivalent to: M 10 10 M 20 20 -->
```

---

## 6. List and Sequence Syntax

### 6.1 Points (for Polygon/Polyline)

```bnf
points ::= wsp* coordinate-pairs? wsp*

coordinate-pairs ::= coordinate-pair (comma-wsp coordinate-pair)*

coordinate-pair ::= coordinate comma-wsp coordinate

coordinate ::= number

comma-wsp ::= (wsp+ comma? wsp*) | (comma wsp*)

comma ::= ","

wsp ::= (#x20 | #x9 | #xD | #xA)
```

**Examples:**
```xml
<polygon points="0,0 100,0 100,100 0,100"/>
<polygon points="0 0, 100 0, 100 100, 0 100"/>
<polyline points="10,10 20,20 30,15 40,25"/>
```

### 6.2 Dasharray

```bnf
dasharray ::= "none" | dasharray-list

dasharray-list ::= length (comma-wsp length)*
```

**Examples:**
```xml
<line stroke-dasharray="5,5"/>              <!-- 5 on, 5 off -->
<line stroke-dasharray="5,10"/>             <!-- 5 on, 10 off -->
<line stroke-dasharray="5,5,10,5"/>         <!-- Complex pattern -->
<line stroke-dasharray="none"/>             <!-- Solid line -->
```

### 6.3 Transform List

Already covered in [Section 3.6](#36-transform-attributes).

**Chaining transforms:**
```xml
<g transform="translate(50,50) rotate(45) scale(2)"/>
```

Processing order: **right-to-left** (like matrix multiplication)
1. Scale by 2
2. Rotate 45°
3. Translate by (50, 50)

---

## 7. Error Handling Patterns

### 7.1 Invalid Attribute Values

**Pattern:**
```
A [condition] is an error (see [Error processing](link)).
```

**Examples from SVG:**

> "A negative value is an error (see Error processing)."

> "A value of zero disables rendering of the element."

> "If the attribute is not specified, the effect is as if a value of '0' were specified."

### 7.2 Error Recovery Guidelines

#### **For Attributes:**

1. **Invalid value:** Use default value
2. **Out of range:** Clamp to valid range or use default
3. **Missing required attribute:** Document may be non-conforming

#### **For Elements:**

1. **Unknown element:** Ignore element and its content
2. **Misnested element:** Best-effort rendering
3. **Unsupported feature:** Graceful degradation

### 7.3 Error Documentation Template

```markdown
**Error Handling:**

- **Invalid [attribute] value:** [recovery behavior]
- **Negative [attribute] value:** An error. [recovery behavior or "Rendering disabled"]
- **Zero [attribute] value:** [effect, often "Disables rendering"]
- **Missing [attribute]:** [default value behavior]

(See [Error Processing](link) for general error handling rules)
```

**Example:**

```markdown
**Error Handling for 'width' and 'height' attributes:**

- **Negative value:** An error. The element is not rendered.
- **Zero value:** Disables rendering of the element.
- **Missing attribute:** Treated as if '0' were specified (element not rendered).
- **Non-numeric value:** An error. Uses default value of '0'.
```

---

## 8. Validation Rules

### 8.1 Structural Validation

#### **Well-Formedness (XML)**

All SVG documents must be well-formed XML:

1. **Single root element:** `<svg>` for stand-alone documents
2. **Properly nested elements:** All tags must be correctly opened and closed
3. **Quoted attribute values:** `<rect width="100"/>` not `<rect width=100/>`
4. **Unique attribute names:** No duplicate attributes on the same element
5. **Entity references:** Use `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`

#### **Namespace Declaration**

```xml
<svg xmlns="http://www.w3.org/2000/svg">
  <!-- SVG content -->
</svg>
```

**With XLink (SVG 1.0/1.1):**
```xml
<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink">
  <use xlink:href="#symbol1"/>
</svg>
```

### 8.2 Attribute Validation

#### **Required Attributes**

Elements must have all `#REQUIRED` attributes:

```xml
<!-- Valid -->
<rect width="100" height="50"/>

<!-- Invalid: missing 'width' and 'height' -->
<rect x="10" y="10"/>
```

#### **Attribute Value Constraints**

**Non-negative lengths:**
```xml
<!-- Valid -->
<rect width="100" height="50"/>

<!-- Invalid: negative width -->
<rect width="-100" height="50"/>
```

**Enumeration values:**
```xml
<!-- Valid -->
<text xml:space="preserve">Text with   spaces</text>

<!-- Invalid: bad enum value -->
<text xml:space="trim">Text</text>
```

### 8.3 Reference Validation

#### **IRI Reference Targets**

References must point to existing elements with matching IDs:

```xml
<!-- Valid -->
<defs>
  <linearGradient id="gradient1">
    <stop offset="0%" stop-color="red"/>
    <stop offset="100%" stop-color="blue"/>
  </linearGradient>
</defs>
<rect fill="url(#gradient1)"/>

<!-- Invalid: #gradient2 does not exist -->
<rect fill="url(#gradient2)"/>
```

**Fallback handling:**
```xml
<!-- With fallback: if #gradient2 not found, use 'red' -->
<rect fill="url(#gradient2) red"/>
```

#### **ID Uniqueness**

Every `id` attribute value must be unique within the document:

```xml
<!-- Valid -->
<rect id="rect1"/>
<rect id="rect2"/>

<!-- Invalid: duplicate id -->
<rect id="rect1"/>
<rect id="rect1"/>    <!-- ERROR: duplicate -->
```

### 8.4 Validation Checklist

**Document Level:**
- [ ] Well-formed XML
- [ ] Valid namespace declarations
- [ ] DOCTYPE declaration (optional but recommended)
- [ ] Root `<svg>` element

**Element Level:**
- [ ] All elements are in DTD/schema
- [ ] Elements properly nested according to content model
- [ ] Required attributes present
- [ ] Attribute values match declared types

**Attribute Level:**
- [ ] Attribute values within valid ranges
- [ ] Enumeration values are from permitted set
- [ ] Length units are recognized
- [ ] Colors in valid format
- [ ] Paths have valid syntax

**Reference Level:**
- [ ] All `id` values are unique
- [ ] All IRI references point to existing elements
- [ ] Referenced elements are of appropriate type

---

## Appendix: Complete Mini-Grammar Reference

### SVG Document Structure

```bnf
svg-document ::= xml-declaration? doctype-declaration? svg-element

xml-declaration ::= "<?xml" version-info encoding-declaration? "?>"

version-info ::= "version" "=" ("'" version "'" | '"' version '"')

version ::= "1.0" | "1.1"

encoding-declaration ::= "encoding" "=" ("'" encoding "'" | '"' encoding '"')

encoding ::= "UTF-8" | "UTF-16" | ...

doctype-declaration ::= "<!DOCTYPE svg PUBLIC" public-id system-id ">"

public-id ::= '"-//W3C//DTD SVG 1.0//EN"'

system-id ::= '"http://www.w3.org/TR/2001/PR-SVG-20010719/DTD/svg10.dtd"'

svg-element ::= "<svg" svg-attributes ">" svg-content "</svg>"
```

### Basic Types Summary

```bnf
/* Numbers */
integer ::= [+-]? [0-9]+
number ::= integer | ([+-]? [0-9]* "." [0-9]+) | floating-point-constant
percentage ::= number "%"

/* Lengths */
length ::= number unit?
unit ::= "em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%"

/* Colors */
color ::= "#" rgb | "rgb(" integer "," integer "," integer ")"
        | "rgb(" percentage "," percentage "," percentage ")"
        | color-keyword

rgb ::= hexdigit hexdigit hexdigit (hexdigit hexdigit hexdigit)?

/* Paint */
paint ::= "none" | "currentColor" | color | funciri | "inherit"
funciri ::= "url(" iri-reference ")" fallback?

/* Transforms */
transform ::= "matrix(" number* ")"
            | "translate(" number number? ")"
            | "scale(" number number? ")"
            | "rotate(" number (number number)? ")"
            | "skewX(" number ")" | "skewY(" number ")"

/* Paths */
path-data ::= moveto-drawto-command-groups
moveto ::= ("M" | "m") coordinate-pair
lineto ::= ("L" | "l") coordinate-pair
curveto ::= ("C" | "c") coordinate-pair coordinate-pair coordinate-pair
closepath ::= ("Z" | "z")

/* Lists */
number-list ::= number (comma-wsp number)*
length-list ::= length (comma-wsp length)*
coordinate-pairs ::= coordinate-pair (comma-wsp coordinate-pair)*

/* Whitespace */
wsp ::= #x20 | #x9 | #xD | #xA
comma-wsp ::= (wsp+ ","? wsp*) | ("," wsp*)
```

---

## Conclusion

This document provides the formal syntax patterns and grammar notation used throughout the SVG 1.0 specification. When creating the FBF.SVG specification:

1. **Use BNF notation** for formal syntax definitions
2. **Follow DTD patterns** for element and attribute declarations
3. **Define error handling** explicitly for each constraint
4. **Provide validation rules** at document, element, and attribute levels
5. **Include complete examples** demonstrating valid and invalid syntax

By adhering to these patterns, the FBF.SVG specification will be precise, implementable, and consistent with W3C standards.
