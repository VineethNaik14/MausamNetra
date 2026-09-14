const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let originalContent = content;

  // 1. Protect text colors on current Mustard Yellow buttons 
  // Currently they are bg-[#34C759] with text-[#1C2833]. 
  // When inverted, they become Teal buttons, so text should become White.
  content = content.replace(/className="([^"]*bg-\[\#34C759\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__BTN_TEXT__]');
    return `className="${updated}"`;
  });
  content = content.replace(/className=\{`([^`]*bg-\[\#34C759\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#1C2833\]/g, 'text-[__BTN_TEXT__]');
    return `className={\`${updated}\`}`;
  });

  // 2. Swap core hex codes using placeholders
  const replacements = [
    { regex: /#24313D/gi, replacement: '__BG_MAIN__' },
    { regex: /#24313D/gi, replacement: '__BG_CARD__' },
    { regex: /#1C2833/gi, replacement: '__BG_DEEP__' },
    { regex: /#34C759/gi, replacement: '__ACCENT__' },
    { regex: /#E8C15A/gi, replacement: '__ACCENT_HOVER__' },
    { regex: /#F4F6F6/gi, replacement: '__TEXT_LIGHT__' },
    { regex: /#D1D1D1/gi, replacement: '__TEXT_MUTED__' },
  ];
  
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  // 3. Resolve placeholders to the INVERTED theme
  const finalReplacements = [
    { regex: /__BG_MAIN__/g, replacement: '#34C759' },        // Main BG -> Mustard
    { regex: /__BG_CARD__/g, replacement: '#EAC864' },        // Cards -> Light Mustard
    { regex: /__BG_DEEP__/g, replacement: '#C4982C' },        // Deep elements -> Dark Mustard
    { regex: /__ACCENT__/g, replacement: '#24313D' },         // Accent/Buttons -> Teal
    { regex: /__ACCENT_HOVER__/g, replacement: '#24313D' },   // Hover -> Dark Teal
    { regex: /__TEXT_LIGHT__/g, replacement: '#1C2833' },     // Light Text -> Deep Teal
    { regex: /__TEXT_MUTED__/g, replacement: '#24313D' },     // Muted Text -> Teal
    { regex: /__BTN_TEXT__/g, replacement: '#F4F6F6' },       // Button Text -> White
  ];
  
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

walkDir('./src');
console.log('Colors inverted successfully.');
