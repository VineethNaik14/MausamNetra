const fs = require('fs');

let cssContent = fs.readFileSync('src/index.css', 'utf8');
// Fix the bg-3d-texture that was mangled by the inversion/reversion script
const textureCSS = `
/* 3D Isometric Cube Texture */
.bg-3d-texture {
  background-color: #24313D;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='103.92' viewBox='0 0 60 103.92' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23073839' fill-opacity='0.25'%3E%3Cpolygon points='30 103.92 0 86.6 0 51.96 30 69.28'/%3E%3Cpolygon points='30 34.64 0 51.96 30 69.28 60 51.96'/%3E%3Cpolygon points='30 51.96 0 34.64 0 0 30 17.32'/%3E%3Cpolygon points='30 -17.32 0 0 30 17.32 60 0'/%3E%3C/g%3E%3Cg fill='%230f7476' fill-opacity='0.25'%3E%3Cpolygon points='30 69.28 60 51.96 60 86.6 30 103.92'/%3E%3Cpolygon points='30 17.32 60 0 60 34.64 30 51.96'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  background-attachment: fixed;
}
`;

cssContent = cssContent.replace(/\/\* 3D Isometric Cube Texture \*\/[\s\S]*?\}\n/m, textureCSS);

fs.writeFileSync('src/index.css', cssContent);

