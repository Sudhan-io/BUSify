import React from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import MetricCard from '../../components/MetricCard';
import {
  Bus,
  Users,
  ShieldCheck,
  RefreshCw,
  Check,
  Upload,
  Calendar,
  MapPin,
  FileSpreadsheet,
  BarChart3,
  Truck,
  ArrowRight
} from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function OfficeOverview() {
  usePageTitle('Overview');
  const {
    manifestData,
    loading,
    manifestError,
    activeScenario,
    broadcastConfirmed,
    setShowCsvModal,
    benchmarkResult,
    handleUploadCsv,
  } = useOutletContext();

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
          subtitle={manifestData ? (manifestData.total_standing > 0 ? "Exceeds seating capacity" : "100% seating equity achieved") : "—"}
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

      {/* Quick Navigation Hub for Officer Destinations */}
      <div className="card space-y-4">
        <div className="border-b border-[#edf1ed] pb-3">
          <p className="kicker" style={{ margin: 0 }}>DISPATCH DIRECTORY</p>
          <h3 className="card-title text-base font-bold">Operational Modules & Workflows</h3>
          <p className="text-xs text-[#69716d]">Direct access to daily fleet scheduling, mapping, manifests, inventory, and simulation audits.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <Link
            to="/office/planning"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <Calendar className="h-4 w-4" />
                </span>
                <span className="badge badge-sage text-[10px]">Step 1</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Daily Planning</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Calibrate academic timetable scenarios and review quantile demand forecasts.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>Configure Scenario</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            to="/office/routes"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <MapPin className="h-4 w-4" />
                </span>
                <span className="badge badge-blue text-[10px]">Step 3</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Routes & Map</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Geospatial corridor navigation, stop sequences, and morning pickup routes.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>View Live Map</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            to="/office/manifest"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <FileSpreadsheet className="h-4 w-4" />
                </span>
                <span className="badge badge-sage text-[10px]">Step 2</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Dispatch Manifest</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Vehicle dispatch roster, driver trip sheets, and daily broadcast approval.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>Open Manifest</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            to="/office/fleet"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <Truck className="h-4 w-4" />
                </span>
                <span className="badge badge-coral text-[10px]">Fleet</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Fleet & Drivers</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Manage bus inventory, seating capacity, driver contacts, and maintenance status.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>Manage Fleet</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            to="/office/students"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <Users className="h-4 w-4" />
                </span>
                <span className="badge badge-blue text-[10px]">Demands</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Students & Demand</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Stop-level passenger headcount, regional commuter distribution, and ridership quotas.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>Inspect Demand</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          <Link
            to="/office/reports"
            className="p-4 rounded-[8px] border border-[#dfe5df] bg-[#f7f8f5] hover:bg-white hover:border-[#18201d] transition-all group flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="p-2 rounded bg-white border border-[#dfe5df] text-[#18201d] group-hover:bg-[#18201d] group-hover:text-white transition-colors">
                  <BarChart3 className="h-4 w-4" />
                </span>
                <span className="badge badge-yellow text-[10px]">Audit</span>
              </div>
              <h4 className="font-bold text-xs text-[#18201d] group-hover:text-[#ff6b00] transition-colors">Reports & History</h4>
              <p className="text-[11px] text-[#69716d] mt-1">Execute 7-day performance backtest audits and view fuel/CO2 institutional savings.</p>
            </div>
            <div className="flex items-center gap-1 text-[11px] font-semibold text-[#18201d] pt-3 mt-2 border-t border-[#edf1ed]">
              <span>View Reports</span>
              <ArrowRight className="h-3 w-3 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
