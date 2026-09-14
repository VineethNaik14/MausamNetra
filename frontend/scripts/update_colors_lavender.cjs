const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // 1. Backgrounds
  // Main background (was dark jade gradient) -> Cream #E9DEC8
  content = content.replace(/bg-gradient-to-br from-\[\#1A5140\] to-\[\#288760\]/g, 'bg-[#E9DEC8]');
  
  // Overlays / Popups (was dark jade) -> Soft Graphite #363636
  content = content.replace(/bg-\[\#1A5140\]\/(50|80|90)/g, 'bg-[#363636]/$1');
  
  // Cards / Secondary Backgrounds -> Lavender Haze #92A9E1 (or white)
  // Let's use a mix: bg-[#92A9E1] for highlighted cards, white for regular.
  content = content.replace(/bg-\[\#288760\]\/40/g, 'bg-white/60');
  
  // Buttons / Highlights -> Soft Graphite
  content = content.replace(/bg-\[\#5CA87C\]/g, 'bg-[#363636]');
  
  // Minor background highlights
  content = content.replace(/bg-\[\#5CA87C\]\/10/g, 'bg-[#363636]/10');
  content = content.replace(/bg-\[\#5CA87C\]\/20/g, 'bg-[#363636]/20');
  content = content.replace(/bg-\[\#5CA87C\]\/50/g, 'bg-[#363636]/50');

  // Hover states for buttons
  content = content.replace(/hover:bg-\[\#34C759\]/g, 'hover:bg-[#202020]');
  
  // 2. Borders
  // Borders were light jade, now Graphite or Lavender
  content = content.replace(/border-\[\#34C759\]\/50/g, 'border-[#363636]/20');
  content = content.replace(/border-\[\#34C759\]\/30/g, 'border-[#363636]/10');
  content = content.replace(/border-\[\#34C759\]/g, 'border-[#363636]/40');

  // 3. Text Colors
  // Old text-white needs to be Graphite #363636 on light backgrounds, 
  // but if it's on a Graphite button, it needs to be Lavender #92A9E1 or Cream #E9DEC8
  // Since we don't know the context exactly, let's just make text-white -> text-[#363636]
  // and we will manually fix buttons if needed.
  content = content.replace(/text-white/g, 'text-[#363636]');
  
  // Accent Text (was medium jade) -> Lavender Haze
  content = content.replace(/text-\[\#5CA87C\]/g, 'text-[#92A9E1]');
  
  // General text (was light jade) -> Graphite
  content = content.replace(/text-\[\#34C759\]\/80/g, 'text-[#363636]/70');
  content = content.replace(/text-\[\#34C759\]/g, 'text-[#363636]/90');
  
  // Hover text on button
  content = content.replace(/hover:text-\[\#1A5140\]/g, 'hover:text-[#92A9E1]');
  
  // Fix specifically the buttons which now have bg-[#363636] and text-[#363636]
  // We want text-[#E9DEC8] or text-[#92A9E1] inside them.
  content = content.replace(/bg-\[\#363636\](\s+.*?)text-\[\#363636\]/g, 'bg-[#363636]$1text-[#E9DEC8]');

  // Shadows
  content = content.replace(/shadow-\[\#1A5140\]/g, 'shadow-[#363636]');
  
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
console.log('Colors updated to Lavender Haze / Soft Graphite palette successfully.');
