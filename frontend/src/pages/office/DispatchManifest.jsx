import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileSpreadsheet,
  Send,
  FileText,
  Check,
  Printer,
  X
} from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function DispatchManifest() {
  usePageTitle('Dispatch Manifest');
  const {
    manifestData,
    loading,
    selectedTripSheet,
    setSelectedTripSheet,
    broadcastConfirmed,
    handleBroadcast,
    setShowCsvModal,
    benchmarkResult,
    handleUploadCsv
  } = useOutletContext();

  const manifestRows = manifestData?.manifest || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 2: OPERATIONAL DRIVER MANIFEST</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Vehicle Dispatch Roster & Trip Sheets</h2>
          <p className="text-xs text-[#69716d]">
            Review stop sequences, allocated passenger loads, and print official driver trip sheets for today's active fleet.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            id="btn-import-csv-manifest-page"
            onClick={() => { setShowCsvModal(true); if (!benchmarkResult) handleUploadCsv(); }}
            className="outline-button text-xs whitespace-nowrap"
          >
            <FileSpreadsheet className="h-3.5 w-3.5" />
            <span>Import CSV / Benchmark</span>
          </button>
          <button
            onClick={handleBroadcast}
            className="coral-button whitespace-nowrap text-xs"
          >
            <Send className="h-3.5 w-3.5" />
            <span>Approve & Dispatch Today's Fleet</span>
          </button>
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

      {/* Summary KPI Cards for Manifest */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card py-3 px-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-[#69716d] block">Total Deployed Fleet</span>
            <strong className="text-base font-bold text-[#18201d]">
              {loading ? '—' : `${manifestData?.total_active_buses ?? 0} Buses`}
            </strong>
          </div>
          <span className="badge badge-sage text-xs">Active</span>
        </div>
        <div className="card py-3 px-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-[#69716d] block">Total Passenger Load</span>
            <strong className="text-base font-bold text-[#18201d]">
              {loading ? '—' : `${manifestData?.total_expected_riders ?? 0} Students`}
            </strong>
          </div>
          <span className="badge badge-coral text-xs">
            {manifestData?.overall_utilization_pct != null ? `${manifestData.overall_utilization_pct}% Utilized` : '—'}
          </span>
        </div>
        <div className="card py-3 px-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-[#69716d] block">Standing Commuters</span>
            <strong className="text-base font-bold text-[#2b6e3b]">
              {loading ? '—' : `${manifestData?.total_standing ?? 0} (Strict Cap)`}
            </strong>
          </div>
          <span className="badge badge-blue text-xs">Zero Standing</span>
        </div>
      </div>

      {/* Manifest Table Card */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
          <div>
            <h3 className="card-title text-base font-bold">Vehicle Dispatch Roster</h3>
            <p className="text-xs text-[#69716d]">Official morning pickup assignment per vehicle.</p>
          </div>
          <span className="badge badge-sage text-xs">{manifestRows.length} Scheduled Trips</span>
        </div>

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
              {manifestRows.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-6 text-xs text-[#69716d]">
                    {loading ? 'Loading operational manifest roster...' : 'No manifest records available for this date.'}
                  </td>
                </tr>
              ) : (
                manifestRows.slice(0, 15).map((row, idx) => (
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
                    <td className="text-xs text-[#69716d] max-w-[220px] truncate" title={(row.stops_list || []).join(' → ')}>
                      {(row.stops_list || []).join(' → ')}
                    </td>
                    <td>
                      <span className="font-bold text-[#18201d]">{row.allocated_riders}</span>
                      <span className="text-[#69716d]"> / {row.capacity} ({row.utilization_pct}%)</span>
                    </td>
                    <td>
                      <button
                        onClick={() => setSelectedTripSheet(row)}
                        className="outline-button py-1 px-2.5 text-xs flex items-center gap-1"
                      >
                        <FileText className="h-3 w-3" />
                        <span>Trip Sheet</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Driver Trip Sheet Modal */}
      {selectedTripSheet && (
        <div className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-[12px] border border-[#dfe5df] max-w-lg w-full p-6 space-y-4 shadow-2xl relative z-10 animate-fade-in">
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
                <span className="font-bold text-[#18201d]">{selectedTripSheet.area_name || selectedTripSheet.area_id}</span>
                <span className="text-[11px] text-[#2b6e3b] font-bold block">{selectedTripSheet.status || 'Active Dispatch'}</span>
              </div>
              <div>
                <span className="text-[#69716d] block">Departure Time</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.departure_time}</span>
              </div>
              <div>
                <span className="text-[#69716d] block">Campus Gate Arrival</span>
                <span className="font-bold text-[#18201d]">{selectedTripSheet.campus_arrival || '08:30 AM'}</span>
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
    </div>
  );
}
