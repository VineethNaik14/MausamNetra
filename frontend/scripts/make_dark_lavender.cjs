const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // Create temporary placeholders
  content = content.replace(/bg-\[\#E9DEC8\]/g, 'bg-TEMP-MAIN-BG');
  content = content.replace(/bg-\[\#363636\](?!\/)/g, 'bg-TEMP-BTN-BG');
  content = content.replace(/text-\[\#363636\]/g, 'text-TEMP-MAIN-TEXT');
  content = content.replace(/text-\[\#E9DEC8\]/g, 'text-TEMP-BTN-TEXT');
  
  // Text Colors
  content = content.replace(/text-TEMP-MAIN-TEXT\/70/g, 'text-[#E0E5F0]/70');
  content = content.replace(/text-TEMP-MAIN-TEXT\/90/g, 'text-[#E0E5F0]/90');
  content = content.replace(/text-TEMP-MAIN-TEXT/g, 'text-[#F5F5F7]');
  
  content = content.replace(/text-TEMP-BTN-TEXT\/70/g, 'text-[#363636]/70');
  content = content.replace(/text-TEMP-BTN-TEXT\/90/g, 'text-[#363636]/90');
  content = content.replace(/text-TEMP-BTN-TEXT/g, 'text-[#363636]');
  
  // Backgrounds
  content = content.replace(/bg-TEMP-MAIN-BG/g, 'bg-[#363636]'); // Main bg becomes Soft Graphite
  content = content.replace(/bg-TEMP-BTN-BG/g, 'bg-[#92A9E1]'); // Buttons become Lavender Haze
  
  // Cards
  content = content.replace(/bg-white\/60/g, 'bg-[#2A2B2E]');
  
  // Translucent backgrounds
  content = content.replace(/bg-\[\#363636\]\/10/g, 'bg-[#92A9E1]/10');
  content = content.replace(/bg-\[\#363636\]\/20/g, 'bg-[#92A9E1]/20');
  content = content.replace(/bg-\[\#363636\]\/50/g, 'bg-[#202123]/80');
  content = content.replace(/bg-\[\#363636\]\/80/g, 'bg-[#202123]/90');
  content = content.replace(/bg-\[\#363636\]\/90/g, 'bg-[#202123]/95');
  
  // Hover states
  content = content.replace(/hover:bg-\[\#202020\]/g, 'hover:bg-[#A3B8F0]'); // button hover
  content = content.replace(/hover:text-\[\#92A9E1\]/g, 'hover:text-[#363636]/80'); // button text hover
  
  // Borders
  content = content.replace(/border-\[\#363636\]\/10/g, 'border-[#92A9E1]/10');
  content = content.replace(/border-\[\#363636\]\/20/g, 'border-[#92A9E1]/20');
  content = content.replace(/border-\[\#363636\]\/40/g, 'border-[#92A9E1]/40');
  content = content.replace(/border-\[\#363636\]/g, 'border-[#92A9E1]/50');

  // Fix map hover that we messed up before
  content = content.replace(/hover:bg-white\/60/g, 'hover:bg-[#404040]');

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
console.log('Palette inverted to Dark Graphite & Lavender Haze successfully.');
