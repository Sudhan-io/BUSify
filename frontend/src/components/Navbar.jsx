import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { LayoutDashboard, UserCheck, Calendar, Building2, ChevronDown, Plus, X, MapPin } from 'lucide-react';
import { statusColor, statusLabel } from '../constants/status';

export default function Navbar({
  activeRole: _activeRole,
  setActiveRole,
  selectedDate,
  setSelectedDate,
  backendStatus,
  activeInstitution,
  institutionsList = [],
  onSelectInstitution,
  onCreateInstitution,
  session = { authenticated: false, role: null, name: null },
  onRequestSignIn,
  onLogout
}) {
  const location = useLocation();
  const navigate = useNavigate();
  const isStudent = location.pathname.startsWith('/student');
  const isOffice = !isStudent;

  const [showCampusMenu, setShowCampusMenu] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);

  // New College Form State
  const [formData, setFormData] = useState({
    name: '',
    short_name: '',
    city: 'Trichy',
    campus_lat: '10.9601',
    campus_lng: '78.0766',
    fleet_size: 10,
    bus_capacity: 55,
  });
  const [formError, setFormError] = useState(null);

  // Parses an integer field, returning undefined when invalid so the backend
  // applies its own documented default. The previous `|| 8` silently forced a
  // fleet of 8 buses regardless of the backend's default of 45.
  const toIntOrUndefined = (value) => {
    const parsed = parseInt(value, 10);
    return Number.isFinite(parsed) ? parsed : undefined;
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim()) {
      setFormError('Institution name is required.');
      return;
    }
    const lat = parseFloat(formData.campus_lat);
    const lng = parseFloat(formData.campus_lng);
    if (isNaN(lat) || isNaN(lng)) {
      setFormError('Valid Latitude and Longitude coordinates are required.');
      return;
    }

    try {
      if (onCreateInstitution) {
        // Field names here are translated to the API contract
        // (campus_code / total_fleet_size / default_capacity) in services/api.js.
        await onCreateInstitution({
          name: formData.name.trim(),
          short_name: formData.short_name.trim() || formData.name.substring(0, 8),
          city: formData.city.trim() || 'Tamil Nadu',
          campus_lat: lat,
          campus_lng: lng,
          fleet_size: toIntOrUndefined(formData.fleet_size),
          bus_capacity: toIntOrUndefined(formData.bus_capacity),
        });
      }
      setShowAddModal(false);
      setShowCampusMenu(false);
      setFormError(null);
      // Reset form
      setFormData({
        name: '',
        short_name: '',
        city: 'Trichy',
        campus_lat: '10.9601',
        campus_lng: '78.0766',
        fleet_size: 10,
        bus_capacity: 55,
      });
    } catch (err) {
      setFormError(err.message || 'Failed to register institution.');
    }
  };

  const setPresetCampus = (preset) => {
    setFormData({
      name: preset.name,
      short_name: preset.short_name,
      city: preset.city,
      campus_lat: String(preset.lat),
      campus_lng: String(preset.lng),
      fleet_size: preset.fleet,
      bus_capacity: 55,
    });
  };

  return (
    <>
      <header className="topbar">
        {/* Brand & Identity (Editorial) */}
        <div className="flex items-center gap-3">
          <Link className="brand" to="/office/overview" aria-label="BUSify Home">
            <span className="brand-mark">B</span>
            <div className="brand-title">
              <span className="brand-name">BUSIFY</span>
              <span className="brand-sub">Transit Intelligence</span>
            </div>
          </Link>

          {/* Scalable Multi-College Switcher Dropdown */}
          <div className="relative">
            <button
              type="button"
              id="btn-campus-switcher"
              onClick={() => setShowCampusMenu(!showCampusMenu)}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-[7px] border border-[#dfe5df] bg-white text-xs font-semibold text-[#18201d] hover:border-[#18201d] transition-all"
              title="Switch or Register Institution"
            >
              <Building2 className="h-3.5 w-3.5 text-[#ff6b00]" />
              <span className="max-w-[140px] truncate">
                {activeInstitution?.short_name || activeInstitution?.name || 'VSB Karur'}
              </span>
              <ChevronDown className="h-3 w-3 text-[#69716d]" />
            </button>

            {/* Dropdown Menu */}
            {showCampusMenu && (
              <div className="absolute left-0 top-full mt-1.5 w-72 bg-white rounded-[9px] border border-[#dfe5df] shadow-xl z-[2000] p-2 space-y-1 animate-fade-in text-xs">
                <div className="px-2 py-1 border-b border-[#edf1ed] flex items-center justify-between text-[#69716d]">
                  <span className="font-bold text-[10px] uppercase tracking-wider">Active Campus</span>
                  <span className="text-[10px]">{institutionsList.length} Registered</span>
                </div>

                <div className="max-h-60 overflow-y-auto space-y-0.5 py-1">
                  {institutionsList.map((inst) => {
                    const isActive = activeInstitution?.id === inst.id;
                    return (
                      <button
                        key={inst.id}
                        type="button"
                        onClick={() => {
                          if (onSelectInstitution) onSelectInstitution(inst);
                          setShowCampusMenu(false);
                        }}
                        className={`w-full text-left p-2 rounded-[6px] flex items-start justify-between gap-2 transition-colors ${
                          isActive
                            ? 'bg-[#18201d] text-white'
                            : 'hover:bg-[#f7f8f5] text-[#18201d]'
                        }`}
                      >
                        <div>
                          <div className="font-semibold text-xs leading-tight">{inst.name}</div>
                          <div className={`text-[10px] flex items-center gap-1.5 mt-0.5 ${isActive ? 'text-white/70' : 'text-[#69716d]'}`}>
                            <MapPin className="h-2.5 w-2.5" />
                            <span>{inst.city}</span>
                            <span>&bull;</span>
                            <span>{inst.fleet_size || 8} Buses</span>
                          </div>
                        </div>
                        {isActive && (
                          <span className="badge badge-sage text-[9px] py-0 shrink-0">Current</span>
                        )}
                      </button>
                    );
                  })}
                </div>

                <div className="pt-1.5 border-t border-[#edf1ed]">
                  <button
                    type="button"
                    id="btn-add-college-trigger"
                    onClick={() => {
                      setShowCampusMenu(false);
                      setShowAddModal(true);
                    }}
                    className="w-full p-2 rounded-[6px] border border-dashed border-[#18201d] text-[#18201d] hover:bg-[#f7f8f5] flex items-center justify-center gap-1.5 font-semibold text-xs transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5 text-[#ff6b00]" />
                    <span>+ Register New College / Campus</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Role Switcher Tabs */}
        <div className="role-tabs">
          <button
            type="button"
            onClick={() => {
              setActiveRole?.('office');
              navigate('/office/overview');
            }}
            className={`role-tab ${isOffice ? 'active' : ''}`}
          >
            <LayoutDashboard className="h-3.5 w-3.5" />
            <span>Transport Office</span>
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveRole?.('student');
              navigate('/student');
            }}
            className={`role-tab ${isStudent ? 'active' : ''}`}
          >
            <UserCheck className="h-3.5 w-3.5" />
            <span>Student Commuter</span>
          </button>
        </div>

        {/* Controls & API Status */}
        <div className="flex items-center gap-3">
          {/* Date Selector */}
          <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-[7px] border border-[#dfe5df] text-xs text-[#18201d]">
            <Calendar className="h-3.5 w-3.5 text-[#69716d]" />
            <input
              type="date"
              value={selectedDate}
              onChange={(e) => setSelectedDate(e.target.value)}
              className="bg-transparent text-[#18201d] focus:outline-none cursor-pointer font-medium"
            />
          </div>

          {/* Live Status Indicator */}
          <div className="hidden sm:flex items-center gap-2 text-xs font-semibold text-[#18201d]">
            <span
              className="status-dot"
              style={{ background: statusColor(backendStatus) }}
              role="status"
              aria-label={`Backend status: ${backendStatus}`}
            />
            <span>{statusLabel(backendStatus)}</span>
            <span className="text-[#69716d] font-normal">&bull; SDG 10 & 11</span>
          </div>

          {/* Officer session control */}
          <div className="flex items-center gap-2 text-xs">
            {session.authenticated ? (
              <>
                <span
                  className="hidden md:inline text-[#69716d] font-normal"
                  title={`Signed in role: ${session.role}`}
                >
                  {session.name || session.role}
                </span>
                <button
                  type="button"
                  onClick={onLogout}
                  className="rounded-lg border border-[#dfe5df] px-3 py-1.5 font-semibold text-[#18201d]
                             hover:bg-[#f2f5f1] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#ff6b00]"
                >
                  Sign out
                </button>
              </>
            ) : (
              <button
                type="button"
                onClick={onRequestSignIn}
                className="rounded-lg bg-[#ff6b00] px-3 py-1.5 font-semibold text-white
                           focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#18201d]"
              >
                Officer sign-in
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Add College / Institution Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-[#18201d]/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] overflow-y-auto">
          <div className="bg-white rounded-[12px] border border-[#18201d] max-w-lg w-full p-6 shadow-2xl space-y-4 my-8 max-h-[92vh] overflow-y-auto animate-fade-in text-xs">
            <div className="flex items-start justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>MULTI-CAMPUS SCALABILITY</p>
                <h3 className="card-title text-base font-bold">Register New College or University</h3>
                <p className="text-xs text-[#69716d]">
                  Configure campus central depot coordinates. All radial geocoding, route generation, and fleet optimization will dynamically anchor here.
                </p>
              </div>
              <button
                onClick={() => { setShowAddModal(false); setFormError(null); }}
                className="text-[#69716d] hover:text-[#18201d] p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Quick Fill Presets */}
            <div className="space-y-1.5 p-3 bg-[#f7f8f5] rounded-[8px] border border-[#dfe5df]">
              <span className="text-[10px] font-bold uppercase tracking-wider text-[#69716d] block">
                Quick-Select Regional Presets:
              </span>
              <div className="flex flex-wrap gap-1.5">
                {[
                  { name: 'Vellore Institute of Technology', short_name: 'VIT Vellore', city: 'Vellore', lat: 12.9698, lng: 79.1559, fleet: 16 },
                  { name: 'Thiagarajar College of Engineering', short_name: 'TCE Madurai', city: 'Madurai', lat: 9.8826, lng: 78.0818, fleet: 10 },
                  { name: 'Government College of Tech Coimbatore', short_name: 'GCT CBE', city: 'Coimbatore', lat: 11.0189, lng: 76.9358, fleet: 12 },
                  { name: 'SRM Institute of Science & Tech', short_name: 'SRM Chennai', city: 'Chennai', lat: 12.8230, lng: 80.0444, fleet: 22 },
                ].map((pre) => (
                  <button
                    key={pre.short_name}
                    type="button"
                    onClick={() => setPresetCampus(pre)}
                    className="px-2 py-1 bg-white hover:bg-[#18201d] hover:text-white rounded border border-[#dfe5df] text-[11px] font-medium transition-colors"
                  >
                    {pre.short_name}
                  </button>
                ))}
              </div>
            </div>

            {/* Form */}
            <form onSubmit={handleCreateSubmit} className="space-y-3">
              <div>
                <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                  Full Institution Name *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Government College of Technology"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs focus:outline-none focus:border-[#18201d]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    Short Display Code
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. GCT CBE"
                    value={formData.short_name}
                    onChange={(e) => setFormData({ ...formData, short_name: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs focus:outline-none focus:border-[#18201d]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    City / District
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Coimbatore"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs focus:outline-none focus:border-[#18201d]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    Campus Depot Latitude *
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    placeholder="10.9601"
                    value={formData.campus_lat}
                    onChange={(e) => setFormData({ ...formData, campus_lat: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs font-mono focus:outline-none focus:border-[#18201d]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    Campus Depot Longitude *
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    required
                    placeholder="78.0766"
                    value={formData.campus_lng}
                    onChange={(e) => setFormData({ ...formData, campus_lng: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs font-mono focus:outline-none focus:border-[#18201d]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    Active Fleet Sizing (Buses)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={formData.fleet_size}
                    onChange={(e) => setFormData({ ...formData, fleet_size: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs focus:outline-none focus:border-[#18201d]"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-semibold text-[#18201d] mb-1">
                    Standard Bus Capacity (Seats)
                  </label>
                  <input
                    type="number"
                    min="20"
                    max="80"
                    value={formData.bus_capacity}
                    onChange={(e) => setFormData({ ...formData, bus_capacity: e.target.value })}
                    className="w-full px-3 py-2 border border-[#dfe5df] rounded-[6px] text-xs focus:outline-none focus:border-[#18201d]"
                  />
                </div>
              </div>

              {formError && (
                <div className="p-2.5 bg-[#fff0f0] border border-[#ffcccc] rounded-[6px] text-xs text-[#c00]">
                  {formError}
                </div>
              )}

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#edf1ed]">
                <button
                  type="button"
                  onClick={() => { setShowAddModal(false); setFormError(null); }}
                  className="outline-button text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  id="btn-submit-add-campus"
                  className="coral-button text-xs font-semibold"
                >
                  Register & Activate Campus
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
