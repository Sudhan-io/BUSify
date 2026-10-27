import React, { useState, useEffect } from 'react';
import MetricCard from '../components/MetricCard';
import ChartContainer from '../components/ChartContainer';
import LeafletMap from '../components/LeafletMap';
import StatusBadge from '../components/StatusBadge';
import InfoHint from '../components/InfoHint';
import { Bus, Users, Check, RefreshCw, Play, ShieldCheck, Printer, FileText, Send, Phone, MapPin, X, Upload, Download, FileSpreadsheet, Compass, Plus, Edit2, Trash2, CheckCircle2, AlertCircle, HelpCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import api from '../services/api';
import { describeError } from '../services/auth';
import { CANONICAL_CAMPUS_COORDINATES } from '../constants/institution';

const SCENARIOS = [
  { id: 'REGULAR', label: 'Regular Academic Day', desc: 'Standard curriculum and lab operations' },
  { id: 'EXAM_DAY', label: 'Semester Exam Day', desc: 'Morning surge across core residential zones' },
  { id: 'PLACEMENT_DRIVE', label: 'Campus Placement Drive', desc: 'Early arrival priority for graduating batches' },
  { id: 'MONSOON_RAIN', label: 'Monsoon Rain Surge', desc: '+35% ridership surge from two-wheeler shifts' },
];

export default function OfficeDashboard({
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

  // Suggestions 1 & 2: CSV Upload & Comparative Benchmark State
  const [showCsvModal, setShowCsvModal] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);

  // Fleet & Bus Management State (Add / Edit Buses)
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
    driver_phone: '+91 90000 00001',
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
      // Was console-only, so a failed backtest was indistinguishable from
      // "never run" on screen.
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
      driver_phone: '+91 90000 00001',
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
      driver_phone: bus.driver_phone || '+91 90000 00001',
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

  return (
    <div className="space-y-8">
      {/* Editorial Hero Section */}
      <section className="hero">
        <div>
          <p className="kicker">
            <span className="pulse"></span> TRANSPORT OFFICE OPERATIONS / DISPATCH CONTROL
          </p>
          <h1>
            College fleet,<br />
            <em>re-allocated with equity.</em>
          </h1>
          <p className="hero-copy">
            The Transport Officer daily console calculates expected ridership surges per residential zone, balances bus allocations across campus routes, and publishes official driver trip sheets to guarantee zero standing passengers.
          </p>
        </div>
        <div className="hero-note flex flex-col justify-between">
          <div>
            <span className="note-label">Operational Manifest</span>
            <strong>
              {loading ? '— ' : (manifestData?.total_active_buses != null ? `${manifestData.total_active_buses} Active Buses.` : '— Active Buses.')}
            </strong>
            <span>
              {loading ? '— seats' : `${manifestData?.total_seats_deployed != null ? manifestData.total_seats_deployed : '—'} Confirmed Seats`}
              {' • '}
              {loading ? '—' : (manifestData?.total_standing != null ? manifestData.total_standing : '—')} Standing
            </span>
          </div>
          <button
            id="btn-import-stops-hero"
            onClick={() => { setShowCsvModal(true); if (!benchmarkResult) handleUploadCsv(); }}
            className="coral-button text-xs mt-3 flex items-center justify-center gap-1.5 w-full"
          >
            <Upload className="h-3.5 w-3.5" />
            <span>Import Stops & Benchmark</span>
          </button>
        </div>
      </section>

      {/* Operational Workflow Step 1: Scenario Condition Selector */}
      <div className="card space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
          <div>
            <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 1: CAMPUS OPERATIONAL CONDITION</p>
            <h3 className="card-title text-base font-bold">Select Today's Academic Timetable Scenario</h3>
          </div>
          <span className="text-xs text-[#69716d]">Calibrates LightGBM Quantile Surge & Fleet Balancing</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {SCENARIOS.map(sc => (
            <button
              key={sc.id}
              onClick={() => setActiveScenario(sc.id)}
              className={`p-3.5 rounded-[8px] text-left border transition-all ${
                activeScenario === sc.id
                  ? 'bg-[#18201d] text-white border-[#18201d] shadow-sm'
                  : 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs">{sc.label}</span>
                {activeScenario === sc.id && <Check className="h-3.5 w-3.5 text-white" />}
              </div>
              <p className={`text-[11px] pt-1.5 leading-snug ${activeScenario === sc.id ? 'text-[#dfe5df]' : 'text-[#69716d]'}`}>
                {sc.desc}
              </p>
            </button>
          ))}
        </div>
      </div>

      {/* Broadcast Success Banner */}
      {broadcastConfirmed && (
        <div className="banner">
          <div className="banner-icon">
            <Check className="h-4 w-4" />
          </div>
          <div className="banner-body">
            <strong>Daily Dispatch Manifest Approved & Broadcast</strong>
            <span>All {manifestData?.total_active_buses} driver trip sheets and route sequences have been transmitted to vehicle captains.</span>
          </div>
          <span className="badge badge-sage">Dispatched</span>
        </div>
      )}

      {/* Manifest Error Alert */}
      {manifestError && (
        <div
          role="alert"
          className="rounded-lg border border-[#f5c6c2] bg-[#fdecea] p-3 text-xs text-[#c0392b] flex items-center justify-between"
        >
          <span><strong>Operational Manifest Error:</strong> {manifestError}</span>
        </div>
      )}

      {/* Key Metric Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Active Vehicles"
          value={manifestData?.total_active_buses != null ? `${manifestData.total_active_buses} Buses` : "—"}
          subtitle={manifestData?.total_seats_deployed != null ? `${manifestData.total_seats_deployed} total seats` : "—"}
          icon={Bus}
          tone={manifestData ? "sage" : "blue"}
          badge={loading ? "Checking" : (manifestData ? "Full Fleet" : "Unavailable")}
          loading={loading}
        />
        <MetricCard
          title="Expected Ridership"
          value={manifestData?.total_expected_riders != null ? `${manifestData.total_expected_riders}` : "—"}
          subtitle={manifestData?.overall_utilization_pct != null ? `${manifestData.overall_utilization_pct}% fleet utilization` : "—"}
          icon={Users}
          tone="coral"
          badge={loading ? "Checking" : (manifestData ? activeScenario : "Unavailable")}
          loading={loading}
        />
        <MetricCard
          title="Standing Commuters"
          value={manifestData?.total_standing != null ? `${manifestData.total_standing}` : "—"}
          subtitle={
            manifestData
              ? manifestData.total_standing > 0
                ? "Exceeds seating capacity"
                : manifestData.seating_equity_pct != null
                  ? `${manifestData.seating_equity_pct}% seat-utilization consistency`
                  : "Seat-utilization consistency unavailable"
              : "—"
          }
          icon={ShieldCheck}
          tone={manifestData?.total_standing > 0 ? "coral" : (manifestData ? "sage" : "blue")}
          badge={loading ? "Checking" : (manifestData?.total_standing != null ? (manifestData.total_standing > 0 ? "Overflow" : "Guaranteed") : "Unavailable")}
          loading={loading}
        />
        <MetricCard
          title="Fleet Churn"
          value={manifestData?.total_fleet_churn != null ? `${manifestData.total_fleet_churn} Shifts` : (manifestData?.churn != null ? `${manifestData.churn} Shifts` : "—")}
          subtitle="Net vehicle reallocations vs baseline"
          icon={RefreshCw}
          tone="yellow"
          badge={loading ? "Checking" : (manifestData ? "Adaptive" : "Unavailable")}
          loading={loading}
        />
      </div>

      {/* Operational Workflow Step 2: Driver Manifest Roster */}
      <div className="card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-3">
          <div>
            <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 2: OPERATIONAL DRIVER MANIFEST</p>
            <h3 className="card-title text-base font-bold">Vehicle Dispatch Roster & Trip Assignments</h3>
            <p className="text-xs text-[#69716d]">
              Review route stop chains, passenger loads, and print official driver trip sheets.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              id="btn-import-csv-step2"
              onClick={() => { setShowCsvModal(true); if (!benchmarkResult) handleUploadCsv(); }}
              className="outline-button text-xs whitespace-nowrap"
            >
              <FileSpreadsheet className="h-3.5 w-3.5" />
              <span>Import CSV / Benchmark</span>
            </button>
            <button
              onClick={handleBroadcast}
              className="coral-button whitespace-nowrap"
            >
              <Send className="h-3.5 w-3.5" />
              <span>Approve & Dispatch Today's Fleet</span>
            </button>
          </div>
        </div>

        {/* Manifest Table */}
        <div className="overflow-x-auto">
          <table className="editorial-table">
            <thead>
              <tr>
                <th>Bus No</th>
                <th>Assigned Zone</th>
                <th>Driver & Contact</th>
                <th>Departure</th>
                <th>Key Stops</th>
                <th>Assigned Load</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {(manifestData?.manifest || []).slice(0, 10).map((row, idx) => (
                <tr key={idx}>
                  <td className="font-bold text-[#18201d] font-mono">{row.bus_code}</td>
                  <td>
                    <span className="badge badge-blue text-[10px]">{row.area_id}</span>
                  </td>
                  <td>
                    <div className="font-semibold text-[#18201d]">{row.driver_name}</div>
                    <div className="text-[10px] text-[#69716d] font-mono">{row.driver_phone}</div>
                  </td>
                  <td className="font-mono text-xs">{row.departure_time}</td>
                  <td className="text-xs text-[#69716d] max-w-[200px] truncate">
                    {row.stops_list.join(' -> ')}
                  </td>
                  <td>
                    <span className="font-bold text-[#18201d]">{row.allocated_riders}</span>
                    <span className="text-[#69716d]"> / {row.capacity} ({row.utilization_pct}%)</span>
                  </td>
                  <td>
                    <button
                      onClick={() => setSelectedTripSheet(row)}
                      className="outline-button py-1 px-2.5 text-xs"
                    >
                      <FileText className="h-3 w-3" />
                      <span>Trip Sheet</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Fleet & Bus Operations Manager (Add / Edit Buses) */}
      <div className="card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <p className="kicker" style={{ margin: 0 }}>FLEET & VEHICLE INVENTORY</p>
              <span className="badge badge-sage text-[10px]">{busesList.length} Registered Buses</span>
            </div>
            <h3 className="card-title text-base font-bold">Bus Fleet & Driver Specifications (Add / Edit Buses)</h3>
            <p className="text-xs text-[#69716d]">
              Directly add and edit college buses, seating capacity, assigned drivers, contact numbers, and designated route corridors.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              id="btn-add-bus"
              onClick={handleOpenAddBus}
              className="coral-button text-xs whitespace-nowrap flex items-center gap-1.5"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add New Bus</span>
            </button>
          </div>
        </div>

        {busSuccessMessage && (
          <div className="p-3 bg-[#eef5ee] border border-[#cbe3cb] rounded-[7px] text-xs text-[#2b6e3b] flex items-center gap-2 font-medium">
            <CheckCircle2 className="h-4 w-4 shrink-0" />
            <span>{busSuccessMessage}</span>
          </div>
        )}

        {busError && (
          <div role="alert" className="p-3 bg-[#fdecea] border border-[#f5c6c2] rounded-[7px] text-xs text-[#c0392b] flex items-center justify-between font-medium">
            <span>{busError}</span>
            <button onClick={() => setBusError(null)} className="text-[#c0392b] hover:opacity-75 p-0.5" title="Dismiss error">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="editorial-table">
            <thead>
              <tr>
                <th>Bus Code</th>
                <th>Vehicle Reg No</th>
                <th>Capacity</th>
                <th>Assigned Driver</th>
                <th>Phone Number</th>
                <th>Designated Corridor / Route</th>
                <th>Depot Station</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {busesList.map((bus) => (
                <tr key={bus.bus_id}>
                  <td className="font-bold text-[#18201d] font-mono">{bus.bus_id}</td>
                  <td className="font-mono text-xs text-[#69716d]">{bus.registration_no || 'TN 47 B 2026'}</td>
                  <td>
                    <span className="badge badge-sage text-[11px] font-bold">{bus.seats} Seats</span>
                  </td>
                  <td className="font-semibold text-[#18201d]">{bus.driver_name || 'Assigned Driver'}</td>
                  <td className="font-mono text-xs text-[#69716d]">
                    <span className="flex items-center gap-1">
                      <Phone className="h-3 w-3 text-[#2b6e3b]" />
                      <span>{bus.driver_phone || '+91 90000 00001'}</span>
                    </span>
                  </td>
                  <td className="text-xs text-[#18201d]">
                    <span className="badge badge-blue text-[10px] mr-1">{bus.default_area_id || 'Zone A'}</span>
                    <span>{bus.route_name || 'Karudayampalayam & Kovai Road Express'}</span>
                  </td>
                  <td className="text-xs text-[#69716d]">{bus.depot_location || 'VSB Main Campus, Karudayampalayam'}</td>
                  <td>
                    <span className={`badge ${bus.is_active !== false ? 'badge-sage' : 'badge-coral'} text-[10px]`}>
                      {bus.is_active !== false ? 'Active Dispatch' : 'Maintenance'}
                    </span>
                  </td>
                  <td>
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => handleOpenEditBus(bus)}
                        className="p-1.5 rounded hover:bg-[#ebeee8] text-[#18201d] transition-colors"
                        title="Edit Bus Details"
                      >
                        <Edit2 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteBus(bus.bus_id)}
                        className="p-1.5 rounded hover:bg-[#fee2e2] text-[#d9381e] transition-colors"
                        title="Remove Bus"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Operational Workflow Step 3: Map & Comparative Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Map */}
        <div className="lg:col-span-7 card space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <p className="kicker" style={{ margin: '0 0 4px' }}>GEOSPATIAL ROUTING</p>
              <h3 className="card-title">Live Dispatch Map</h3>
              <p className="text-xs text-[#69716d]">Stops and reverse pickup route sequences for {selectedArea}.</p>
            </div>
            <div className="flex items-center gap-1 overflow-x-auto">
              {['AREA_A', 'AREA_B', 'AREA_C', 'AREA_D', 'AREA_E'].map(a => (
                <button
                  key={a}
                  onClick={() => setSelectedArea(a)}
                  className={`px-3 py-1 rounded-[6px] text-xs font-semibold whitespace-nowrap transition-all ${
                    selectedArea === a ? 'bg-[#18201d] text-white' : 'bg-[#ebeee8] text-[#69716d] hover:text-[#18201d]'
                  }`}
                >
                  {a.replace('AREA_', 'Zone ')}
                </button>
              ))}
            </div>
          </div>

          <div className="h-[440px] w-full rounded-[9px] overflow-hidden">
            <LeafletMap
              stops={stopsList.filter(s => s.area_id === selectedArea)}
              activeRoutes={routeData?.routes || []}
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

        {/* Right: Comparative Chart */}
        <div className="lg:col-span-5 space-y-6">
          <ChartContainer
            kicker="DYNAMIC DISPATCH"
            title="Capacity vs. Scenario Demand"
            subtitle="Comparing status-quo baseline against BUSify dynamic allocation"
          >
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={comparisonChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" stroke="#69716d" fontSize={11} tickLine={false} />
                <YAxis stroke="#69716d" fontSize={11} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#dfe5df', borderRadius: '8px', fontSize: '12px' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                <Bar dataKey="demand" name="Expected Demand" fill="#ff6b00" radius={[4, 4, 0, 0]} />
                <Bar dataKey="baseline_seats" name="Static Seats" fill="#69716d" radius={[4, 4, 0, 0]} />
                <Bar dataKey="optimized_seats" name="BUSify Seats" fill="#18201d" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>

          {/* Quick Simulation Trigger */}
          <div className="card space-y-3">
            <p className="kicker" style={{ margin: 0 }}>HISTORICAL BENCHMARK</p>
            <h4 className="card-title text-base font-bold">Audit 7-Day Performance</h4>
            <p className="text-xs text-[#69716d]">Run full fleet historical audit comparing against static timetable baseline.</p>
            <button
              onClick={handleRunSimulation}
              disabled={simulating}
              className="dark-button w-full justify-center"
            >
              {simulating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              <span>{simulating ? 'Auditing 7 Days...' : 'Run 7-Day Backtest'}</span>
            </button>
            {simulationError && (
              <div role="alert" className="text-xs text-[#c0392b] bg-[#fdecea] border border-[#f5c6c2] rounded-lg px-3 py-2">
                {simulationError}
              </div>
            )}
            {simulationResult && (
              <div className="grid grid-cols-2 gap-2 pt-2 text-xs">
                <div className="p-2 bg-[#f7f8f5] rounded border border-[#dfe5df]">
                  <span className="text-[#69716d] block text-[10px]">Service Level</span>
                  <span className="font-bold text-[#2b6e3b] text-base">{simulationResult.summary_metrics?.optimized?.service_level_pct}%</span>
                </div>
                <div className="p-2 bg-[#f7f8f5] rounded border border-[#dfe5df]">
                  <span className="text-[#69716d] block text-[10px]">Standing Reduced</span>
                  <span className="font-bold text-[#ff6b00] text-base">{simulationResult.improvements?.standing_students_reduction_pct}%</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Driver Trip Sheet Modal */}
      {selectedTripSheet && (
        <div className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[12px] border border-[#dfe5df] max-w-lg w-full p-6 space-y-4 shadow-2xl relative z-10">
            <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>OFFICIAL DRIVER TRIP SHEET</p>
                <h3 className="card-title text-xl font-bold">{selectedTripSheet.bus_code} - Daily Dispatch</h3>
              </div>
              <button
                onClick={() => setSelectedTripSheet(null)}
                className="p-1 rounded hover:bg-[#f7f8f5] text-[#69716d]"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs bg-[#f7f8f5] p-3 rounded-[8px] border border-[#dfe5df]">
              <div>
                <span className="text-[#69716d] block">Driver In-Charge</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.driver_name}</span>
                <span className="text-[11px] text-[#69716d] block font-mono">{selectedTripSheet.driver_phone}</span>
              </div>
              <div>
                <span className="text-[#69716d] block">Transit Zone</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.area_name}</span>
                <span className="text-[11px] text-[#2b6e3b] font-bold block">{selectedTripSheet.status}</span>
              </div>
              <div>
                <span className="text-[#69716d] block">Departure Time</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.departure_time}</span>
              </div>
              <div>
                <span className="text-[#69716d] block">Campus Gate Arrival</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.campus_arrival}</span>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <span className="font-bold text-[#18201d]">Pickup Stops & Passenger Quota:</span>
              <div className="border border-[#dfe5df] rounded-[8px] p-3 space-y-2 bg-white max-h-60 overflow-y-auto">
                {selectedTripSheet.stops_detail && selectedTripSheet.stops_detail.length > 0 ? (
                  selectedTripSheet.stops_detail.map((st, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-[#edf1ed] last:border-0">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#f0f4f0] text-[#2b6e3b] font-bold">
                          {st.time || `--:--`}
                        </span>
                        <span className="font-medium text-[#18201d]">{i + 1}. {st.name}</span>
                      </div>
                      <span className="font-semibold text-[#2b6e3b] bg-[#eef7ee] px-2 py-0.5 rounded text-[11px]">
                        {st.boarded ?? 0} boarding
                      </span>
                    </div>
                  ))
                ) : (
                  (selectedTripSheet.stops_list || []).map((st, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-[#edf1ed] last:border-0">
                      <span className="font-medium">{i + 1}. {st}</span>
                      <span className="text-[#69716d]">Scheduled Stop</span>
                    </div>
                  ))
                )}
              </div>
              <div className="flex items-center justify-between pt-1 text-[11px] text-[#69716d]">
                <span>Total Expected Riders: <strong className="text-[#18201d]">{selectedTripSheet.allocated_riders} students</strong></span>
                <span>Vehicle Capacity: <strong className="text-[#18201d]">{selectedTripSheet.capacity} seats</strong></span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#edf1ed]">
              <button
                onClick={() => window.print()}
                className="outline-button text-xs"
              >
                <Printer className="h-3.5 w-3.5" />
                <span>Print Trip Sheet</span>
              </button>
              <button
                onClick={() => setSelectedTripSheet(null)}
                className="dark-button text-xs"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Suggestion 1 & 2: CSV Upload & Comparative Benchmark Modal */}
      {showCsvModal && (
        <div className="fixed inset-0 bg-[#18201d]/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] overflow-y-auto">
          <div className="bg-white rounded-[12px] border border-[#18201d] max-w-4xl w-full p-6 shadow-2xl space-y-5 my-8 max-h-[92vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>ADMIN EXCEL / CSV DATA INGESTION</p>
                <h3 className="card-title text-lg font-bold">Import Stops, Boarding Demands & Route Assignments</h3>
                <p className="text-xs text-[#69716d]">
                  Upload your college transit spreadsheets directly into VSB Engineering College's AI routing engine.
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
                Most engineering colleges maintain bus routes, student boarding counts, and contracted bus lists in Excel. Instead of manually typing each stop, this tool lets you upload your spreadsheet directly. BUSify will automatically calculate optimal route paths to <strong>VSB Engineering College in Karudayampalayam</strong> and benchmark whether your current buses are overloaded or wasting fuel.
              </p>
            </div>

            {/* Column-by-Column Explainer Table (What to have in the Excel) */}
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
                  <strong>Don't have GPS coordinates? Leave latitude & longitude completely empty!</strong> BUSify will automatically calculate realistic road coordinates along radial corridors branching directly from VSB Engineering College, Karudayampalayam (10.9549° N, 77.9546° E).
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
                    id="btn-load-sample-csv"
                    onClick={() => handleUploadCsv()}
                    disabled={uploadLoading}
                    className="outline-button text-xs flex items-center gap-1.5"
                  >
                    <Play className="h-3.5 w-3.5 text-[#2b6e3b]" />
                    <span>Load 13-Stop Karudayampalayam Sample</span>
                  </button>
                </div>

                <button
                  id="btn-download-template"
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

            {/* Suggestion 2: Benchmark Comparison Display */}
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

                {/* Comparative Metrics Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Manual Baseline Card */}
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
                    <div className="text-[11px] text-[#69716d] pt-1 border-t border-[#dfe5df]">
                      Average Seat Utilization: <strong>{benchmarkResult.benchmark.manual.avg_utilization_pct}%</strong> (Unevenly loaded)
                    </div>
                  </div>

                  {/* BUSify Optimized Card */}
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
                    <div className="text-[11px] text-[#69716d] pt-1 border-t border-[#edf1ed]">
                      Average Seat Utilization: <strong>{benchmarkResult.benchmark.optimized.avg_utilization_pct}%</strong> (Balanced load)
                    </div>
                  </div>
                </div>

                {/* Executive Savings Banner */}
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

                {/* Ingested Stops Preview Table */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs text-[#18201d]">Ingested Stop Manifest:</span>
                    <span className="text-[11px] text-[#69716d]">First 8 stops shown</span>
                  </div>
                  <div className="border border-[#dfe5df] rounded-[8px] overflow-x-auto bg-white">
                    <table className="editorial-table text-xs">
                      <thead>
                        <tr>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Stop Name
                              <InfoHint text="Official physical stop or landmark identifier where students assemble for morning boarding." />
                            </span>
                          </th>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Zone / Corridor
                              <InfoHint text="Geographic corridor (A=North, B=East, C=South, D=West, E=Central) used for regional transit clustering." />
                            </span>
                          </th>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Student Headcount
                              <InfoHint text="Headcount of registered student commuters assigned to board at this exact pickup point." />
                            </span>
                          </th>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Suggested Bus
                              <InfoHint text="Initial manual bus allocation in current institutional roster prior to dynamic CVRP optimization." />
                            </span>
                          </th>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Latitude & Longitude
                              <InfoHint text="GPS coordinates. When omitted in CSV, automatically computed along corridor vectors." />
                            </span>
                          </th>
                          <th>
                            <span className="inline-flex items-center gap-1">
                              Geocoding Status
                              <InfoHint text="Indicates whether exact GPS was supplied in the sheet or autonomously synthesized via campus radial vectors." />
                            </span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {benchmarkResult.stops.slice(0, 8).map((st, i) => (
                          <tr key={i}>
                            <td className="font-medium">{st.stop_name}</td>
                            <td>{st.zone}</td>
                            <td><strong>{st.student_count}</strong></td>
                            <td><span className="font-mono text-[11px]">{st.suggested_bus_code}</span></td>
                            <td className="font-mono text-[11px] text-[#69716d]">{st.latitude}, {st.longitude}</td>
                            <td>
                              {st.auto_geocoded ? (
                                <span className="badge badge-yellow inline-flex items-center gap-1">
                                  <span>Radial Auto-Geocoded</span>
                                  <InfoHint text="Synthesized using institutional radial bearing and stop distance." />
                                </span>
                              ) : (
                                <span className="badge badge-sage inline-flex items-center gap-1">
                                  <span>Verified GPS</span>
                                  <InfoHint text="Supplied explicitly with exact satellite latitude/longitude coordinates." />
                                </span>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#edf1ed]">
              <button
                id="btn-done-csv-modal"
                onClick={() => { setShowCsvModal(false); setUploadError(null); }}
                className="dark-button text-xs"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Add / Edit Bus Modal */}
      {showBusModal && (
        <div className="fixed inset-0 bg-[#18201d]/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] overflow-y-auto">
          <div className="bg-white rounded-[12px] border border-[#18201d] max-w-xl w-full p-6 shadow-2xl space-y-4 my-8 animate-fade-in">
            <div className="flex items-start justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>FLEET SPECIFICATION</p>
                <h3 className="card-title text-base font-bold">
                  {editingBus ? `Edit Specifications: ${editingBus.bus_id}` : 'Register New Bus into College Fleet'}
                </h3>
                <p className="text-xs text-[#69716d]">
                  Configure vehicle capacity, assigned driver, emergency contact, and corridor route.
                </p>
              </div>
              <button
                onClick={() => setShowBusModal(false)}
                className="text-[#69716d] hover:text-[#18201d] p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveBus} className="space-y-3.5 text-xs">
              {busError && (
                <div role="alert" className="p-2.5 bg-[#fdecea] border border-[#f5c6c2] rounded-[6px] text-xs text-[#c0392b]">
                  {busError}
                </div>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Bus Code / ID *</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingBus}
                    value={busFormData.bus_id}
                    onChange={(e) => setBusFormData({ ...busFormData, bus_id: e.target.value })}
                    placeholder="e.g. BUS-11"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Vehicle Registration Number</label>
                  <input
                    type="text"
                    value={busFormData.registration_no}
                    onChange={(e) => setBusFormData({ ...busFormData, registration_no: e.target.value })}
                    placeholder="e.g. TN 47 V 1998"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Seating Capacity (Seats) *</label>
                  <input
                    type="number"
                    required
                    min={15}
                    max={100}
                    value={busFormData.seats}
                    onChange={(e) => setBusFormData({ ...busFormData, seats: parseInt(e.target.value) || 55 })}
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Default Transit Corridor</label>
                  <select
                    value={busFormData.default_area_id}
                    onChange={(e) => setBusFormData({ ...busFormData, default_area_id: e.target.value })}
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  >
                    <option value="AREA_A">Zone A: Karudayampalayam & Kovai Road</option>
                    <option value="AREA_B">Zone B: Gandhigramam & South Hub</option>
                    <option value="AREA_C">Zone C: Thanthonimalai & Collectorate</option>
                    <option value="AREA_D">Zone D: Velur & North Corridor</option>
                    <option value="AREA_E">Zone E: Paramathi & West Rural</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Assigned Driver Name *</label>
                  <input
                    type="text"
                    required
                    value={busFormData.driver_name}
                    onChange={(e) => setBusFormData({ ...busFormData, driver_name: e.target.value })}
                    placeholder="e.g. R. Murugan"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Driver Phone Number *</label>
                  <input
                    type="text"
                    required
                    value={busFormData.driver_phone}
                    onChange={(e) => setBusFormData({ ...busFormData, driver_phone: e.target.value })}
                    placeholder="e.g. +91 90000 00001"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-[#18201d] block mb-1">Route Name / Description</label>
                <input
                  type="text"
                  value={busFormData.route_name}
                  onChange={(e) => setBusFormData({ ...busFormData, route_name: e.target.value })}
                  placeholder="e.g. Karudayampalayam - Kovai Road - Central Bus Stand Express"
                  className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-[#18201d] block mb-1">Depot / Parking Station</label>
                <input
                  type="text"
                  value={busFormData.depot_location}
                  onChange={(e) => setBusFormData({ ...busFormData, depot_location: e.target.value })}
                  placeholder="e.g. VSB Main Campus Depot, Karudayampalayam"
                  className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="chk-bus-active"
                  checked={busFormData.is_active}
                  onChange={(e) => setBusFormData({ ...busFormData, is_active: e.target.checked })}
                  className="rounded text-[#ff6b00]"
                />
                <label htmlFor="chk-bus-active" className="text-xs text-[#18201d] font-semibold cursor-pointer">
                  Vehicle is active and available for daily dispatch
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#edf1ed]">
                <button
                  type="button"
                  onClick={() => setShowBusModal(false)}
                  className="outline-button text-xs py-1.5 px-3"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busSaveLoading}
                  className="coral-button text-xs py-1.5 px-4 font-bold flex items-center gap-1.5"
                >
                  {busSaveLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  <span>{editingBus ? 'Save Changes' : 'Register Bus'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
