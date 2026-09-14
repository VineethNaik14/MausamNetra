const fs = require('fs');
const path = require('path');

function replaceInFile(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');

  // Colors to replace
  const replacements = [
    { regex: /#161616/gi, replacement: '#24313D' },   // Deep Dark Background -> Dark Teal
    { regex: /#222222/gi, replacement: '#24313D' },   // Elevated Card Backgrounds -> Teal
    { regex: /#0F0F0F/gi, replacement: '#1C2833' },   // Deepest elements -> Deep Teal
    { regex: /#F498AE/gi, replacement: '#34C759' },   // Accent Pink -> Mustard Yellow
    { regex: /#F7B5C6/gi, replacement: '#E8C15A' },   // Hover Accent Pink -> Lighter Mustard
  ];

  let originalContent = content;
  replacements.forEach(({ regex, replacement }) => {
    content = content.replace(regex, replacement);
  });

  // Fix contrast for text on Mustard Yellow backgrounds
  // Find any className that contains bg-[#34C759] and replace text-[#F4F6F6] with text-[#1C2833] inside it
  content = content.replace(/className="([^"]*bg-\[\#34C759\][^"]*)"/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[#1C2833]');
    return `className="${updated}"`;
  });
  
  // Also handle conditional classNames like: className={`... bg-[#34C759] ...`}
  content = content.replace(/className=\{`([^`]*bg-\[\#34C759\][^`]*)`\}/g, (match, p1) => {
    let updated = p1.replace(/text-\[\#F4F6F6\]/g, 'text-[#1C2833]');
    return `className={\`${updated}\`}`;
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
console.log('Teal and Mustard theme applied successfully.');
