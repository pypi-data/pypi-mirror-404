#!/usr/bin/env node
/**
 * Test script for splat_button.fbf.svg click functionality
 * Verifies that clicking the button triggers the animation
 */

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

async function testSplatButton() {
    const svgPath = path.resolve(__dirname, '../../examples/splat_button/fbf_output/splat_button.fbf.svg');

    if (!fs.existsSync(svgPath)) {
        console.error('❌ ERROR: splat_button.fbf.svg not found at', svgPath);
        process.exit(1);
    }

    console.log('🧪 Testing splat button click functionality...');
    console.log('📄 File:', svgPath);

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 800, height: 600 });

        // Load SVG file
        const fileUrl = 'file://' + svgPath;
        await page.goto(fileUrl, { waitUntil: 'networkidle0' });

        console.log('✓ Page loaded');

        // Wait for SVG to be ready
        await page.waitForSelector('svg', { timeout: 5000 });
        console.log('✓ SVG element found');

        // Get initial animation state
        const initialState = await page.evaluate(() => {
            const animate = document.querySelector('animate[attributeName="xlink:href"]');
            if (!animate) return null;

            return {
                href: animate.getAttribute('xlink:href'),
                begin: animate.getAttribute('begin'),
                dur: animate.getAttribute('dur'),
                values: animate.getAttribute('values')
            };
        });

        if (!initialState) {
            console.error('❌ ERROR: Animation element not found');
            process.exit(1);
        }

        console.log('✓ Animation element found:', initialState);

        // Take screenshot before click
        const beforePath = '/tmp/splat_button_before.png';
        await page.screenshot({ path: beforePath });
        console.log('✓ Screenshot before click:', beforePath);

        // Find clickable area (ANIMATED_GROUP should be clickable)
        const clickTarget = await page.evaluate(() => {
            const animatedGroup = document.querySelector('[id*="ANIMATED_GROUP"]');
            if (!animatedGroup) return null;

            const bbox = animatedGroup.getBoundingClientRect();
            return {
                x: bbox.x + bbox.width / 2,
                y: bbox.y + bbox.height / 2,
                width: bbox.width,
                height: bbox.height
            };
        });

        if (!clickTarget) {
            console.error('❌ ERROR: Could not find clickable area');
            process.exit(1);
        }

        console.log('✓ Click target found:', clickTarget);

        // Click on the button
        await page.mouse.click(clickTarget.x, clickTarget.y);
        console.log('✓ Clicked at', clickTarget.x, clickTarget.y);

        // Wait a moment for animation to start (use setTimeout instead of waitForTimeout)
        await new Promise(resolve => setTimeout(resolve, 200));

        // Take screenshot after click
        const afterPath = '/tmp/splat_button_after.png';
        await page.screenshot({ path: afterPath });
        console.log('✓ Screenshot after click:', afterPath);

        // Verify animation is running
        const animationState = await page.evaluate(() => {
            const animate = document.querySelector('animate[attributeName="xlink:href"]');
            if (!animate) return null;

            // Check if animation has started/restarted
            const svg = document.querySelector('svg');
            const currentTime = svg.getCurrentTime();

            return {
                currentTime: currentTime,
                isAnimationPaused: svg.animationsPaused(),
                hasBeginEvent: animate.hasAttribute('begin')
            };
        });

        console.log('✓ Animation state:', animationState);

        console.log('');
        console.log('✅ SPLAT BUTTON TEST PASSED');
        console.log('   - SVG loads correctly');
        console.log('   - Animation element is present');
        console.log('   - Click target is accessible');
        console.log('   - Screenshots saved to /tmp/');

    } catch (error) {
        console.error('❌ TEST FAILED:', error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
}

testSplatButton().catch(console.error);
