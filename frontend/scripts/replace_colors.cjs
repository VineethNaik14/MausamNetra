const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Replace backgrounds
  content = content.replace(/bg-gray-950/g, 'bg-black');
  content = content.replace(/bg-gray-900/g, 'bg-black');
  content = content.replace(/bg-gray-800/g, 'bg-[#1a0006]');
  
  // Replace borders
  content = content.replace(/border-gray-800\/50/g, 'border-[#6D001A]/30');
  content = content.replace(/border-gray-800/g, 'border-[#6D001A]/50');
  content = content.replace(/border-gray-700/g, 'border-[#6D001A]');
  
  // Replace blue (primary buttons) with burgundy
  content = content.replace(/bg-blue-600/g, 'bg-[#6D001A]');
  content = content.replace(/hover:bg-blue-500/g, 'hover:bg-[#8A0021]');
  content = content.replace(/text-blue-400/g, 'text-[#ff6b8b]');
  content = content.replace(/text-blue-500/g, 'text-[#ff6b8b]');
  content = content.replace(/ring-blue-500/g, 'ring-[#6D001A]');
  content = content.replace(/border-blue-500/g, 'border-[#6D001A]');
  content = content.replace(/shadow-blue-900\/20/g, 'shadow-[#6D001A]/20');
  
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
console.log('Replaced colors successfully.');
