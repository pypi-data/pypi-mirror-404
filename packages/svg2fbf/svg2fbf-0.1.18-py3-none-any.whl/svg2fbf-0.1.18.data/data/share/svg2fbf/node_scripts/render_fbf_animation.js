/**
 * render_fbf_animation.js
 *
 * Captures frames from FBF SVG animation using Puppeteer and headless Chrome
 *
 * The FBF format uses SMIL animation with animation_type="once", meaning:
 * - Animation plays once from start to finish
 * - Uses discrete frame switching (no interpolation)
 * - Auto-starts (no click required)
 *
 * Usage:
 *   node render_fbf_animation.js <fbf_svg_path> <output_dir> <frame_count> <fps> <width> <height>
 *
 * Example:
 *   node render_fbf_animation.js animation.fbf.svg ./output 10 10 1920 1080
 *
 * Output:
 *   Creates frame_0001.png, frame_0002.png, ... in output_dir
 *
 * Exit codes:
 *   0 - Success
 *   1 - Error (with error message to stderr)
 */

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

/**
 * Capture frames from FBF animation
 *
 * @param {string} fbfPath - Path to FBF SVG file
 * @param {string} outputDir - Directory to save frame PNGs
 * @param {number} frameCount - Number of frames to capture
 * @param {number} fps - Frames per second (must match svg2fbf --speed argument)
 * @param {number} width - Viewport width in pixels
 * @param {number} height - Viewport height in pixels
 */
async function captureAnimationFrames(fbfPath, outputDir, frameCount, fps, width, height) {
  let browser = null;

  try {
    // Ensure output directory exists
    // Why: Need place to save captured frames
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Launch headless Chrome
    // Why: Need browser to render SMIL animations
    browser = await puppeteer.launch({
      headless: 'new',
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-web-security',
        '--force-color-profile=srgb',
        '--autoplay-policy=no-user-gesture-required'  // Why: Allow SMIL animations to auto-start
      ]
    });

    const page = await browser.newPage();

    // Set viewport
    // Why: Consistent rendering dimensions for pixel-perfect comparison
    await page.setViewport({
      width: parseInt(width),
      height: parseInt(height),
      deviceScaleFactor: 1
    });

    // Read FBF SVG file
    // Why: Need to embed in HTML for rendering
    if (!fs.existsSync(fbfPath)) {
      throw new Error(`FBF SVG file not found: ${fbfPath}`);
    }

    const svgContent = fs.readFileSync(fbfPath, 'utf-8');

    // Create HTML wrapper
    // Why: Puppeteer needs HTML context
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

    // Load HTML with FBF SVG
    // Why: Start the SMIL animation
    await page.setContent(htmlContent, {
      waitUntil: 'networkidle0'
    });

    // Wait for fonts to load
    // Why: Fonts must be loaded before accurate rendering
    await page.evaluateHandle('document.fonts.ready');

    // Calculate frame timing
    // Why: Need to capture at exact frame boundaries
    const frameDuration = 1000 / parseFloat(fps);  // milliseconds per frame

    console.log(`📹 Capturing ${frameCount} frames at ${fps} FPS (${frameDuration}ms per frame)...`);

    // DEBUG: Check animation status, restart it, and record start time
    // Why: SMIL animations might have already played or not started correctly
    // CRITICAL: Must record start time in SAME evaluate call to avoid network latency
    const { animationInfo, animationStartTime } = await page.evaluate(() => {
      // Find the PROSKENION use element
      const proskenion = document.getElementById('PROSKENION');
      if (!proskenion) return { animationInfo: { error: 'PROSKENION not found' }, animationStartTime: 0 };

      // Find the animate element
      const animateElement = proskenion.querySelector('animate');
      if (!animateElement) return { animationInfo: { error: 'animate element not found' }, animationStartTime: 0 };

      // Check current animation state
      const currentHref = proskenion.getAttribute('href') || proskenion.getAttributeNS('http://www.w3.org/1999/xlink', 'href');

      // Force restart the animation by calling beginElement()
      // Why: Ensures animation starts fresh from frame 0
      animateElement.beginElement();

      // Record start time IMMEDIATELY after beginElement()
      // Why: Avoid network latency between separate evaluate() calls (~100ms delay causes +1 frame shift!)
      const startTime = performance.now();

      return {
        animationInfo: {
          currentHref: currentHref,
          animationBegin: animateElement.getAttribute('begin'),
          animationDur: animateElement.getAttribute('dur'),
          animationValues: animateElement.getAttribute('values'),
          restarted: true
        },
        animationStartTime: startTime
      };
    });

    console.log(`  📊 Animation info:`, animationInfo);

    // Wait briefly for first frame to render after restart
    // Why: Give browser time to paint first frame after beginElement()
    const initializationDelay = Math.min(frameDuration * 0.3, 50);
    await new Promise(resolve => setTimeout(resolve, initializationDelay));

    // Capture each frame
    // Why: Compare these with input SVG renders pixel-by-pixel
    for (let i = 0; i < frameCount; i++) {
      // Calculate target time for this frame
      // Why: Frame i should be captured at (i * frameDuration) + (frameDuration / 2)
      //      The +frameDuration/2 captures the middle of the frame, avoiding edge artifacts
      const targetTime = (i * frameDuration) + (frameDuration / 2);

      // Wait until we reach the target time
      // Why: Must capture at exact moment to get correct frame
      const currentTime = await page.evaluate(() => performance.now());
      const waitTime = Math.max(0, targetTime - (currentTime - animationStartTime));

      if (waitTime > 0) {
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }

      // Capture frame
      // Note: Removed extra 50ms wait that was causing +50ms timing offset
      // The waitTime calculation already ensures we're at the correct frame time
      // Why: This PNG represents what FBF animation shows at this frame
      const frameNumber = String(i + 1).padStart(4, '0');
      const framePath = path.join(outputDir, `frame_${frameNumber}.png`);

      await page.screenshot({
        path: framePath,
        type: 'png',
        omitBackground: true
      });

      console.log(`  ✓ Frame ${i + 1}/${frameCount} captured (${targetTime.toFixed(1)}ms)`);
    }

    console.log(`✅ All ${frameCount} frames captured successfully`);

  } catch (error) {
    console.error(`❌ Error capturing animation frames: ${error.message}`);
    throw error;
  } finally {
    // Always close browser
    // Why: Prevent resource leaks
    if (browser) {
      await browser.close();
    }
  }
}

// Parse command-line arguments
// Why: Called from Python with these parameters
const args = process.argv.slice(2);

if (args.length !== 6) {
  console.error('Usage: node render_fbf_animation.js <fbf_svg_path> <output_dir> <frame_count> <fps> <width> <height>');
  process.exit(1);
}

const [fbfPath, outputDir, frameCount, fps, width, height] = args;

// Execute frame capture
captureAnimationFrames(fbfPath, outputDir, frameCount, fps, width, height)
  .then(() => {
    process.exit(0);
  })
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
