const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Fix semi-transparent backgrounds that the first regex missed
  content = content.replace(/bg-\[\#171717\]\/50/g, 'bg-[#1A5140]/50');
  content = content.replace(/bg-\[\#171717\]\/80/g, 'bg-[#1A5140]/80');
  content = content.replace(/bg-\[\#171717\]\/90/g, 'bg-[#1A5140]/90');
  
  content = content.replace(/bg-\[\#262626\]\/50/g, 'bg-[#288760]/50');
  
  // Fix text that might still be grey
  content = content.replace(/text-gray-400/g, 'text-[#34C759]/80');
  content = content.replace(/text-gray-300/g, 'text-[#34C759]');
  content = content.replace(/text-gray-200/g, 'text-white');
  content = content.replace(/text-gray-500/g, 'text-[#5CA87C]');
  
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
