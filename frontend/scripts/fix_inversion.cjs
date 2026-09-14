const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  
  // The main backgrounds were accidentally made pink (bg-[#F498AE]). Let's fix them to bg-[#161616].
  // Specifically:
  // min-h-screen bg-[#F498AE] -> min-h-screen bg-[#161616]
  // h-screen w-screen bg-[#F498AE] -> h-screen w-screen bg-[#161616]
  // flex-1 overflow-auto p-4 md:p-6 bg-[#F498AE] -> bg-[#161616]
  content = content.replace(/min-h-screen bg-\[\#F498AE\]/g, 'min-h-screen bg-[#161616]');
  content = content.replace(/h-screen w-screen bg-\[\#F498AE\]/g, 'h-screen w-screen bg-[#161616]');
  content = content.replace(/overflow-auto p-4 md:p-6 bg-\[\#F498AE\]/g, 'overflow-auto p-4 md:p-6 bg-[#161616]');
  
  // Navbar
  // nav className="bg-[#F498AE] -> nav className="bg-[#161616]
  content = content.replace(/<nav className="bg-\[\#F498AE\]/g, '<nav className="bg-[#161616]');
  
  // Dropdown menu
  // w-56 bg-[#F498AE] border -> w-56 bg-[#222222] border
  content = content.replace(/w-56 bg-\[\#F498AE\] border/g, 'w-56 bg-[#222222] border');

  // Let's also check other layout backgrounds
  // In UserLogin.tsx and AdminLogin.tsx, the background is in min-h-screen bg-[#F498AE] (already covered)
  // But there's a card inside it: bg-[#F498AE] p-3 rounded-xl
  content = content.replace(/bg-\[\#F498AE\] p-3 rounded-xl/g, 'bg-[#222222] p-3 rounded-xl');

  // IncidentDetail.tsx
  // bg-[#F498AE] p-5 rounded-xl -> bg-[#222222] p-5 rounded-xl
  content = content.replace(/bg-\[\#F498AE\] p-5 rounded-xl/g, 'bg-[#222222] p-5 rounded-xl');
  
  // PublicDashboard.tsx
  // select className="... bg-[#F498AE]" -> bg-[#222222]
  content = content.replace(/py-2 bg-\[\#F498AE\] border border-\[\#F498AE\]\/20 text-\[\#F4F6F6\]/g, 'py-2 bg-[#222222] border border-[#F498AE]/20 text-[#F4F6F6]');

  // What about buttons? "px-4 py-2 bg-[#F498AE] text-[#F4F6F6]" -> these SHOULD be pink! So keep them.
  // Wait, I replaced "py-2 bg-[#F498AE]" which might hit buttons.
  // Let's revert that and be specific.
  
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
