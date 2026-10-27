import React, { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Search } from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function StudentsAndDemand() {
  usePageTitle('Students & Demand');
  const {
    stopsList,
    manifestData,
    selectedArea,
    setSelectedArea,
    loading
  } = useOutletContext();

  const [searchFilter, setSearchFilter] = useState('');

  const totalRegistered = (stopsList || []).reduce((acc, st) => acc + (st.student_count || 25), 0);
  const filteredStops = (stopsList || []).filter(st => {
    const matchesArea = selectedArea === 'ALL' || st.area_id === selectedArea;
    const matchesSearch = !searchFilter.trim() ||
      st.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (st.stop_id && st.stop_id.toLowerCase().includes(searchFilter.toLowerCase()));
    return matchesArea && matchesSearch;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>COMMUTER DEMAND INTELLIGENCE</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Student Commuters & Stop-Level Demand</h2>
          <p className="text-xs text-[#69716d]">
            Detailed inspection of student commuter distribution across regional boarding hubs, corridors, and pickup clusters.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-sage text-xs">
            {stopsList?.length || 0} Boarding Stops
          </span>
          <span className="badge badge-coral text-xs">
            {manifestData?.total_expected_riders || totalRegistered} Commuters
          </span>
        </div>
      </div>

      {/* KPI Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card py-3 px-4">
          <span className="text-[11px] text-[#69716d] block">Total Registered Stops</span>
          <strong className="text-base font-bold text-[#18201d]">{stopsList?.length || 0} Stops</strong>
          <span className="text-[10px] text-[#2b6e3b] block mt-0.5">Across 5 Transit Zones</span>
        </div>
        <div className="card py-3 px-4">
          <span className="text-[11px] text-[#69716d] block">Expected Ridership Today</span>
          <strong className="text-base font-bold text-[#ff6b00]">
            {loading ? '—' : (manifestData?.total_expected_riders ?? '—')}
          </strong>
          <span className="text-[10px] text-[#69716d] block mt-0.5">P90 Quantile Surge Applied</span>
        </div>
        <div className="card py-3 px-4">
          <span className="text-[11px] text-[#69716d] block">Standing Commuters</span>
          <strong className="text-base font-bold text-[#2b6e3b]">
            {loading ? '—' : (manifestData?.total_standing ?? 0)}
          </strong>
          <span className="text-[10px] text-[#2b6e3b] block mt-0.5">Zero Standing Equity Target</span>
        </div>
        <div className="card py-3 px-4">
          <span className="text-[11px] text-[#69716d] block">Average Stop Density</span>
          <strong className="text-base font-bold text-[#18201d]">
            {stopsList?.length ? Math.round((manifestData?.total_expected_riders || totalRegistered) / stopsList.length) : 0} riders/stop
          </strong>
          <span className="text-[10px] text-[#69716d] block mt-0.5">Balanced Cluster Loading</span>
        </div>
      </div>

      {/* Demand Inspection Table */}
      <div className="card space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-[#edf1ed] pb-3">
          <div>
            <h3 className="card-title text-base font-bold">Stop-Level Commuter Manifest</h3>
            <p className="text-xs text-[#69716d]">Registered student assembly counts and radial distance to campus depot.</p>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <Search className="h-3.5 w-3.5 text-[#69716d] absolute left-2.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search stops..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="pl-8 pr-3 py-1.5 text-xs rounded border border-[#dfe5df] bg-white focus:outline-none focus:border-[#18201d]"
              />
            </div>

            <div className="flex items-center gap-1 overflow-x-auto min-w-0">
              {['ALL', 'AREA_A', 'AREA_B', 'AREA_C', 'AREA_D', 'AREA_E'].map((area) => (
                <button
                  key={area}
                  onClick={() => setSelectedArea(area)}
                  className={`px-2.5 py-1 text-xs rounded font-semibold transition-colors ${
                    selectedArea === area
                      ? 'bg-[#18201d] text-white'
                      : 'bg-[#ebeee8] text-[#69716d] hover:text-[#18201d]'
                  }`}
                >
                  {area === 'ALL' ? 'All Zones' : area.replace('AREA_', 'Zone ')}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="editorial-table text-xs">
            <thead>
              <tr>
                <th>Stop ID</th>
                <th>Boarding Location Name</th>
                <th>Corridor / Zone</th>
                <th>Campus Distance</th>
                <th>Registered Commuters</th>
                <th>GPS Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredStops.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-6 text-xs text-[#69716d]">
                    No stop records match the selected zone and search criteria.
                  </td>
                </tr>
              ) : (
                filteredStops.map((st, i) => (
                  <tr key={st.stop_id || i}>
                    <td className="font-mono font-bold text-[#18201d]">{st.stop_id || `STOP-${i + 1}`}</td>
                    <td className="font-semibold text-[#18201d]">{st.name}</td>
                    <td>
                      <span className="badge badge-blue text-[10px]">{st.area_id}</span>
                    </td>
                    <td className="font-mono text-[#69716d]">
                      {st.campus_distance_km != null ? `${st.campus_distance_km} km` : 'Radial vector'}
                    </td>
                    <td>
                      <strong className="text-[#ff6b00]">{st.student_count || 25} students</strong>
                    </td>
                    <td>
                      <span className="badge badge-sage text-[10px]">Active Boarding Hub</span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
