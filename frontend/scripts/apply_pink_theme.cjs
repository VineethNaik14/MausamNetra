const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Colors to replace based on the image
  const replacements = [
    { regex: /#363636/gi, replacement: '#161616' },   // Deep Dark Background (from Soft Graphite)
    { regex: /#2A2B2E/gi, replacement: '#222222' },   // Elevated Card Backgrounds
    { regex: /#202123/gi, replacement: '#0F0F0F' },   // Deepest elements (Map overlays)
    { regex: /#92A9E1/gi, replacement: '#F498AE' },   // Accent Pink (from Lavender)
    { regex: /#A3B8F0/gi, replacement: '#F7B5C6' },   // Hover Accent Pink
    { regex: /#F5F5F7/gi, replacement: '#F4F6F6' },   // Stark White Text
    { regex: /#E0E5F0/gi, replacement: '#D1D1D1' },   // Muted Grey for secondary text
  ];

  let originalContent = content;
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  if (originalContent !== content) {
    fs.writeFileSync(filePath, content);
  }
}

function walkDir(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      walkDir(fullPath);
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      replaceInFile(fullPath);
    }
  }
}

walkDir('./src');
console.log('Palette inverted to Dark Grey and Bold Pink successfully.');
