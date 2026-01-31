/**
 * calculate_bbox.js
 *
 * Calculates the bounding box of an SVG file using Puppeteer and headless Chrome
 * Returns the bbox as JSON that can be used to create a viewBox attribute
 *
 * Usage:
 *   node calculate_bbox.js <svg_path>
 *
 * Output (JSON to stdout):
 *   {"x": 0, "y": 0, "width": 800, "height": 600}
 *
 * Exit codes:
 *   0 - Success
 *   1 - Error (with error message to stderr)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Calculate SVG bounding box including fill, stroke, and markers
 *
 * @param {string} svgPath - Path to input SVG file
 * @returns {Promise<{x: number, y: number, width: number, height: number}>}
 */
async function calculateBBox(svgPath) {
  let browser = null;

  try {
    // Launch headless Chrome
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--force-color-profile=srgb'
      ]
    });

    const page = await browser.newPage();

    // Set a large viewport to ensure SVG can render fully
    await page.setViewport({
      width: 4096,
      height: 4096,
      deviceScaleFactor: 1
    });

    // Read SVG file
    if (!fs.existsSync(svgPath)) {
      throw new Error(`SVG file not found: ${svgPath}`);
    }

    const svgContent = fs.readFileSync(svgPath, 'utf-8');

    // Create HTML wrapper for SVG
    // Why: Puppeteer needs HTML context to evaluate DOM methods
    const htmlContent = `
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
              overflow: visible;
              background: transparent;
            }
            svg {
              display: block;
            }
          </style>
        </head>
        <body>
          ${svgContent}
        </body>
      </html>
    `;

    // Load HTML with embedded SVG
    await page.setContent(htmlContent, {
      waitUntil: 'networkidle0'
    });

    // Wait for fonts to load
    await page.evaluateHandle('document.fonts.ready');

    // Additional wait to ensure complete rendering
    await new Promise(resolve => setTimeout(resolve, 500));

    // Calculate bounding box in browser context
    // Why: getBBox() only works in browser, not in Node.js
    const bbox = await page.evaluate(() => {
      // Get the root SVG element
      // Handle both <svg> and <svg:svg> (namespace prefix)
      let svg = document.querySelector('svg');
      if (!svg) {
        // Try namespaced version
        svg = document.querySelector('svg\\:svg');
      }
      if (!svg) {
        // Try getting first SVG element via namespace URI
        svg = document.getElementsByTagNameNS('http://www.w3.org/2000/svg', 'svg')[0];
      }
      if (!svg) {
        throw new Error('No SVG element found in document');
      }

      // Method 1: Try getBBox() on the root SVG element
      // This gets the bounding box of all content INCLUDING stroke and markers
      try {
        const bbox = svg.getBBox({
          fill: true,        // Include fill geometry
          stroke: true,      // Include stroke geometry (CRITICAL for accurate bounds)
          markers: true,     // Include marker geometry
          clipped: false     // Don't clip to viewport
        });

        // getBBox returns a DOMRect with x, y, width, height
        return {
          x: bbox.x,
          y: bbox.y,
          width: bbox.width,
          height: bbox.height
        };
      } catch (error) {
        // Fallback: getBBox without options (older browsers)
        // This might not include stroke, so we need to add padding
        try {
          const bbox = svg.getBBox();

          // Estimate stroke width by checking all elements
          let maxStrokeWidth = 0;
          const allElements = svg.querySelectorAll('*');
          allElements.forEach(el => {
            const strokeWidth = window.getComputedStyle(el).strokeWidth;
            if (strokeWidth && strokeWidth !== 'none') {
              const width = parseFloat(strokeWidth);
              if (!isNaN(width) && width > maxStrokeWidth) {
                maxStrokeWidth = width;
              }
            }
          });

          // Add padding for stroke (half on each side)
          const padding = Math.ceil(maxStrokeWidth / 2) + 1;

          return {
            x: bbox.x - padding,
            y: bbox.y - padding,
            width: bbox.width + (padding * 2),
            height: bbox.height + (padding * 2)
          };
        } catch (fallbackError) {
          // Last resort: use getBoundingClientRect()
          // This gives us the pixel bounding box in viewport coordinates
          const rect = svg.getBoundingClientRect();

          // For SVGs without viewBox, this gives us the rendered size
          // We'll assume origin at (0, 0)
          return {
            x: 0,
            y: 0,
            width: Math.ceil(rect.width),
            height: Math.ceil(rect.height)
          };
        }
      }
    });

    // Validate bbox
    if (!bbox || typeof bbox.width !== 'number' || typeof bbox.height !== 'number') {
      throw new Error('Invalid bounding box calculated');
    }

    if (bbox.width <= 0 || bbox.height <= 0) {
      throw new Error(`Invalid bounding box dimensions: width=${bbox.width}, height=${bbox.height}`);
    }

    // Add safety padding to prevent clipping from anti-aliasing or rendering differences
    // Why: getBBox() returns the *exact* bounds, but rendering might need a pixel or two extra
    //      especially for anti-aliased edges, stroke caps, and line joins
    const SAFETY_PADDING = 2;  // pixels on each side

    // Round coordinates to avoid floating point precision issues
    // Why: viewBox values should be clean numbers for svg2fbf
    const result = {
      x: Math.floor((bbox.x - SAFETY_PADDING) * 100) / 100,  // Expand left
      y: Math.floor((bbox.y - SAFETY_PADDING) * 100) / 100,  // Expand top
      width: Math.ceil((bbox.width + (SAFETY_PADDING * 2)) * 100) / 100,  // Wider
      height: Math.ceil((bbox.height + (SAFETY_PADDING * 2)) * 100) / 100  // Taller
    };

    return result;

  } catch (error) {
    throw new Error(`Failed to calculate bounding box: ${error.message}`);
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Parse command-line arguments
const args = process.argv.slice(2);

if (args.length !== 1) {
  console.error('Usage: node calculate_bbox.js <svg_path>');
  console.error('');
  console.error('Calculates the bounding box of an SVG file including fill, stroke, and markers.');
  console.error('Outputs JSON to stdout: {"x": 0, "y": 0, "width": 800, "height": 600}');
  process.exit(1);
}

const [svgPath] = args;

// Execute bbox calculation
calculateBBox(svgPath)
  .then((bbox) => {
    // Output JSON to stdout for Python to parse
    console.log(JSON.stringify(bbox));
    process.exit(0);
  })
  .catch((error) => {
    console.error(`❌ Error: ${error.message}`);
    process.exit(1);
  });
