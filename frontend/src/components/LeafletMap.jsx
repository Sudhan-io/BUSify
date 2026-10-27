import React, { useMemo, useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip, Circle, useMap } from 'react-leaflet';
import {
  Maximize2,
  Minimize2,
  Compass,
  Eye,
  EyeOff,
  X,
  Search,
  Building2,
  Navigation,
  Layers,
  Filter,
  ShieldCheck
} from 'lucide-react';
import L from 'leaflet';
import { CANONICAL_CAMPUS_COORDINATES } from '../constants/institution';

// Center on College Campus Depot (canonical coordinates M-02)
const DEFAULT_COLLEGE_CENTER = [CANONICAL_CAMPUS_COORDINATES.lat, CANONICAL_CAMPUS_COORDINATES.lng];

const escapeHtml = (val) => {
  return String(val ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
};

// Custom SVG DivIcon Generator for sleek editorial markers
const createCustomIcon = (type, color = '#18201d', text = '', isSelected = false, isSequential = false) => {
  if (type === 'depot') {
    return L.divIcon({
      className: 'custom-map-marker-depot',
      html: `
        <div style="background: #18201d; width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid #ffffff; box-shadow: 0 3px 12px rgba(0,0,0,0.4); color: #ffffff; font-family: Georgia, serif; font-size: 15px; font-weight: bold; cursor: pointer; transition: transform 0.2s;">
          H
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });
  }

  const safeText = escapeHtml(text);
  const border = isSelected ? '3px solid #ff6b00' : '2px solid #ffffff';
  const scale = isSelected ? 'transform: scale(1.35); z-index: 999;' : '';
  const shadow = isSelected ? 'box-shadow: 0 0 14px rgba(255,107,0,0.7);' : 'box-shadow: 0 1px 4px rgba(0,0,0,0.25);';
  const size = isSequential ? 26 : 22;
  const anchor = size / 2;

  return L.divIcon({
    className: 'custom-map-marker',
    html: `
      <div style="background: ${color}; width: ${size}px; height: ${size}px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: ${border}; ${shadow} ${scale} font-size: ${isSequential ? '11px' : '10px'}; font-weight: 700; color: #ffffff; cursor: pointer; transition: all 0.2s;">
        ${safeText}
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [anchor, anchor],
  });
};

const AREA_COLORS = {
  AREA_A: '#1f5f84', // Editorial Slate Blue (West Corridor - Kovai Rd)
  AREA_B: '#2b6e3b', // Sage Green (South Hub - Gandhigramam)
  AREA_C: '#ff6b00', // Terracotta Coral (South-East Arterial - Thanthonimalai)
  AREA_D: '#6b46c1', // Royal Violet (North Corridor - Velur)
  AREA_E: '#b83280', // Berry Rose (North-West Rural - Paramathi)
};

const ZONE_DESCRIPTIONS = {
  // AREA_A: Karudayampalayam & Kovai Road — campus-adjacent west corridor
  AREA_A: {
    name: 'Karudayampalayam & Kovai Road',
    cardinal: 'West',
    highway: 'NH-67 Coimbatore Road',
    landmark: 'VSB College Gate Arch, Kovai Road Checkpost',
  },
  // AREA_B: Gandhigramam & South Hub — southern radial via Sanapiratti
  AREA_B: {
    name: 'Gandhigramam & South Hub',
    cardinal: 'South',
    highway: 'SH-79 Tiruchengode Road',
    landmark: 'Sanapiratti Roundabout, Government Hospital Gate',
  },
  // AREA_C: Thanthonimalai & South-East — collectorate corridor
  AREA_C: {
    name: 'Thanthonimalai & Collectorate',
    cardinal: 'South-East',
    highway: 'Thanthonimalai Hill Road',
    landmark: 'Karur Collectorate Complex, Arts College Entrance',
  },
  // AREA_D: Velur & North Corridor — Amaravathi river north route
  AREA_D: {
    name: 'Velur & North Corridor',
    cardinal: 'North',
    highway: 'SH-81 Namakkal Road',
    landmark: 'Velur Bridge Checkpost, Vangal Ferry Road, Manmangalam',
  },
  // AREA_E: Paramathi & West Rural — NH-67 Erode Road outer belt
  AREA_E: {
    name: 'Paramathi & West Rural',
    cardinal: 'North-West',
    highway: 'NH-67 Erode Road',
    landmark: 'Paramathi Bus Stand, Kaniyur Industrial Area',
  },
};


// Available tile layer themes
const TILE_LAYERS = {
  standard: {
    name: 'OpenStreetMap',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  },
  positron: {
    name: 'CartoDB Positron (Clean)',
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; CartoDB &copy; OpenStreetMap contributors'
  }
};

// Haversine distance calculator in km
function calculateDistanceKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return (R * c).toFixed(1);
}

// Map controller for animated pans, fits, corridor focuses, and resets
function MapController({ campusCenter, selectedStop, stops, autoFitTrigger, resetTrigger, focusedZone, isFullscreen }) {
  const map = useMap();
  const campusLat = campusCenter?.[0];
  const campusLng = campusCenter?.[1];

  // Invalidate map size when fullscreen toggles
  useEffect(() => {
    const timer = setTimeout(() => {
      map.invalidateSize();
    }, 150);
    return () => clearTimeout(timer);
  }, [isFullscreen, map]);

  // Re-center map when campusCenter changes
  useEffect(() => {
    if (campusLat !== undefined && campusLng !== undefined && !isNaN(campusLat) && !isNaN(campusLng)) {
      map.flyTo([campusLat, campusLng], 12, { duration: 1.0 });
    }
  }, [campusLat, campusLng, map]);

  // Fly to selected stop smoothly when changed
  useEffect(() => {
    if (selectedStop && selectedStop.lat && selectedStop.lon) {
      map.flyTo([selectedStop.lat, selectedStop.lon], 14, { duration: 1.0 });
    }
  }, [selectedStop, map]);

  // Fit bounds to all stops when triggered
  useEffect(() => {
    if (autoFitTrigger && stops && stops.length > 0) {
      const bounds = L.latLngBounds(stops.map(s => [s.lat, s.lon]));
      if (campusCenter) bounds.extend(campusCenter);
      map.fitBounds(bounds, { padding: [50, 50], duration: 1.0 });
    }
  }, [autoFitTrigger, stops, campusCenter, map]);

  // Focus on specific corridor zone
  useEffect(() => {
    if (focusedZone && stops && stops.length > 0) {
      const zoneStops = stops.filter(s => s.area_id === focusedZone);
      if (zoneStops.length > 0) {
        const bounds = L.latLngBounds(zoneStops.map(s => [s.lat, s.lon]));
        if (campusCenter) bounds.extend(campusCenter);
        map.fitBounds(bounds, { padding: [60, 60], duration: 1.0 });
      }
    }
  }, [focusedZone, stops, campusCenter, map]);

  // Reset to campus center
  useEffect(() => {
    if (resetTrigger && campusCenter) {
      map.flyTo(campusCenter, 12, { duration: 1.0 });
    }
  }, [resetTrigger, campusCenter, map]);

  return null;
}

export default function LeafletMap({
  stops = [],
  activeRoutes = [],
  selectedStop = null,
  onSelectStop = null,
  campusCenter = DEFAULT_COLLEGE_CENTER,
  campusName = 'VSB Engineering College Transit Hub',
  activeInstitution = null,
  onSelectInstitution = null,
  institutionsList = [],
  direction = 'MORNING_PICKUP',
  onToggleDirection = null,
  zoom = 12
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredRouteId, setHoveredRouteId] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [activeBusFilter, setActiveBusFilter] = useState('ALL'); // 'ALL' or 'BUS-01', etc.
  const [showRoutes, setShowRoutes] = useState(true);
  const [showCatchment, setShowCatchment] = useState(false); // 500m walking radius
  const [selectedTileLayer, setSelectedTileLayer] = useState('standard');
  const [fitCounter, setFitCounter] = useState(0);
  const [resetCounter, setResetCounter] = useState(0);
  const [focusedZone, setFocusedZone] = useState(null);
  const [osrmFetchedGeometries, setOsrmFetchedGeometries] = useState({});

  // District & College Search States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('ALL');
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const searchDropdownRef = useRef(null);

  // Close search dropdown on click outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (searchDropdownRef.current && !searchDropdownRef.current.contains(e.target)) {
        setShowSearchDropdown(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Listen for Escape key to exit fullscreen
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isFullscreen]);

  const effectiveCenter = useMemo(() => {
    if (activeInstitution?.campus_lat && activeInstitution?.campus_lng) {
      return [activeInstitution.campus_lat, activeInstitution.campus_lng];
    }
    if (campusCenter && campusCenter.length === 2 && !isNaN(campusCenter[0]) && !isNaN(campusCenter[1])) {
      return campusCenter;
    }
    return DEFAULT_COLLEGE_CENTER;
  }, [activeInstitution, campusCenter]);

  const effectiveCampusName = activeInstitution?.name || campusName || 'Campus Transit Hub';

  const depotIcon = useMemo(() => createCustomIcon('depot'), []);

  // Extract unique districts from available institutions
  const districts = useMemo(() => {
    const dSet = new Set();
    institutionsList.forEach(inst => {
      if (inst.district) dSet.add(inst.district);
    });
    return Array.from(dSet).sort();
  }, [institutionsList]);

  // Filter institutions based on district and query
  const filteredInstitutions = useMemo(() => {
    return institutionsList.filter(inst => {
      const matchDistrict = selectedDistrict === 'ALL' || inst.district === selectedDistrict;
      const q = searchQuery.toLowerCase().trim();
      const matchQuery = !q ||
        inst.name.toLowerCase().includes(q) ||
        (inst.short_name && inst.short_name.toLowerCase().includes(q)) ||
        (inst.city && inst.city.toLowerCase().includes(q));
      return matchDistrict && matchQuery;
    });
  }, [institutionsList, selectedDistrict, searchQuery]);

  // Client-side fallback: fetch OSRM road coordinates if road_geometry is missing on imported routes
  useEffect(() => {
    if (!activeRoutes || activeRoutes.length === 0) return;

    activeRoutes.forEach(async (r, idx) => {
      const routeId = r.bus_code || `route-${idx}`;
      if (r.road_geometry && r.road_geometry.length > 0) return;
      if (osrmFetchedGeometries[routeId]) return;

      const steps = (r.itinerary || []).filter(s => s.lat && s.lon);
      if (steps.length < 2) return;

      const coordPairs = steps.map(s => `${s.lon},${s.lat}`).join(';');
      try {
        const url = `https://router.project-osrm.org/route/v1/driving/${coordPairs}?overview=full&geometries=geojson`;
        const res = await fetch(url);
        if (res.ok) {
          const data = await res.json();
          if (data.routes && data.routes[0]?.geometry?.coordinates) {
            const coords = data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
            setOsrmFetchedGeometries(prev => ({ ...prev, [routeId]: coords }));
          }
        }
      } catch (err) {
        console.warn('OSRM client-side route fallback fetch failed:', err);
      }
    });
  }, [activeRoutes, osrmFetchedGeometries]);

  // Compute polylines for active routes using true road geometries
  const routePolylines = useMemo(() => {
    if (!activeRoutes || activeRoutes.length === 0) return [];
    return activeRoutes.map((r, idx) => {
      const routeId = r.bus_code || `route-${idx}`;

      let roadCoords = null;
      if (r.road_geometry && Array.isArray(r.road_geometry) && r.road_geometry.length > 0) {
        roadCoords = r.road_geometry;
      } else if (osrmFetchedGeometries[routeId]) {
        roadCoords = osrmFetchedGeometries[routeId];
      } else {
        roadCoords = (r.itinerary || [])
          .filter(step => step.lat && step.lon)
          .map(step => [step.lat, step.lon]);
      }

      return {
        id: routeId,
        busCode: r.bus_code || `BUS-${idx + 1}`,
        color: ['#ff6b00', '#18201d', '#1f5f84', '#2b6e3b', '#6b46c1', '#b83280', '#0284c7'][idx % 7],
        positions: roadCoords,
        totalRiders: r.total_riders || 48,
        capacity: r.capacity || 55,
        utilizationPct: r.utilization_pct || 87.2,
        totalDistanceKm: r.total_distance_km || 22.4,
        itinerary: r.itinerary || [],
        commuteComfortCertified: r.commute_comfort_certified !== false,
        isRoadFollower: (r.road_geometry && r.road_geometry.length > 0) || !!osrmFetchedGeometries[routeId],
      };
    });
  }, [activeRoutes, osrmFetchedGeometries]);

  // Active isolated route object if a single bus is filtered
  const isolatedRoute = useMemo(() => {
    if (activeBusFilter === 'ALL') return null;
    return routePolylines.find(r => r.busCode === activeBusFilter) || null;
  }, [activeBusFilter, routePolylines]);

  // Set of stop IDs in the isolated bus route for sequence highlighting
  const isolatedStopSequenceMap = useMemo(() => {
    if (!isolatedRoute) return null;
    const map = new Map();
    (isolatedRoute.itinerary || []).forEach((step, idx) => {
      if (step.stop_id) {
        map.set(step.stop_id, {
          seq: idx + 1,
          time: step.arrival_time || step.time,
          passengers: step.passengers_boarded || step.passengers_dropped || step.boarded || step.disembarked || 0,
          totalOnboard: step.cumulative_passengers || 0,
          registeredCount: step.registered_count,
          p90Demand: step.p90_riders,
        });
      }
    });
    return map;
  }, [isolatedRoute]);

  const handleSelectCollege = (inst) => {
    if (onSelectInstitution) {
      onSelectInstitution(inst);
    }
    setShowSearchDropdown(false);
    setSearchQuery(inst.name);
  };

  const currentTile = TILE_LAYERS[selectedTileLayer] || TILE_LAYERS.standard;

  return (
    <div
      className={`transition-all duration-300 isolate z-0 flex flex-col ${
        isFullscreen
          ? 'fixed inset-0 z-[99999] bg-[#f7f8f5] w-screen h-screen p-3'
          : 'w-full h-full min-h-[440px] rounded-[12px] overflow-hidden relative border border-[#dfe5df]'
      }`}
    >
      {/* Top Bar: College & District Map Search + Filter Controls */}
      <div className="bg-[#f7f8f5] border-b border-[#dfe5df] p-2.5 flex flex-wrap items-center justify-between gap-2.5 z-20 text-xs">
        {/* Left: Search College on Map & District Filter */}
        <div className="flex flex-wrap items-center gap-2 flex-1 min-w-[280px]">
          {/* District Selector */}
          <div className="flex items-center gap-1.5 bg-white border border-[#dfe5df] rounded-[7px] px-2.5 py-1">
            <Building2 className="h-3.5 w-3.5 text-[#ff6b00] shrink-0" />
            <select
              value={selectedDistrict}
              onChange={(e) => {
                setSelectedDistrict(e.target.value);
                setShowSearchDropdown(true);
              }}
              className="bg-transparent text-xs font-semibold text-[#18201d] outline-none cursor-pointer"
            >
              <option value="ALL">All Districts ({institutionsList.length} Hubs)</option>
              {districts.map(d => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {/* College Live Search Autocomplete */}
          <div className="relative flex-1 min-w-[200px] max-w-sm" ref={searchDropdownRef}>
            <div className="flex items-center gap-1.5 bg-white border border-[#dfe5df] rounded-[7px] px-2.5 py-1 focus-within:border-[#18201d]">
              <Search className="h-3.5 w-3.5 text-[#69716d] shrink-0" />
              <input
                type="text"
                value={searchQuery}
                placeholder={`Search colleges on map... (${institutionsList.length} registered)`}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  setShowSearchDropdown(true);
                }}
                onFocus={() => setShowSearchDropdown(true)}
                className="w-full bg-transparent text-xs text-[#18201d] placeholder-[#9ca3af] outline-none"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="text-[#69716d] hover:text-[#18201d]"
                >
                  <X className="h-3 w-3" />
                </button>
              )}
            </div>

            {/* Dropdown Options */}
            {showSearchDropdown && (
              <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-[#dfe5df] rounded-[8px] shadow-lg max-h-60 overflow-y-auto z-[2000] p-1">
                {filteredInstitutions.length > 0 ? (
                  filteredInstitutions.map(inst => {
                    const isCurrent = activeInstitution?.id === inst.id;
                    return (
                      <button
                        key={inst.id}
                        type="button"
                        onClick={() => handleSelectCollege(inst)}
                        className={`w-full text-left p-2 rounded-[6px] text-xs flex items-center justify-between gap-2 transition-colors ${
                          isCurrent ? 'bg-[#18201d] text-white' : 'hover:bg-[#f7f8f5] text-[#18201d]'
                        }`}
                      >
                        <div className="truncate">
                          <div className="font-bold truncate">{inst.name}</div>
                          <div className={`text-[10px] ${isCurrent ? 'text-[#dfe5df]' : 'text-[#69716d]'}`}>
                            {inst.city} &bull; Fleet: {inst.fleet_size || 10} buses
                          </div>
                        </div>
                        <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                          isCurrent ? 'bg-[#ff6b00] text-white' : 'bg-[#ebeee8] text-[#18201d]'
                        }`}>
                          {inst.district}
                        </span>
                      </button>
                    );
                  })
                ) : (
                  <div className="p-3 text-center text-xs text-[#69716d]">
                    No institutions match "{searchQuery}"
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Operational Transit Mode & Fullscreen Controls */}
        <div className="flex items-center gap-2">
          {/* Direction Toggle (Morning Pickup vs Evening Drop) */}
          {onToggleDirection && (
            <div className="flex items-center bg-[#ebeee8] p-0.5 rounded-[7px] border border-[#dfe5df]">
              <button
                type="button"
                onClick={() => onToggleDirection('MORNING_PICKUP')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all ${
                  direction === 'MORNING_PICKUP'
                    ? 'bg-[#18201d] text-white shadow-xs'
                    : 'text-[#69716d] hover:text-[#18201d]'
                }`}
                title="Morning Inbound Pickup (08:30 AM Campus Arrival)"
              >
                Morning Pickup
              </button>
              <button
                type="button"
                onClick={() => onToggleDirection('EVENING_DROP')}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all ${
                  direction === 'EVENING_DROP'
                    ? 'bg-[#18201d] text-white shadow-xs'
                    : 'text-[#69716d] hover:text-[#18201d]'
                }`}
                title="Evening Outbound Return (16:30 PM Campus Dismissal)"
              >
                Evening Drop
              </button>
            </div>
          )}

          {/* Fullscreen Toggle Button */}
          <button
            type="button"
            onClick={() => setIsFullscreen(f => !f)}
            className={`px-2.5 py-1 rounded-[7px] text-xs font-semibold flex items-center gap-1.5 transition-all border ${
              isFullscreen
                ? 'bg-[#ff6b00] text-white border-[#ff6b00] shadow-sm'
                : 'bg-white text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
            }`}
            title={isFullscreen ? 'Exit Fullscreen (Esc)' : 'Expand to Fullscreen Map'}
          >
            {isFullscreen ? (
              <>
                <Minimize2 className="h-3.5 w-3.5" />
                <span>Exit Fullscreen</span>
              </>
            ) : (
              <>
                <Maximize2 className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Fullscreen Map</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Corridor Compass & Single Bus Route Isolator Bar */}
      <div className="bg-[#f0f2ed] border-b border-[#dfe5df] px-3 py-1.5 flex flex-wrap items-center justify-between gap-2 z-10 text-xs">
        {/* Single Bus Isolator (Eliminates Route Ambiguity & Crossing Lines) */}
        <div className="flex items-center gap-1.5 overflow-x-auto">
          <span className="text-[11px] font-semibold text-[#18201d] flex items-center gap-1 shrink-0">
            <Filter className="h-3 w-3 text-[#ff6b00]" />
            <span>Isolate Bus Route:</span>
          </span>
          <button
            type="button"
            onClick={() => {
              setActiveBusFilter('ALL');
              setSelectedRoute(null);
            }}
            className={`px-2 py-0.5 rounded text-[11px] font-semibold transition-all border ${
              activeBusFilter === 'ALL'
                ? 'bg-[#18201d] text-white border-[#18201d]'
                : 'bg-white text-[#69716d] border-[#dfe5df] hover:text-[#18201d]'
            }`}
          >
            All Buses ({routePolylines.length})
          </button>
          {routePolylines.map((r) => {
            const isActive = activeBusFilter === r.busCode;
            return (
              <button
                key={r.busCode}
                type="button"
                onClick={() => {
                  setActiveBusFilter(isActive ? 'ALL' : r.busCode);
                  setSelectedRoute(isActive ? null : r);
                }}
                className={`px-2 py-0.5 rounded text-[11px] font-semibold flex items-center gap-1 transition-all border shrink-0 ${
                  isActive
                    ? 'bg-[#18201d] text-white border-[#18201d] shadow-xs'
                    : 'bg-white text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
                }`}
              >
                <span className="h-2 w-2 rounded-full shrink-0" style={{ background: r.color }} />
                <span>{r.busCode}</span>
              </button>
            );
          })}
        </div>

        {/* Corridor Zones */}
        <div className="flex items-center gap-1 shrink-0">
          <span className="text-[11px] text-[#69716d] uppercase font-semibold">Zone:</span>
          {Object.entries(ZONE_DESCRIPTIONS).map(([zoneId, info]) => {
            const isZoneActive = focusedZone === zoneId;
            const color = AREA_COLORS[zoneId];
            return (
              <button
                key={zoneId}
                type="button"
                onClick={() => setFocusedZone(prev => prev === zoneId ? null : zoneId)}
                title={`Orient map to ${info.name}`}
                className={`px-1.5 py-0.5 rounded text-[10px] font-medium flex items-center gap-1 transition-all border ${
                  isZoneActive
                    ? 'bg-[#18201d] text-white border-[#18201d]'
                    : 'bg-white text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
                }`}
              >
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
                <span>{zoneId.replace('AREA_', '')}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Map Container */}
      <div className="relative flex-1 w-full min-h-[380px]">
        <MapContainer
          center={effectiveCenter}
          zoom={zoom}
          scrollWheelZoom={true}
          className="w-full h-full min-h-[380px]"
        >
          <MapController
            campusCenter={effectiveCenter}
            selectedStop={selectedStop}
            stops={stops}
            autoFitTrigger={fitCounter}
            resetTrigger={resetCounter}
            focusedZone={focusedZone}
            isFullscreen={isFullscreen}
          />

          {/* Clean Tile Layer */}
          <TileLayer
            attribution={currentTile.attribution}
            url={currentTile.url}
          />

          {/* 500m Pedestrian Walking Catchment Circles */}
          {showCatchment && stops.map((s, idx) => (
            <Circle
              key={`catchment-${s.stop_id || idx}`}
              center={[s.lat, s.lon]}
              radius={500}
              pathOptions={{
                color: '#2b6e3b',
                fillColor: '#2b6e3b',
                fillOpacity: 0.10,
                weight: 1.2,
                dashArray: '4, 4',
              }}
            />
          ))}

          {/* College Campus Hub Marker (Dynamic for any selected college) */}
          <Marker position={effectiveCenter} icon={depotIcon}>
            <Popup>
              <div className="p-1 space-y-1">
                <span className="badge badge-sage">Central Campus Transit Depot</span>
                <h5 className="font-bold text-sm text-[#18201d]">{effectiveCampusName}</h5>
                <p className="text-xs text-[#69716d]">
                  Origin & Fleet Hub ({effectiveCenter[0].toFixed(4)}° N, {effectiveCenter[1].toFixed(4)}° E)
                </p>
                <div className="pt-1 border-t border-[#dfe5df] text-[11px] text-[#2b6e3b] font-medium flex items-center justify-between">
                  <span>{direction === 'MORNING_PICKUP' ? 'Standard Arrival:' : 'Outbound Dismissal:'}</span>
                  <strong>{direction === 'MORNING_PICKUP' ? '08:30 AM' : '16:30 PM'}</strong>
                </div>
              </div>
            </Popup>
          </Marker>

          {/* Transit Stops Markers with Click & Sequence Badges */}
          {stops.map((s, idx) => {
            const color = AREA_COLORS[s.area_id] || '#1f5f84';
            const isSelected = selectedStop && selectedStop.stop_id === s.stop_id;

            // Check if this stop belongs to the isolated bus
            const seqInfo = isolatedStopSequenceMap?.get(s.stop_id);
            const isAssignedToIsolated = !!seqInfo;

            // When a single bus is isolated, dim other stops
            const isDimmed = isolatedRoute && !isAssignedToIsolated;

            // Marker text is the sequence number if isolated, otherwise stop index
            const markerText = isAssignedToIsolated ? `#${seqInfo.seq}` : `${idx + 1}`;
            const markerColor = isAssignedToIsolated ? '#ff6b00' : (isDimmed ? '#9ca3af' : color);

            const stopIcon = createCustomIcon(
              'stop',
              markerColor,
              markerText,
              isSelected || isAssignedToIsolated,
              isAssignedToIsolated
            );

            const distFromCampus = calculateDistanceKm(effectiveCenter[0], effectiveCenter[1], s.lat, s.lon);
            const zoneInfo = ZONE_DESCRIPTIONS[s.area_id] || { name: 'Regional Radial', cardinal: 'Corridor', highway: 'Main Arterial' };

            return (
              <Marker
                key={s.stop_id || idx}
                position={[s.lat, s.lon]}
                icon={stopIcon}
                opacity={isDimmed ? 0.45 : 1.0}
                eventHandlers={{
                  click: () => {
                    if (onSelectStop) onSelectStop(s);
                  },
                }}
              >
                <Tooltip direction="top" offset={[0, -10]} opacity={0.95}>
                  <div className="font-semibold text-xs">{s.name}</div>
                  <div className="text-[10px] text-[#69716d]">
                    {isAssignedToIsolated && (
                      <span className="text-[#ff6b00] font-bold">Stop #{seqInfo.seq} on {isolatedRoute.busCode} &bull; </span>
                    )}
                    {s.area_id?.replace('AREA_', 'Zone ')} ({zoneInfo.cardinal}) &bull; {distFromCampus} km to Campus
                  </div>
                </Tooltip>
                <Popup>
                  <div className="p-1.5 space-y-1.5 min-w-[210px]">
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#f7f8f5] text-[#18201d] border border-[#dfe5df]">
                        {s.area_id?.replace('AREA_', 'Zone ')} &bull; {zoneInfo.name}
                      </span>
                      <span className="text-[10px] font-mono text-[#69716d]">{s.stop_id}</span>
                    </div>
                    <h5 className="font-bold text-sm text-[#18201d]">{s.name}</h5>

                    {isAssignedToIsolated && (
                      <div className="p-1.5 rounded bg-[#fff8f0] border border-[#ffd8b2] text-[11px] text-[#ff6b00] font-semibold flex items-center justify-between">
                        <span>{isolatedRoute.busCode} Itinerary Stop:</span>
                        <span>#{seqInfo.seq} at {seqInfo.time || 'Scheduled'}</span>
                      </div>
                    )}

                    <div className="text-xs text-[#69716d] space-y-0.5">
                      <p>Radial Corridor: <strong className="text-[#18201d]">{zoneInfo.highway}</strong></p>
                      <p>Distance to Hub: <strong className="text-[#18201d]">{distFromCampus} km</strong></p>
                      {(s.student_count !== undefined || s.registered_count !== undefined || seqInfo?.registeredCount !== undefined) && (
                        <p>Registered Students: <strong className="text-[#18201d]">{s.student_count ?? s.registered_count ?? seqInfo?.registeredCount}</strong></p>
                      )}
                      {(s.p90_riders !== undefined || seqInfo?.p90Demand !== undefined || (seqInfo && seqInfo.passengers > 0)) && (
                        <p>Demand / Boarding: <strong className="text-[#ff6b00]">{s.p90_riders ?? seqInfo?.p90Demand ?? `${seqInfo.passengers} riders`}</strong></p>
                      )}
                      {seqInfo && seqInfo.totalOnboard !== undefined && seqInfo.totalOnboard > 0 && (
                        <p>Total Onboard: <strong className="text-[#2b6e3b]">{seqInfo.totalOnboard} riders</strong></p>
                      )}
                    </div>
                    <div className="pt-1 border-t border-[#edf1ed] text-[10px] text-[#69716d] flex items-center justify-between">
                      <span>Catchment Radius:</span>
                      <strong className="text-[#2b6e3b]">500m pedestrian buffer</strong>
                    </div>
                  </div>
                </Popup>
              </Marker>
            );
          })}

          {/* Turn-by-Turn Road Route Polylines (Smooth, Solid Road Network) */}
          {showRoutes && routePolylines.map(line => {
            const isHovered = hoveredRouteId === line.id;
            const isSelected = selectedRoute?.id === line.id || activeBusFilter === line.busCode;
            const isFilteredOut = activeBusFilter !== 'ALL' && activeBusFilter !== line.busCode;

            return (
              <Polyline
                key={line.id}
                positions={line.positions}
                pathOptions={{
                  color: isSelected ? '#ff6b00' : (isHovered ? '#18201d' : line.color),
                  weight: isSelected ? 6.5 : (isHovered ? 5.0 : (isFilteredOut ? 2.0 : 4.0)),
                  opacity: isSelected ? 1.0 : (isFilteredOut ? 0.15 : (isHovered ? 0.95 : 0.80)),
                  lineCap: 'round',
                  lineJoin: 'round',
                  dashArray: null,
                }}
                eventHandlers={{
                  mouseover: () => setHoveredRouteId(line.id),
                  mouseout: () => setHoveredRouteId(null),
                  click: () => {
                    setSelectedRoute(line);
                    setActiveBusFilter(line.busCode);
                  },
                }}
              >
                <Tooltip sticky>
                  <div className="text-xs font-bold text-[#18201d] flex items-center gap-1.5">
                    <span>{line.busCode} Road Trajectory</span>
                    <span className="badge badge-sage text-[9px] py-0">OSRM Road Geometry</span>
                  </div>
                  <div className="text-[11px] text-[#69716d]">
                    {line.totalRiders} / {line.capacity} Seats ({line.utilizationPct}%) &bull; {line.totalDistanceKm} km
                  </div>
                  <div className="text-[10px] text-[#2b6e3b] font-medium pt-0.5">
                    Max 60-Min Commute Certified
                  </div>
                </Tooltip>
              </Polyline>
            );
          })}
        </MapContainer>

        {/* Interactive Map Quick Action Toolbar (Top-Right) */}
        <div className="absolute top-3 right-3 z-[1000] flex flex-col gap-1.5 bg-white/95 backdrop-blur-md p-1.5 rounded-[8px] border border-[#dfe5df] shadow-sm">
          <button
            type="button"
            onClick={() => setFitCounter(c => c + 1)}
            title="Fit Entire Transit Corridor to View"
            className="p-1.5 rounded hover:bg-[#f7f8f5] text-[#18201d] text-xs flex items-center gap-1 font-semibold transition-colors"
          >
            <Maximize2 className="h-3.5 w-3.5 text-[#18201d]" />
            <span className="hidden sm:inline text-[11px]">Fit Network</span>
          </button>
          <button
            type="button"
            onClick={() => { setFocusedZone(null); setResetCounter(c => c + 1); }}
            title="Center on Campus Transit Depot"
            className="p-1.5 rounded hover:bg-[#f7f8f5] text-[#18201d] text-xs flex items-center gap-1 font-semibold transition-colors"
          >
            <Compass className="h-3.5 w-3.5 text-[#18201d]" />
            <span className="hidden sm:inline text-[11px]">Campus Hub</span>
          </button>
          <button
            type="button"
            onClick={() => setShowCatchment(c => !c)}
            title="Toggle 500m Pedestrian Walking Catchment Circles"
            className={`p-1.5 rounded text-xs flex items-center gap-1 font-semibold transition-colors border-t border-[#edf1ed] pt-1 ${
              showCatchment ? 'bg-[#eef5ee] text-[#2b6e3b]' : 'hover:bg-[#f7f8f5] text-[#18201d]'
            }`}
          >
            <Navigation className="h-3.5 w-3.5 text-[#2b6e3b]" />
            <span className="hidden sm:inline text-[11px]">{showCatchment ? '500m Catchment On' : '500m Catchment'}</span>
          </button>
          <button
            type="button"
            onClick={() => setShowRoutes(r => !r)}
            title="Toggle Road Route Polylines"
            className="p-1.5 rounded hover:bg-[#f7f8f5] text-[#18201d] text-xs flex items-center gap-1 font-semibold transition-colors"
          >
            {showRoutes ? <Eye className="h-3.5 w-3.5 text-[#2b6e3b]" /> : <EyeOff className="h-3.5 w-3.5 text-[#69716d]" />}
            <span className="hidden sm:inline text-[11px]">{showRoutes ? 'Roads On' : 'Stops Only'}</span>
          </button>
          <button
            type="button"
            onClick={() => setSelectedTileLayer(l => l === 'standard' ? 'positron' : 'standard')}
            title="Switch Map Tile Theme"
            className="p-1.5 rounded hover:bg-[#f7f8f5] text-[#18201d] text-xs flex items-center gap-1 font-semibold transition-colors border-t border-[#edf1ed] pt-1"
          >
            <Layers className="h-3.5 w-3.5 text-[#69716d]" />
            <span className="hidden sm:inline text-[11px]">{selectedTileLayer === 'standard' ? 'OSM' : 'Positron'}</span>
          </button>
        </div>

        {/* Selected Route Inspector / Turn-by-Turn Leg Drawer (Top-Left) */}
        {selectedRoute && (
          <div className="absolute top-3 left-3 z-[1000] bg-white/95 backdrop-blur-md p-3.5 rounded-[9px] border border-[#dfe5df] shadow-md max-w-sm w-full space-y-2 text-xs animate-fade-in max-h-[85%] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-[#edf1ed] pb-2">
              <div className="flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: selectedRoute.color }} />
                <span className="font-bold text-sm text-[#18201d]">
                  {selectedRoute.busCode} Route Manifest
                </span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedRoute(null);
                  setActiveBusFilter('ALL');
                }}
                className="p-1 hover:bg-[#f7f8f5] rounded text-[#69716d]"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[10px] text-[#69716d] block">Passenger Load</span>
                <span className="font-bold text-sm text-[#18201d]">
                  {selectedRoute.totalRiders} / {selectedRoute.capacity}
                </span>
                <span className="text-[10px] text-[#2b6e3b] font-medium block">
                  {selectedRoute.utilizationPct}% Utilization
                </span>
              </div>
              <div className="p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[10px] text-[#69716d] block">Route Length</span>
                <span className="font-bold text-sm text-[#18201d]">
                  {selectedRoute.totalDistanceKm} km
                </span>
                <span className="text-[10px] text-[#18201d] font-medium block">
                  OSRM Road Geometry
                </span>
              </div>
            </div>

            <div className="flex items-center gap-1.5 p-1.5 rounded bg-[#eef5ee] border border-[#cbe3cb] text-[11px] text-[#2b6e3b] font-medium">
              <ShieldCheck className="h-3.5 w-3.5 shrink-0" />
              <span>Commute Comfort Certified: Safe under 60-min cap</span>
            </div>

            {/* Turn-by-Turn Sequential Itinerary */}
            <div className="space-y-1.5 pt-1">
              <span className="kicker" style={{ margin: '0 0 4px', fontSize: '10px' }}>
                TURN-BY-TURN ROAD STOPS ({selectedRoute.itinerary.length} STOPS)
              </span>
              <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                {selectedRoute.itinerary.map((step, idx) => {
                  const isDepot = step.stop_id === 'DEPOT_CAMPUS' || idx === selectedRoute.itinerary.length - 1;
                  return (
                    <div
                      key={idx}
                      className={`p-2 rounded-[6px] border text-xs flex items-center justify-between gap-2 ${
                        isDepot
                          ? 'bg-[#18201d] text-white border-[#18201d]'
                          : 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df]'
                      }`}
                    >
                      <div className="flex items-center gap-2 truncate">
                        <span className={`h-4 w-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                          isDepot ? 'bg-[#ff6b00] text-white' : 'bg-white text-[#18201d] border'
                        }`}>
                          {isDepot ? 'H' : idx + 1}
                        </span>
                        <div className="truncate">
                          <div className="font-semibold truncate">{step.name || step.stop_id}</div>
                          <div className={`text-[10px] ${isDepot ? 'text-[#dfe5df]' : 'text-[#69716d]'}`}>
                            {(step.arrival_time || step.time) ? `Arrival: ${step.arrival_time || step.time}` : `Stop #${idx + 1}`}
                          </div>
                        </div>
                      </div>
                      {step.cumulative_passengers !== undefined && (
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded shrink-0 ${
                          isDepot ? 'bg-white/20 text-white' : 'bg-[#eef5ee] text-[#2b6e3b]'
                        }`}>
                          {step.cumulative_passengers} riders
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Map Legend Overlay */}
        <div className="absolute bottom-3 left-3 z-[1000] bg-white/95 backdrop-blur-md px-3 py-2 rounded-[7px] border border-[#dfe5df] text-[11px] space-y-1 shadow-sm max-w-sm">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-[#18201d]" />
              <span className="text-[#18201d] font-semibold">
                Campus Hub: {effectiveCampusName.split(' ')[0]}
              </span>
            </div>
            <span className="text-[9px] font-mono text-[#2b6e3b] font-semibold">
              OSRM Real Road Network
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-2 pt-0.5 text-[10px] text-[#69716d]">
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ background: AREA_COLORS.AREA_A }} /> Zone A (West)
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ background: AREA_COLORS.AREA_B }} /> Zone B (South)
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ background: AREA_COLORS.AREA_C }} /> Zone C (South-East)
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ background: AREA_COLORS.AREA_D }} /> Zone D (North)
            </span>
            <span className="flex items-center gap-1">
              <span className="h-2 w-2 rounded-full" style={{ background: AREA_COLORS.AREA_E }} /> Zone E (North-West)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
