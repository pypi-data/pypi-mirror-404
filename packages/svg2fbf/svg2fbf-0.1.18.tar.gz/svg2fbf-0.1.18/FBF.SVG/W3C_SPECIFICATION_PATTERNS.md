# W3C Specification Patterns for FBF.SVG

**Based on analysis of SVG 1.0 Specification (W3C Proposed Recommendation, 19 July 2001)**

This document extracts the documentation patterns, templates, and conventions used in the original SVG 1.0 W3C specification to guide the development of the FBF.SVG specification.

---

## Table of Contents

1. [Document Structure](#1-document-structure)
2. [Introduction Patterns](#2-introduction-patterns)
3. [Terminology and Definitions](#3-terminology-and-definitions)
4. [Feature Documentation Template](#4-feature-documentation-template)
5. [Processing Model Specification](#5-processing-model-specification)
6. [DOM Interface Specification](#6-dom-interface-specification)
7. [Data Type Definitions](#7-data-type-definitions)
8. [Conformance Requirements](#8-conformance-requirements)
9. [Status and Boilerplate](#9-status-and-boilerplate)
10. [Best Practices Summary](#10-best-practices-summary)

---

## 1. Document Structure

### 1.1 Overall Organization

The SVG 1.0 specification follows a logical progression:

1. **Header Section**
   - Document identification (title, status, date, URL)
   - Editor information
   - W3C logo and institutional affiliation
   - Navigation links (previous, next, contents, elements, attributes, properties, index)
   - Copyright notice

2. **Abstract** (concise, 1-2 sentences)
   - States the specification's purpose
   - Identifies what is being defined

3. **Status of this Document**
   - Current W3C process stage
   - Review period information
   - Patent disclosures
   - Legal disclaimers

4. **Table of Contents**
   - Hierarchical listing of all sections
   - Appendices listed separately

5. **Main Content Sections** (organized progressively):
   - **Foundational** (Introduction, Concepts, Rendering Model, Basic Data Types)
   - **Core Features** (Document Structure, Styling, Coordinate Systems, Paths, Shapes, Text, etc.)
   - **Advanced Capabilities** (Filters, Interactivity, Linking, Scripting, Animation, Fonts, Metadata)
   - **Extensibility and Compatibility**

6. **Appendices** (A-O):
   - DTD and DOM specifications
   - Language bindings (IDL, Java, ECMAScript)
   - Implementation requirements and conformance
   - Accessibility and internationalization
   - Optimization guidance
   - Comprehensive indexes

### 1.2 Navigation Structure

Each chapter includes:
- Breadcrumb navigation (previous, next, contents)
- Section numbering (hierarchical: 1.1, 1.1.1, etc.)
- Internal anchor links for cross-referencing
- Hyperlinked cross-references throughout

---

## 2. Introduction Patterns

### 2.1 Introduction Section Structure

The introduction comprises six main subsections:

#### **Section 1.1: About [Technology]**
- Explains what the technology is (concise definition)
- Describes core capabilities (graphic object types, features)
- Discusses interactive capabilities
- Covers DOM access and event handlers
- Mentions accessibility considerations

**Template:**
```
[Technology] is a language for [primary purpose] in [format/medium].

[Technology] offers three types of [primary elements]:
1. [Type 1] - [description]
2. [Type 2] - [description]
3. [Type 3] - [description]

[Technology] supports [interactive features], including [specific capabilities].

[Accessibility statement]
```

#### **Section 1.2: MIME Type and File Extensions**
- MIME type designation
- Standard file extension
- Compressed variant extension (if applicable)
- Platform-specific notes (Macintosh, Windows, Unix)

**Template:**
```
**MIME Type:** [type]/[subtype]
**File Extension:** .[ext]
**Compressed Extension:** .[compressed-ext]

Platform-specific considerations:
- Macintosh: [details]
- Windows: [details]
- Unix/Linux: [details]
```

#### **Section 1.3: Namespace and Identifiers**
- Namespace URI
- Public identifier
- System identifier
- DOCTYPE declaration example

**Template:**
```
**Namespace URI:** [URI]
**Public Identifier:** [identifier]
**System Identifier:** [identifier]

Sample DOCTYPE declaration:
```xml
<!DOCTYPE [root-element] PUBLIC "[public-id]" "[system-id]">
```
```

#### **Section 1.4: W3C Compatibility**
- Relationship with other W3C standards (bullet list)
- Integration points with existing technologies
- Compliance with international standards

**Template:**
```
[Technology] is compatible with the following W3C Recommendations and standards:

- **[Standard 1]:** [how it's used/integrated]
- **[Standard 2]:** [how it's used/integrated]
- **[Standard 3]:** [how it's used/integrated]
...
```

#### **Section 1.5: Terminology**
- RFC 2119 keywords (MUST, SHOULD, MAY)
- Distinction between normative and informative content
- Document conventions

**Template:**
```
This specification uses the key words "MUST", "MUST NOT", "REQUIRED", "SHALL",
"SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL"
as defined in [RFC2119].

**Normative** sections describe required behavior for conforming implementations.
**Informative** sections provide guidance, examples, and explanatory material.
```

#### **Section 1.6: Definitions**
- Alphabetically arranged glossary
- 30-40+ key terms
- Cross-referenced to specification sections
- See [Section 3](#3-terminology-and-definitions) for detailed format

---

## 3. Terminology and Definitions

### 3.1 Glossary Format

**Structure:**
- **Alphabetical ordering** of all terms
- **Bold, lowercase** term names
- **Definition paragraph(s)** following each term
- **Element/component references** in brackets with links: `['element-name']`
- **Cross-references** to other definitions and sections using hash links
- **Section citations** in parentheses: `(See [Section Name](link))`

### 3.2 Definition Pattern

**Template:**
```markdown
**[term name]**

[Primary definition paragraph explaining the concept clearly and concisely]

[Additional context or technical details if needed]

[References to related elements: '['element1']', '['element2']', '['element3']']

(See [Related Section](link#anchor))
```

### 3.3 Definition Examples

**Example 1: Simple Definition**
```markdown
**canvas**

The surface onto which the document is rendered. The canvas is initialized to transparent
and extends infinitely in all directions. At render time, the canvas is typically
defined by the output device dimensions.

(See the discussion of the [SVG canvas](coords.html#SVGCanvas))
```

**Example 2: Categorical Definition**
```markdown
**graphics element**

One of the element types that can cause graphics to be drawn onto the target canvas.
Specifically: ['path'], ['text'], ['rect'], ['circle'], ['ellipse'], ['line'],
['polyline'], ['polygon'], ['image'], and ['use'].
```

**Example 3: Technical Definition**
```markdown
**transformation matrix**

A 3x3 matrix representing affine transformations in two-dimensional space, represented
in homogeneous coordinates:

x' y' 1 = x y 1 * [a c e]
                  [b d f]
                  [0 0 1]

This allows translation, scaling, rotation, skewing, and combinations thereof to be
expressed as matrix multiplication.

(See [Coordinate Systems and Transformations](coords.html))
```

### 3.4 Cross-Referencing Patterns

- **Internal definitions:** `See also: [other term](#other-term)`
- **Section references:** `(See [Chapter Name](file.html#section))`
- **Element references:** `['element-name']` (linked to element definition)
- **Attribute references:** `'attribute-name'` (linked to attribute definition)

---

## 4. Feature Documentation Template

### 4.1 Element Definition Structure

Every element in the specification follows a consistent seven-part template:

#### **Part 1: Introductory Overview**
- Prose explaining purpose and use cases
- When and why to use this element
- Relationship to other elements

**Template:**
```markdown
The '[element-name]' element [primary purpose]. It is used to [use case description].

[Contextual information about relationships and behavior]
```

#### **Part 2: DTD Formal Definition**
- XML Document Type Definition syntax
- Allowed child elements with cardinality
- Entity references for element groups

**Template:**
```xml
<!ELEMENT element-name (child-element1?, child-element2*, child-element3+, ...) >
<!ATTLIST element-name
  %stdAttrs;
  %PresentationAttributes-All;
  attribute1 CDATA #IMPLIED
  attribute2 CDATA #REQUIRED
  attribute3 (value1|value2|value3) "value1"
  ...
>
```

**Cardinality notation:**
- `?` = zero or one
- `*` = zero or more
- `+` = one or more
- No symbol = exactly one

#### **Part 3: Attribute Declarations**
- Complete `<!ATTLIST>` block
- Element-specific attributes
- Inherited attribute groups (`%stdAttrs;`, `%PresentationAttributes-All;`, etc.)
- Reference attributes (`xlink:href`, etc.)

#### **Part 4: Attribute Definitions Section**

Each attribute documented with:
- **Name** (in definition list format)
- **Data type** (e.g., `<length>`, `<number>`, `<string>`, enumeration)
- **Default value** or "none"
- **Semantic explanation** (what it does, how it affects behavior)
- **Animatability** ("Animatable: yes" or "Animatable: no")

**Template:**
```markdown
**Attributes:**

- **attribute-name** = "[data-type](#data-type)"

  [Semantic description of what this attribute controls]

  [Any constraints or special behaviors]

  Default value: [value or "none"]

  Animatable: [yes/no]

- **attribute-name-2** = "value1 | value2 | value3"

  [Description]

  Default value: value1

  Animatable: no
```

#### **Part 5: Practical Examples**

Complete, working code samples:
- **XML source code** in syntax-highlighted blocks
- **Visual rendering** (embedded SVG or linked image)
- **Link to live example** (if applicable)
- **Explanation** of key aspects demonstrated

**Template:**
```markdown
**Example:**

[Brief description of what this example demonstrates]

```xml
<element-name attribute1="value1" attribute2="value2">
  <child-element />
  <!-- Example content -->
</element-name>
```

[Visual rendering or link to rendered example]

[Explanation of key aspects]
```

#### **Part 6: DOM Interface Specifications**

For elements with programmatic interfaces:
- **IDL definition** (Interface Definition Language)
- **Interface inheritance** (extends which interface)
- **Attribute mappings** (DOM properties to XML attributes)
- **Method signatures** with parameters and return types
- **Exception specifications**

**Template:**
```idl
interface SVGElementName : SVGParentInterface {
  readonly attribute SVGType property1;
  attribute SVGType property2;

  SVGReturnType methodName(SVGParamType param1, SVGParamType param2) raises(SVGException);
};
```

**Attribute documentation:**
```markdown
**DOM Interface Attributes:**

- **property1** (readonly SVGType)

  Corresponds to attribute '[attribute-name]' on the given element.

- **property2** (SVGType)

  [Description of property behavior]

  **Exceptions on setting:**
  - `NO_MODIFICATION_ALLOWED_ERR`: Raised when attribute is readonly
```

**Method documentation:**
```markdown
**DOM Interface Methods:**

- **methodName**(param1, param2)

  [Description of what the method does]

  **Parameters:**
  - `param1` (SVGParamType): [parameter description]
  - `param2` (SVGParamType): [parameter description]

  **Returns:** SVGReturnType - [return value description]

  **Exceptions:**
  - `EXCEPTION_NAME`: [when this exception is raised]
```

#### **Part 7: Cross-References**

Links to related specifications:
- Coordinate systems
- Styling rules
- Animation capabilities
- Processing model
- Conformance requirements

**Template:**
```markdown
**See also:**
- [Coordinate Systems and Transformations](coords.html)
- [Styling](styling.html)
- [Animation](animate.html)
```

### 4.2 Complete Element Documentation Example

```markdown
## 5.3 The 'rect' element

The 'rect' element defines a rectangle which is axis-aligned with the current user
coordinate system. Rounded rectangles can be achieved by setting appropriate values
for attributes 'rx' and 'ry'.

**DTD:**

```xml
<!ELEMENT rect (%descTitleMetadata;,(%animationElements;)*) >
<!ATTLIST rect
  %stdAttrs;
  %testAttrs;
  %langSpaceAttrs;
  %externalResourcesRequired;
  %styleAttrs;
  %PresentationAttributes-All;
  %graphicsElementEvents;
  transform %transformList; #IMPLIED
  x %coordinate; #IMPLIED
  y %coordinate; #IMPLIED
  width %length; #REQUIRED
  height %length; #REQUIRED
  rx %length; #IMPLIED
  ry %length; #IMPLIED
>
```

**Attributes:**

- **x** = "[&lt;coordinate&gt;](#coordinate)"

  The x-axis coordinate of the side of the rectangle which has the smaller x-axis
  coordinate value in the current user coordinate system.

  If the attribute is not specified, the effect is as if a value of "0" were specified.

  Animatable: yes

- **y** = "[&lt;coordinate&gt;](#coordinate)"

  The y-axis coordinate of the side of the rectangle which has the smaller y-axis
  coordinate value in the current user coordinate system.

  If the attribute is not specified, the effect is as if a value of "0" were specified.

  Animatable: yes

- **width** = "[&lt;length&gt;](#length)"

  The width of the rectangle.

  A negative value is an error (see [Error processing](implnotes.html#ErrorProcessing)).
  A value of zero disables rendering of the element.

  Animatable: yes

- **height** = "[&lt;length&gt;](#length)"

  The height of the rectangle.

  A negative value is an error (see [Error processing](implnotes.html#ErrorProcessing)).
  A value of zero disables rendering of the element.

  Animatable: yes

- **rx** = "[&lt;length&gt;](#length)"

  For rounded rectangles, the x-axis radius of the ellipse used to round off the
  corners of the rectangle.

  A negative value is an error (see [Error processing](implnotes.html#ErrorProcessing)).

  See the notes on 'auto' sizing for 'rx' and 'ry'.

  Animatable: yes

- **ry** = "[&lt;length&gt;](#length)"

  For rounded rectangles, the y-axis radius of the ellipse used to round off the
  corners of the rectangle.

  A negative value is an error (see [Error processing](implnotes.html#ErrorProcessing)).

  See the notes on 'auto' sizing for 'rx' and 'ry'.

  Animatable: yes

**Example rect01:**

```xml
<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 20010719//EN"
  "http://www.w3.org/TR/2001/PR-SVG-20010719/DTD/svg10.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.0">
  <desc>Example rect01 - rectangle with sharp corners</desc>

  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398"
        fill="none" stroke="blue" stroke-width="2"/>

  <rect x="400" y="100" width="400" height="200"
        fill="yellow" stroke="navy" stroke-width="10"/>
</svg>
```

[View this example as SVG (SVG-enabled browsers only)](examples/rect01.svg)

**DOM Interface:**

```idl
interface SVGRectElement : SVGElement,
                           SVGTests,
                           SVGLangSpace,
                           SVGExternalResourcesRequired,
                           SVGStylable,
                           SVGTransformable,
                           SVGEventTarget {
  readonly attribute SVGAnimatedLength x;
  readonly attribute SVGAnimatedLength y;
  readonly attribute SVGAnimatedLength width;
  readonly attribute SVGAnimatedLength height;
  readonly attribute SVGAnimatedLength rx;
  readonly attribute SVGAnimatedLength ry;
};
```

**Attributes:**

- **x** (readonly SVGAnimatedLength)
  Corresponds to attribute 'x' on the given 'rect' element.

- **y** (readonly SVGAnimatedLength)
  Corresponds to attribute 'y' on the given 'rect' element.

- **width** (readonly SVGAnimatedLength)
  Corresponds to attribute 'width' on the given 'rect' element.

- **height** (readonly SVGAnimatedLength)
  Corresponds to attribute 'height' on the given 'rect' element.

- **rx** (readonly SVGAnimatedLength)
  Corresponds to attribute 'rx' on the given 'rect' element.

- **ry** (readonly SVGAnimatedLength)
  Corresponds to attribute 'ry' on the given 'rect' element.
```

---

## 5. Processing Model Specification

### 5.1 How to Describe Algorithms and Processing Steps

The SVG specification uses **descriptive procedural language** rather than formal pseudocode.

#### **Pattern 1: Procedural Sequencing**

Use ordered steps with clear temporal hierarchy:

**Template:**
```markdown
The [operation] is performed in the following order:

1. First, [step 1 description]
2. Then, [step 2 description]
3. Finally, [step 3 description]
```

**Example:**
```markdown
The fill is painted first, then the stroke, and then the marker symbols.
```

#### **Pattern 2: Conceptual Models**

Use analogies and conceptual descriptions:

**Template:**
```markdown
[Technology] uses a "[model name]" model, where [analogy description].

This means that [implications of the model].
```

**Example:**
```markdown
SVG uses a "painters model" of rendering. Paint is applied in successive operations
to the output device such that each operation paints over some area of the output
device. When the area overlaps a previously painted area, the new paint partially
or completely obscures the old.
```

#### **Pattern 3: Mathematical References**

For precision-critical operations, reference formal mathematical definitions:

**Template:**
```markdown
[Operation] follows the mathematical rules for [mathematical concept] as described
in [reference].

Specifically: [formula or equation if needed]
```

**Example:**
```markdown
Compositing operations follow the (mathematical) rules for compositing described
under Simple Alpha Blending in [PORTERDUFF].
```

#### **Pattern 4: Conditional Logic**

Describe processing with clear conditionals:

**Template:**
```markdown
If [condition], then [action]. Otherwise, [alternative action].

When [trigger condition]:
1. [step 1]
2. [step 2]
3. [step 3]
```

**Example:**
```markdown
For groups, the processing model consists of:

1. Creating a temporary raster image
2. Rendering child elements onto the temporary raster
3. Applying filter effects (if any) to the temporary raster
4. Compositing the result into the parent canvas, taking into account any
   group-level masking and opacity settings
```

#### **Pattern 5: Implementation Flexibility**

Acknowledge that implementations may vary while results must match:

**Template:**
```markdown
A conforming implementation is not required to implement the model in exactly this way,
but the result on any supported device shall match that described by this model to
within acceptable tolerances.
```

**Example:**
```markdown
A real implementation is not required to implement the model in this way, but the
result on any device supported by the implementation shall match that described by
this model.
```

### 5.2 Complete Processing Model Example

```markdown
## 3.3 Rendering Order

Elements in SVG are positioned in three dimensions. In addition to their position
on the x and y axis of the viewport, SVG elements are also positioned on the z-axis.
The position on the z-axis defines the order in which they are painted.

Along the z-axis, elements are grouped into "stacking contexts".

**Painting Order:**

The painting order for graphics elements is:

1. The 'fill' is painted first
2. Then the 'stroke' is painted
3. Finally, the marker symbols are painted, in order along the outline of the shape

Each of these is painted in accordance with the values of the fill-opacity,
stroke-opacity, and opacity properties.

**Stacking Context:**

A new stacking context is created by:
- The root 'svg' element
- Any element which has the property 'opacity' set to a value other than 1
- Any element which has one of the properties 'filter', 'mask', or 'clip-path' set

Within a stacking context, elements are painted in document order (first element
painted first, subsequent elements painted on top).
```

---

## 6. DOM Interface Specification

### 6.1 Interface Definition Language (IDL) Format

The SVG specification uses **Web IDL** (Interface Definition Language) to formally specify DOM interfaces.

#### **Basic IDL Structure**

**Template:**
```idl
interface InterfaceName : ParentInterface {
  // Constants
  const unsigned short CONSTANT_NAME = value;

  // Readonly attributes
  readonly attribute Type attributeName;

  // Mutable attributes
  attribute Type mutableAttribute;

  // Methods
  ReturnType methodName(ParamType param1, ParamType param2) raises(ExceptionName);
};
```

#### **Exception Definitions**

**Template:**
```idl
exception ExceptionName {
  unsigned short code;
};

// Exception constants
const unsigned short EXCEPTION_TYPE_1 = 0;
const unsigned short EXCEPTION_TYPE_2 = 1;
```

**Example:**
```idl
exception SVGException {
  unsigned short code;
};

const unsigned short SVG_WRONG_TYPE_ERR = 0;
const unsigned short SVG_INVALID_VALUE_ERR = 1;
const unsigned short SVG_MATRIX_NOT_INVERTABLE = 2;
```

### 6.2 Naming Conventions

**Rule 1: camelCase for Properties and Methods**

"Property or method names start with the initial keyword in lowercase, and each
subsequent word starts with a capital letter."

- Correct: `getBBox`, `getScreenCTM`, `pathLength`
- Incorrect: `get_bbox`, `GetScreenCTM`, `path_length`

**Rule 2: UPPERCASE for Constants**

```idl
const unsigned short CONSTANT_NAME = value;
```

**Rule 3: Interface Naming**

- Element interfaces: `SVG[ElementName]Element`
- Type interfaces: `SVG[TypeName]`
- List interfaces: `SVG[TypeName]List`
- Animated interfaces: `SVGAnimated[TypeName]`

Examples:
- `SVGRectElement`
- `SVGLength`
- `SVGLengthList`
- `SVGAnimatedLength`

### 6.3 Attribute Documentation Pattern

**Template:**
```markdown
**[attributeName]** ([readonly] Type)

[Description of what this attribute represents]

Corresponds to attribute '[xml-attribute-name]' on the given '[element-name]' element.

[Additional behavior notes]

**Exceptions on setting:**
- `EXCEPTION_NAME`: [when raised]
```

**Example:**
```markdown
**width** (readonly SVGAnimatedLength)

Corresponds to attribute 'width' on the given 'rect' element.

Returns an SVGAnimatedLength object representing the current animated value of
the 'width' attribute.

**Exceptions on setting:**
- `NO_MODIFICATION_ALLOWED_ERR`: Raised on an attempt to change the value of a
  readonly attribute.
```

### 6.4 Method Documentation Pattern

**Template:**
```markdown
**methodName**(param1, param2, ...)

[Description of what the method does and when to use it]

**Parameters:**
- `param1` (Type): [parameter description]
- `param2` (Type): [parameter description]

**Returns:** ReturnType - [description of return value]

**Exceptions:**
- `EXCEPTION_NAME_1`: [condition that raises this exception]
- `EXCEPTION_NAME_2`: [condition that raises this exception]

**Example:**
```javascript
[code example demonstrating usage]
```
```

**Complete Example:**
```markdown
**getBBox**()

Returns the tight bounding box in current user space (i.e., after application of
the 'transform' attribute, if any) on the geometry of all contained graphics
elements, exclusive of stroke-width and filter effects.

**Parameters:** None

**Returns:** SVGRect - An SVGRect object that defines the bounding box.

**Exceptions:** None

**Example:**
```javascript
var rect = document.getElementById("myRect");
var bbox = rect.getBBox();
console.log("Width: " + bbox.width + ", Height: " + bbox.height);
```
```

### 6.5 Code Examples Pattern

Provide implementation examples in **multiple languages**:

#### **JavaScript/ECMAScript Example:**

```javascript
// Event listener example
myElement.addEventListener("DOMActivate", myAction1, false);

function myAction1(evt) {
  // Handle event
  var target = evt.target;
  // ...
}
```

#### **Java Example:**

```java
// Event listener example
EventTarget target = (EventTarget) myElement;
target.addEventListener("DOMActivate", new MyActionListener(), false);

class MyActionListener implements EventListener {
  public void handleEvent(Event evt) {
    // Handle event
  }
}
```

### 6.6 Complete DOM Interface Example

```markdown
## 8.7.2 Interface SVGPathElement

The SVGPathElement interface corresponds to the 'path' element.

```idl
interface SVGPathElement : SVGElement,
                           SVGTests,
                           SVGLangSpace,
                           SVGExternalResourcesRequired,
                           SVGStylable,
                           SVGTransformable,
                           SVGEventTarget {
  readonly attribute SVGAnimatedNumber pathLength;

  float getTotalLength();
  SVGPoint getPointAtLength(in float distance);
  unsigned long getPathSegAtLength(in float distance);
};
```

**Attributes:**

- **pathLength** (readonly SVGAnimatedNumber)

  Corresponds to attribute 'pathLength' on the given 'path' element.

**Methods:**

- **getTotalLength**()

  Returns the user agent's computed value for the total length of the path using
  the user agent's distance-along-a-path algorithm, as a distance in the current
  user coordinate system.

  **Parameters:** None

  **Returns:** float - The total length of the path.

  **Exceptions:** None

- **getPointAtLength**(distance)

  Returns the (x,y) coordinate in user space which is distance units along the
  path, utilizing the user agent's distance-along-a-path algorithm.

  **Parameters:**
  - `distance` (float): The distance along the path, relative to the start of
    the path, as a distance in the current user coordinate system.

  **Returns:** SVGPoint - The point at the specified distance along the path.

  **Exceptions:** None

- **getPathSegAtLength**(distance)

  Returns the index into the path segment list which is distance units along
  the path, utilizing the user agent's distance-along-a-path algorithm.

  **Parameters:**
  - `distance` (float): The distance along the path, relative to the start of
    the path, as a distance in the current user coordinate system.

  **Returns:** unsigned long - The index of the path segment, where the first
    path segment is number 0.

  **Exceptions:** None
```

---

## 7. Data Type Definitions

### 7.1 Type Definition Structure

Each data type is documented with:

1. **Syntax specification** (format rules)
2. **DOM representation** (corresponding interface)
3. **Value constraints** (min/max ranges, permitted formats)
4. **Unit identifiers** (optional or required suffixes)
5. **Examples** of valid values

### 7.2 Basic Type Pattern

**Template:**
```markdown
### [Type Name] (&lt;type-name&gt;)

[Description of what this type represents]

**Syntax:**

[BNF grammar or format description]

**DOM Representation:**

[Interface name or primitive type]

**Value Range:**

[Minimum and maximum values, or enumeration of permitted values]

**Examples:**

- `[example1]` - [explanation]
- `[example2]` - [explanation]

**Notes:**

[Any special behaviors, validation rules, or constraints]
```

### 7.3 Type Definition Examples

#### **Example 1: Integer Type**

```markdown
### Integer (&lt;integer&gt;)

An integer is a whole number without a decimal point.

**Syntax:**

An <integer> is specified as an optional sign character ('+' or '-') followed by
one or more digits '0' to '9':

```
integer ::= [+-]? [0-9]+
```

**DOM Representation:**

Mapped to a long or int in language bindings.

**Value Range:**

SVG implementations must support integer values that are at least within the range
-2,147,483,648 to 2,147,483,647 (i.e., the range of a signed 32-bit integer).

**Examples:**

- `0`
- `123`
- `-456`
- `+789`

**Notes:**

- Leading zeros are permitted but have no significance
- Negative values are indicated by a leading minus sign
- The '+' sign is optional for positive values
```

#### **Example 2: Number Type**

```markdown
### Number (&lt;number&gt;)

A number represents a real number value.

**Syntax:**

Real numbers are specified in one of two ways:

1. **Decimal notation:** An optional sign character ('+' or '-') followed by zero
   or more digits, followed by a dot (.) and one or more digits

2. **Scientific notation:** An optional sign, followed by one or more digits,
   optionally followed by a dot and zero or more digits, followed by 'e' or 'E'
   and an exponent

```
number ::= integer
         | [+-]? [0-9]* "." [0-9]+
         | [+-]? [0-9]+ "." [0-9]* ([eE] [+-]? [0-9]+)?
```

**Context-Specific Rules:**

- **CSS properties:** Only decimal notation is allowed
- **XML attributes:** Both decimal and scientific notation are allowed

**Value Range:**

A conforming SVG viewer must support at least single-precision floating point
values with a minimum range of -3.4e+38F to +3.4e+38F.

**Examples:**

- `0`
- `123.456`
- `-0.5`
- `3.14159`
- `1.23e-4` (XML attributes only)
- `6.022e23` (XML attributes only)

**DOM Representation:**

Mapped to float or double in language bindings.
```

#### **Example 3: Length Type**

```markdown
### Length (&lt;length&gt;)

A length is a distance measurement consisting of a number and an optional unit identifier.

**Syntax:**

```
length ::= number ("em" | "ex" | "px" | "in" | "cm" | "mm" | "pt" | "pc" | "%")?
```

**Unit Identifiers:**

- `em` - the 'font-size' of the relevant font
- `ex` - the 'x-height' of the relevant font
- `px` - pixels (user units)
- `in` - inches (1in = 2.54cm)
- `cm` - centimeters
- `mm` - millimeters (1mm = 0.1cm)
- `pt` - points (1pt = 1/72in)
- `pc` - picas (1pc = 12pt)
- `%` - percentage of viewport or element size (context-dependent)

**Unitless Values:**

A number without a unit identifier represents a distance in the current user
coordinate system.

**Examples:**

- `10` - 10 user units
- `2em` - twice the current font size
- `50%` - 50 percent (interpretation depends on context)
- `5cm` - 5 centimeters
- `0.5in` - half an inch

**DOM Representation:**

SVGLength interface

**Notes:**

- Negative values may be invalid depending on context (e.g., 'width', 'height')
- Percentage values are resolved relative to a reference value that depends on
  the attribute and element context
```

### 7.4 Enumeration Type Pattern

**Template:**
```markdown
### [Type Name] (enumeration)

[Description of what values in this enumeration represent]

**Valid Values:**

- **value1**: [when to use this value and what it means]
- **value2**: [when to use this value and what it means]
- **value3**: [when to use this value and what it means]

**Default Value:** [default-value]

**Examples:**

```xml
<element attribute="value1" />
<element attribute="value2" />
```

**Notes:**

[Case sensitivity, error handling, etc.]
```

**Example:**
```markdown
### Paint Values

The 'fill' and 'stroke' properties specify the paint to use for filling and
stroking a given graphics element.

**Valid Values:**

- **none**: No paint is applied
- **currentColor**: Use the value of the 'color' property
- **&lt;color&gt;**: A color value (e.g., "red", "#FF0000", "rgb(255,0,0)")
- **&lt;funciri&gt;**: A reference to a paint server element (gradient or pattern)
- **inherit**: Inherit the value from the parent element

**Default Value:**

- For 'fill': black
- For 'stroke': none

**Examples:**

```xml
<rect fill="red" stroke="blue" />
<rect fill="url(#gradient1)" stroke="none" />
<rect fill="currentColor" />
```

**Notes:**

Values are case-sensitive. Color keywords must be lowercase.
```

### 7.5 List Type Pattern

**Template:**
```markdown
### [Type Name] List

A list of [type] values.

**Syntax:**

```
list ::= value (separator value)*
separator ::= "," wsp* | wsp+
wsp ::= (#x20 | #x9 | #xD | #xA)
```

**Separators:**

Lists can be separated by:
- Commas (with optional whitespace)
- Whitespace (spaces, tabs, line feeds, carriage returns, form-feeds)
- A combination of commas and whitespace

**Examples:**

```
1, 2, 3
1 2 3
1,2,3
1, 2 3, 4
```

**DOM Representation:**

[InterfaceName]List interface providing indexed access to list members.
```

---

## 8. Conformance Requirements

### 8.1 Conformance Classes

The specification defines **distinct conformance categories** for different types of artifacts and implementations.

**Template:**
```markdown
## Conformance

This specification defines conformance criteria for the following classes:

### [Class 1 Name]

[Description of what this class includes]

A conforming [class 1] must satisfy all of the following criteria:

1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

### [Class 2 Name]

[Description of what this class includes]

A conforming [class 2] must satisfy all of the following criteria:

1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

[Continue for each conformance class]
```

### 8.2 SVG 1.0 Conformance Classes

**Example from SVG:**

```markdown
## 1. Conformance

This specification defines six conformance classes:

### 1.1 Conforming SVG Document Fragments

An SVG document fragment is a conforming SVG document fragment if it adheres to
the specification described in this document (Scalable Vector Graphics (SVG) 1.0
Specification).

### 1.2 Conforming SVG Stand-Alone Files

An SVG stand-alone file is a conforming SVG stand-alone file if:

1. It is an XML document
2. The root element is an 'svg' element
3. The root 'svg' element is in the SVG namespace
4. The SVG document fragment rooted at the 'svg' element is a conforming SVG
   document fragment

### 1.3 Conforming SVG Included Document Fragments

An SVG included document fragment is a conforming SVG included document fragment if:

1. It appears as part of a parent XML document
2. The SVG fragment is a conforming SVG document fragment

### 1.4 Conforming SVG Generators

A conforming SVG generator is a program which:

1. Always creates at least one of: conforming SVG document fragments, conforming
   SVG stand-alone files, or conforming SVG included document fragments

### 1.5 Conforming SVG Interpreters

A conforming SVG interpreter is a program which:

1. Can parse and process SVG document fragments

There are two sub-classes of conforming SVG interpreters:

**1.5.1 Conforming Static SVG Interpreters**

- Must support all features defined as required in this specification, except
  animation elements and the 'cursor' element

**1.5.2 Conforming Dynamic SVG Interpreters**

- Must support all features defined as required in this specification, including
  animation elements and the 'cursor' element

### 1.6 Conforming SVG Viewers

A conforming SVG viewer is a program which:

1. Is a conforming SVG interpreter
2. Can render SVG content to some output media

There are two sub-classes of conforming SVG viewers:

**1.6.1 Conforming Static SVG Viewers**

- Built on a conforming static SVG interpreter

**1.6.2 Conforming Dynamic SVG Viewers**

- Built on a conforming dynamic SVG interpreter

**1.6.3 Conforming High-Quality SVG Viewers**

A conforming high-quality SVG viewer is a conforming SVG viewer which:

1. Supports at least one of the following: rasterization to a device with at
   least 24 bits per pixel, rasterization to a PostScript or PDF printer,
   conversion to PostScript or PDF
2. Supports all required features with high quality
3. Uses anti-aliasing algorithms for high-quality rendering
```

### 8.3 Requirement Language

Use precise language based on **RFC 2119**:

| Keyword | Meaning | Example |
|---------|---------|---------|
| **MUST** | Absolute requirement | "The 'svg' element MUST be in the SVG namespace" |
| **MUST NOT** | Absolute prohibition | "Negative width values MUST NOT be used" |
| **REQUIRED** | Synonym for MUST | "The 'width' attribute is REQUIRED" |
| **SHALL** | Synonym for MUST | "The viewer SHALL render the element" |
| **SHALL NOT** | Synonym for MUST NOT | "The parser SHALL NOT accept malformed data" |
| **SHOULD** | Strong recommendation | "Implementations SHOULD support anti-aliasing" |
| **SHOULD NOT** | Strong recommendation against | "Authors SHOULD NOT rely on this behavior" |
| **RECOMMENDED** | Synonym for SHOULD | "Use of UTF-8 encoding is RECOMMENDED" |
| **MAY** | Optional/permitted | "Implementations MAY optimize rendering" |
| **OPTIONAL** | Synonym for MAY | "The 'title' element is OPTIONAL" |

### 8.4 Normative vs. Non-Normative Content

Clearly distinguish normative requirements from informative guidance:

**Template:**
```markdown
## [Section Name]

> **Note:** This section is [normative/informative].

[Content]
```

**Normative Example:**
```markdown
## 5. Document Structure

> **Note:** This appendix is normative.

The 'svg' element is the root element for SVG documents. All SVG content MUST
be contained within an 'svg' element.
```

**Non-Normative Example:**
```markdown
## B. Implementation Notes

> **Note:** This appendix is informative.

This section provides guidance for implementers. While following these suggestions
is highly recommended, they are not strict requirements for conformance.
```

### 8.5 Feature Requirements Table

For complex specifications, use tables to indicate feature requirements:

**Template:**

| Feature | Static | Dynamic | Notes |
|---------|--------|---------|-------|
| [Feature 1] | Required | Required | [explanation] |
| [Feature 2] | Optional | Required | [explanation] |
| [Feature 3] | N/A | Required | [explanation] |

**Example:**

| Feature | Static SVG | Dynamic SVG | Notes |
|---------|------------|-------------|-------|
| Basic shapes | Required | Required | rect, circle, ellipse, line, polyline, polygon |
| Paths | Required | Required | Full path syntax support |
| Animation | Not applicable | Required | animate, animateTransform, animateMotion, set |
| Scripting | Not applicable | Required | Event handlers and DOM manipulation |
| Interactivity | Optional | Required | Event attributes on graphics elements |

---

## 9. Status and Boilerplate

### 9.1 "Status of this Document" Section

This section appears at the beginning of the specification, before the table of contents.

**Structure:**

1. **Opening Disclaimer**
2. **Current Status and Review Period**
3. **Previous Recommendation History**
4. **Ongoing Work and Discussion**
5. **Implementation Background**
6. **Legal Disclaimers**
7. **Patents and Process**
8. **Organizational Context**

**Complete Template:**

```markdown
## Status of this Document

This section describes the status of this document at the time of its publication.
Other documents may supersede this document. A list of current W3C publications
and the latest revision of this technical report can be found in the [W3C technical
reports index](https://www.w3.org/TR/).

### Current Status

This document is a [status level] published on [date]. The W3C invites review and
feedback from all interested parties.

[For Proposed Recommendations:]
From [start date] until [end date], W3C Advisory Committee representatives are
encouraged to review this document and submit feedback through [mechanism].

The Director will announce the disposition of this document after the [duration]
waiting period following [end date].

### Previous Versions

This specification has been derived from:
- [[Previous Status](URL)] - [date]
- [[Earlier Status](URL)] - [date]

[Changes since last version description]

### Discussion and Feedback

Discussion of this specification takes place on the [working group name] mailing
list [[email address](mailto:address)]. Archives are available at [archive URL].

Issues and comments can be submitted to:
- [Issue tracker](URL)
- [Mailing list](mailto:address)

### Implementation Status

[Description of existing implementations that justify advancement to current status]

This specification has been implemented by:
- [Implementation 1]
- [Implementation 2]
- [Implementation 3]

### Legal and Process

**Publication as a [status] does not imply endorsement by the W3C Membership.**
This is still a draft document and may be updated, replaced or made obsolete by
other documents at any time. It is inappropriate to cite W3C [status documents]
as other than "work in progress."

### Patents

[Patent policy statement]

There are [no known/known] patent disclosures associated with this specification.
[Links to disclosure pages]

This document was produced by a group operating under the [W3C Patent Policy](URL).
W3C maintains a [public list of any patent disclosures](URL) made in connection
with the deliverables of the group.

### Organizational Context

This document was produced by the [Working Group Name] as part of the [W3C Activity
Name]. The goals of the [Working Group Name] are discussed in the [Working Group
Charter](URL).
```

**SVG 1.0 Example:**

```markdown
## Status of this Document

This section describes the status of this document at the time of its publication.
Other documents may supersede this document. A list of current W3C publications
and the latest revision of this technical report can be found in the W3C technical
reports index at http://www.w3.org/TR/.

This document is a Proposed Recommendation published on 19 July, 2001. The W3C
invites public review of this specification.

From that date until 16 August, 2001, W3C Advisory Committee representatives are
encouraged to review this document and submit feedback through their Advisory
Committee representative.

The Director will announce the disposition of this document after the 14-day
waiting period following 16 August, 2001.

This specification is being advanced to Proposed Recommendation based on substantial
implementation experience. A variety of SVG generators, viewers, and transcoders
have been developed both inside and outside of the SVG working group.

This is still a draft document and may be updated, replaced or made obsolete by
other documents at any time. It is inappropriate to cite W3C Proposed Recommendations
as other than "work in progress."

Publication as a Proposed Recommendation does not imply endorsement by the W3C
membership.

There are patent disclosures and license commitments associated with the SVG 1.0
specification. Please consult the SVG Patent Statements page and W3C Patent Policy
for further information.

This document has been produced as part of the W3C Graphics Activity.
```

### 9.2 W3C Copyright Notice

**Standard Copyright Template:**

```markdown
Copyright © [year(s)] [W3C®](https://www.w3.org/) ([MIT](https://www.csail.mit.edu/),
[ERCIM](https://www.ercim.eu/), [Keio](https://www.keio.ac.jp/),
[Beihang](https://ev.buaa.edu.cn/)), All Rights Reserved.

W3C [liability](https://www.w3.org/Consortium/Legal/ipr-notice#Legal_Disclaimer),
[trademark](https://www.w3.org/Consortium/Legal/ipr-notice#W3C_Trademarks), and
[permissive document license](https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document)
rules apply.
```

**SVG 1.0 Example:**

```markdown
Copyright ©1998, 1999, 2000, 2001 W3C® (MIT, INRIA, Keio), All Rights Reserved.

W3C liability, trademark, document use and software licensing rules apply.
```

### 9.3 Abstract Section

The abstract is a **concise summary** (1-3 sentences) that appears immediately after the header and before the status section.

**Template:**

```markdown
## Abstract

This specification defines [what is being specified] for [purpose]. [Additional
sentence providing key context or scope].
```

**SVG 1.0 Example:**

```markdown
## Abstract

This specification defines the features and syntax for Scalable Vector Graphics
(SVG), a language for describing two-dimensional vector and mixed vector/raster
graphics in XML.
```

**Other Examples:**

```markdown
## Abstract (CSS Example)

This specification describes the common values and units that CSS properties
accept and the syntax used for describing them in CSS property definitions.
```

```markdown
## Abstract (DOM Example)

This specification defines a platform-neutral model for events and event flow.
The specification is designed with two main goals: to design an event system
which allows registration of event listeners and describes event flow through
a tree structure, and to provide a standard module of events for user interface
control and document mutation notifications, including defined contextual information
for each of these event types.
```

### 9.4 Document Identification Header

**Template:**

```markdown
# [Full Specification Title] [Version]

W3C [Status] [Date]

**This version:**
[URL of this version]

**Latest published version:**
[URL of latest published version]

**Latest editor's draft:**
[URL of editor's draft]

**Previous version:**
[URL of previous version] (or "none" for first publications)

**Editors:**
[Editor Name] ([Affiliation]) &lt;[email]&gt;
[Editor Name 2] ([Affiliation]) &lt;[email]&gt;

**Authors:**
[Author Name] ([Affiliation])
[Author Name 2] ([Affiliation])

**Feedback:**
[Preferred mechanism for feedback - email, GitHub, etc.]
```

**SVG 1.0 Example:**

```markdown
# Scalable Vector Graphics (SVG) 1.0 Specification

W3C Proposed Recommendation 19 July, 2001

**This version:**
http://www.w3.org/TR/2001/PR-SVG-20010719/

**Latest version:**
http://www.w3.org/TR/SVG/

**Previous version:**
http://www.w3.org/TR/2001/CR-SVG-20010319/

**Editor:**
Jon Ferraiolo, Adobe Systems &lt;jon.ferraiolo@adobe.com&gt;
```

---

## 10. Best Practices Summary

### 10.1 Documentation Principles

1. **Clarity and Precision**
   - Use clear, unambiguous language
   - Define all technical terms in the glossary
   - Provide examples for complex concepts

2. **Consistency**
   - Follow the same structure for all similar elements
   - Use consistent terminology throughout
   - Apply formatting conventions uniformly

3. **Completeness**
   - Document all attributes and their effects
   - Specify default values explicitly
   - Include error handling and edge cases

4. **Cross-Referencing**
   - Link related sections extensively
   - Reference formal specifications (RFC 2119, DOM, CSS, etc.)
   - Provide navigational aids (TOC, index, breadcrumbs)

5. **Implementation Guidance**
   - Distinguish normative requirements from informative guidance
   - Provide DOM interfaces for programmatic access
   - Include practical code examples

6. **Accessibility**
   - Use semantic HTML markup
   - Provide text alternatives for diagrams
   - Ensure examples are accessible

### 10.2 Structural Checklist

- [ ] Document header with version, status, editors
- [ ] Abstract (1-3 sentences)
- [ ] Status of this Document section
- [ ] Copyright notice
- [ ] Table of Contents
- [ ] Introduction chapter with:
  - [ ] About section
  - [ ] MIME type and file extensions
  - [ ] Namespace and identifiers
  - [ ] W3C compatibility
  - [ ] Terminology (RFC 2119 keywords)
  - [ ] Definitions (alphabetical glossary)
- [ ] Foundational chapters (concepts, rendering model, basic types)
- [ ] Feature chapters following the element documentation template
- [ ] Processing model descriptions
- [ ] DOM interface specifications
- [ ] Conformance chapter
- [ ] Appendices (DTD, bindings, indexes)

### 10.3 Element Documentation Checklist

For each element:
- [ ] Introductory prose explaining purpose
- [ ] DTD formal definition
- [ ] Attribute declarations (ATTLIST)
- [ ] Attribute definitions (with data types, defaults, animatability)
- [ ] Practical examples with code
- [ ] DOM interface (IDL definition)
- [ ] DOM attribute documentation
- [ ] DOM method documentation
- [ ] Cross-references to related sections

### 10.4 Writing Style Guidelines

**Use:**
- Active voice ("The viewer renders..." not "The element is rendered...")
- Present tense ("This attribute specifies..." not "This attribute will specify...")
- Formal technical language
- RFC 2119 keywords (MUST, SHOULD, MAY) for normative requirements
- Descriptive but concise prose

**Avoid:**
- Marketing language or hype
- Vague or ambiguous statements
- Implementation-specific details (unless in informative notes)
- Unnecessary jargon without definitions
- Overly long paragraphs or run-on sentences

### 10.5 Example Quality Standards

Every example should:
- [ ] Be complete and self-contained
- [ ] Use valid syntax
- [ ] Include necessary namespace declarations
- [ ] Demonstrate best practices
- [ ] Be accompanied by explanatory text
- [ ] Show actual rendered output or link to live example
- [ ] Cover common use cases
- [ ] Illustrate edge cases where relevant

### 10.6 Conformance Documentation Standards

- [ ] Define all conformance classes clearly
- [ ] Specify requirements for each class using RFC 2119 keywords
- [ ] Provide rationale for requirements where helpful
- [ ] Distinguish mandatory from optional features
- [ ] Include feature requirement tables if applicable
- [ ] Address error handling and recovery
- [ ] Specify validation criteria

---

## Appendix A: Quick Reference Templates

### A.1 Element Definition Quick Template

```markdown
## [Section Number] The '[element-name]' Element

[Purpose and use case description]

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
interface SVGElementName : SVGElement {
  readonly attribute SVGType property;
};
```
```

### A.2 Data Type Definition Quick Template

```markdown
### [Type Name] (&lt;type-name&gt;)

[Description]

**Syntax:** [BNF or format description]

**Value Range:** [min to max or enumeration]

**Examples:** `value1`, `value2`

**DOM Representation:** [interface name]
```

### A.3 Processing Model Quick Template

```markdown
## [Operation Name]

[Description of what this operation does]

**Processing Steps:**

1. [Step 1]
2. [Step 2]
3. [Step 3]

**Implementation Note:** [Flexibility statement if applicable]
```

---

## Appendix B: SVG 1.0 Specification Links

### B.1 Primary Resources

- **SVG 1.0 Specification:** https://www.w3.org/TR/2001/PR-SVG-20010719/
- **Introduction:** https://www.w3.org/TR/2001/PR-SVG-20010719/intro.html
- **Document Structure:** https://www.w3.org/TR/2001/PR-SVG-20010719/struct.html
- **Rendering Model:** https://www.w3.org/TR/2001/PR-SVG-20010719/render.html
- **Basic Data Types:** https://www.w3.org/TR/2001/PR-SVG-20010719/types.html
- **Paths:** https://www.w3.org/TR/2001/PR-SVG-20010719/paths.html
- **DOM Interface:** https://www.w3.org/TR/2001/PR-SVG-20010719/svgdom.html
- **Conformance:** https://www.w3.org/TR/2001/PR-SVG-20010719/conform.html

### B.2 Referenced Standards

- **RFC 2119 (Key words):** https://www.w3.org/TR/2001/PR-SVG-20010719/refs.html#ref-RFC2119
- **XML 1.0:** https://www.w3.org/TR/REC-xml
- **Namespaces in XML:** https://www.w3.org/TR/REC-xml-names/
- **DOM Level 2:** https://www.w3.org/TR/DOM-Level-2-Core/
- **CSS2:** https://www.w3.org/TR/REC-CSS2/

---

## Appendix C: Applying These Patterns to FBF.SVG

### C.1 FBF.SVG Specification Structure

Based on these patterns, the FBF.SVG specification should include:

1. **Header and Metadata**
   - Title: "Frame-by-Frame SVG (FBF.SVG) Specification"
   - Version number (e.g., 1.0)
   - Status (Draft, Candidate Recommendation, etc.)
   - Editors and authors
   - Date of publication

2. **Abstract**
   - 1-2 sentence description of FBF.SVG format
   - Purpose: frame-by-frame animation format

3. **Status of this Document**
   - Current status and review period
   - Links to issue tracker and mailing list
   - Implementation status

4. **Introduction**
   - About FBF.SVG
   - MIME type: `image/fbf-svg+xml`
   - File extension: `.fbf.svg` or `.fbfsvg`
   - Namespace: TBD
   - Compatibility with SVG 1.1/2.0
   - Terminology and RFC 2119 keywords
   - Definitions (timeline, frame, keyframe, interpolation, etc.)

5. **Core Concepts**
   - FBF.SVG rendering model
   - Timeline and frame model
   - Layer system
   - Collision detection framework

6. **Document Structure**
   - Root element (`<fbf:animation>` or similar)
   - Metadata elements
   - Timeline structure
   - Frame definitions
   - Layer organization

7. **Timeline and Frame Model**
   - Frame numbering and timing
   - Keyframes vs. tweened frames
   - Frame attributes and properties

8. **Layers and Composition**
   - Layer types (static, animated, collision)
   - Layer ordering and z-index
   - Visibility and opacity

9. **Collision Detection**
   - Collision layer specification
   - Detection algorithms
   - Collision response metadata

10. **Coordinate Systems and Transformations**
    - Canvas coordinate system
    - Frame-specific transformations
    - Layer transformations

11. **Styling and Presentation**
    - CSS compatibility
    - Frame-specific styling
    - Animation properties

12. **Interactivity and Scripting**
    - Event model
    - DOM interface for FBF.SVG
    - JavaScript API

13. **Metadata and Annotations**
    - Frame metadata
    - Collision metadata
    - Authoring metadata

14. **Conformance**
    - Conformance classes:
      - Conforming FBF.SVG documents
      - Conforming FBF.SVG generators
      - Conforming FBF.SVG viewers (static and dynamic)
      - Conforming FBF.SVG editors

15. **Appendices**
    - XML Schema or DTD
    - DOM IDL definitions
    - Example documents
    - Migration guide from SVG
    - Implementation notes
    - Index of elements, attributes, properties

### C.2 Priority Elements to Document

Focus initial documentation efforts on:

1. **`<fbf:animation>` root element**
2. **`<fbf:timeline>` and `<fbf:frame>` elements**
3. **`<fbf:layer>` element**
4. **`<fbf:collision-layer>` element**
5. **Frame metadata elements**
6. **Core data types** (frame-time, layer-id, collision-type, etc.)

### C.3 Documentation Tools and Workflow

Consider using:

- **ReSpec** (W3C documentation framework): https://respec.org/
- **Bikeshed** (specification preprocessor): https://tabatkins.github.io/bikeshed/
- **Markdown + pandoc** for initial drafting
- **GitHub Pages** for hosting draft specifications
- **Issue tracking** for feedback and revisions

---

## Conclusion

This document provides a comprehensive set of patterns, templates, and conventions extracted from the SVG 1.0 W3C specification. By following these patterns, the FBF.SVG specification will maintain consistency with established W3C practices, improving clarity, usability, and adoption potential.

**Key Takeaways:**

1. **Structure matters:** Follow a clear, logical progression from introduction through concepts to features
2. **Consistency is critical:** Use the same format for all similar elements
3. **Be complete:** Document every attribute, method, and behavior
4. **Provide examples:** Include practical, working examples throughout
5. **Define conformance:** Clearly specify what it means to be conformant
6. **Cross-reference extensively:** Link related concepts and sections
7. **Distinguish normative from informative:** Use RFC 2119 keywords appropriately
8. **Support multiple audiences:** Serve both implementers and content authors

Following these guidelines will result in a professional, clear, and implementable specification for FBF.SVG.
