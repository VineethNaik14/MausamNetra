const fs = require('fs');

let content = fs.readFileSync('src/maps/IncidentMap.tsx', 'utf8');

// We need to import CircleMarker and Navigation
// `import { AlertTriangle, MapPin, Info, X } from 'lucide-react';` -> add Navigation
content = content.replace(/import \{ AlertTriangle, MapPin, Info, X \} from 'lucide-react';/, "import { AlertTriangle, MapPin, Info, X, Navigation } from 'lucide-react';");

// `import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';` -> add CircleMarker
content = content.replace(/import \{ MapContainer, TileLayer, Marker, Popup, useMap \} from 'react-leaflet';/, "import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';");

// Define UserLocationControl component
const userLocationComponent = `
function UserLocationControl() {
  const map = useMap();
  const [userLocation, setUserLocation] = useState<[number, number] | null>(null);
  const [isLocating, setIsLocating] = useState(false);

  const handleLocate = () => {
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const loc: [number, number] = [position.coords.latitude, position.coords.longitude];
        setUserLocation(loc);
        map.flyTo(loc, 10, { duration: 1.5 });
        setIsLocating(false);
      },
      (error) => {
        console.error('Error getting location', error);
        alert('Unable to retrieve your location');
        setIsLocating(false);
      },
      { enableHighAccuracy: true }
    );
  };

  return (
    <>
      <div className="absolute top-4 left-4 z-[400]">
        <button
          onClick={(e) => { e.stopPropagation(); handleLocate(); }}
          className={\`p-3 bg-[#222222] border border-[#F498AE]/40 rounded-full shadow-xl hover:bg-[#F498AE] hover:text-[#161616] text-[#F498AE] transition-all \${isLocating ? 'animate-pulse' : ''}\`}
          title="Locate Me"
        >
          <Navigation className="h-5 w-5" />
        </button>
      </div>
      {userLocation && (
        <CircleMarker 
          center={userLocation} 
          radius={8}
          pathOptions={{ fillColor: '#F498AE', color: '#F4F6F6', weight: 2, opacity: 1, fillOpacity: 1 }}
        >
          <Popup>
            <div className="text-[#161616] font-medium text-sm">You are here</div>
          </Popup>
        </CircleMarker>
      )}
    </>
  );
}
`;

content = content.replace('export function IncidentMap', userLocationComponent + '\nexport function IncidentMap');

// Insert <UserLocationControl /> inside MapContainer
content = content.replace(/<MapController selectedEventId=\{selectedEventId\} events=\{events\} \/>/g, '<MapController selectedEventId={selectedEventId} events={events} />\n        <UserLocationControl />');

fs.writeFileSync('src/maps/IncidentMap.tsx', content);
