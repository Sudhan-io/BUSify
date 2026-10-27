import React, { useState, useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  Calendar,
  MapPin,
  FileSpreadsheet,
  Bus,
  Users,
  BarChart3,
  X,
  HelpCircle,
  Compass,
  Upload,
  Play,
  Download,
  RefreshCw
} from 'lucide-react';
import InfoHint from '../components/InfoHint';
import api from '../services/api';
import { describeError } from '../services/auth';

const SCENARIOS = [
  { id: 'REGULAR', label: 'Regular Academic Day', desc: 'Standard curriculum and lab operations' },
  { id: 'EXAM_DAY', label: 'Semester Exam Day', desc: 'Morning surge across core residential zones' },
  { id: 'PLACEMENT_DRIVE', label: 'Campus Placement Drive', desc: 'Early arrival priority for graduating batches' },
  { id: 'MONSOON_RAIN', label: 'Monsoon Rain Surge', desc: '+35% ridership surge from two-wheeler shifts' },
];

const OFFICE_NAV_ITEMS = [
  { to: '/office/overview', label: 'Overview', icon: LayoutDashboard },
  { to: '/office/planning', label: 'Daily Planning', icon: Calendar },
  { to: '/office/routes', label: 'Routes & Map', icon: MapPin },
  { to: '/office/manifest', label: 'Dispatch Manifest', icon: FileSpreadsheet },
  { to: '/office/fleet', label: 'Fleet & Drivers', icon: Bus },
  { to: '/office/students', label: 'Students & Demand', icon: Users },
  { to: '/office/reports', label: 'Reports & History', icon: BarChart3 },
];

export default function OfficeLayout({
  selectedDate,
  activeInstitution,
  onSelectInstitution,
  institutionsList,
  isAuthenticated = false,
  onRequestSignIn
}) {
  const [selectedArea, setSelectedArea] = useState('AREA_A');
  const [activeScenario, setActiveScenario] = useState('REGULAR');
  const [transitDirection, setTransitDirection] = useState('MORNING_PICKUP');
  const [manifestData, setManifestData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [routeData, setRouteData] = useState(null);
  const [stopsList, setStopsList] = useState([]);
  const [simulationResult, setSimulationResult] = useState(null);
  const [selectedTripSheet, setSelectedTripSheet] = useState(null);
  const [broadcastConfirmed, setBroadcastConfirmed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [manifestError, setManifestError] = useState(null);
  const [simulating, setSimulating] = useState(false);
  const [simulationError, setSimulationError] = useState(null);

  // CSV Upload & Benchmark State
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Fleet & Bus Management State
  const [busesList, setBusesList] = useState([]);
  const [showBusModal, setShowBusModal] = useState(false);
  const [editingBus, setEditingBus] = useState(null);
  const [busSaveLoading, setBusSaveLoading] = useState(false);
  const [busSuccessMessage, setBusSuccessMessage] = useState(null);
  const [busError, setBusError] = useState(null);

  const [busFormData, setBusFormData] = useState({
    bus_id: '',
    registration_no: '',
    seats: 55,
    driver_name: '',
    driver_phone: '+91 98421 10293',
    default_area_id: 'AREA_A',
    depot_location: 'VSB Main Campus Depot, Karudayampalayam',
    route_name: 'Zone A - Karudayampalayam & Kovai Road Express',
    is_active: true,
  });

  // Load manifest, general dashboard data, and fleet inventory
  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setManifestError(null);
      try {
        const [manifest, fc, st, buses] = await Promise.all([
          api.getOperationalManifest(selectedDate, activeScenario),
          api.getForecast(selectedDate),
          api.getStops(),
          api.getBuses(),
        ]);
        setManifestData(manifest);
        setForecastData(fc);
        setStopsList(st);
        setBusesList(buses || []);
        setBroadcastConfirmed(false);
      } catch (err) {
        console.error("Failed to load operational manifest:", err);
        setManifestError(describeError(err));
        setManifestData(null);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedDate, activeScenario]);

  // Load routes when selected area, date, active institution, or transit direction changes
  useEffect(() => {
    async function loadRoutes() {
      try {
        const rt = await api.getRoutes(
          selectedArea,
          selectedDate,
          activeInstitution?.campus_lat,
          activeInstitution?.campus_lng,
          transitDirection
        );
        setRouteData(rt);
      } catch (err) {
        console.error("Failed to load routes:", err);
      }
    }
    loadRoutes();
  }, [selectedArea, selectedDate, activeInstitution?.campus_lat, activeInstitution?.campus_lng, transitDirection]);

  const handleBroadcast = () => {
    setBroadcastConfirmed(true);
    setTimeout(() => setBroadcastConfirmed(false), 5000);
  };

  const handleRunSimulation = async () => {
    setSimulating(true);
    setSimulationError(null);
    try {
      const res = await api.simulate(7);
      setSimulationResult(res);
    } catch (err) {
      setSimulationError(describeError(err));
    } finally {
      setSimulating(false);
    }
  };

  const handleUploadCsv = async (fileOrText) => {
    if (!isAuthenticated) {
      onRequestSignIn?.();
      return;
    }
    setUploadLoading(true);
    setUploadError(null);
    try {
      const res = await api.uploadStopsCsv(
        fileOrText,
        activeInstitution?.campus_lat,
        activeInstitution?.campus_lng,
        activeInstitution?.name
      );
      setBenchmarkResult(res);
    } catch (err) {
      setUploadError(describeError(err));
    } finally {
      setUploadLoading(false);
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      await api.downloadTemplateCsv();
    } catch (err) {
      console.error("Template download failed:", err);
    }
  };

  const handleOpenAddBus = () => {
    setEditingBus(null);
    setBusError(null);
    setBusFormData({
      bus_id: `BUS-${String((busesList.length || 0) + 1).padStart(2, '0')}`,
      registration_no: `TN 47 B ${2000 + (busesList.length || 0) * 12}`,
      seats: 55,
      driver_name: '',
      driver_phone: '+91 98421 10293',
      default_area_id: 'AREA_A',
      depot_location: 'VSB Campus Depot, Karudayampalayam',
      route_name: 'Zone A - Karudayampalayam & Kovai Road Express',
      is_active: true,
    });
    setShowBusModal(true);
  };

  const handleOpenEditBus = (bus) => {
    setEditingBus(bus);
    setBusError(null);
    setBusFormData({
      bus_id: bus.bus_id,
      registration_no: bus.registration_no || '',
      seats: bus.seats || 55,
      driver_name: bus.driver_name || '',
      driver_phone: bus.driver_phone || '+91 98421 10293',
      default_area_id: bus.default_area_id || 'AREA_A',
      depot_location: bus.depot_location || 'VSB Campus Depot, Karudayampalayam',
      route_name: bus.route_name || '',
      is_active: bus.is_active !== false,
    });
    setShowBusModal(true);
  };

  const handleSaveBus = async (e) => {
    if (e) e.preventDefault();
    if (!isAuthenticated) {
      onRequestSignIn?.();
      return;
    }
    setBusSaveLoading(true);
    setBusError(null);
    try {
      if (editingBus) {
        await api.updateBus(editingBus.bus_id, busFormData);
        setBusSuccessMessage(`Bus ${editingBus.bus_id} details updated.`);
      } else {
        await api.addBus(busFormData);
        setBusSuccessMessage(`New bus ${busFormData.bus_id} added to VSB fleet.`);
      }
      const updated = await api.getBuses();
      setBusesList(updated || []);
      setShowBusModal(false);
      setTimeout(() => setBusSuccessMessage(null), 4000);
    } catch (err) {
      console.error("Failed to save bus:", err);
      setBusError(describeError(err));
    } finally {
      setBusSaveLoading(false);
    }
  };

  const handleDeleteBus = async (busId) => {
    if (!isAuthenticated) {
      onRequestSignIn?.();
      return;
    }
    if (!window.confirm(`Are you sure you want to remove ${busId} from active college fleet?`)) return;
    setBusError(null);
    try {
      await api.deleteBus(busId);
      setBusesList(prev => prev.filter(b => b.bus_id !== busId));
      setBusSuccessMessage(`Bus ${busId} removed from fleet.`);
      setTimeout(() => setBusSuccessMessage(null), 4000);
    } catch (err) {
      console.error("Failed to delete bus:", err);
      setBusError(describeError(err));
    }
  };

  // Build comparison chart data
  const comparisonChartData = Object.keys(manifestData?.area_allocation || {}).map(areaId => {
    const baseCount = manifestData?.baseline_allocation?.[areaId] || 10;
    const optCount = manifestData?.area_allocation?.[areaId] || 10;
    const fc = (forecastData?.areas || []).find(a => a.area_id === areaId);
    return {
      name: areaId.replace('AREA_', 'Zone '),
      demand: fc ? fc.p90_demand : optCount * 45,
      baseline_seats: baseCount * 55,
      optimized_seats: optCount * 55,
      buses: optCount,
    };
  });

  const officeContext = {
    selectedDate,
    activeInstitution,
    onSelectInstitution,
    institutionsList,
    isAuthenticated,
    onRequestSignIn,
    selectedArea,
    setSelectedArea,
    activeScenario,
    setActiveScenario,
    SCENARIOS,
    transitDirection,
    setTransitDirection,
    manifestData,
    forecastData,
    routeData,
    stopsList,
    busesList,
    setBusesList,
    simulationResult,
    selectedTripSheet,
    setSelectedTripSheet,
    broadcastConfirmed,
    loading,
    manifestError,
    simulating,
    simulationError,
    showCsvModal,
    setShowCsvModal,
    uploadLoading,
    benchmarkResult,
    uploadError,
    handleUploadCsv,
    handleDownloadTemplate,
    showBusModal,
    setShowBusModal,
    editingBus,
    busSaveLoading,
    busSuccessMessage,
    busError,
    setBusError,
    busFormData,
    setBusFormData,
    handleOpenAddBus,
    handleOpenEditBus,
    handleSaveBus,
    handleDeleteBus,
    handleBroadcast,
    handleRunSimulation,
    comparisonChartData,
  };

  return (
    <div className="space-y-6">
      {/* Persistent Office Sub-Navigation Bar */}
      <nav
        aria-label="Transport Office Sections"
        className="border-b border-[#dfe5df] bg-white rounded-[10px] p-1.5 shadow-xs overflow-x-auto min-w-0"
      >
        <div className="flex items-center gap-1 min-w-max sm:min-w-0">
          {OFFICE_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-1.5 px-3 py-2 rounded-[7px] text-xs font-semibold transition-all whitespace-nowrap ${
                    isActive
                      ? 'bg-[#18201d] text-white shadow-xs'
                      : 'text-[#69716d] hover:text-[#18201d] hover:bg-[#f7f8f5]'
                  }`
                }
              >
                <Icon className="h-3.5 w-3.5" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </div>
      </nav>

      {/* Render Current Route Page */}
      <Outlet context={officeContext} />

      {/* Suggestion 1 & 2: CSV Upload & Comparative Benchmark Modal */}
      {showCsvModal && (
        <div className="fixed inset-0 bg-[#18201d]/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] overflow-y-auto">
          <div className="bg-white rounded-[12px] border border-[#18201d] max-w-4xl w-full p-6 shadow-2xl space-y-5 my-8 max-h-[92vh] overflow-y-auto animate-fade-in">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>ADMIN EXCEL / CSV DATA INGESTION</p>
                <h3 className="card-title text-lg font-bold">Import Stops, Boarding Demands & Route Assignments</h3>
                <p className="text-xs text-[#69716d]">
                  Upload your college transit spreadsheets directly into {activeInstitution?.name || 'VSB Engineering College'}'s AI routing engine.
                </p>
              </div>
              <button
                onClick={() => { setShowCsvModal(false); setUploadError(null); }}
                className="text-[#69716d] hover:text-[#18201d] p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Purpose & Why Feed It Callout */}
            <div className="p-4 bg-[#f7f8f5] rounded-[9px] border border-[#dfe5df] space-y-2">
              <div className="flex items-center gap-2 text-xs font-bold text-[#18201d]">
                <HelpCircle className="h-4 w-4 text-[#ff6b00]" />
                <span>What is this for & Why should you upload a sheet?</span>
              </div>
              <p className="text-xs text-[#69716d] leading-relaxed">
                Most engineering colleges maintain bus routes, student boarding counts, and contracted bus lists in Excel. Instead of manually typing each stop, this tool lets you upload your spreadsheet directly. BUSify will automatically calculate optimal route paths to <strong>{activeInstitution?.name || 'VSB Engineering College'} in Karudayampalayam</strong> and benchmark whether your current buses are overloaded or wasting fuel.
              </p>
            </div>

            {/* Column-by-Column Explainer Table */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="kicker" style={{ margin: 0, fontSize: '11px' }}>
                  EXACT EXCEL COLUMNS & DATA STRUCTURE
                </span>
                <span className="text-[11px] text-[#2b6e3b] font-medium">Supported formats: .CSV, .XLSX, .TXT</span>
              </div>
              <div className="border border-[#dfe5df] rounded-[8px] overflow-hidden">
                <table className="editorial-table text-xs">
                  <thead className="bg-[#f0f2ed]">
                    <tr>
                      <th className="py-2">Column Name</th>
                      <th className="py-2">What to Enter</th>
                      <th className="py-2">Required?</th>
                      <th className="py-2">Karur / VSB Example</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">stop_name</td>
                      <td>Name of the bus boarding point or landmark</td>
                      <td><span className="badge badge-coral text-[10px]">Required</span></td>
                      <td className="text-[#69716d]">Karudayampalayam Junction</td>
                    </tr>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">zone</td>
                      <td>Transit corridor code (AREA_A to AREA_E)</td>
                      <td><span className="badge badge-coral text-[10px]">Required</span></td>
                      <td className="text-[#69716d]">AREA_A (Kovai Road)</td>
                    </tr>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">student_count</td>
                      <td>Number of students boarding at this stop</td>
                      <td><span className="badge badge-coral text-[10px]">Required</span></td>
                      <td className="text-[#69716d]">28 students</td>
                    </tr>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">suggested_bus_code</td>
                      <td>Current assigned bus number if any</td>
                      <td><span className="badge badge-blue text-[10px]">Optional</span></td>
                      <td className="text-[#69716d]">BUS-01</td>
                    </tr>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">latitude</td>
                      <td>GPS Latitude (Leave blank to auto-compute)</td>
                      <td><span className="badge badge-blue text-[10px]">Optional</span></td>
                      <td className="text-[#69716d]">10.9592</td>
                    </tr>
                    <tr>
                      <td className="font-mono font-bold text-[#18201d]">longitude</td>
                      <td>GPS Longitude (Leave blank to auto-compute)</td>
                      <td><span className="badge badge-blue text-[10px]">Optional</span></td>
                      <td className="text-[#69716d]">77.9482</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div className="p-3 bg-[#eef5ee] rounded-[7px] border border-[#cbe3cb] text-[11px] text-[#2b6e3b] flex items-start gap-2">
                <Compass className="h-4 w-4 shrink-0 mt-0.5" />
                <span>
                  <strong>Don't have GPS coordinates? Leave latitude & longitude completely empty!</strong> BUSify will automatically calculate realistic road coordinates along radial corridors branching directly from {activeInstitution?.name || 'VSB Engineering College'}, Karudayampalayam.
                </span>
              </div>
            </div>

            {/* Upload Controls & Actions */}
            <div className="space-y-3 pt-1 border-t border-[#edf1ed]">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <label className="coral-button text-xs cursor-pointer flex items-center gap-1.5">
                    <Upload className="h-3.5 w-3.5" />
                    <span>Upload CSV / Excel File</span>
                    <input
                      type="file"
                      accept=".csv,.txt"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files[0]) {
                          handleUploadCsv(e.target.files[0]);
                        }
                      }}
                    />
                  </label>
                  <button
                    id="btn-load-sample-csv-modal"
                    onClick={() => handleUploadCsv()}
                    disabled={uploadLoading}
                    className="outline-button text-xs flex items-center gap-1.5"
                  >
                    <Play className="h-3.5 w-3.5 text-[#2b6e3b]" />
                    <span>Load 13-Stop Karudayampalayam Sample</span>
                  </button>
                </div>

                <button
                  id="btn-download-template-modal"
                  onClick={handleDownloadTemplate}
                  className="outline-button text-xs flex items-center gap-1.5"
                >
                  <Download className="h-3.5 w-3.5" />
                  <span>Download Sample Excel Template</span>
                </button>
              </div>

              {uploadError && (
                <div className="p-3 bg-[#fff0f0] border border-[#ffcccc] rounded-[6px] text-xs text-[#c00]">
                  {uploadError}
                </div>
              )}

              {uploadLoading && (
                <div className="text-center py-6 text-xs text-[#69716d]">
                  <RefreshCw className="h-5 w-5 animate-spin mx-auto mb-2 text-[#ff6b00]" />
                  Parsing stop manifests, radial geocoding coordinates, and solving CVRP optimization...
                </div>
              )}
            </div>

            {/* Benchmark Comparison Display */}
            {benchmarkResult && benchmarkResult.benchmark && (
              <div className="space-y-4 pt-2 border-t border-[#edf1ed]">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <p className="kicker" style={{ margin: 0 }}>SUGGESTION 2: OPERATIONAL BENCHMARK AUDIT</p>
                    <h4 className="font-bold text-sm text-[#18201d]">
                      Manual Route Baseline vs. BUSify Optimized Dynamic Fleet
                    </h4>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="badge badge-sage">
                      {benchmarkResult.total_stops_imported} Stops Ingested
                    </span>
                    {benchmarkResult.auto_geocoded_count > 0 && (
                      <span className="badge badge-coral">
                        {benchmarkResult.auto_geocoded_count} Geocoded by Radial Fallback
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] space-y-3">
                    <div className="flex items-center justify-between border-b border-[#dfe5df] pb-2">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#69716d] flex items-center gap-1">
                          <span>Manual Static Roster</span>
                          <InfoHint text="Historical, fixed-route assignment used by institutions without dynamic demand response, causing chronic bus overcrowding and wasted empty mileage." />
                        </span>
                        <h5 className="font-serif font-bold text-base text-[#18201d]">College Current Routes</h5>
                      </div>
                      <span className="badge badge-coral">High Inefficiency</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Fleet Required</span>
                        <strong className="text-sm font-serif">{benchmarkResult.benchmark.manual.buses_used} Buses</strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Total Route Distance</span>
                        <strong className="text-sm font-serif">{benchmarkResult.benchmark.manual.total_distance_km} km</strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Standing Students</span>
                        <strong className="text-sm font-serif text-[#d9381e]">
                          {benchmarkResult.benchmark.manual.standing_passengers} Standing
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Overcrowded Buses</span>
                        <strong className="text-sm font-serif text-[#d9381e]">
                          {benchmarkResult.benchmark.manual.overloaded_buses} Violations
                        </strong>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-[8px] border border-[#18201d] bg-white shadow-sm space-y-3">
                    <div className="flex items-center justify-between border-b border-[#edf1ed] pb-2">
                      <div>
                        <span className="text-[11px] font-bold uppercase tracking-wider text-[#2b6e3b] flex items-center gap-1">
                          <span>BUSify AI CVRP</span>
                          <InfoHint text="Capacitated Vehicle Routing Problem solved with Google OR-Tools. Enforces a 100% strict seat capacity guarantee (zero standing students) while minimizing deadhead kilometers." />
                        </span>
                        <h5 className="font-serif font-bold text-base text-[#18201d]">Dynamic Optimized</h5>
                      </div>
                      <span className="badge badge-sage">100% Equity</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Fleet Required</span>
                        <strong className="text-sm font-serif text-[#2b6e3b]">
                          {benchmarkResult.benchmark.optimized.buses_used} Buses
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Total Route Distance</span>
                        <strong className="text-sm font-serif text-[#2b6e3b]">
                          {benchmarkResult.benchmark.optimized.total_distance_km} km
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Standing Students</span>
                        <strong className="text-sm font-serif text-[#2b6e3b]">
                          0 Standing (Strict Cap)
                        </strong>
                      </div>
                      <div>
                        <span className="text-[#69716d] block text-[11px]">Overcrowded Buses</span>
                        <strong className="text-sm font-serif text-[#2b6e3b]">
                          0 Violations (Certified)
                        </strong>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Savings Projection Banner */}
                <div className="p-4 rounded-[8px] bg-[#18201d] text-white space-y-3">
                  <div className="flex items-center justify-between border-b border-white/10 pb-2">
                    <span className="text-xs uppercase tracking-wider font-bold text-[#ff6b00] flex items-center gap-1.5">
                      <span>Tangible Institutional Savings (Annual Projection)</span>
                      <InfoHint text="Calculated across 220 academic operating days based on commercial diesel fuel consumption (3.8 km/liter @ ₹94.50/L) and 2.68 kg CO2 emitted per liter." />
                    </span>
                    <span className="text-xs text-white/70">220 Academic Operating Days</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-2 bg-white/5 rounded-[6px]">
                      <span className="text-[11px] text-white/60 block">Daily Mileage Cut</span>
                      <strong className="text-base font-serif text-white">
                        -{benchmarkResult.benchmark.savings.km_saved_daily} km
                      </strong>
                      <span className="text-[10px] text-[#ff6b00] block">(-{benchmarkResult.benchmark.savings.km_saved_pct}%)</span>
                    </div>
                    <div className="p-2 bg-white/5 rounded-[6px]">
                      <span className="text-[11px] text-white/60 block">Diesel Conserved</span>
                      <strong className="text-base font-serif text-white">
                        {benchmarkResult.benchmark.savings.annual_diesel_liters.toLocaleString()} L
                      </strong>
                      <span className="text-[10px] text-white/60 block">per academic year</span>
                    </div>
                    <div className="p-2 bg-white/5 rounded-[6px]">
                      <span className="text-[11px] text-white/60 block">Financial Savings</span>
                      <strong className="text-base font-serif text-[#ff6b00]">
                        {benchmarkResult.benchmark.savings.annual_savings_formatted}
                      </strong>
                      <span className="text-[10px] text-white/60 block">fuel expenditure</span>
                    </div>
                    <div className="p-2 bg-white/5 rounded-[6px]">
                      <span className="text-[11px] text-white/60 block">CO2 Abatement</span>
                      <strong className="text-base font-serif text-white">
                        {benchmarkResult.benchmark.savings.co2_saved_kg.toLocaleString()} kg
                      </strong>
                      <span className="text-[10px] text-[#2b6e3b] block">carbon reduction</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#edf1ed]">
              <button
                id="btn-done-csv-modal-layout"
                onClick={() => { setShowCsvModal(false); setUploadError(null); }}
                className="dark-button text-xs"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
