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
          const svg = document.querySelector('svg');
          const onloadAttr = svg.getAttribute('onload');
          console.log('onload attribute value:', onloadAttr);
          
          // Try to find the function
          console.log('typeof onLoad:', typeof onLoad);
          console.log('typeof window.onLoad:', typeof window.onLoad);
          
          // Dispatch load event
          const loadEvent = new Event('load', { bubbles: false, cancelable: false });
          try {
            svg.dispatchEvent(loadEvent);
            console.log('Load event dispatched successfully');
          } catch (e) {
            console.log('Error dispatching:', e.message);
          }
          
          setTimeout(() => {
            const paths = document.querySelectorAll('path');
            console.log('Path count:', paths.length);
          }, 1000);
        </script>
      </body>
    </html>
  `;
  
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 2000));
  
  await browser.close();
}

test().catch(console.error);
