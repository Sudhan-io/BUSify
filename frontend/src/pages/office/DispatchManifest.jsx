import React, { useState, useMemo, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  FileSpreadsheet,
  Send,
  FileText,
  Check,
  Printer,
  X,
  ChevronLeft,
  ChevronRight,
  AlertCircle,
  Filter,
  ShieldCheck,
  RefreshCw
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
    approvingPlan,
    planApprovalError,
    setPlanApprovalError,
    planApprovalSuccess,
    setShowCsvModal,
    benchmarkResult,
    handleUploadCsv,
    isAuthenticated,
    onRequestSignIn
  } = useOutletContext();

  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [zoneFilter, setZoneFilter] = useState('ALL');

  const manifestRows = useMemo(() => manifestData?.manifest || [], [manifestData?.manifest]);
  const isApproved = manifestData?.is_approved || manifestData?.plan_status === 'APPROVED';
  const hasInsufficientFleet = manifestData?.has_insufficient_fleet;

  // Filter rows by zone if selected
  const filteredRows = useMemo(() => {
    if (zoneFilter === 'ALL') return manifestRows;
    return manifestRows.filter((r) => r.area_id === zoneFilter);
  }, [manifestRows, zoneFilter]);

  // Pagination calculations (Resolves M-09)
  const effectivePageSize = pageSize === 'ALL' ? filteredRows.length : Number(pageSize);
  const totalPages = Math.max(1, Math.ceil(filteredRows.length / (effectivePageSize || 1)));
  const safePage = Math.min(currentPage, totalPages);

  const paginatedRows = useMemo(() => {
    if (pageSize === 'ALL') return filteredRows;
    const start = (safePage - 1) * effectivePageSize;
    return filteredRows.slice(start, start + effectivePageSize);
  }, [filteredRows, safePage, effectivePageSize, pageSize]);

  const startRecord = filteredRows.length === 0 ? 0 : (safePage - 1) * (pageSize === 'ALL' ? filteredRows.length : effectivePageSize) + 1;
  const endRecord = pageSize === 'ALL' ? filteredRows.length : Math.min(safePage * effectivePageSize, filteredRows.length);

  const handleZoneFilterChange = (zone) => {
    setZoneFilter(zone);
    setCurrentPage(1);
  };

  useEffect(() => {
    if (!selectedTripSheet) return;
    const handleTripSheetKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedTripSheet(null);
      }
    };
    window.addEventListener('keydown', handleTripSheetKeyDown);
    return () => window.removeEventListener('keydown', handleTripSheetKeyDown);
  }, [selectedTripSheet, setSelectedTripSheet]);

  const handlePageSizeChange = (size) => {
    setPageSize(size);
    setCurrentPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 2: OPERATIONAL DRIVER MANIFEST</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Vehicle Dispatch Roster & Trip Sheets</h2>
          <p className="text-xs text-[#69716d]">
            Review stop sequences, allocated passenger loads, and persist official driver trip sheets for today's active fleet.
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
            onClick={() => {
              if (!isAuthenticated) {
                onRequestSignIn?.();
              } else {
                handleBroadcast();
              }
            }}
            disabled={approvingPlan || loading || manifestRows.length === 0 || hasInsufficientFleet}
            className={`whitespace-nowrap text-xs flex items-center gap-1.5 ${
              hasInsufficientFleet
                ? 'bg-[#dfe5df] text-[#69716d] cursor-not-allowed py-2 px-3 rounded-[8px]'
                : isApproved
                ? 'bg-[#2b6e3b] text-white py-2 px-3 rounded-[8px] hover:bg-[#235830] transition-colors'
                : 'coral-button'
            }`}
          >
            {approvingPlan ? (
              <>
                <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                <span>Persisting Plan...</span>
              </>
            ) : isApproved ? (
              <>
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Re-Approve & Save Dispatch</span>
              </>
            ) : (
              <>
                <Send className="h-3.5 w-3.5" />
                <span>Approve & Dispatch Today's Fleet</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Plan Approval Error Banner */}
      {planApprovalError && (
        <div className="p-3.5 rounded-[8px] bg-[#fdf2f2] border border-[#f8b4b4] flex items-center justify-between text-xs text-[#9b1c1c]">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span><strong>Approval Error:</strong> {planApprovalError}</span>
          </div>
          <button
            onClick={() => setPlanApprovalError(null)}
            className="text-[#9b1c1c] hover:opacity-75"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Insufficient Fleet Warning */}
      {hasInsufficientFleet && (
        <div className="p-3.5 rounded-[8px] bg-[#fff8f0] border border-[#ffd8a8] flex items-start gap-2.5 text-xs text-[#d9480f]">
          <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
          <div>
            <strong>Fleet Shortage Detected:</strong> Available active buses in database are fewer than the required optimal corridor allocation. Unassigned routes cannot be dispatched until additional vehicles are activated under Fleet & Drivers.
          </div>
        </div>
      )}

      {/* Broadcast / Plan Approved Success Banner */}
      {(broadcastConfirmed || isApproved) && !planApprovalError && (
        <div className="banner">
          <div className="banner-icon">
            <Check className="h-4 w-4" />
          </div>
          <div className="banner-body">
            <strong>Daily Dispatch Manifest Officially Persisted to Database</strong>
            <span>
              {planApprovalSuccess || `All ${manifestData?.total_active_buses ?? manifestRows.length} vehicle routes and driver trip sheets are approved in the plans registry.`}
            </span>
          </div>
          <span className="badge badge-sage">Plan Persisted</span>
        </div>
      )}

      {/* Summary KPI Cards for Manifest */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
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
            <span className="text-[11px] text-[#69716d] block">Seating Equity</span>
            <strong className="text-base font-bold text-[#2b6e3b]">
              {loading ? '—' : `${manifestData?.seating_equity_pct ?? 100}%`}
            </strong>
          </div>
          <span className="badge badge-blue text-xs">Balanced</span>
        </div>
        <div className="card py-3 px-4 flex items-center justify-between">
          <div>
            <span className="text-[11px] text-[#69716d] block">Plan Registry Status</span>
            <strong className="text-base font-bold text-[#18201d]">
              {loading ? '—' : isApproved ? 'Approved' : 'Draft'}
            </strong>
          </div>
          <span className={`badge text-xs ${isApproved ? 'badge-sage' : 'badge-blue'}`}>
            {isApproved ? 'DB Persisted' : 'Unsaved Draft'}
          </span>
        </div>
      </div>

      {/* Manifest Table Card */}
      <div className="card space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-3">
          <div>
            <h3 className="card-title text-base font-bold">Vehicle Dispatch Roster</h3>
            <p className="text-xs text-[#69716d]">Official morning pickup assignment sourced from database fleet records.</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            {/* Zone Filter Dropdown */}
            <div className="flex items-center gap-1.5 text-xs text-[#69716d]">
              <Filter className="h-3.5 w-3.5" />
              <select
                value={zoneFilter}
                onChange={(e) => handleZoneFilterChange(e.target.value)}
                className="rounded border border-[#dfe5df] bg-white px-2 py-1 text-xs text-[#18201d] focus:outline-none focus:border-[#18201d]"
                aria-label="Filter routes by zone"
              >
                <option value="ALL">All Zones ({manifestRows.length})</option>
                <option value="AREA_A">Zone A</option>
                <option value="AREA_B">Zone B</option>
                <option value="AREA_C">Zone C</option>
                <option value="AREA_D">Zone D</option>
                <option value="AREA_E">Zone E</option>
              </select>
            </div>

            {/* Page Size Selector (Resolves M-09) */}
            <div className="flex items-center gap-1.5 text-xs text-[#69716d]">
              <span>Show:</span>
              <select
                value={pageSize}
                onChange={(e) => handlePageSizeChange(e.target.value)}
                className="rounded border border-[#dfe5df] bg-white px-2 py-1 text-xs text-[#18201d] focus:outline-none focus:border-[#18201d]"
                aria-label="Records per page"
              >
                <option value="10">10</option>
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="ALL">All ({filteredRows.length})</option>
              </select>
            </div>
            <span className="badge badge-sage text-xs">{filteredRows.length} Scheduled Trips</span>
          </div>
        </div>

        {/* Table View */}
        <div className="overflow-x-auto">
          <table className="editorial-table text-xs">
            <thead>
              <tr>
                <th>Bus No</th>
                <th>Assigned Zone</th>
                <th>Driver & Contact</th>
                <th>Departure</th>
                <th>Key Stops</th>
                <th>Assigned Load</th>
                <th>Plan Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRows.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-8 text-xs text-[#69716d]">
                    {loading ? 'Loading operational manifest roster...' : 'No manifest records available for this filter.'}
                  </td>
                </tr>
              ) : (
                paginatedRows.map((row, idx) => {
                  const isUnassigned = row.bus_code === 'UNASSIGNED';
                  return (
                    <tr key={idx} className={isUnassigned ? 'bg-[#fff5f5]' : undefined}>
                      <td className="font-bold text-[#18201d] font-mono">
                        {isUnassigned ? (
                          <span className="badge badge-coral text-[10px]">Unassigned</span>
                        ) : (
                          row.bus_code
                        )}
                      </td>
                      <td>
                        <span className="badge badge-blue text-[10px]">{row.area_id}</span>
                      </td>
                      <td>
                        <div className={`font-semibold ${isUnassigned ? 'text-[#c81e1e]' : 'text-[#18201d]'}`}>
                          {row.driver_name}
                        </div>
                        <div className="text-[10px] text-[#69716d] font-mono">{row.driver_phone}</div>
                      </td>
                      <td className="font-mono text-xs">{row.departure_time}</td>
                      <td className="text-xs text-[#69716d] max-w-[200px] truncate" title={(row.stops_list || []).join(' → ')}>
                        {(row.stops_list || []).join(' → ')}
                      </td>
                      <td>
                        <span className="font-bold text-[#18201d]">{row.allocated_riders}</span>
                        <span className="text-[#69716d]"> / {row.capacity} ({row.utilization_pct}%)</span>
                      </td>
                      <td>
                        {isApproved ? (
                          <span className="badge badge-sage text-[10px]">Approved</span>
                        ) : isUnassigned ? (
                          <span className="badge badge-coral text-[10px]">Shortage</span>
                        ) : (
                          <span className="badge badge-blue text-[10px]">Draft</span>
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          onClick={() => setSelectedTripSheet(row)}
                          disabled={isUnassigned}
                          className="outline-button py-1 px-2.5 text-xs flex items-center gap-1 disabled:opacity-50"
                        >
                          <FileText className="h-3 w-3" />
                          <span>Trip Sheet</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Functional Pagination Controls (Resolves M-09) */}
        {filteredRows.length > 0 && pageSize !== 'ALL' && (
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-[#edf1ed] text-xs text-[#69716d]">
            <div>
              Showing <strong>{startRecord}</strong> to <strong>{endRecord}</strong> of <strong>{filteredRows.length}</strong> trips
            </div>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={safePage <= 1}
                className="outline-button py-1 px-2 text-xs flex items-center gap-1 disabled:opacity-40"
                aria-label="Previous page"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <span>Prev</span>
              </button>

              <div className="flex items-center gap-1 px-1">
                {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setCurrentPage(p)}
                    className={`h-6 w-6 rounded text-xs font-semibold flex items-center justify-center transition-colors ${
                      safePage === p
                        ? 'bg-[#18201d] text-white'
                        : 'text-[#69716d] hover:bg-[#f7f8f5] border border-[#dfe5df]'
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={safePage >= totalPages}
                className="outline-button py-1 px-2 text-xs flex items-center gap-1 disabled:opacity-40"
                aria-label="Next page"
              >
                <span>Next</span>
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Driver Trip Sheet Modal */}
      {selectedTripSheet && (
        <div className="fixed inset-0 z-[9999] bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="trip-sheet-title"
            className="bg-white rounded-[12px] border border-[#dfe5df] max-w-lg w-full p-6 space-y-4 shadow-2xl relative z-10 animate-fade-in"
          >
            <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>OFFICIAL DRIVER TRIP SHEET</p>
                <h3 id="trip-sheet-title" className="card-title text-xl font-bold">
                  {selectedTripSheet.bus_code} - Daily Dispatch
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedTripSheet(null)}
                className="p-1 rounded hover:bg-[#f7f8f5] text-[#69716d]"
                aria-label="Close trip sheet"
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
                <span className="text-[11px] text-[#2b6e3b] font-bold block">
                  {isApproved ? 'Approved Dispatch' : 'Draft Assignment'}
                </span>
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
                type="button"
                onClick={() => window.print()}
                className="outline-button text-xs"
              >
                <Printer className="h-3.5 w-3.5" />
                <span>Print Trip Sheet</span>
              </button>
              <button
                type="button"
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
