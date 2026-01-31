#!/usr/bin/env python3
"""
svg2fbf Test Constants - Central source of truth for all test configuration values.

This module defines all constants used by the svg2fbf test system (testrunner.py).
Constants are divided into configurable and non-configurable categories.

NON-CONFIGURABLE TEST VALUES:
    These values MUST remain fixed for tests to work correctly. They ensure:
    - Deterministic test behavior (fps=1 means 1 frame per second, predictable timing)
    - Complete test coverage (animation_type="once" ensures all frames are tested)
    - Automated test execution (auto_start=true, play_on_click=false for automation)

CONFIGURABLE VALUES:
    These values can be adjusted based on test requirements:
    - Tolerance values for image comparison
    - Precision settings for coordinate calculations
    - Directory paths and file formats
"""

# ============================================================================
# NON-CONFIGURABLE TEST VALUES
# ============================================================================
# Why non-configurable: These values are essential for test automation and
# deterministic behavior. Changing them would break the test system.

# Animation timing
FPS = 1.0
# Why: FPS=1 ensures exactly 1 frame per second for deterministic timing.
# This makes frame capture predictable and prevents timing-related flakiness.
# Tests rely on this to capture frames at precise intervals.

ANIMATION_TYPE = "once"
# Why: animation_type="once" ensures the animation plays through all frames
# exactly once and stops. This guarantees complete test coverage of all frames.
# Other values like "loop" or "bounce" would cause infinite loops or skip frames.

PLAY_ON_CLICK = False
# Why: play_on_click=false ensures animation auto-starts without user interaction.
# Tests are automated and cannot click buttons. This must be false.

AUTO_START = True
# Why: auto_start=true ensures animation begins immediately on page load.
# Tests need immediate frame capture without waiting for user interaction.
# This is critical for automated testing in headless browsers.

# SVG rendering
PRESERVE_ASPECT_RATIO = "xMidYMid meet"
# Why: This ensures SVGs are centered and scaled proportionally to fit the viewport.
# xMidYMid = align to center (both horizontally and vertically)
# meet = scale to fit while preserving aspect ratio
# This matches svg2fbf's default behavior for consistent rendering.

# ============================================================================
# CONFIGURABLE DEFAULT VALUES
# ============================================================================
# These values can be adjusted based on specific test requirements.
# They represent sensible defaults but can be overridden per E2E test session.

# Test tolerances for image comparison
DEFAULT_IMAGE_TOLERANCE = 0.05
# Purpose: Maximum allowed percentage difference between input and output images.
# Range: 0.0 (exact match) to 1.0 (100% different)
# Why 0.05: Allows for minor rendering differences while catching real bugs.

DEFAULT_PIXEL_TOLERANCE = 0.004
# Purpose: Per-pixel color difference threshold (normalized 0-1 per channel).
# Range: 0.0 (exact match) to 1.0 (completely different color)
# Why 0.004: Approximately 1/256, allows for 1-bit color variation per channel.

DEFAULT_MAX_FRAMES = 50
# Purpose: Maximum number of frames to process in an E2E test session.
# Why 50: Prevents runaway tests while allowing reasonably long animations.

# Precision settings for coordinate calculations
DEFAULT_PRECISION_DIGITS = 28
# Purpose: Number of decimal digits for coordinate precision in SVG transforms.
# Why 28: Maximum precision supported by svg2fbf, ensures no rounding errors.

DEFAULT_PRECISION_CDIGITS = 28
# Purpose: Number of decimal digits for coordinate precision in color values.
# Why 28: Matches coordinate precision for consistency.

# E2E test session creation settings
DEFAULT_FRAME_NUMBER_FORMAT = "frame{:05d}.svg"
# Purpose: Filename format for numbered frame files in E2E test sessions.
# Why this format: 5 digits (00001-99999) matches svg2fbf standard.
# Example: frame00001.svg, frame00002.svg, etc.

DEFAULT_CREATE_SESSION_ENCODING = "utf-8"
# Purpose: Character encoding for reading SVG files during E2E test session creation.
# Why UTF-8: Universal standard, supports all SVG content including Unicode.

# ============================================================================
# DIRECTORY STRUCTURE CONSTANTS
# ============================================================================
# These define the standard directory layout for E2E test sessions and results.

# Directory names (relative to project root or E2E test session directory)
DIR_RESULTS = "tests/sessions"
# Purpose: Top-level directory for all E2E test session results.

DIR_TESTS = "tests"
# Purpose: Directory containing test code and utilities.

DIR_NODE_SCRIPTS = "node_scripts"
# Purpose: Directory containing Node.js/Puppeteer rendering scripts (inside tests/).

DIR_INPUT_FRAMES = "input_frames"
# Purpose: E2E test session-level directory containing original SVG frames.

DIR_INPUT_FRAMES_PNG = "input_frames_png"
# Purpose: Run-level directory containing rendered PNGs from input SVGs.

DIR_OUTPUT_FRAMES_PNG = "output_frames_png"
# Purpose: Run-level directory containing captured PNGs from FBF animation.

DIR_FBF_OUTPUT = "fbf_output"
# Purpose: Run-level directory containing generated FBF SVG files.

DIR_DIFF_PNG = "diff_png"
# Purpose: Run-level directory containing grayscale difference maps.

# File names
FILE_SESSION_METADATA = "session_metadata.json"
# Purpose: JSON file storing E2E test session configuration and metadata.

FILE_TEST_ANIMATION = "test_animation.fbf.svg"
# Purpose: Generated FBF animation file for testing.

# ============================================================================
# COMMAND-LINE AND SUBPROCESS CONSTANTS
# ============================================================================

# Timeout values (in seconds)
TIMEOUT_BBOX_CALCULATION = 30
# Purpose: Timeout for Node.js script calculating SVG bounding boxes.
# Why 30s: Generous timeout for complex SVGs with many elements.

TIMEOUT_SVG2FBF_CONVERSION = 300
# Purpose: Timeout for svg2fbf conversion process (5 minutes).
# Why 300s: Large animations with many frames can take several minutes.

# Browser configuration - dynamically detected
# Purpose: Chrome is recommended for svg2fbf (best SVG rendering)
# Fallback: System default browser if Chrome not installed
# Implementation: See get_preferred_browser() in testrunner.py

# ============================================================================
# NUMBERING PRIORITY CONSTANTS
# ============================================================================
# These define the priority ladder for extracting frame numbers from filenames.
# Higher numbers = higher priority in candidate selection.

# Priority ranges (used internally by NumberingPriorityLadder)
PRIORITY_UNDERSCORE_5_DIGITS = 35
# Pattern: filename_00001.svg (5 digits after underscore)
# Why highest priority: This is the svg2fbf standard format.

PRIORITY_UNDERSCORE_OTHER = 30
# Pattern: filename_001.svg (other digit counts after underscore)
# Why high priority: Underscore is a clear separator.

PRIORITY_HYPHEN_5_DIGITS = 25
# Pattern: filename-00001.svg (5 digits after hyphen)
# Why medium-high: Hyphen is common separator.

PRIORITY_HYPHEN_OTHER = 20
# Pattern: filename-001.svg (other digit counts after hyphen)

PRIORITY_DOT_SVG = 300
# Pattern: filename.00001.svg (digits between dots)
# Why 300: Special handling for dot separator patterns.

PRIORITY_EMBEDDED_5_DIGITS = 15
# Pattern: frame00001.svg (5 embedded digits)
# Why medium: Less clear than delimited numbers.

PRIORITY_EMBEDDED_OTHER = 10
# Pattern: frame001.svg (other embedded digit counts)

PRIORITY_NO_NUMBER = 0
# Pattern: filename.svg (no number found)
# Why lowest: Files without numbers get first available slot.

# ============================================================================
# PYPROJECT.TOML CONFIGURATION STRUCTURE
# ============================================================================
# This defines the structure of the [tool.svg2fbf.test] section in pyproject.toml.

# Default configuration dictionary (used to populate/validate pyproject.toml)
PYPROJECT_DEFAULTS = {
    "tool": {
        "svg2fbf": {
            "test": {
                # Test tolerances
                "image_tolerance": DEFAULT_IMAGE_TOLERANCE,
                "pixel_tolerance": DEFAULT_PIXEL_TOLERANCE,
                "max_frames": DEFAULT_MAX_FRAMES,
                # Animation settings (NON-CONFIGURABLE in tests)
                "fps": FPS,
                "animation_type": ANIMATION_TYPE,
                # Precision settings
                "precision_digits": DEFAULT_PRECISION_DIGITS,
                "precision_cdigits": DEFAULT_PRECISION_CDIGITS,
                # Session creation settings
                "frame_number_format": DEFAULT_FRAME_NUMBER_FORMAT,
                "create_session_encoding": DEFAULT_CREATE_SESSION_ENCODING,
            }
        },
        "pytest": {
            "ini_options": {
                "minversion": "6.0",
                "addopts": "-ra -q --strict-markers",
                "testpaths": ["tests"],
                "python_files": "test_*.py",
                "python_classes": "Test*",
                "python_functions": "test_*",
                "markers": [
                    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
                    "integration: marks tests as integration tests",
                    "unit: marks tests as unit tests",
                ],
            }
        },
    }
}

# ============================================================================
# SVG2FBF COMMAND-LINE ARGUMENTS
# ============================================================================
# Standard arguments used when invoking svg2fbf for tests.

SVG2FBF_SPEED_ARG = "--speed=1.0"
# Why: Matches FPS=1 for deterministic timing.

SVG2FBF_ANIMATION_TYPE_ARG = "--animation_type=once"
# Why: Ensures complete test coverage of all frames.

SVG2FBF_DIGITS_ARG = "--digits=28"
# Why: Maximum precision for coordinate transforms.

SVG2FBF_CDIGITS_ARG = "--cdigits=28"
# Why: Maximum precision for color coordinates.

# ============================================================================
# PNG FILENAME FORMATS
# ============================================================================

PNG_INPUT_FRAME_FORMAT = "input_frame_{:04d}.png"
# Purpose: Format for input PNG filenames (rendered from SVG).
# Example: input_frame_0001.png, input_frame_0002.png

PNG_OUTPUT_FRAME_FORMAT = "fbf_frame_{:04d}.png"
# Purpose: Format for output PNG filenames (captured from FBF).
# Example: fbf_frame_0001.png, fbf_frame_0002.png

PNG_DIFF_FRAME_FORMAT = "diff_gray_frame_{:04d}.png"
# Purpose: Format for difference map PNG filenames.
# Example: diff_gray_frame_0001.png, diff_gray_frame_0002.png

# ============================================================================
# MISCELLANEOUS CONSTANTS
# ============================================================================

# E2E Test Session ID format
SESSION_ID_FORMAT = "test_session_{:03d}_{:d}frames"
# Purpose: Format for E2E test session directory names.
# Example: test_session_001_5frames, test_session_077_23frames

SESSION_ID_TEMP_SUFFIX = "_temp"
# Purpose: Suffix for temporary E2E test session directories during creation.
# Example: test_session_001_temp

# Timestamp format
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"
# Purpose: Format for run directories inside E2E test sessions.
# Example: 20250109_143022

# Terminal output formatting
SEPARATOR_WIDTH = 80
# Purpose: Width of separator lines (=== lines) in terminal output.

# SVG viewBox validation
VIEWBOX_COMPONENT_COUNT = 4
# Purpose: Number of components in a valid viewBox attribute.
# Format: "x y width height" (4 space-separated values)
