const fs = require('fs');

const content = `import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { IncidentEvent } from '../types';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, MapPin, Info, X } from 'lucide-react';

const colorMap: Record<string, string> = {
  'Flood': '#ef4444',
  'Heavy Rain': '#f97316',
  'Heatwave': '#eab308',
  'Thunderstorm': '#3b82f6',
  'Fog': '#a855f7',
  'Other': '#6b7280'
};

const getEventImage = (type: string) => {
  const imageMap: Record<string, string> = {
    'Flood': 'https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&q=80&w=400',
    'Heavy Rain': 'https://images.unsplash.com/photo-1515694346937-94d85e41e6f0?auto=format&fit=crop&q=80&w=400',
    'Heatwave': 'https://images.unsplash.com/photo-1524222717473-730000096953?auto=format&fit=crop&q=80&w=400',
    'Thunderstorm': 'https://images.unsplash.com/photo-1605727216801-e27ce1d0ce49?auto=format&fit=crop&q=80&w=400',
    'Fog': 'https://images.unsplash.com/photo-1485236715568-ddc5ee6ca227?auto=format&fit=crop&q=80&w=400',
  };
  return imageMap[type] || 'https://images.unsplash.com/photo-1580193769210-b8d1c049a7d9?auto=format&fit=crop&q=80&w=400';
};

// Custom component to handle flyTo when a marker is clicked
function MapController({ selectedEventId, events }: { selectedEventId: string | null, events: IncidentEvent[] }) {
  const map = useMap();
  useEffect(() => {
    if (selectedEventId) {
      const event = events.find(e => e.id === selectedEventId);
      if (event) {
        map.flyTo([event.location.lat, event.location.lng], 8, { duration: 1.5 });
      }
    }
  }, [selectedEventId, map, events]);
  return null;
}

export function IncidentMap({ events }: { events: IncidentEvent[] }) {
  const navigate = useNavigate();
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const selectedEvent = events.find(e => e.id === selectedEventId);

  const handleClosePanel = () => {
    setSelectedEventId(null);
  };

  const createCustomIcon = (type: string, isSelected: boolean) => {
    const color = colorMap[type] || colorMap['Other'];
    const scale = isSelected ? 'scale(1.2) translateY(-4px)' : 'scale(1) translateY(0)';
    
    const html = \`
      <div style="position: relative; width: 32px; height: 32px; transform-style: preserve-3d; transition: transform 0.2s; transform: \${scale};">
        <div style="position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); width: 16px; height: 8px; background: radial-gradient(ellipse at center, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 70%);"></div>
        <div style="position: relative; width: 32px; height: 32px; background-color: \${color}; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
          <div style="width: 12px; height: 12px; background-color: white; border-radius: 50%; transform: rotate(45deg);"></div>
        </div>
      </div>
    \`;

    return L.divIcon({
      html,
      className: 'custom-leaflet-icon',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
  };

  // Center of India roughly
  const defaultCenter: [number, number] = [20.5937, 78.9629];

  return (
    <div className="relative w-full h-full bg-[#363636] rounded-xl overflow-hidden border border-[#92A9E1]/20 shadow-lg group">
      
      <MapContainer 
        center={defaultCenter} 
        zoom={4} 
        style={{ width: '100%', height: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapController selectedEventId={selectedEventId} events={events} />

        {events.map((event) => (
          <Marker 
            key={event.id}
            position={[event.location.lat, event.location.lng]}
            icon={createCustomIcon(event.event_type, selectedEventId === event.id)}
            eventHandlers={{
              click: () => {
                setSelectedEventId(event.id);
              },
            }}
          />
        ))}
      </MapContainer>

      {/* Selected Event Details Panel */}
      {selectedEvent && (
        <div className="absolute top-4 right-4 w-72 bg-[#202123]/95 backdrop-blur-xl border border-[#92A9E1]/20 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col transform transition-all duration-300 animate-in slide-in-from-right-8">
          <div className="relative h-32 w-full overflow-hidden">
            <button 
              onClick={handleClosePanel}
              className="absolute top-2 right-2 z-10 p-1.5 bg-[#202123]/80 hover:bg-[#202123]/90 rounded-full text-[#363636] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
            <img 
              src={getEventImage(selectedEvent.event_type)} 
              alt={selectedEvent.event_type}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-[#1A5140] to-transparent" />
            <div className="absolute top-2 left-2 bg-[#202123]/90 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border border-[#92A9E1]/40 shadow-md" style={{ color: colorMap[selectedEvent.event_type] || 'white' }}>
              {selectedEvent.event_type}
            </div>
          </div>
          
          <div className="p-4 flex-1">
            <h3 className="font-bold text-lg text-[#363636] mb-1">{selectedEvent.severity} Severity</h3>
            <p className="text-sm text-[#363636]/70 mb-4 flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {selectedEvent.location.city}, {selectedEvent.location.state}
            </p>
            
            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-[#202123]/90 p-2.5 rounded-lg border border-[#92A9E1]/20 text-center">
                <div className="text-xs text-[#92A9E1] mb-1 uppercase tracking-wider">Confidence</div>
                <div className="font-semibold text-[#363636] text-lg">{selectedEvent.confidence}%</div>
              </div>
              <div className="bg-[#202123]/90 p-2.5 rounded-lg border border-[#92A9E1]/20 text-center">
                <div className="text-xs text-[#92A9E1] mb-1 uppercase tracking-wider">Reports</div>
                <div className="font-semibold text-[#363636] text-lg">{selectedEvent.report_counts.total}</div>
              </div>
            </div>

            <button 
              onClick={() => navigate(\`/events/\${selectedEvent.id}\`)}
              className="w-full py-2.5 bg-[#92A9E1] hover:bg-[#A3B8F0] hover:text-[#363636]/80 text-[#363636] rounded-lg text-sm font-medium transition-colors shadow-lg shadow-[#363636]/20 cursor-pointer"
            >
              View Full Details
            </button>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-6 left-6 z-[40] bg-[#202123]/90 backdrop-blur-md border border-[#92A9E1]/20 rounded-lg p-4 shadow-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        <h4 className="text-xs font-semibold text-[#363636]/70 uppercase tracking-wider flex items-center gap-2 mb-3">
          <Info className="h-3.5 w-3.5" />
          Incident Legend
        </h4>
        <div className="grid grid-cols-2 gap-x-6 gap-y-2">
          {Object.entries(colorMap).map(([type, color]) => (
            <div key={type} className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full border border-[#92A9E1]/40 shadow-sm" 
                style={{ backgroundColor: color }}
              />
              <span className="text-sm text-[#363636]/90">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
`;

fs.writeFileSync('src/maps/IncidentMap.tsx', content);
