const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace Base Backgrounds with Jade Gradients or Solid Jade
  // Using #1A5140 (darkest) and #288760 (medium dark) for backgrounds
  content = content.replace(/bg-\[\#171717\]/g, 'bg-gradient-to-br from-[#1A5140] to-[#288760]');
  content = content.replace(/bg-\[\#262626\]/g, 'bg-[#288760]/40');
  content = content.replace(/hover:bg-\[\#262626\]/g, 'hover:bg-[#5CA87C]/30');
  
  // Replace Accents, Borders, Text with Lighter Jade Tones
  // Using #5CA87C (medium light) and #34C759 (lightest)
  content = content.replace(/border-\[\#F25623\]/g, 'border-[#34C759]');
  content = content.replace(/bg-\[\#F25623\]/g, 'bg-[#5CA87C]');
  content = content.replace(/hover:bg-\[\#d14417\]/g, 'hover:bg-[#34C759] hover:text-[#1A5140]');
  content = content.replace(/text-\[\#F25623\]/g, 'text-[#34C759]');
  content = content.replace(/ring-\[\#F25623\]/g, 'ring-[#34C759]');
  content = content.replace(/shadow-\[\#F25623\]/g, 'shadow-[#1A5140]');
  
  // Clean up any double backgrounds that might occur from regex
  content = content.replace(/bg-gradient-to-br from-\[\#1A5140\] to-\[\#288760\]\/50/g, 'bg-[#1A5140]/50');
  content = content.replace(/bg-gradient-to-br from-\[\#1A5140\] to-\[\#288760\]\/80/g, 'bg-[#1A5140]/80');
  content = content.replace(/bg-gradient-to-br from-\[\#1A5140\] to-\[\#288760\]\/90/g, 'bg-[#1A5140]/90');
  
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
console.log('Colors updated to Jade Horizon palette successfully.');
