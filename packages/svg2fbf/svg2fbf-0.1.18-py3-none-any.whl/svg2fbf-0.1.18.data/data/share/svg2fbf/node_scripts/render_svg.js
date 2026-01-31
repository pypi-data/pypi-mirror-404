/**
 * render_svg.js
 *
 * Renders a single SVG file to PNG using Puppeteer and headless Chrome
 *
 * Usage:
 *   node render_svg.js <svg_path> <output_png_path> <width> <height> [transform] [viewbox] [preserveAspectRatio]
 *
 * Example:
 *   node render_svg.js input.svg output.png 1920 1080
 *   node render_svg.js input.svg output.png 1920 1080 "" "" "none"
 *
 * Exit codes:
 *   0 - Success
 *   1 - Error (with error message to stderr)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Render SVG to PNG
 *
 * @param {string} svgPath - Path to input SVG file
 * @param {string} outputPath - Path to output PNG file
 * @param {number} width - Viewport width in pixels
 * @param {number} height - Viewport height in pixels
 * @param {string} transform - Optional SVG transform string (e.g., "matrix(0.42 0 0 0.42 0 0)")
 *                            This is the EXACT transform calculated by svg2fbf.py
 * @param {string} targetViewBox - Optional viewBox string to use (e.g., "0 0 600 400")
 *                                When transform is provided, this should be the FIRST frame's viewBox
 * @param {string} preserveAspectRatio - Optional preserveAspectRatio value (e.g., "xMidYMid meet", "none")
 *                                      Default: "xMidYMid meet"
 *                                      Use "none" for animations with negative viewBox coordinates
 */
async function renderSVG(svgPath, outputPath, width, height, transform = null, targetViewBox = null, preserveAspectRatio = "xMidYMid meet") {
  let browser = null;

  try {
    // Launch headless Chrome
    // Why: Provides consistent SVG rendering engine
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',  // Why: Avoid /dev/shm memory issues in containers
        '--disable-web-security',    // Why: Allow loading local files
        '--force-color-profile=srgb', // Why: Consistent color space
        '--font-render-hinting=none', // Why: Disable font hinting for consistent rendering
        '--disable-font-subpixel-positioning', // Why: Disable sub-pixel font positioning
        '--disable-lcd-text'          // Why: Disable LCD text rendering (sub-pixel anti-aliasing)
      ]
    });

    const page = await browser.newPage();

    // Set viewport size
    // Why: Ensures SVG renders at specified dimensions
    await page.setViewport({
      width: parseInt(width),
      height: parseInt(height),
      deviceScaleFactor: 1  // Why: Avoid retina scaling for consistent pixel counts
    });

    // Read SVG file
    // Why: Need to embed in HTML for proper rendering
    if (!fs.existsSync(svgPath)) {
      throw new Error(`SVG file not found: ${svgPath}`);
    }

    let svgContent = fs.readFileSync(svgPath, 'utf-8');

    // If transform is provided, wrap SVG content in a <g> element with that transform
    // Why: This applies svg2fbf's EXACT per-frame transform (calculated by svg2fbf_frame_processor)
    if (transform) {
      // Extract SVG content (everything between <svg...> and </svg>)
      // CRITICAL: Must handle multiline <svg...> tags correctly
      // Why: Regex `/<svg[^>]*>/` fails on multiline tags, `indexOf('>')` finds wrong position

      // Find the complete opening <svg...> tag (may span multiple lines)
      // Why: Use a regex that handles newlines with the 's' flag (dotAll)
      // Note: Also handles namespace prefixes like <ns0:svg> from XML libraries
      const svgOpenTagMatch = svgContent.match(/<(?:\w+:)?svg[\s\S]*?>/);
      if (!svgOpenTagMatch) {
        throw new Error('Could not find opening <svg> tag in SVG file');
      }

      const svgOpenTag = svgOpenTagMatch[0];

      // Detect namespace prefix and build closing tag
      const namespaceMatch = svgOpenTag.match(/<(\w+:)?svg/);
      const nsPrefix = namespaceMatch && namespaceMatch[1] ? namespaceMatch[1] : '';
      const svgEndTag = `</${nsPrefix}svg>`;

      const contentStart = svgOpenTagMatch.index + svgOpenTag.length;
      const contentEnd = svgContent.lastIndexOf(svgEndTag);

      if (contentEnd === -1) {
        throw new Error('Could not find closing </svg> tag in SVG file');
      }

      const svgInnerContent = svgContent.substring(contentStart, contentEnd);

      // SAFEGUARD: Detect nested <svg> tags that would cause double scaling
      // Why: Nested SVG tags have their own viewBox which causes unwanted additional scaling
      // Note: Also checks for namespace prefixes like <ns0:svg>
      const nestedSvgMatch = svgInnerContent.match(/<(?:\w+:)?svg[\s\S]*?>/);
      if (nestedSvgMatch) {
        throw new Error(
          'CRITICAL: Detected nested <svg> tag in extracted content! ' +
          'This would cause double scaling. The SVG file structure is unexpected. ' +
          `Nested tag found at position ${nestedSvgMatch.index} in inner content. ` +
          'Expected structure: <svg>...[content without nested svg]...</svg>'
        );
      }

      // Wrap content with transform (exactly as svg2fbf does)
      const wrappedContent = `<g transform="${transform}">${svgInnerContent}</g>`;

      // Rebuild SVG with wrapped content (use previously detected closing tag)
      svgContent = svgOpenTag + wrappedContent + svgEndTag;
    }

    // Normalize SVG tag for consistent rendering
    // Why: Remove width/height attributes, keep viewBox, use preserveAspectRatio="xMidYMid meet"
    // CRITICAL: Use [\s\S]*? to handle multiline <svg...> tags
    // Note: Also handles namespace prefixes like <ns0:svg> from XML libraries
    const svgMatch = svgContent.match(/<(?:\w+:)?svg[\s\S]*?>/);
    if (svgMatch) {
      const svgTag = svgMatch[0];

      // Determine which viewBox to use
      // Why: When transform is provided, use targetViewBox (first frame's dimensions)
      //      Otherwise, extract from current SVG
      let viewBox = null;
      if (targetViewBox) {
        // Use provided viewBox (first frame's dimensions for transformed frames)
        viewBox = targetViewBox;
      } else {
        // Extract viewBox from current SVG
        const viewBoxMatch = svgTag.match(/viewBox=["']([^"']+)["']/);
        if (viewBoxMatch) {
          viewBox = viewBoxMatch[1];
        } else {
          // No viewBox - calculate from width/height
          const widthMatch = svgTag.match(/width=["']([0-9.]+)/);
          const heightMatch = svgTag.match(/height=["']([0-9.]+)/);
          const w = widthMatch ? widthMatch[1] : '1024';
          const h = heightMatch ? heightMatch[1] : '768';
          viewBox = `0 0 ${w} ${h}`;
        }
      }

      // Normalize SVG tag
      // Why: Build the preserveAspectRatio attribute only if a value is provided
      const preserveAspectRatioAttr = preserveAspectRatio ? ` preserveAspectRatio="${preserveAspectRatio}"` : '';

      // SAFETY: Check if SVG already has explicit pixel-based width/height
      // WHY: If the SVG has explicit dimensions (added by testrunner), preserve them
      //      instead of replacing with percentages. Percentages don't work properly
      //      in Puppeteer when the viewBox is much smaller than the viewport.
      const widthMatch = svgTag.match(/width=["'](\d+)["']/);
      const heightMatch = svgTag.match(/height=["'](\d+)["']/);
      const hasExplicitDimensions = widthMatch && heightMatch;

      let newSvgTag;
      if (hasExplicitDimensions) {
        // ⚠️ CRITICAL: Preserve existing pixel dimensions AND viewBox - don't replace anything!
        //
        // WHY THIS MATTERS:
        // =================
        // The SVG already has correct width/height/viewBox set by testrunner's properlySizeDoc().
        // These three attributes work together to scale the SVG correctly:
        //
        // Example that WORKS (don't touch it!):
        //   <svg viewBox="0 0 80 60" width="480" height="360">
        //   - viewBox defines coordinate system: 80 units wide, 60 units tall
        //   - width/height define rendered size: 480px wide, 360px tall
        //   - Browser scales 80x60 coordinate space to 480x360 pixels (6x scale)
        //   - Result: Content fills the entire 480x360 canvas ✓
        //
        // Example that BREAKS (what we used to do):
        //   <svg viewBox="0 0 480 360" width="480" height="360">
        //   - viewBox defines coordinate system: 480 units wide, 360 units tall
        //   - width/height define rendered size: 480px wide, 360px tall
        //   - Browser uses 1:1 scale (480 units = 480px)
        //   - Original 80x60 content appears tiny in corner! ✗
        //
        // HISTORY:
        // ========
        // Bug discovered in Frame 9 testing (2025-11-10):
        // - Frame 9 has viewBox="0 0 80 60" (small coordinate space)
        // - Testrunner added width="480" height="360" for proper scaling
        // - render_svg.js was replacing viewBox with "0 0 480 360"
        // - This broke the 6x scaling, making content appear tiny
        // - Fix: DON'T replace viewBox when explicit dimensions exist
        //
        // ⚠️ DO NOT CHANGE THIS LOGIC WITHOUT TESTING FRAME 9, 18, 26, 34!
        //
        newSvgTag = svgTag
          .replace(/preserveAspectRatio=["'][^"']*["']/g, '');

        if (preserveAspectRatio) {
          newSvgTag = newSvgTag.replace(/<(?:\w+:)?svg/, (match) => `${match} preserveAspectRatio="${preserveAspectRatio}"`);
        }
      } else {
        // No explicit dimensions - use percentage-based sizing (original behavior)
        newSvgTag = svgTag
          .replace(/width=["'][^"']*["']/g, '')
          .replace(/height=["'][^"']*["']/g, '')
          .replace(/preserveAspectRatio=["'][^"']*["']/g, '')
          .replace(/viewBox=["'][^"']*["']/g, '')
          .replace(/<(?:\w+:)?svg/, (match) => `${match} width="100%" height="100%" viewBox="${viewBox}"${preserveAspectRatioAttr}`);
      }

      svgContent = svgContent.replace(svgTag, newSvgTag);

      // SAFEGUARD: Verify subsequent frames match first frame's dimensions
      // Why: FBF animations require all frames to have identical viewBox
      // When: Only check when transform is provided (indicates subsequent frame)
      if (transform && targetViewBox) {
        // Parse the normalized viewBox we just set
        const actualViewBox = viewBox;

        if (actualViewBox !== targetViewBox) {
          throw new Error(
            `CRITICAL BUG: Subsequent frame has wrong viewBox!\n` +
            `Expected (first frame): ${targetViewBox}\n` +
            `Got (current frame):    ${actualViewBox}\n` +
            `This indicates the frame processor failed to return first frame's viewBox!`
          );
        }

        // Verify preserveAspectRatio matches expected value
        // Note: Empty string means attribute should be omitted (for negative viewBox coords)
        const expectedPreserveAspect = preserveAspectRatio || '(none)';
        const actualPreserveAspect = preserveAspectRatio || '(none)';

        if (actualPreserveAspect !== expectedPreserveAspect) {
          throw new Error(
            `CRITICAL BUG: Subsequent frame has wrong preserveAspectRatio!\n` +
            `Expected: ${expectedPreserveAspect}\n` +
            `Got:      ${actualPreserveAspect}`
          );
        }

        // Note: width/height are always set to 100% for the viewport, so we don't check them
        // The actual dimensions are determined by the viewBox
      }
    }

    // CRITICAL: For SVGs with scripts/onload, we must load the file directly when NO transform is needed
    // Why: SVG files may contain scripts with XML entities (&lt;, &gt;, etc.) that don't execute
    //      correctly when the SVG is embedded as a string in HTML. Loading the file directly
    //      ensures proper XML parsing and script execution.
    // Limitation: When transforms ARE needed, we must embed the SVG, which breaks scripts.
    //             This is an inherent limitation - you can't both transform AND execute scripts.
    const hasOnload = svgContent.includes('onload=');
    const hasScript = svgContent.includes('<script');
    const needsTransform = transform && transform.trim() !== '';

    let htmlContent;

    let useSvgDirectly = false;

    if ((hasOnload || hasScript) && !needsTransform) {
      // For SVGs with scripts and NO transform, load the SVG file directly
      // Why: This allows scripts to execute properly with correct XML entity handling
      useSvgDirectly = true;
      htmlContent = null;  // Won't be used
    } else {
      // Either no scripts, OR we need to apply transforms (which requires embedding)
      // LIMITATION: If SVG has scripts AND needs transforms, scripts won't execute correctly
      // Create HTML wrapper for SVG
      // Why: Puppeteer needs HTML context, not raw SVG
      htmlContent = `
        <!DOCTYPE html>
        <html>
          <head>
            <meta charset="UTF-8">
            <style>
              * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
              }
              html, body {
                width: 100%;
                height: 100%;
                overflow: hidden;
                background: transparent;
              }
              svg {
                display: block;
                width: 100%;
                height: 100%;
              }
              /* CRITICAL: Force consistent font rendering across contexts
                 Why: Generic fonts like "sans-serif" resolve differently, causing pixel differences
                 Solution: Force all SVG text to use Arial (widely available, consistent rendering) */
              text, tspan {
                font-family: Arial, sans-serif !important;
              }
            </style>
          </head>
          <body>
            ${svgContent}
          </body>
        </html>
      `;
    }

    // Load content - either HTML wrapper or SVG file directly
    if (useSvgDirectly) {
      // Navigate directly to the SVG file
      // Why: SVG with scripts needs to be loaded as standalone document for proper execution
      const absoluteSvgPath = path.resolve(svgPath);
      await page.goto(`file://${absoluteSvgPath}`, {
        waitUntil: 'networkidle0'  // Why: Wait for all resources and scripts to load
      });

      // Wait for SVG scripts to execute (onload handlers, etc.)
      // Why: Scripts may generate content dynamically
      await new Promise(resolve => setTimeout(resolve, 3000));
    } else {
      // Load HTML wrapper with embedded SVG
      await page.setContent(htmlContent, {
        waitUntil: 'networkidle0'  // Why: Wait for all resources (fonts, images) to load
      });
    }

    // Wait for fonts to load
    // Why: Fonts affect rendering, must be loaded before screenshot
    await page.evaluateHandle('document.fonts.ready');

    // Additional wait to ensure complete rendering
    // Why: Give browser time to paint everything
    await new Promise(resolve => setTimeout(resolve, 500));

    // Capture screenshot
    // Why: This is the actual PNG rendering of the SVG
    await page.screenshot({
      path: outputPath,
      type: 'png',
      omitBackground: true  // Why: Preserve transparency for SVGs without background
    });

    console.log(`✓ Rendered: ${path.basename(svgPath)} → ${path.basename(outputPath)}`);

  } catch (error) {
    console.error(`❌ Error rendering SVG: ${error.message}`);
    throw error;
  } finally {
    // Always close browser to free resources
    // Why: Prevent memory leaks and zombie processes
    if (browser) {
      await browser.close();
    }
  }
}

// Parse command-line arguments
// Why: Script is called from Python with these parameters
const args = process.argv.slice(2);

if (args.length < 4 || args.length > 7) {
  console.error('Usage: node render_svg.js <svg_path> <output_png_path> <width> <height> [transform] [viewbox] [preserveAspectRatio]');
  console.error('  transform:            Optional SVG transform string (e.g., "matrix(0.42 0 0 0.42 0 0)")');
  console.error('                        This is the EXACT transform calculated by svg2fbf.py');
  console.error('  viewbox:              Optional viewBox string (e.g., "0 0 600 400")');
  console.error('                        When transform is provided, this should be the first frame\'s viewBox');
  console.error('  preserveAspectRatio:  Optional preserveAspectRatio value (e.g., "xMidYMid meet", "none")');
  console.error('                        Default: "xMidYMid meet", use "none" for negative viewBox coordinates');
  console.error('');
  console.error('First frame: omit transform and viewbox (uses SVG\'s own viewBox)');
  console.error('Subsequent frames: provide both transform and viewbox to match first frame');
  process.exit(1);
}

const [svgPath, outputPath, width, height, transform, targetViewBox, preserveAspectRatio] = args;

// Execute rendering
renderSVG(svgPath, outputPath, width, height, transform, targetViewBox, preserveAspectRatio)
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
