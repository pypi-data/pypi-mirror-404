const puppeteer = require('puppeteer');
const fs = require('fs');

async function test() {
  const browser = await puppeteer.launch({ headless: 'new' });
  const page = await browser.newPage();
  
  // Enable console logging from the page
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  
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
          console.log('HTML loaded');
          const svg = document.querySelector('svg');
          console.log('SVG element found:', !!svg);
          console.log('SVG has onload attr:', svg && svg.hasAttribute('onload'));
          
          // Manually dispatch load event
          const loadEvent = new Event('load', { bubbles: false, cancelable: false });
          svg.dispatchEvent(loadEvent);
          console.log('Load event dispatched');
          
          setTimeout(() => {
            const paths = document.querySelectorAll('path');
            console.log('Path elements after 500ms:', paths.length);
          }, 500);
          
          setTimeout(() => {
            const paths = document.querySelectorAll('path');
            console.log('Path elements after 2s:', paths.length);
          }, 2000);
        </script>
      </body>
    </html>
  `;
  
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 3000));
  
  await browser.close();
}

test().catch(console.error);
