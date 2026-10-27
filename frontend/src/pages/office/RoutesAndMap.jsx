import React from 'react';
import { useOutletContext } from 'react-router-dom';
import LeafletMap from '../../components/LeafletMap';
import { Navigation, Route as RouteIcon } from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';
import { CANONICAL_CAMPUS_COORDINATES } from '../../constants/institution';

const ZONES = [
  { id: 'AREA_A', name: 'Zone A', corridor: 'Karudayampalayam & Kovai Rd' },
  { id: 'AREA_B', name: 'Zone B', corridor: 'Gandhigramam & South Hub' },
  { id: 'AREA_C', name: 'Zone C', corridor: 'Thanthonimalai & Collectorate' },
  { id: 'AREA_D', name: 'Zone D', corridor: 'Velur & North Corridor' },
  { id: 'AREA_E', name: 'Zone E', corridor: 'Paramathi & West Rural' },
];

export default function RoutesAndMap() {
  usePageTitle('Routes & Map');
  const {
    stopsList,
    routeData,
    selectedArea,
    setSelectedArea,
    transitDirection,
    setTransitDirection,
    activeInstitution,
    onSelectInstitution,
    institutionsList
  } = useOutletContext();

  const currentZoneStops = (stopsList || []).filter(s => s.area_id === selectedArea);
  const activeRoutes = routeData?.routes || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 3: GEOSPATIAL TRANSIT INTELLIGENCE</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Live Dispatch Map & Route Corridors</h2>
          <p className="text-xs text-[#69716d]">
            Interactive radial corridor map, stop coordinates, and vehicle transit paths centered on {activeInstitution?.name || 'College Campus'}.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-sage text-xs">
            {currentZoneStops.length} Stops in {selectedArea.replace('AREA_', 'Zone ')}
          </span>
          <span className="badge badge-blue text-xs">
            {activeRoutes.length} Active Routes
          </span>
        </div>
      </div>

      {/* Main Map Card */}
      <div className="card space-y-4">
        {/* NAV-004 Fix: min-w-0 on flex containers and responsive wrapping for zone filters */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 min-w-0">
          <div className="min-w-0">
            <h3 className="card-title text-base font-bold flex items-center gap-1.5">
              <Navigation className="h-4 w-4 text-[#ff6b00]" />
              <span>Corridor Dispatch Explorer</span>
            </h3>
            <p className="text-xs text-[#69716d]">
              Select corridor to inspect physical boarding points and vehicle pathing.
            </p>
          </div>

          {/* Zone filter button bar with overflow fix and zero minimum width */}
          <div className="min-w-0 overflow-x-auto pb-1 pt-0.5">
            <div className="flex items-center gap-1.5 flex-nowrap sm:flex-wrap">
              {ZONES.map(z => (
                <button
                  key={z.id}
                  onClick={() => setSelectedArea(z.id)}
                  className={`px-3 py-1.5 rounded-[7px] text-xs font-semibold whitespace-nowrap transition-all shrink-0 ${
                    selectedArea === z.id
                      ? 'bg-[#18201d] text-white shadow-sm'
                      : 'bg-[#ebeee8] text-[#69716d] hover:text-[#18201d] hover:bg-[#dfe5df]'
                  }`}
                  title={`${z.name}: ${z.corridor}`}
                >
                  <span>{z.name}</span>
                  <span className="hidden lg:inline text-[10px] opacity-70 ml-1">({z.corridor.split('&')[0].trim()})</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Map Container */}
        <div className="h-[480px] w-full rounded-[9px] overflow-hidden border border-[#dfe5df]">
          <LeafletMap
            stops={currentZoneStops}
            activeRoutes={activeRoutes}
            campusCenter={[activeInstitution?.campus_lat ?? CANONICAL_CAMPUS_COORDINATES.lat, activeInstitution?.campus_lng ?? CANONICAL_CAMPUS_COORDINATES.lng]}
            campusName={activeInstitution?.name || 'VSB Engineering College Transit Hub'}
            activeInstitution={activeInstitution}
            onSelectInstitution={onSelectInstitution}
            institutionsList={institutionsList}
            direction={transitDirection}
            onToggleDirection={setTransitDirection}
          />
        </div>
      </div>

      {/* Corridor Stops & Route Detail Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Stop Points in Zone */}
        <div className="lg:col-span-6 card space-y-3">
          <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
            <div>
              <p className="kicker" style={{ margin: 0 }}>STOP INVENTORY</p>
              <h4 className="card-title text-sm font-bold">Stops in {selectedArea.replace('AREA_', 'Zone ')}</h4>
            </div>
            <span className="text-xs text-[#69716d]">{currentZoneStops.length} Registered Points</span>
          </div>

          <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1">
            {currentZoneStops.length === 0 ? (
              <p className="text-xs text-[#69716d] p-3 text-center">No stop data found for this zone.</p>
            ) : (
              currentZoneStops.map((st, i) => (
                <div
                  key={st.stop_id || i}
                  className="p-2.5 rounded-[7px] border border-[#dfe5df] bg-[#f7f8f5] flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="h-5 w-5 rounded-full bg-[#18201d] text-white flex items-center justify-center text-[10px] font-bold">
                      {i + 1}
                    </span>
                    <div>
                      <div className="font-semibold text-[#18201d]">{st.name}</div>
                      <div className="text-[10px] text-[#69716d] font-mono">
                        {typeof st.lat === 'number' && typeof st.lng === 'number'
                          ? `${st.lat.toFixed(4)}, ${st.lng.toFixed(4)}`
                          : (st.lat && st.lng ? `${st.lat}, ${st.lng}` : 'Coordinates auto-calculated')}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="badge badge-sage font-mono text-[10px]">{st.stop_id}</span>
                    {st.campus_distance_km != null && (
                      <div className="text-[10px] text-[#69716d] mt-0.5">{st.campus_distance_km} km</div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Route Sequences */}
        <div className="lg:col-span-6 card space-y-3">
          <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
            <div>
              <p className="kicker" style={{ margin: 0 }}>VEHICLE ROUTE SEQUENCES</p>
              <h4 className="card-title text-sm font-bold">Active Itineraries ({transitDirection === 'MORNING_PICKUP' ? 'Morning Pickup' : 'Evening Dropoff'})</h4>
            </div>
            <span className="badge badge-coral text-[10px]">{transitDirection}</span>
          </div>

          <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
            {activeRoutes.length === 0 ? (
              <div className="p-4 rounded-[7px] bg-[#f7f8f5] text-center text-xs text-[#69716d]">
                No active routes calculated for this zone condition.
              </div>
            ) : (
              activeRoutes.map((rt, idx) => (
                <div key={idx} className="p-3 rounded-[8px] border border-[#dfe5df] bg-white space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <RouteIcon className="h-3.5 w-3.5 text-[#ff6b00]" />
                      <span className="font-bold font-mono text-[#18201d]">{rt.bus_id || `Route ${idx + 1}`}</span>
                    </div>
                    <span className="text-[11px] text-[#2b6e3b] font-semibold">
                      {rt.total_distance_km ? `${rt.total_distance_km.toFixed(1)} km` : 'Optimal Route'}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#69716d] flex items-center gap-1">
                    <span className="font-medium text-[#18201d]">Stops:</span>
                    <span className="truncate max-w-[280px]">
                      {(rt.stops || rt.itinerary || []).map(s => s.name || s).join(' → ')}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
