# REX Requirements Analysis for FBF.SVG Streaming Documentation

**Analysis Date:** 2025-11-10
**Source Document:** [W3C Remote Events for XML (REX) Requirements](https://www.w3.org/TR/rex-reqs/)
**Purpose:** Extract documentation patterns and best practices for FBF.SVG streaming capabilities

---

## Executive Summary

The REX Requirements document (W3C Working Group Note, 02 February 2006) provides a minimalist, principle-based approach to documenting streaming/progressive transmission requirements for XML-based content. While lightweight in structure, it offers valuable insights for how FBF.SVG's streaming capabilities should be documented.

**Key Takeaway:** REX prioritizes *architectural integration* and *capability statements* over detailed protocol specifications, making it suitable for requirements documentation but insufficient as an implementation guide.

---

## 1. Requirements Format Analysis

### Structure Used by REX

REX employs a **three-tier categorical structure** without alphanumeric requirement identifiers:

```
1. Functional Requirements (5 requirements)
   ├─ Core capabilities the technology must provide
   └─ "WHAT" the system does

2. Format Requirements (5 requirements)
   ├─ Structural and syntactic constraints
   └─ "HOW" the system is expressed

3. Ecosystem Requirements (6 requirements)
   ├─ Integration with broader standards
   └─ "WHERE" the system fits in the web architecture
```

### Conformance Language

Requirements use **RFC 2119** keywords with strict consistency:

- **MUST** (15 instances) - Mandatory requirements
- **SHOULD** (1 instance) - Recommended but optional
- **MAY** (0 instances) - Not used in this document

### Example Format

```
MUST permit a document tree to be modified, locally or remotely
```

No additional metadata (priority, rationale, test criteria) accompanies each requirement.

### **Recommendation for FBF.SVG:**

✅ **Adopt a hybrid approach:**

```
FBF-STREAM-001 [MUST] Support progressive rendering of frame-by-frame content
    Category: Functional
    Priority: P0 (Critical)
    Rationale: Enables streaming playback before full download completes
    Test Criteria: Frame N renders before frame N+1 is fully received
    Related: FBF-PERF-003, FBF-NET-012
```

This combines REX's categorical clarity with explicit traceability and testability that REX lacks.

---

## 2. Use Cases Documentation

### What REX Does

**No explicit use cases are documented.** The abstract mentions general purposes:

> "transmission or synchronisation of remote documents"

But no discrete scenarios like:
- "User starts playing animation before download completes"
- "Server pushes updated frames to active clients"
- "Client recovers from network interruption mid-stream"

### Impact on Requirements

Without use cases, requirements feel abstract and disconnected from real-world problems.

### **Recommendation for FBF.SVG:**

❌ **Do NOT follow REX's omission of use cases.**

✅ **Document explicit streaming use cases:**

```markdown
## Use Case: Progressive Animation Playback

**Actor:** Web application displaying FBF.SVG animation
**Goal:** Begin playback before full file download
**Preconditions:** Browser supports FBF.SVG streaming
**Flow:**
1. Browser requests FBF.SVG file via HTTP
2. First N frames arrive (header + partial content)
3. Browser begins rendering frames 0 to N-1
4. Additional frames arrive incrementally
5. Browser continues playback seamlessly
6. Playback completes when all frames received

**Success Criteria:**
- First frame renders within T1 seconds of request
- No visible stutter between arriving frames
- Memory usage remains bounded during streaming

**Related Requirements:** FBF-STREAM-001, FBF-STREAM-004, FBF-PERF-007
```

Link each requirement back to 1+ use cases to demonstrate necessity.

---

## 3. Protocol Definitions

### What REX Provides

**Minimal technical detail.** Requirements state *capabilities* without specifying *mechanisms*:

> "MUST support timing facilities (at least to differentiate between delivery time and activation time)"

No protocol structures, message formats, or transmission sequences are defined.

> "MUST be transport independent"

Explicitly defers transport-layer choices to implementations.

### Why This Approach?

REX is a **requirements document**, not a specification. It establishes *what* must exist, leaving *how* to separate technical specifications.

### **Recommendation for FBF.SVG:**

✅ **Separate requirements from protocol specification:**

**In Requirements Document:**
```
FBF-STREAM-003 [MUST] Support chunk-based transmission
    The format MUST allow transmission of discrete frame chunks
    without requiring the entire file to be available.
```

**In Protocol Specification (separate document):**
```
## FBF Streaming Protocol v1.0

### Chunk Structure
Each chunk MUST contain:
- Chunk header (8 bytes)
  ├─ Magic number: 0x46424643 ("FBFC")
  ├─ Chunk type: 0x01 (FRAME), 0x02 (HEADER), 0x03 (METADATA)
  └─ Payload length: uint32 (bytes)
- Chunk payload (N bytes)
- CRC32 checksum (4 bytes)

### Transmission Sequence
1. Client sends HTTP GET request with Accept: application/fbf-svg+stream
2. Server responds with 200 OK, Transfer-Encoding: chunked
3. Server sends HEADER chunk containing global metadata
4. Server sends sequential FRAME chunks
5. Server sends EOF marker
```

---

## 4. Terminology and Definitions

### What REX Provides

**Minimal terminology section.** Terms are mentioned contextually but rarely defined:

- "streaming protocols" (mentioned once)
- "transport layer"
- "error-free and ordered delivery"

REX assumes readers understand referenced standards (DOM 3 Events, XPath 1.0) without providing independent definitions.

### **Recommendation for FBF.SVG:**

✅ **Include a comprehensive terminology section:**

```markdown
## Terminology

### Core Terms

**Frame**
A single discrete image in a frame-by-frame animation sequence. Frames are numbered sequentially starting from 0.

**Chunk**
A self-contained unit of data that can be transmitted independently. A chunk may contain one or more frames.

**Progressive Rendering**
The ability to display initial content before the entire document is received, with additional content appearing as it arrives.

**Streaming**
Transmission of FBF.SVG content where rendering begins before transmission completes, enabling immediate playback.

**Buffering**
Temporary storage of received but not-yet-rendered frames to smooth playback during variable network conditions.

### Network Terms

**Latency**
Time delay between requesting data and beginning to receive it (round-trip time).

**Throughput**
Amount of data successfully transmitted per unit time (typically bytes/second).

**Jitter**
Variability in packet arrival times during streaming transmission.

**Head-of-Line Blocking**
Condition where a delayed packet prevents processing of subsequent packets that have already arrived.

### Conformance Terms

This specification uses RFC 2119 keywords:
- **MUST** / **REQUIRED** - Mandatory requirement
- **SHOULD** / **RECOMMENDED** - Strong recommendation
- **MAY** / **OPTIONAL** - Discretionary choice
```

---

## 5. Security Considerations

### What REX Provides

**Nothing.** Security considerations are completely absent from the REX requirements document.

No mention of:
- Authentication/authorization
- Encryption/confidentiality
- Integrity verification
- Denial-of-service prevention
- Injection attacks
- Privacy concerns

### Why This Matters for FBF.SVG

Streaming protocols introduce security risks beyond static file delivery:
- **Resource exhaustion:** Malicious server could send infinite frames
- **Content injection:** Compromised stream could inject malicious frames
- **Privacy leaks:** Timing side-channels could reveal user behavior
- **Cache poisoning:** Incomplete/corrupted streams cached incorrectly

### **Recommendation for FBF.SVG:**

❌ **Do NOT omit security considerations like REX does.**

✅ **Include a dedicated security section:**

```markdown
## Security Considerations

### 7.1 Resource Exhaustion

**Threat:** Malicious server sends infinite stream of frames to exhaust client memory.

**Mitigation:** Clients MUST enforce maximum frame count declared in header. If frame count exceeds declared value, client MUST terminate stream and discard content.

```xml
<fbf:header maxFrames="1000" />
<!-- If more than 1000 frames received, abort -->
```

### 7.2 Content Integrity

**Threat:** Network attacker modifies frames during transmission (MITM attack).

**Mitigation:** Clients SHOULD verify checksums for each received chunk. Servers SHOULD support HTTPS/TLS for encrypted transmission.

```xml
<fbf:frame id="42" checksum="sha256:a3f2c1..."/>
```

### 7.3 Denial of Service

**Threat:** Attacker requests numerous concurrent streams to overload server.

**Mitigation:** Servers MAY implement rate limiting per client IP. Servers SHOULD prioritize completing active streams over starting new ones.

### 7.4 Privacy

**Threat:** Streaming metadata leaks user behavior (pause/resume patterns, viewing duration).

**Mitigation:** Clients SHOULD NOT send frame-level acknowledgments unless required by protocol. Servers SHOULD minimize logging of per-frame client interactions.

### 7.5 Cross-Origin Restrictions

**Threat:** Malicious site embeds sensitive FBF.SVG content from another origin.

**Mitigation:** FBF.SVG streaming MUST respect CORS (Cross-Origin Resource Sharing) policies. Clients MUST NOT render cross-origin streams unless explicit CORS headers permit.
```

---

## 6. Examples and Illustrations

### What REX Provides

**Zero examples.** No code samples, XML snippets, message flows, or streaming scenarios.

Requirements remain entirely abstract without concrete demonstrations.

### Impact on Usability

Without examples, implementers must infer correct usage from abstract requirements, increasing risk of divergent implementations and interoperability failures.

### **Recommendation for FBF.SVG:**

❌ **Do NOT follow REX's lack of examples.**

✅ **Provide extensive examples throughout:**

#### Example 1: Basic Streaming Response

```http
GET /animation.fbf.svg HTTP/1.1
Host: example.com
Accept: application/fbf-svg+stream

HTTP/1.1 200 OK
Content-Type: application/fbf-svg+stream
Transfer-Encoding: chunked

[CHUNK 1: HEADER]
<fbf:svg version="1.0" frameCount="100" fps="30">
  <fbf:metadata>
    <fbf:title>Streaming Animation Demo</fbf:title>
  </fbf:metadata>
  <fbf:defs>
    <!-- Shared resources -->
  </fbf:defs>
</fbf:svg>

[CHUNK 2: FRAMES 0-9]
<fbf:frameSet start="0" count="10">
  <fbf:frame id="0">
    <circle cx="50" cy="50" r="10"/>
  </fbf:frame>
  <!-- ... frames 1-9 ... -->
</fbf:frameSet>

[CHUNK 3: FRAMES 10-19]
<!-- ... continues ... -->
```

#### Example 2: Client Buffering Strategy

```javascript
class FBFStreamingPlayer {
  constructor(url, bufferSize = 30) {
    this.url = url;
    this.bufferSize = bufferSize; // frames
    this.receivedFrames = [];
    this.currentFrame = 0;
    this.playing = false;
  }

  async start() {
    const response = await fetch(this.url);
    const reader = response.body.getReader();

    // Start playing once buffer threshold met
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;

      const frames = this.parseChunk(value);
      this.receivedFrames.push(...frames);

      // Begin playback after buffer fills
      if (!this.playing && this.receivedFrames.length >= this.bufferSize) {
        this.playing = true;
        this.render();
      }
    }
  }

  render() {
    if (this.currentFrame < this.receivedFrames.length) {
      this.displayFrame(this.receivedFrames[this.currentFrame]);
      this.currentFrame++;
      setTimeout(() => this.render(), 1000 / this.fps);
    } else if (this.streamComplete) {
      this.stop();
    } else {
      // Wait for more frames to arrive
      setTimeout(() => this.render(), 100);
    }
  }
}
```

#### Example 3: Error Recovery

```xml
<!-- Client receives corrupted chunk -->
<fbf:frameSet start="50" count="10">
  <fbf:frame id="50" checksum="abc123">
    <circle cx="50" cy="50" r="corrupted_data_here
  </fbf:frame>
</fbf:frameSet>

<!-- Client response: -->
{
  "error": "CHECKSUM_MISMATCH",
  "frameId": 50,
  "action": "REQUEST_RETRANSMIT"
}

<!-- Server retransmits: -->
<fbf:frameSet start="50" count="1" retransmit="true">
  <fbf:frame id="50" checksum="abc123">
    <circle cx="50" cy="50" r="10"/>
  </fbf:frame>
</fbf:frameSet>
```

---

## 7. Document Status and Conformance

### REX's Approach

- **Status:** W3C Working Group Note (not a Recommendation)
- **Disclaimer:** "It is inappropriate to cite this document as other than work in progress"
- **Consensus:** Notes "lack of full consensus among working groups"

This positions REX as *exploratory* rather than *normative*.

### **Recommendation for FBF.SVG:**

✅ **Clearly state specification maturity:**

```markdown
## Status of This Document

This document is a **Working Draft** of the FBF.SVG Streaming Protocol Specification.

**Current Status:** DRAFT v0.3
**Last Modified:** 2025-11-10
**Expected Stable Release:** Q2 2026

### Stability Guarantees

- **Unstable:** Protocol message formats may change without notice
- **Experimental:** Implementations should not be deployed to production
- **Feedback Welcome:** Comments via GitHub Issues

### Implementation Status

- **Proof-of-concept:** Reference implementation in JavaScript
- **Interoperability:** No multi-vendor implementations yet
- **Test Suite:** Basic conformance tests available

### Path to Recommendation

1. ✅ Requirements gathered (COMPLETE)
2. 🔄 Draft specification (IN PROGRESS)
3. ⏳ Reference implementation
4. ⏳ Test suite completion
5. ⏳ Multi-vendor implementations
6. ⏳ Interoperability testing
7. ⏳ Candidate Recommendation
8. ⏳ Proposed Recommendation
```

---

## 8. Integration with Existing FBF.SVG Documentation

### How to Incorporate Streaming Documentation

```
fbf-svg-documentation/
├── 01-introduction.md
├── 02-core-format.md
├── 03-frame-structure.md
├── 04-rendering-model.md
├── 05-streaming-protocol.md        ← NEW: Based on REX analysis
│   ├── 5.1-requirements.md
│   ├── 5.2-use-cases.md
│   ├── 5.3-protocol-specification.md
│   ├── 5.4-security.md
│   └── 5.5-examples.md
├── 06-javascript-api.md
├── 07-conformance.md
└── appendices/
    ├── A-terminology.md
    └── B-references.md
```

### Cross-References

Link streaming concepts to core FBF.SVG features:

```markdown
## Frame Dependencies (Section 3.4)

Frames MAY reference shared resources defined in `<fbf:defs>`.

**Streaming Implications:** When streaming FBF.SVG content, the `<fbf:defs>`
section MUST be transmitted before any frames that reference it. See
[Streaming Protocol §5.3.2](05-streaming-protocol.md#chunk-ordering) for
transmission order requirements.
```

---

## 9. Key Lessons from REX

### What REX Does Well

✅ **Clear categorical organization** (Functional, Format, Ecosystem)
✅ **Consistent conformance language** (RFC 2119)
✅ **Technology-agnostic requirements** (transport independence)
✅ **Focus on integration** (ecosystem requirements)

### What REX Omits

❌ No use cases linking requirements to real-world problems
❌ No examples demonstrating correct usage
❌ No security considerations for network protocols
❌ No testability criteria for requirements
❌ No implementation guidance or protocol details

### **Strategic Recommendation:**

**Use REX as a template for high-level requirements, but supplement with:**

1. **Use cases** showing why each requirement exists
2. **Examples** demonstrating correct implementation
3. **Security analysis** for streaming scenarios
4. **Testability criteria** enabling conformance verification
5. **Separate protocol specification** with technical details

---

## 10. Actionable Next Steps for FBF.SVG

### Immediate Actions

1. **Create streaming requirements document** using REX's categorical structure
2. **Document 5-10 streaming use cases** with explicit actor/goal/flow
3. **Draft security considerations** covering resource exhaustion, integrity, DoS, privacy
4. **Write 10+ examples** showing streaming message flows and client implementations

### Medium-Term Actions

5. **Develop protocol specification** separate from requirements document
6. **Create conformance test suite** for streaming behavior
7. **Build reference implementation** demonstrating streaming playback
8. **Write integration guide** for embedding FBF.SVG streaming in web applications

### Long-Term Actions

9. **Gather implementation feedback** from early adopters
10. **Revise specification** based on real-world deployment experience
11. **Pursue standardization** if FBF.SVG gains adoption
12. **Develop interoperability tests** for multi-vendor implementations

---

## 11. Template: FBF.SVG Streaming Requirements

Based on REX analysis, here's a starter template:

```markdown
# FBF.SVG Streaming Requirements v1.0

## Status
Working Draft - 2025-11-10

## 1. Functional Requirements

### 1.1 Progressive Rendering
FBF-STREAM-001 [MUST] The format MUST support progressive rendering where
initial frames can be displayed before the complete document is received.

**Rationale:** Enables immediate playback for large animations, improving
perceived performance.

**Use Cases:** UC-STREAM-001 (Progressive Playback), UC-STREAM-003 (Adaptive Quality)

**Test Criteria:** Frame N renders successfully with frames N+1 to N+K not yet received.

### 1.2 Chunk-Based Transmission
FBF-STREAM-002 [MUST] The format MUST allow transmission in discrete chunks
where each chunk can be processed independently.

**Rationale:** Supports HTTP chunked transfer encoding and packet-based protocols.

**Use Cases:** UC-STREAM-001 (Progressive Playback)

**Test Criteria:** Client successfully processes chunk N without requiring chunk N+1.

## 2. Format Requirements

### 2.1 Header Declaration
FBF-STREAM-010 [MUST] The format MUST include a header declaring total frame
count before any frames are transmitted.

**Rationale:** Allows clients to allocate resources and display progress indicators.

**Use Cases:** UC-STREAM-002 (Bandwidth Adaptation)

**Test Criteria:** Parser can determine total frame count from first received chunk.

## 3. Ecosystem Requirements

### 3.1 HTTP Compatibility
FBF-STREAM-020 [MUST] The streaming protocol MUST be implementable over
standard HTTP/1.1 and HTTP/2.

**Rationale:** Leverages existing web infrastructure without requiring custom protocols.

**Use Cases:** UC-STREAM-001, UC-STREAM-004 (CDN Distribution)

**Test Criteria:** Successfully streams over nginx, Apache, Cloudflare CDN.

## 4. Security Requirements

### 4.1 Resource Limits
FBF-STREAM-030 [MUST] Clients MUST enforce maximum frame count and memory limits.

**Rationale:** Prevents resource exhaustion attacks from malicious servers.

**Related:** Security Considerations §7.1

**Test Criteria:** Client rejects stream exceeding declared frame count.
```

---

## 12. Comparison Matrix: REX vs. FBF.SVG Needs

| Aspect | REX Approach | FBF.SVG Recommendation |
|--------|--------------|------------------------|
| **Requirement IDs** | None (categorical only) | ✅ Alphanumeric IDs (FBF-STREAM-001) |
| **Use Cases** | ❌ Not documented | ✅ Explicit scenarios with flows |
| **Examples** | ❌ None provided | ✅ Extensive code/XML samples |
| **Security** | ❌ Not addressed | ✅ Dedicated security section |
| **Protocol Details** | ❌ Abstract only | ✅ Separate protocol specification |
| **Testability** | ❌ No test criteria | ✅ Explicit test criteria per requirement |
| **Terminology** | Minimal | ✅ Comprehensive glossary |
| **Conformance** | RFC 2119 | ✅ RFC 2119 + test suite |
| **Integration** | Ecosystem requirements | ✅ Ecosystem + implementation guides |
| **Versioning** | Not specified | ✅ Explicit version compatibility rules |

---

## Conclusion

The REX requirements document provides a useful **structural foundation** for FBF.SVG streaming documentation through its categorical organization and conformance language. However, its minimalist approach omits critical elements (use cases, examples, security, testability) that modern specifications require.

**FBF.SVG should:**
- ✅ Adopt REX's categorical structure (Functional, Format, Ecosystem)
- ✅ Use RFC 2119 conformance keywords consistently
- ✅ Maintain REX's principle of transport independence
- ❌ Avoid REX's omissions by adding use cases, examples, and security
- ✅ Separate high-level requirements from detailed protocol specifications
- ✅ Provide explicit testability criteria and implementation guidance

By learning from both REX's strengths and weaknesses, FBF.SVG can create streaming documentation that is both architecturally sound and practically useful for implementers.

---

## References

1. [Remote Events for XML (REX) Requirements](https://www.w3.org/TR/rex-reqs/) - W3C Working Group Note, 02 February 2006
2. [RFC 2119: Key words for use in RFCs to Indicate Requirement Levels](https://www.rfc-editor.org/rfc/rfc2119)
3. [W3C Manual of Style](https://www.w3.org/2001/06/manual/)
4. [Architecture of the World Wide Web, Volume One](https://www.w3.org/TR/webarch/)

---

**Document Prepared By:** Claude (Sonnet 4.5)
**For Project:** FBF.SVG Streaming Protocol Development
**Date:** 2025-11-10
