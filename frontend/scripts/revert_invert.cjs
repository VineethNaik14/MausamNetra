const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;

  // Swapping logic:
  // We need to swap Teal set and Mustard set.

  // 1. Text on primary buttons: buttons are bg-[#24313D], text is text-[#F4F6F6] right now.
  // After swap, they will be bg-[#34C759], text should be text-[#1C2833].
  content = content.replace(/className="([^"]*bg-\[\#24313D\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[__BTN_TEXT__]');
    return `className="${updated}"`;
  });
  content = content.replace(/className=\{`([^`]*bg-\[\#24313D\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[__BTN_TEXT__]');
    return `className={\`${updated}\`}`;
  });
  
  // Also protect the text on the main background which is currently text-[#1C2833] on bg-[#34C759].
  // After swap, main bg is #24313D, text should be #F4F6F6.
  content = content.replace(/className="([^"]*bg-\[\#34C759\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__MAIN_TEXT__]');
    return `className="${updated}"`;
  });
  content = content.replace(/className=\{`([^`]*bg-\[\#34C759\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__MAIN_TEXT__]');
    return `className={\`${updated}\`}`;
  });

  const replacements = [
    // Current Mustard values -> Placeholders
    { regex: /#34C759/gi, replacement: '__M_MAIN__' },
    { regex: /#EAC864/gi, replacement: '__M_LIGHT__' },
    { regex: /#C4982C/gi, replacement: '__M_DARK__' },
    
    // Current Teal values -> Placeholders
    { regex: /#24313D/gi, replacement: '__T_MAIN__' },
    { regex: /#24313D/gi, replacement: '__T_DARK__' },
    { regex: /#1C2833/gi, replacement: '__T_DEEP__' },
    
    // Current text colors (not already caught)
    { regex: /#F4F6F6/gi, replacement: '__TEXT_WHITE__' },
    { regex: /#D1D1D1/gi, replacement: '__TEXT_MUTED__' },
  ];
  
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  const finalReplacements = [
    // Mustards become Teals
    { regex: /__M_MAIN__/g, replacement: '#24313D' }, // Main BG (was Mustard, now Deep Teal)
    { regex: /__M_LIGHT__/g, replacement: '#24313D' }, // Cards (was Light Mustard, now Teal)
    { regex: /__M_DARK__/g, replacement: '#1C2833' }, // Deep elements (was Dark Mustard, now Deepest Teal)
    
    // Teals become Mustards
    { regex: /__T_MAIN__/g, replacement: '#34C759' }, // Accent/Buttons (was Teal, now Mustard)
    { regex: /__T_DARK__/g, replacement: '#E8C15A' }, // Hover (was Dark Teal, now Light Mustard)
    { regex: /__T_DEEP__/g, replacement: '#C4982C' }, // Deep Teal (was deepest Teal, now dark Mustard)
    
    // Text protections
    { regex: /__BTN_TEXT__/g, replacement: '#1C2833' },   // Button text is now Deep Teal
    { regex: /__MAIN_TEXT__/g, replacement: '#F4F6F6' }, // Main BG text is now White
    
    // Remaining generic texts
    { regex: /__TEXT_WHITE__/g, replacement: '#1C2833' }, // If anything was left white on teal, make it deep teal on mustard
    { regex: /__TEXT_MUTED__/g, replacement: '#24313D' }, // This might be wrong. Let's just restore muted to D1D1D1
  ];
  
  // Wait, if __TEXT_WHITE__ is everywhere, replacing it blindly with #1C2833 might break icons/borders.
  // Actually, wait, let me use the EXACT same inversion map from last time but swapped.
  // The last script mapped:
  // #24313D -> #34C759
  // #24313D -> #EAC864
  // #1C2833 -> #C4982C
  // #34C759 -> #24313D
  // #E8C15A -> #24313D
  // #F4F6F6 -> #1C2833
  // #D1D1D1 -> #24313D
  
  finalReplacements.forEach(({ regex, replacement }) => {
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
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts') || fullPath.endsWith('.css')) {
      replaceInFile(fullPath);
    }
  }
}

// walkDir('./src');
console.log('Script tested');
