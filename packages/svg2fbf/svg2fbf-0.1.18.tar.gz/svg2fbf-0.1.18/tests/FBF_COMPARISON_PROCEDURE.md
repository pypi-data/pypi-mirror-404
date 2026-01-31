# FBF Frame Comparison - Critical Procedures

**IMPORTANT**: This document describes the CORRECT procedures for comparing FBF animation files. These procedures are essential for accurate frame capture and comparison.

## Table of Contents

1. [Overview](#overview)
2. [The 1 FPS Workaround](#the-1-fps-workaround)
3. [XML Preservation Requirement](#xml-preservation-requirement)
4. [Complete Implementation](#complete-implementation)
5. [Common Mistakes to Avoid](#common-mistakes-to-avoid)
6. [Testing the Comparator](#testing-the-comparator)

---

## Overview

The FBF Frame Comparator (`compare_fbf.py`) compares two FBF animation files by:
1. Creating temporary 1 FPS copies
2. Rendering frames with Puppeteer
3. Comparing frames pixel-by-pixel
4. Generating HTML reports

**Two Critical Requirements:**
- ✅ **1 FPS Workaround**: Must slow animations to 1 FPS for accurate capture
- ✅ **XML Preservation**: Must preserve all XML attributes/namespaces

---

## The 1 FPS Workaround

### Why It's Needed

**Problem**: Puppeteer frame capture timing is unreliable at high FPS (>4 FPS)
- Animation plays too fast for accurate timestamp-based capture
- Frame capture misses frames or captures wrong frames
- Results in false positives ("all frames identical" when they're not)

**Solution**: Temporarily modify FBF files to play at 1 FPS (1 second per frame)
- Frame 1 at 0s, Frame 2 at 1s, Frame 3 at 2s, etc.
- Puppeteer can accurately capture at precise timestamps
- No timing precision issues

### How to Implement

Modify the `<animate>` element in the FBF file:

```python
def create_1fps_copy(fbf_path: Path, frame_count: int, output_dir: Path) -> Path:
    """
    Create temporary 1 FPS version for accurate frame capture.

    Modifications:
    - dur="{frame_count}s"      # 1 second per frame
    - begin="0s"                 # Auto-start (no click)
    - repeatCount="1"            # Play once (don't loop)
    """
```

**CRITICAL**: These modifications ensure:
1. Animation plays at exactly 1 FPS
2. Animation auto-starts (Puppeteer can't click)
3. Animation plays once completely (captures all frames)

### Example Transformation

**Before (Original FBF):**
```xml
<animate attributeName="xlink:href"
         begin="click"
         dur="2.75s"
         repeatCount="indefinite"
         ... />
```

**After (1 FPS Copy):**
```xml
<animate attributeName="xlink:href"
         begin="0s"
         dur="21s"
         repeatCount="1"
         ... />
```

---

## XML Preservation Requirement

### Why It's Critical

**Problem**: Using `xml.etree.ElementTree.write()` corrupts FBF files
- Strips XML namespaces (e.g., `xmlns:xlink`, `xmlns:rdf`)
- Creates invalid SVG documents
- Browser renders as plain text instead of graphics
- All frames appear "identical" because they're all broken

**Solution**: Use regex string replacement instead of XML parsing
- Preserves ALL attributes exactly as written
- Preserves ALL namespaces
- Preserves ALL formatting
- Ensures valid SVG output

### Correct Implementation

**❌ WRONG - Do NOT use this:**
```python
# This BREAKS the FBF file!
tree = ET.parse(fbf_path)
root = tree.getroot()
# ... modify elements ...
tree.write(temp_file)  # ← CORRUPTS XML!
```

**✅ CORRECT - Use this:**
```python
# Read as text
with open(fbf_path, 'r', encoding='utf-8') as f:
    svg_content = f.read()

# Use regex to modify attributes
import re
animate_pattern = r'(<animate[^>]*attributeName="xlink:href"[^>]*)(dur="[^"]*")([^>]*>)'

def replace_animate_attrs(match):
    before = match.group(1)
    after = match.group(3)

    # Build new attributes
    new_attrs = f'dur="{frame_count}s"'
    result = before + new_attrs + after

    # Modify other attributes
    result = re.sub(r'begin="click"', 'begin="0s"', result)
    result = re.sub(r'repeatCount="[^"]*"', 'repeatCount="1"', result)

    return result

modified_content = re.sub(animate_pattern, replace_animate_attrs, svg_content, flags=re.DOTALL)

# Write as text
with open(temp_file, 'w', encoding='utf-8') as f:
    f.write(modified_content)
```

### Why String Replacement Works

1. **Preserves structure**: Everything stays exactly as written
2. **Preserves namespaces**: `xmlns:xlink`, `xmlns:rdf`, etc. untouched
3. **Preserves formatting**: Whitespace, comments, CDATA all preserved
4. **Surgical changes**: Only modifies specific attributes, nothing else
5. **No parsing artifacts**: No XML serialization issues

---

## Complete Implementation

### Full Procedure

```python
def create_1fps_copy(fbf_path: Path, frame_count: int, output_dir: Path) -> Path:
    """
    Create temporary 1 FPS version of FBF file.

    CRITICAL REQUIREMENTS:
    1. Use string replacement (NOT XML parsing)
    2. Modify exactly 3 attributes: dur, begin, repeatCount
    3. Preserve all other content exactly as is
    """
    # Read as text (preserves XML structure)
    with open(fbf_path, 'r', encoding='utf-8') as f:
        svg_content = f.read()

    # Find and modify animate element
    import re

    animate_pattern = r'(<animate[^>]*attributeName="xlink:href"[^>]*)(dur="[^"]*")([^>]*>)'

    def replace_animate_attrs(match):
        before = match.group(1)
        after = match.group(3)

        # Set 1 FPS timing
        new_attrs = f'dur="{frame_count}s"'
        result = before + new_attrs + after

        # Auto-start (no click)
        result = re.sub(r'begin="click"', 'begin="0s"', result)

        # Play once (don't loop)
        result = re.sub(r'repeatCount="[^"]*"', 'repeatCount="1"', result)

        return result

    # Apply transformation
    modified_content = re.sub(animate_pattern, replace_animate_attrs, svg_content, flags=re.DOTALL)

    # Save temporary file
    temp_file = output_dir / f"{fbf_path.stem}_1fps_temp.fbf.svg"
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    return temp_file
```

### Usage Pattern

```python
# Create 1 FPS copies
file1_1fps = create_1fps_copy(file1, frame_count, output_dir)
file2_1fps = create_1fps_copy(file2, frame_count, output_dir)

try:
    # Render frames at 1 FPS
    frames1 = renderer.render_fbf_animation_frames(
        file1_1fps,
        output_dir,
        frame_count,
        fps=1.0  # MUST be 1.0
    )

    frames2 = renderer.render_fbf_animation_frames(
        file2_1fps,
        output_dir,
        frame_count,
        fps=1.0  # MUST be 1.0
    )

    # Compare frames...

finally:
    # Clean up temporary files
    if file1_1fps.exists():
        file1_1fps.unlink()
    if file2_1fps.exists():
        file2_1fps.unlink()
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using XML Parsing

```python
# WRONG - Corrupts FBF file
tree = ET.parse(fbf_path)
tree.write(temp_file)
```

**Why it fails**: Strips namespaces, creates invalid SVG, renders as text

**Fix**: Use string replacement instead

---

### ❌ Mistake 2: Capturing at Original FPS

```python
# WRONG - Timing unreliable
renderer.render_fbf_animation_frames(
    original_fbf,      # Original file at 4 FPS
    output_dir,
    frame_count,
    fps=4.0           # Too fast!
)
```

**Why it fails**: Puppeteer timing precision insufficient, misses frames

**Fix**: Create 1 FPS copy first, then capture at 1.0 FPS

---

### ❌ Mistake 3: Not Cleaning Up Temp Files

```python
# WRONG - Leaves temporary files
file1_1fps = create_1fps_copy(file1, frame_count, output_dir)
# ... render frames ...
# Temp file never deleted!
```

**Why it fails**: Accumulates temp files, wastes disk space

**Fix**: Use try/finally block to ensure cleanup

---

### ❌ Mistake 4: Forgetting Auto-Start

```python
# WRONG - Animation won't start
# Forgot to change begin="click" to begin="0s"
```

**Why it fails**: Puppeteer can't simulate clicks, animation never starts

**Fix**: Always modify `begin` attribute to "0s"

---

### ❌ Mistake 5: Infinite Loop

```python
# WRONG - Animation loops forever
# Forgot to change repeatCount="indefinite" to repeatCount="1"
```

**Why it fails**: Puppeteer tries to capture infinite frames, hangs

**Fix**: Always set `repeatCount="1"`

---

## Testing the Comparator

### Verify It's Working

```bash
# Test with two FBF files
uv run python compare_fbf.py file1.fbf.svg file2.fbf.svg

# Expected output:
# ⚙️  Creating 1 FPS temporary copies...
# ✓ Temporary files created
# 🎬 Rendering frames from File 1 at 1 FPS...
# ✓ Rendered N frames
# 🎬 Rendering frames from File 2 at 1 FPS...
# ✓ Rendered N frames
# 🧹 Cleaning up temporary files...
# ✓ Temporary files removed
# 📊 Comparing N frames...
# ✅ SUCCESS: All frames are identical!
```

### Check for Correct Rendering

1. **Open HTML report**: All frames should show proper graphics
2. **Not plain text**: If you see text instead of graphics, XML preservation failed
3. **All frames captured**: Frame count should match (including pingpong backward frames)

### Debug Checklist

If comparison fails:

1. ✅ **Check temp files**: Do they have valid XML?
   ```bash
   xmllint --noout temp_file_1fps.fbf.svg
   ```

2. ✅ **Check namespaces**: Are they preserved?
   ```bash
   grep "xmlns:" temp_file_1fps.fbf.svg
   ```

3. ✅ **Check timing**: Is dur="Ns" where N = frame_count?
   ```bash
   grep 'dur=' temp_file_1fps.fbf.svg
   ```

4. ✅ **Check auto-start**: Is begin="0s"?
   ```bash
   grep 'begin=' temp_file_1fps.fbf.svg
   ```

5. ✅ **Check play once**: Is repeatCount="1"?
   ```bash
   grep 'repeatCount=' temp_file_1fps.fbf.svg
   ```

---

## Summary

**Two Critical Requirements:**

1. **1 FPS Workaround**
   - Modify `dur`, `begin`, `repeatCount` attributes
   - Ensures accurate frame capture timing
   - Prevents frame capture errors

2. **XML Preservation**
   - Use regex string replacement (NOT XML parsing)
   - Preserves all namespaces and attributes
   - Ensures valid SVG rendering

**Always Remember:**
- ✅ Read as text, modify with regex, write as text
- ✅ Create 1 FPS copies before rendering
- ✅ Render at exactly 1.0 FPS
- ✅ Clean up temp files in finally block
- ❌ NEVER use ET.write() on FBF files
- ❌ NEVER capture at original FPS

**Test Results Should Show:**
- Proper frame graphics (not text)
- All frames captured (including pingpong backward)
- Accurate pixel-perfect comparison
- Clean temp file cleanup

---

**Last Updated**: 2025-11-08
**Status**: Production-ready, tested and verified
