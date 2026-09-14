const fs = require('fs');

// 1. Add CSS class for the 3D texture
let cssContent = fs.readFileSync('src/index.css', 'utf8');

const textureCSS = `
/* 3D Isometric Cube Texture */
.bg-3d-texture {
  background-color: #34C759;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='103.92' viewBox='0 0 60 103.92' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c4982c' fill-opacity='0.25'%3E%3Cpolygon points='30 103.92 0 86.6 0 51.96 30 69.28'/%3E%3Cpolygon points='30 34.64 0 51.96 30 69.28 60 51.96'/%3E%3Cpolygon points='30 51.96 0 34.64 0 0 30 17.32'/%3E%3Cpolygon points='30 -17.32 0 0 30 17.32 60 0'/%3E%3C/g%3E%3Cg fill='%23eac864' fill-opacity='0.25'%3E%3Cpolygon points='30 69.28 60 51.96 60 86.6 30 103.92'/%3E%3Cpolygon points='30 17.32 60 0 60 34.64 30 51.96'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  background-attachment: fixed;
}
`;

if (!cssContent.includes('bg-3d-texture')) {
  fs.appendFileSync('src/index.css', textureCSS);
}

// 2. Update layout files
const filesToUpdate = [
  'src/components/layout/PublicLayout.tsx',
  'src/components/layout/AdminLayout.tsx',
  'src/pages/admin/AdminLogin.tsx',
  'src/pages/UserLogin.tsx',
  'src/App.tsx'
];

filesToUpdate.forEach(file => {
  if (fs.existsSync(file)) {
    let content = fs.readFileSync(file, 'utf8');
    // Replace the main screen background
    content = content.replace(/className="min-h-screen bg-\[\#34C759\]/g, 'className="min-h-screen bg-[#34C759] bg-3d-texture');
    content = content.replace(/className="h-screen w-screen bg-\[\#34C759\]/g, 'className="h-screen w-screen bg-[#34C759] bg-3d-texture');
    
    // Also update AdminLayout inner container if it has bg-[#34C759]
    content = content.replace(/className="flex-1 overflow-auto p-4 md:p-6 bg-\[\#34C759\]"/g, 'className="flex-1 overflow-auto p-4 md:p-6 bg-[#34C759] bg-3d-texture"');

    fs.writeFileSync(file, content);
  }
});

console.log('3D texture applied successfully!');
