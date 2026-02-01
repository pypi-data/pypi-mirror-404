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
          
          // Check if there are any path elements initially
          setTimeout(() => {
            const paths = document.querySelectorAll('path');
            console.log('Path elements after 1s:', paths.length);
          }, 1000);
          
          setTimeout(() => {
            const paths = document.querySelectorAll('path');
            console.log('Path elements after 3s:', paths.length);
          }, 3000);
        </script>
      </body>
    </html>
  `;
  
  await page.setContent(htmlContent, { waitUntil: 'networkidle0' });
  await new Promise(r => setTimeout(r, 4000));
  
  await browser.close();
}

test().catch(console.error);
