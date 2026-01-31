const puppeteer = require('puppeteer');
const fs = require('fs');

async function test() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Enable console and error logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', error => console.log('PAGE ERROR:', error.message));
  
  await page.setViewport({ width: 480, height: 360, deviceScaleFactor: 1 });
  
  const svgPath = '../../tests/sessions/test_session_004_284frames/input_frames/frame00001.svg';
  let svgContent = fs.readFileSync(svgPath, 'utf-8');
  
  const htmlContent = `
    <!DOCTYPE html>
    <html>
      <head><meta charset="UTF-8"></head>
      <body style="margin:0;padding:0;">
        ${svgContent}
        <script>
          setTimeout(() => {
            const scripts = document.querySelectorAll('script');
            console.log('Total script tags:', scripts.length);
            
            const svgScripts = document.querySelector('svg').querySelectorAll('script');
            console.log('Script tags inside SVG:', svgScripts.length);
            
            // Check if onLoad function exists
            console.log('onLoad defined:', typeof onLoad);
            console.log('window.onLoad defined:', typeof window.onLoad);
          }, 100);
        </script>
      </body>
    </html>
  `;
  
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 1000));
  
  await browser.close();
}

test().catch(console.error);
