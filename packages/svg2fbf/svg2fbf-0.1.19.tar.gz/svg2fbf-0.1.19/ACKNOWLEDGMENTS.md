# Acknowledgments

svg2fbf would not be possible without the following projects, organizations, and standards:

## Major Code Contributors

### Scour - SVG Optimizer and Cleaner
**Copyright © Scour Project Contributors**

**Significant portions of svg2fbf's code were adapted from the Scour project.**

Scour is an excellent SVG optimization tool that provides powerful algorithms for:
- SVG element optimization and cleanup
- Path data optimization and precision control
- Gradient deduplication and merging
- Element hashing and duplicate detection
- XML serialization and formatting
- Namespace handling and cleanup

svg2fbf incorporates many of these algorithms and techniques, with adaptations for frame-by-frame animation workflows. We are deeply grateful to the Scour developers for their outstanding work and for releasing their code under the Apache License 2.0, which made this project possible.

**Key Scour Contributors:**
- Louis Simard (original author)
- Jeff Schiller
- Sebastian Pipping
- And many other contributors

**Scour Project Links:**
- **Repository**: https://github.com/scour-project/scour
- **License**: Apache License 2.0
- **Documentation**: https://github.com/scour-project/scour/wiki

**Our sincere gratitude to the entire Scour team for their exceptional contributions to SVG optimization!**

## Standards and Specifications

### SVG Specification
**Copyright © World Wide Web Consortium (W3C®)**

svg2fbf implements the Scalable Vector Graphics (SVG) specification maintained by the W3C.

- **Website**: https://www.w3.org/Graphics/SVG/
- **Specification**: https://www.w3.org/TR/SVG2/
- **License**: W3C Software and Document License

We acknowledge the W3C SVG Working Group for their ongoing work in maintaining and evolving the SVG standard.

### SMIL Animation
**Copyright © World Wide Web Consortium (W3C®)**

The frame-by-frame animation functionality uses SMIL (Synchronized Multimedia Integration Language) elements as defined in the SVG specification.

- **Specification**: https://www.w3.org/TR/smil-animation/

## Academic Research

### Timed-Fragmentation of SVG Documents

We acknowledge the foundational research on SVG animation optimization and memory management:

**Concolato, C., Le Feuvre, J., & Moissinac, J. C. (2007, August).**
*Timed-fragmentation of SVG documents to control the playback memory usage.*
In Proceedings of the 2007 ACM symposium on Document engineering (pp. 121-124).

- **DOI**: https://dl.acm.org/doi/abs/10.1145/1284420.1284453

This research on SVG document fragmentation and memory control for animation playback provided valuable insights into efficient SVG animation techniques. **The FBF.SVG streaming capabilities and frame-at-end architecture (Section 13 of the specification) are directly inspired by this work.** The timed fragmentation approach demonstrated in this paper enables FBF players to manage memory efficiently during real-time streaming scenarios, including live presentations, LLM-generated avatars, vector GUI streaming, and AI roleplay visual feedback.

## Dependencies

### NumPy
**Copyright © NumPy Developers**

svg2fbf uses NumPy for numerical operations and matrix transformations.

- **Website**: https://numpy.org/
- **License**: BSD 3-Clause License
- **Version**: ≥2.2.0

## Community and Support

We acknowledge the broader SVG and open-source communities for their tools, libraries, and knowledge sharing.

## Contributors

Special thanks to all contributors who have helped improve svg2fbf through code, bug reports, documentation, and feature requests.

---

*If you believe your project should be acknowledged here, please open an issue or submit a pull request.*
