const fs = require('fs');

let content = fs.readFileSync('src/maps/IncidentMap.tsx', 'utf8');

// The user wants a smooth and simple animation on the path element (the location marker).
// Let's add an SVG animation via CSS in the global styles.
// And update the pathOptions className to use that animation.

content = content.replace(
  "pathOptions={{ fillColor: '#F498AE', color: '#F4F6F6', weight: 2, opacity: 1, fillOpacity: 1 }}",
  "pathOptions={{ fillColor: '#F498AE', color: '#F4F6F6', weight: 2, opacity: 1, fillOpacity: 1, className: 'user-location-pulse' }}"
);

fs.writeFileSync('src/maps/IncidentMap.tsx', content);

// Now update index.css to add the animation
let cssContent = fs.readFileSync('src/index.css', 'utf8');

const cssAnimation = `

/* Smooth pulse animation for User Location Marker */
.user-location-pulse {
  animation: location-pulse 2s cubic-bezier(0.4, 0, 0.2, 1) infinite alternate;
  transform-origin: center;
  transform-box: fill-box;
}

@keyframes location-pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.6;
  }
  100% {
    transform: scale(1.1);
    opacity: 1;
  }
}
`;

if (!cssContent.includes('.user-location-pulse')) {
  fs.appendFileSync('src/index.css', cssAnimation);
}
