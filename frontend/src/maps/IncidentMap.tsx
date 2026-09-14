import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { IncidentEvent } from '../types';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle, MapPin, Info, X, Navigation,
  Waves, CloudRain, CloudLightning, Thermometer, CloudFog, Wind, Tornado, Zap, CloudSnow, HelpCircle,
} from 'lucide-react';
import { EVENT_COLORS, getEventColor } from '../lib/eventColors';

const EVENT_ICONS: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  'Flood': Waves,
  'Heavy Rainfall': CloudRain,
  'Thunderstorm': CloudLightning,
  'Heatwave': Thermometer,
  'Fog': CloudFog,
  'Dust Storm': Wind,
  'Strong Wind': Wind,
  'Cyclone': Tornado,
  'Lightning': Zap,
  'Hailstorm': CloudSnow,
  'Other': HelpCircle,
};

function getEventIcon(type: string) {
  return EVENT_ICONS[type] || HelpCircle;
}

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
          className={`p-3 bg-[#24313D] border border-[#34C759]/40 rounded-full shadow-xl hover:bg-[#34C759] hover:text-[#24313D] text-[#34C759] transition-all ${isLocating ? 'animate-pulse' : ''}`}
          title="Locate Me"
        >
          <Navigation className="h-5 w-5" />
        </button>
      </div>
      {userLocation && (
        <Marker
          position={userLocation}
          zIndexOffset={1000}
          icon={L.divIcon({
            html: `
              <div class="user-location-marker-container">
                <div class="user-location-ring"></div>
                <div class="user-location-dot"></div>
              </div>
            `,
            className: '',
            iconSize: [24, 24],
            iconAnchor: [12, 12]
          })}
        >
          <Popup>
            <div className="text-[#24313D] font-medium text-sm">You are here</div>
          </Popup>
        </Marker>
      )}
    </>
  );
}

export function IncidentMap({ events }: { events: IncidentEvent[] }) {
  const navigate = useNavigate();
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [legendOpen, setLegendOpen] = useState(true);

  const legendRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!legendOpen) return;
    const handleClickOutside = (e: MouseEvent) => {
      if (legendRef.current && !legendRef.current.contains(e.target as Node)) {
        setLegendOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [legendOpen]);
  const selectedEvent = events.find(e => e.id === selectedEventId);

  const handleClosePanel = () => {
    setSelectedEventId(null);
  };

  const createCustomIcon = (type: string, isSelected: boolean) => {
    const color = getEventColor(type);
    const scale = isSelected ? 'scale(1.2) translateY(-4px)' : 'scale(1) translateY(0)';
    const html = `
      <div style="position: relative; width: 32px; height: 32px; transform-style: preserve-3d; transition: transform 0.2s; transform: ${scale};">
        <div style="position: absolute; bottom: -8px; left: 50%; transform: translateX(-50%); width: 16px; height: 8px; background: radial-gradient(ellipse at center, rgba(0,0,0,0.6) 0%, rgba(0,0,0,0) 70%);"></div>
        <div style="position: relative; width: 32px; height: 32px; background-color: ${color}; border-radius: 50% 50% 50% 0; transform: rotate(-45deg); border: 2px solid white; box-shadow: 0 4px 8px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center;">
          <div style="width: 12px; height: 12px; background-color: white; border-radius: 50%; transform: rotate(45deg);"></div>
        </div>
      </div>
    `;

    return L.divIcon({
      html,
      className: 'custom-leaflet-icon',
      iconSize: [32, 32],
      iconAnchor: [16, 32],
    });
  };

  // Center of India roughly
  const defaultCenter: [number, number] = [20.5937, 78.9629];
  // Roughly covers Kashmir down to Kanyakumari, Gujarat across to the
  // Northeast states. Leaflet will "rubber-band" back inside this box
  // whenever the user pans or zooms out past it.
  const indiaBounds: [[number, number], [number, number]] = [
    [6.0, 68.0],   // southwest corner
    [37.6, 97.5],  // northeast corner
  ];
  return (
    <div className="relative w-full h-full bg-[#24313D] rounded-xl overflow-hidden border border-[#34C759]/20 shadow-lg group">

      <MapContainer
        center={defaultCenter}
        zoom={4}
        minZoom={4}
        maxBounds={indiaBounds}
        maxBoundsViscosity={1.0}
        style={{ width: '100%', height: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.maptiler.com/copyright/">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={`https://api.maptiler.com/maps/hybrid/{z}/{x}/{y}.jpg?key=${import.meta.env.VITE_MAPTILER_API_KEY}`}
          tileSize={512}
          zoomOffset={-1}
          maxZoom={20}
        />

        <MapController selectedEventId={selectedEventId} events={events} />
        <UserLocationControl />

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
        <div className="absolute top-4 right-4 w-72 bg-[#1C2833]/95 backdrop-blur-xl border border-[#34C759]/20 rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col transform transition-all duration-300 animate-in slide-in-from-right-8">
          <div
            className="relative h-32 w-full overflow-hidden flex items-center justify-center"
            style={{ background: `linear-gradient(135deg, ${getEventColor(selectedEvent.event_type)}33, #1C2833 85%)` }}
          >
            <button
              onClick={handleClosePanel}
              className="absolute top-2 right-2 z-10 p-1.5 bg-[#1C2833]/80 hover:bg-[#1C2833]/90 rounded-full text-[#F4F6F6] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
            {(() => {
              const Icon = getEventIcon(selectedEvent.event_type);
              return <Icon className="w-14 h-14" style={{ color: getEventColor(selectedEvent.event_type) }} />;
            })()}
            <div className="absolute top-2 left-2 bg-[#1C2833]/90 backdrop-blur-sm px-2 py-1 rounded text-[10px] font-bold tracking-wider uppercase border border-[#34C759]/40 shadow-md" style={{ color: getEventColor(selectedEvent.event_type) }}>
              {selectedEvent.event_type}
            </div>
          </div>

          <div className="p-4 flex-1">
            <h3 className="font-bold text-lg text-[#F4F6F6] mb-1">{selectedEvent.severity} Severity</h3>
            <p className="text-sm text-[#34C759]/70 mb-4 flex items-center gap-1">
              <MapPin className="h-3.5 w-3.5" />
              {selectedEvent.location.city}, {selectedEvent.location.state}
            </p>

            <div className="grid grid-cols-2 gap-3 mb-5">
              <div className="bg-[#1C2833]/90 p-2.5 rounded-lg border border-[#34C759]/20 text-center">
                <div className="text-xs text-[#34C759] mb-1 uppercase tracking-wider">Confidence</div>
                <div className="font-semibold text-[#F4F6F6] text-lg">{selectedEvent.confidence}%</div>
              </div>
              <div className="bg-[#1C2833]/90 p-2.5 rounded-lg border border-[#34C759]/20 text-center">
                <div className="text-xs text-[#34C759] mb-1 uppercase tracking-wider">Reports</div>
                <div className="font-semibold text-[#F4F6F6] text-lg">{selectedEvent.report_counts.total}</div>
              </div>
            </div>

            <button
              onClick={() => navigate(`/events/${selectedEvent.id}`)}
              className="w-full py-2.5 bg-[#34C759] hover:bg-[#E8C15A] hover:text-[#24313D]/80 text-[#24313D] rounded-lg text-sm font-medium transition-colors shadow-lg shadow-[#24313D]/20 cursor-pointer"
            >
              View Full Details
            </button>
          </div>
        </div>
      )}

      {/* Legend */}
          <div className="absolute bottom-6 left-6 z-[40]" ref={legendRef}>
        {legendOpen ? (
          <div className="bg-[#1C2833]/95 backdrop-blur-md border border-[#34C759]/20 rounded-lg p-4 shadow-xl">
            <div className="flex items-center justify-between gap-6 mb-3">
              <h4 className="text-sm font-medium text-[#34C759]/90 flex items-center gap-2">
                <Info className="h-3.5 w-3.5" />
                Legend
              </h4>
              <button
                onClick={() => setLegendOpen(false)}
                className="text-[#34C759]/60 hover:text-[#F4F6F6] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] rounded"
                aria-label="Hide legend"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
            <div className="grid grid-cols-2 gap-x-6 gap-y-2">
              {Object.entries(EVENT_COLORS).map(([type, color]) => (
                <div key={type} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full border border-[#34C759]/40 shadow-sm"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-sm text-[#34C759]/90">{type}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <button
            onClick={() => setLegendOpen(true)}
            className="p-2.5 bg-[#1C2833]/90 border border-[#34C759]/20 rounded-full shadow-lg text-[#34C759] hover:bg-[#24313D] transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759]"
            aria-label="Show legend"
          >
            <Info className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  );
}
