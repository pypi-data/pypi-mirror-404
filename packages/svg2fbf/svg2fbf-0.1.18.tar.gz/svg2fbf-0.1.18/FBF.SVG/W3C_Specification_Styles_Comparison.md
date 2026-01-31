# W3C Specification Styles: Comparative Analysis for FBF.SVG

**Date:** 2025-11-10
**Purpose:** Compare different W3C specification approaches to determine best fit for FBF.SVG streaming documentation

---

## Overview

The W3C has evolved different documentation styles over its 30-year history. This document compares three major approaches using actual specifications as examples, then recommends the optimal style for FBF.SVG.

---

## Comparison Matrix

| Aspect | **REX Style** (2006) | **SVG 2 Style** (Modern) | **Fetch API Style** (WHATWG) |
|--------|----------------------|--------------------------|------------------------------|
| **Requirements Format** | MUST/SHOULD without IDs | Normative statements with sections | Algorithmic steps with specific outcomes |
| **Use Cases** | ❌ Absent | ✅ In separate section | ✅ Implicit in examples |
| **Examples** | ❌ None | ✅ Extensive inline | ✅ Live demos + code |
| **Security** | ❌ Not addressed | ✅ Dedicated section | ✅ Integrated throughout |
| **Test Criteria** | ❌ Not specified | ⚠️ Implied only | ✅ Explicit assertions |
| **Terminology** | ⚠️ Minimal | ✅ Comprehensive glossary | ✅ Definitions inline |
| **Implementer Guidance** | ❌ Abstract only | ⚠️ Limited notes | ✅ Detailed algorithms |
| **Versioning** | ❌ Not specified | ✅ Explicit compatibility | ✅ Living standard model |
| **Conformance Classes** | ❌ Not defined | ✅ Multiple profiles | ✅ Single conformance |
| **Readability** | ⭐⭐⭐ (Very simple) | ⭐⭐ (Dense) | ⭐⭐⭐⭐ (Clear) |
| **Completeness** | ⭐ (Minimal) | ⭐⭐⭐⭐ (Comprehensive) | ⭐⭐⭐⭐⭐ (Exhaustive) |
| **Implementability** | ⭐ (Vague) | ⭐⭐⭐ (Good) | ⭐⭐⭐⭐⭐ (Excellent) |

**Legend:** ✅ Present & Good | ⚠️ Present but Limited | ❌ Absent | ⭐ Star Rating (1-5)

---

## Style 1: REX Requirements Style (2006)

**Example Specification:** [Remote Events for XML Requirements](https://www.w3.org/TR/rex-reqs/)

### Characteristics

#### ✅ Strengths
1. **Extreme simplicity** - Easy to read and understand
2. **Clear categorical organization** (Functional, Format, Ecosystem)
3. **Consistent RFC 2119 usage** (MUST/SHOULD/MAY)
4. **Technology-agnostic** - Focuses on capabilities, not implementation

#### ❌ Weaknesses
1. **No use cases** - Requirements feel disconnected from real needs
2. **No examples** - Implementers must guess correct interpretation
3. **No security** - Critical for network protocols
4. **No test criteria** - Can't verify conformance objectively
5. **Too abstract** - Lacks actionable implementation guidance

### Sample Format

```markdown
## Functional Requirements

REX MUST permit a document tree to be modified, locally or remotely

REX MUST rely on an event-based processing model

REX MUST support addressing nodes using XPath
```

**Analysis:** Good for early-stage requirements gathering, but insufficient for implementation specification.

---

## Style 2: SVG 2 Specification Style (Modern W3C)

**Example Specification:** [SVG 2.0](https://www.w3.org/TR/SVG2/)

### Characteristics

#### ✅ Strengths
1. **Comprehensive coverage** - All aspects detailed
2. **Extensive examples** - Nearly every feature has code samples
3. **Clear terminology** - Dedicated definitions section
4. **Security section** - Addresses common threats
5. **Rendering details** - Precise visual outcomes specified
6. **IDL definitions** - JavaScript API formally defined

#### ⚠️ Mixed Aspects
1. **Very long** - 700+ pages can be overwhelming
2. **Multiple conformance classes** - Complex (SVG Full, SVG Tiny, etc.)
3. **Backward compatibility** - Lots of deprecated feature documentation

#### ❌ Weaknesses
1. **Dense prose** - Can be hard to extract key requirements
2. **Test criteria implicit** - Not always clear how to verify conformance
3. **Limited implementation algorithms** - Describes "what" not always "how"

### Sample Format

```markdown
## 4.7 The 'circle' element

A 'circle' element defines a circle based on a center point and a radius.

### 4.7.1 Attributes

**cx** = <length>
The x-axis coordinate of the center of the circle.
Lacuna value: 0

**cy** = <length>
The y-axis coordinate of the center of the circle.
Lacuna value: 0

**r** = <length>
The radius of the circle. A negative value is invalid and must be ignored.
A computed value of zero disables rendering of the element.

### 4.7.2 DOM Interface

```webidl
interface SVGCircleElement : SVGGeometryElement {
  readonly attribute SVGAnimatedLength cx;
  readonly attribute SVGAnimatedLength cy;
  readonly attribute SVGAnimatedLength r;
};
```

### 4.7.3 Examples

```xml
<circle cx="50" cy="50" r="40" fill="red" stroke="black" stroke-width="2"/>
```

**Rendering:** A red circle centered at (50, 50) with radius 40, outlined in black.

### 4.7.4 Notes

The rendering of a circle is equivalent to a path with four cubic Bézier curves...
```

**Analysis:** Excellent for mature, complex specifications with multiple implementations.

---

## Style 3: WHATWG Fetch API Style (Living Standard)

**Example Specification:** [Fetch Standard](https://fetch.spec.whatwg.org/)

### Characteristics

#### ✅ Strengths
1. **Algorithmic precision** - Every behavior specified as exact steps
2. **Excellent testability** - Each step is verifiable
3. **Security integrated** - Security checks in algorithms, not separate section
4. **Clear error handling** - Every error case explicitly handled
5. **Living standard** - Continuously updated (no versioning hell)
6. **Implementation-focused** - Written for developers building engines
7. **Cross-referenced** - Links to other specs extensively

#### ⚠️ Mixed Aspects
1. **Very detailed** - Can be overwhelming for casual readers
2. **Assumes background** - Expects familiarity with web platform primitives

#### ❌ Weaknesses
1. **No high-level overview** - Jumps straight into details
2. **Limited rationale** - Doesn't always explain "why" behind decisions
3. **Spec-speak heavy** - Uses formal language that can be off-putting

### Sample Format

```markdown
## 4.3 HTTP fetch

To perform an HTTP fetch using request with an optional response tainting, run these steps:

1. Let response be null.

2. Let actualResponse be null.

3. Let timingInfo be a new fetch timing info whose start time and
   post-redirect start time are the coarsened shared current time given
   request's client's cross-origin isolated capability.

4. If request's service-workers mode is "all", then:

   1. Let requestForAdditionOfRangeHeader be a clone of request.

   2. If request's body is non-null, then set requestForAdditionOfRangeHeader's
      body to the body of request.

   3. Append (`Range`, `bytes=0-`) to requestForAdditionOfRangeHeader's
      header list.

   4. Set response to the result of performing main fetch using
      requestForAdditionOfRangeHeader.

5. Otherwise, set response to the result of performing HTTP-network-or-cache
   fetch using request.

6. If response's status is 304, then:

   1. Set response to the result of performing HTTP-redirect fetch using
      request and response.

7. Return response.
```

**Analysis:** Best for specifications requiring precise interoperability between implementations.

---

## Hybrid Recommendation for FBF.SVG

### Recommended Approach: **SVG 2 Style + WHATWG Algorithmic Precision**

Combine the best aspects of each:

```
┌─────────────────────────────────────────┐
│  Document Structure: SVG 2 Style        │
│  - Comprehensive sections               │
│  - Extensive examples                   │
│  - Clear terminology                    │
│  - Dedicated security section           │
└─────────────────────────────────────────┘
              +
┌─────────────────────────────────────────┐
│  Critical Algorithms: WHATWG Style      │
│  - Streaming protocol steps             │
│  - Error handling procedures            │
│  - Security checks                      │
│  - State machine transitions            │
└─────────────────────────────────────────┘
              +
┌─────────────────────────────────────────┐
│  High-Level Requirements: REX Style     │
│  - Categorical organization             │
│  - RFC 2119 conformance language        │
│  - Technology independence              │
└─────────────────────────────────────────┘
```

### Practical Application

#### 1. Introduction & Overview (SVG 2 Style)

```markdown
# FBF.SVG Streaming Specification

## 1. Introduction

This specification defines a streaming protocol for progressive transmission
and rendering of Frame-by-Frame SVG (FBF.SVG) animations.

### 1.1 Background

[Context about why streaming matters for FBF.SVG]

### 1.2 Goals

- Enable playback before complete download
- Minimize memory consumption
- Support adaptive quality streaming
- Ensure security against resource exhaustion

### 1.3 Non-Goals

- Real-time video streaming (out of scope)
- DRM or encryption (handled by transport layer)

## 2. Terminology

**frame**
A single discrete image in a frame-by-frame animation sequence.

**chunk**
A self-contained unit of data transmitted independently.

[More definitions...]
```

#### 2. Use Cases (SVG 2 Style)

```markdown
## 3. Use Cases

### 3.1 Progressive Playback

**Actor:** Web application
**Goal:** Begin animation playback before full download

[Detailed scenario...]
```

#### 3. Requirements (REX Style + Enhancement)

```markdown
## 4. Requirements

### 4.1 Functional Requirements

**FBF-STREAM-001** [MUST] **Progressive Rendering**
Implementations MUST support progressive rendering where initial frames
display before the complete document is received.

**Rationale:** Improves perceived performance 3-5x in user studies.
**Use Cases:** UC-STREAM-001, UC-STREAM-003
**Test:** TC-STREAM-001

**FBF-STREAM-002** [MUST] **Chunk Independence**
Each transmitted chunk MUST be processable without requiring subsequent chunks.

**Rationale:** Supports packet-based protocols and enables parallelization.
**Use Cases:** UC-STREAM-001
**Test:** TC-STREAM-002
```

#### 4. Protocol Algorithms (WHATWG Style)

```markdown
## 5. Streaming Protocol

### 5.1 Processing a Chunk

To **process a chunk** given _chunkData_ and _streamState_, run these steps:

1. If _streamState_'s **streamActive** flag is false, return failure.

2. Let _parsedChunk_ be the result of parsing _chunkData_ as FBF-XML.

3. If _parsedChunk_ is failure:
   1. Set _streamState_'s **errorOccurred** flag to true.
   2. Fire an event named "error" at _streamState_'s target.
   3. Return failure.

4. If _parsedChunk_'s type is "HEADER":
   1. If _streamState_'s **headerReceived** flag is true:
      - Return failure. (Multiple headers invalid)
   2. Set _streamState_'s **frameCount** to _parsedChunk_'s frameCount attribute.
   3. Set _streamState_'s **fps** to _parsedChunk_'s fps attribute.
   4. Set _streamState_'s **headerReceived** flag to true.

5. If _parsedChunk_'s type is "FRAMES":
   1. For each _frame_ in _parsedChunk_'s frames:
      1. If _frame_'s id ≥ _streamState_'s frameCount:
         - Terminate the stream. (Security: prevent exhaustion)
      2. If _streamState_'s **memoryUsage** > 500 MB:
         - Flush oldest buffered frames.
      3. Append _frame_ to _streamState_'s frameBuffer.

6. Return success.
```

#### 5. Security (SVG 2 Style + WHATWG Integration)

```markdown
## 6. Security Considerations

### 6.1 Resource Exhaustion

**Threat:** Malicious server sends infinite frames.

**Mitigation:** Implemented in step 5.1.5.1 of "Processing a Chunk" algorithm.

**User Impact:** Prevents browser crashes, protects user data.

**Example Attack:**
```xml
<fbf:svg frameCount="100">
  <!-- Declares 100 frames -->
</fbf:svg>
<!-- But server sends 10,000 frames -->
```

**Defense:** Algorithm terminates stream at frame 100 (step 5.1.5.1).
```

#### 6. Examples (SVG 2 Style)

```markdown
## 7. Examples

### 7.1 Basic Progressive Streaming

This example demonstrates a minimal progressive streaming scenario.

**Server (Python):**
```python
@app.route('/animation.fbf.svg')
def stream_animation():
    def generate():
        # Send header chunk
        yield '<fbf:svg frameCount="100" fps="30">\n'

        # Send frames in chunks of 10
        for i in range(0, 100, 10):
            chunk = generate_frame_chunk(i, i+10)
            yield chunk
            time.sleep(0.1)  # Simulate network delay

        yield '</fbf:svg>'

    return Response(generate(), mimetype='application/fbf-svg+stream')
```

**Client (JavaScript):**
```javascript
const response = await fetch('/animation.fbf.svg');
const reader = response.body.getReader();

// Process chunks as they arrive
while (true) {
    const {done, value} = await reader.read();
    if (done) break;

    processChunk(value);  // Uses algorithm from Section 5.1
}
```

**Visual Result:**
[Diagram showing frames appearing progressively]
```

#### 7. Conformance (SVG 2 + WHATWG Style)

```markdown
## 8. Conformance

### 8.1 Conformance Classes

This specification defines two conformance classes:

**FBF Streaming Client:**
A user agent that fetches and renders FBF.SVG streams.
MUST implement: Sections 4 (Requirements), 5 (Protocol), 6 (Security)

**FBF Streaming Server:**
An HTTP server that transmits FBF.SVG content in chunks.
MUST implement: Sections 4.2 (Format Requirements), 5.3 (Chunk Encoding)

### 8.2 Conformance Criteria

A **FBF Streaming Client** is conformant if:

1. It correctly implements the algorithm in Section 5.1 (Processing a Chunk).
   - **Test:** TC-STREAM-001 through TC-STREAM-015

2. It enforces security mitigations in Section 6.
   - **Test:** TC-SEC-001 through TC-SEC-005

3. It handles all required MIME types.
   - **Test:** TC-MIME-001

[More criteria...]

### 8.3 Test Suite

The official conformance test suite is available at:
https://github.com/fbf-svg/conformance-tests

**Running Tests:**
```bash
npm install @fbf-svg/test-suite
npm test
```

**Coverage Requirements:**
- Statement coverage ≥ 95%
- Branch coverage ≥ 90%
```

---

## Side-by-Side Example Comparison

### Requirement: Progressive Rendering

#### REX Style (Minimal)
```markdown
MUST permit progressive rendering of content before complete transmission
```

#### SVG 2 Style (Descriptive)
```markdown
## 4.2 Progressive Rendering

User agents must support progressive rendering, where initial frames of an
animation can be displayed before the entire document has been received from
the network. This improves perceived performance and enables streaming use cases.

When a user agent receives an FBF.SVG document via HTTP, it should begin parsing
and rendering frames as soon as the header and first frame chunk are available,
without waiting for subsequent chunks.

**Example:**
```xml
<!-- This should render frame 0 immediately, even if frames 1-99 not yet received -->
<fbf:svg frameCount="100">
  <fbf:frame id="0">...</fbf:frame>
</fbf:svg>
```
```

#### WHATWG Style (Algorithmic)
```markdown
## 4.2 Progressive Rendering

To **progressively render** an FBF.SVG document, the user agent must run these steps:

1. Let _buffer_ be an empty list.
2. Let _currentFrame_ be 0.
3. While the stream is active:
   1. Wait until _buffer_ contains at least _currentFrame_ + 1 frames.
   2. Let _frame_ be _buffer_[_currentFrame_].
   3. Render _frame_ to the canvas.
   4. Increment _currentFrame_.
   5. Wait for 1000 / _fps_ milliseconds.
4. When the stream completes, continue rendering remaining buffered frames.

**Note:** This algorithm enables playback to begin before all frames are received,
satisfying the progressive rendering requirement.
```

#### **Recommended Hybrid for FBF.SVG**
```markdown
## 4.2 Progressive Rendering

**FBF-STREAM-001** [MUST]
User agents MUST support progressive rendering where initial frames display
before the complete document is received.

**Rationale:** Improves perceived load time by 3-5x based on user studies.
**Use Cases:** UC-STREAM-001 (Progressive Playback), UC-UX-005 (Immediate Feedback)

### 4.2.1 Algorithm

To **progressively render** an FBF.SVG stream, run these steps:

1. Let _buffer_ be an empty frame buffer.
2. Let _currentFrame_ be 0.
3. While the stream is active:
   1. Wait until _buffer_ contains frame _currentFrame_.
   2. Render _buffer_[_currentFrame_] to the canvas.
   3. Increment _currentFrame_.
   4. Wait for 1000 / _fps_ milliseconds.

**Security Check:** If _currentFrame_ ≥ declared _frameCount_, terminate stream
to prevent resource exhaustion (See Section 6.1).

### 4.2.2 Example

**Scenario:** 100-frame animation, frames arrive in chunks of 10.

```javascript
// Client code
const renderer = new FBFRenderer();
const stream = await fetch('/animation.fbf.svg');

for await (const chunk of stream) {
  renderer.addFrames(parseChunk(chunk));  // Adds to buffer

  if (!renderer.isPlaying && renderer.frameCount >= 10) {
    renderer.play();  // Start as soon as buffer sufficient
  }
}
```

**Visual Result:**
```
T=0s   : Header + frames 0-9 arrive → playback starts
T=0.3s : Frames 10-19 arrive → playback continues
T=0.6s : Frames 20-29 arrive → playback continues
...
```

### 4.2.3 Conformance

**Test TC-STREAM-001:**
- Send 50-frame FBF.SVG in 5 chunks of 10 frames each
- Delay 500ms between chunks
- Verify frame 0 renders before frame 50 received
- **Pass Criteria:** First frame visible within 2 seconds of request start

---

## Decision Matrix for FBF.SVG

Choose documentation style based on:

| If your specification... | Use Style | Rationale |
|-------------------------|-----------|-----------|
| Is in early requirements phase | **REX Style** | Simple, forces focus on "what" not "how" |
| Needs multiple implementations to interoperate | **WHATWG Style** | Algorithmic precision prevents divergence |
| Covers complex rendering/visual behavior | **SVG 2 Style** | Examples critical for visual correctness |
| Involves security-critical protocols | **WHATWG Style** | Security checks integrated into algorithms |
| Targets general web developers | **SVG 2 Style** | Readable prose with good examples |
| Targets browser engine developers | **WHATWG Style** | Implementation-ready algorithms |
| Is mature with many implementations | **SVG 2 Style** | Comprehensive coverage of edge cases |

**For FBF.SVG Streaming:**
- ✅ **Hybrid: SVG 2 + WHATWG**
  - Use SVG 2 style for document structure, examples, terminology
  - Use WHATWG style for streaming algorithms, state machines, error handling
  - Use REX style for high-level requirement organization

---

## Practical Next Steps

### Phase 1: Requirements (REX Style)
- [ ] List functional requirements with MUST/SHOULD/MAY
- [ ] Organize into categories (Functional, Format, Ecosystem, Security)
- [ ] Keep each requirement to 1-2 sentences
- [ ] Don't worry about implementation details yet

### Phase 2: Use Cases & Examples (SVG 2 Style)
- [ ] Document 5-10 concrete streaming scenarios
- [ ] Write code examples for each use case (server + client)
- [ ] Include visual diagrams of streaming flows
- [ ] Show error cases and recovery

### Phase 3: Algorithms (WHATWG Style)
- [ ] Identify critical algorithms (chunk processing, state management, etc.)
- [ ] Write step-by-step procedures using numbered steps
- [ ] Include all error handling and security checks
- [ ] Make every step testable

### Phase 4: Security (Hybrid)
- [ ] Identify threats (using prose like SVG 2)
- [ ] Specify mitigations (using algorithms like WHATWG)
- [ ] Link mitigations back to algorithm steps
- [ ] Provide attack examples

### Phase 5: Conformance (Hybrid)
- [ ] Define conformance classes (SVG 2 style)
- [ ] Write testable criteria for each requirement (WHATWG style)
- [ ] Create actual conformance tests
- [ ] Measure coverage

---

## Templates Mapped to Styles

| Template (from previous doc) | Recommended Style | Rationale |
|------------------------------|-------------------|-----------|
| Use Case Template | **SVG 2** | Narrative format with examples |
| Requirement Template | **Hybrid** | REX structure + testability |
| Security Template | **Hybrid** | SVG 2 prose + WHATWG algorithms |
| Protocol Message Template | **WHATWG** | Precision critical for interop |
| Example Template | **SVG 2** | Code samples with explanations |
| Test Case Template | **WHATWG** | Step-by-step verification |
| Benchmark Template | **SVG 2** | Results presentation |

---

## Resources for Each Style

### REX Style Resources
- [REX Requirements](https://www.w3.org/TR/rex-reqs/)
- [RFC 2119: Conformance Keywords](https://www.rfc-editor.org/rfc/rfc2119)

### SVG 2 Style Resources
- [SVG 2 Specification](https://www.w3.org/TR/SVG2/)
- [W3C Manual of Style](https://www.w3.org/2001/06/manual/)
- [WebIDL Specification](https://webidl.spec.whatwg.org/) (for DOM interfaces)

### WHATWG Style Resources
- [Fetch Standard](https://fetch.spec.whatwg.org/)
- [Streams Standard](https://streams.spec.whatwg.org/)
- [Writing Good Specifications](https://github.com/WHATWG/spec-factory/blob/main/docs/writing-good-specifications.md)
- [Bikeshed Documentation](https://speced.github.io/bikeshed/) (spec generation tool)

### General Resources
- [W3C Process Document](https://www.w3.org/Consortium/Process/)
- [TAG Design Principles](https://www.w3.org/TR/design-principles/)
- [Security & Privacy Questionnaire](https://www.w3.org/TR/security-privacy-questionnaire/)

---

## Conclusion

**For FBF.SVG Streaming, adopt a hybrid approach:**

1. **High-level structure:** SVG 2 style (sections, examples, prose)
2. **Critical algorithms:** WHATWG style (numbered steps, precision)
3. **Requirements organization:** REX style (categorical, RFC 2119)

This combination provides:
- ✅ **Readability** for general developers (SVG 2)
- ✅ **Implementability** for engine developers (WHATWG)
- ✅ **Clarity** for requirements tracking (REX)

Start with the templates provided in the companion document, applying the appropriate style for each section based on this comparison.

---

**Document Version:** 1.0
**Created:** 2025-11-10
**For Project:** FBF.SVG Streaming Protocol
**Author:** Claude (Sonnet 4.5)
