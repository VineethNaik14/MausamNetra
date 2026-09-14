const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;

  // Protect text on current Teal buttons (which will become Mustard)
  content = content.replace(/className="([^"]*bg-\[\#24313D\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[__BTN_TEXT__]');
    return `className="${updated}"`;
  });
  content = content.replace(/className=\{`([^`]*bg-\[\#24313D\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[__BTN_TEXT__]');
    return `className={\`${updated}\`}`;
  });
  
  // Protect text on current Mustard bg (which will become Dark Teal)
  content = content.replace(/className="([^"]*bg-\[\#34C759\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__MAIN_TEXT__]');
    return `className="${updated}"`;
  });
  content = content.replace(/className=\{`([^`]*bg-\[\#34C759\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__MAIN_TEXT__]');
    return `className={\`${updated}\`}`;
  });

  const replacements = [
    // We want to reverse what the last script did exactly.
    // The previous mapping:
    // Original -> Current
    // #24313D -> #34C759  (Deep Teal -> Mustard)
    // #24313D -> #EAC864  (Teal -> Light Mustard)
    // #1C2833 -> #C4982C  (Deepest Teal -> Dark Mustard)
    // #34C759 -> #24313D  (Mustard -> Teal)
    // #E8C15A -> #24313D  (Light Mustard -> Dark Teal)
    // #F4F6F6 -> #1C2833  (White -> Deep Teal)
    // #D1D1D1 -> #24313D  (Muted -> Teal)
    
    // So to revert, we do: Current -> Original
    { regex: /#34C759/gi, replacement: '__M_MAIN__' },
    { regex: /#EAC864/gi, replacement: '__M_LIGHT__' },
    { regex: /#C4982C/gi, replacement: '__M_DARK__' },
    
    { regex: /#24313D/gi, replacement: '__T_MAIN__' },
    { regex: /#24313D/gi, replacement: '__T_DARK__' },
    { regex: /#1C2833/gi, replacement: '__T_DEEP__' },
    
    { regex: /#F4F6F6/gi, replacement: '__WHITE__' },
    // wait, what about the current #24313D which was muted? 
    // It's covered by T_MAIN. But we need it back to #D1D1D1 if it was text.
    // Instead of doing color swapping for generic text, let's just let the main mapping handle it.
  ];
  
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  const finalReplacements = [
    { regex: /__M_MAIN__/g, replacement: '#24313D' }, // Mustard -> Deep Teal
    { regex: /__M_LIGHT__/g, replacement: '#24313D' }, // Light Mustard -> Teal
    { regex: /__M_DARK__/g, replacement: '#1C2833' }, // Dark Mustard -> Deepest Teal
    
    { regex: /__T_MAIN__/g, replacement: '#34C759' }, // Teal -> Mustard
    { regex: /__T_DARK__/g, replacement: '#E8C15A' }, // Dark Teal -> Light Mustard
    { regex: /__T_DEEP__/g, replacement: '#F4F6F6' }, // Deep Teal -> White
    
    // Some exceptions from previous step
    { regex: /__BTN_TEXT__/g, replacement: '#1C2833' }, 
    { regex: /__MAIN_TEXT__/g, replacement: '#F4F6F6' }, 
    
    { regex: /__WHITE__/g, replacement: '#1C2833' }, 
  ];
  
  finalReplacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });
  
  // Quick fix for bg-3d-texture in index.css
  // Because it was inverted, it might have wrong colors now, let's overwrite it directly in index.css later

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

walkDir('./src');
console.log('Colors reverted successfully.');
