#!/usr/bin/env node

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

// Read SVG file
const svgPath = path.resolve(__dirname, '../assets/icon-design.svg');
const pngPath = path.resolve(__dirname, '../icon.png');

const svgBuffer = fs.readFileSync(svgPath);

// Convert SVG to PNG
sharp(svgBuffer, {
  density: 300
})
  .resize(1024, 1024)
  .png()
  .toFile(pngPath)
  .then(() => {
    const stats = fs.statSync(pngPath);
    const sizeKB = (stats.size / 1024).toFixed(2);
    console.log(`✓ Icon created: ${pngPath}`);
    console.log(`✓ Size: ${sizeKB} KB`);

    if (stats.size > 50000) {
      console.warn(`⚠ Warning: Icon size is ${sizeKB} KB (target: <50 KB)`);
    } else {
      console.log(`✓ Size is within target (<50 KB)`);
    }
  })
  .catch(err => {
    console.error('Error converting SVG to PNG:', err);
    process.exit(1);
  });
