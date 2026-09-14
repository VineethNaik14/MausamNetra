const fs = require('fs');

let content = fs.readFileSync('src/maps/IncidentMap.tsx', 'utf8');

// Replace CircleMarker usage with Marker + divIcon
const oldMarker = `{userLocation && (
        <CircleMarker 
          center={userLocation} 
          radius={8}
          pathOptions={{ fillColor: '#F498AE', color: '#F4F6F6', weight: 2, opacity: 1, fillOpacity: 1, className: 'user-location-pulse' }}
        >
          <Popup>
            <div className="text-[#161616] font-medium text-sm">You are here</div>
          </Popup>
        </CircleMarker>
      )}`;

const newMarker = `      {userLocation && (
        <Marker 
          position={userLocation} 
          zIndexOffset={1000}
          icon={L.divIcon({
            html: \`
              <div class="user-location-marker-container">
                <div class="user-location-ring"></div>
                <div class="user-location-dot"></div>
              </div>
            \`,
            className: '',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          })}
        >
          <Popup>
            <div className="text-[#161616] font-medium text-sm">You are here</div>
          </Popup>
        </Marker>
      )}`;

content = content.replace(oldMarker, newMarker.trim());
fs.writeFileSync('src/maps/IncidentMap.tsx', content);

// Update CSS
let cssContent = fs.readFileSync('src/index.css', 'utf8');
const newCss = `
/* Stable HTML User Location Marker */
.user-location-marker-container {
  position: relative;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-location-dot {
  width: 14px;
  height: 14px;
  background-color: #F498AE;
  border: 2.5px solid #F4F6F6;
  border-radius: 50%;
  z-index: 2;
  box-shadow: 0 0 6px rgba(0,0,0,0.4);
}

.user-location-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 24px;
  height: 24px;
  margin-top: -12px;
  margin-left: -12px;
  background-color: #F498AE;
  border-radius: 50%;
  z-index: 1;
  animation: user-ring-pulse 2s ease-out infinite;
}

@keyframes user-ring-pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  100% {
    transform: scale(3);
    opacity: 0;
  }
}
`;

cssContent += newCss;
fs.writeFileSync('src/index.css', cssContent);
