const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace Backgrounds
  content = content.replace(/bg-black/g, 'bg-[#171717]');
  content = content.replace(/bg-\[\#1a0006\]/g, 'bg-[#262626]');
  content = content.replace(/hover:bg-\[\#1a0006\]/g, 'hover:bg-[#262626]');
  
  // Replace Accents, Borders, Text
  content = content.replace(/border-\[\#6D001A\]/g, 'border-[#F25623]');
  content = content.replace(/bg-\[\#6D001A\]/g, 'bg-[#F25623]');
  content = content.replace(/hover:bg-\[\#8A0021\]/g, 'hover:bg-[#d14417]');
  content = content.replace(/hover:bg-\[\#4A0012\]/g, 'hover:bg-[#d14417]');
  content = content.replace(/text-\[\#ff6b8b\]/g, 'text-[#F25623]');
  content = content.replace(/ring-\[\#6D001A\]/g, 'ring-[#F25623]');
  content = content.replace(/shadow-\[\#6D001A\]/g, 'shadow-[#F25623]');
  
  fs.writeFileSync(filePath, content);
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
console.log('Colors updated to #171717 and #F25623 successfully.');
