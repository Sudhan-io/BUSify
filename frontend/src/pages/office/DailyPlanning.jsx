import React from 'react';
import { useOutletContext } from 'react-router-dom';
import ChartContainer from '../../components/ChartContainer';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Check } from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function DailyPlanning() {
  usePageTitle('Daily Planning');
  const {
    activeScenario,
    setActiveScenario,
    SCENARIOS,
    comparisonChartData,
    manifestData,
    loading
  } = useOutletContext();
  const hasComparisonData = comparisonChartData.length > 0;

  return (
    <div className="space-y-6">
      {/* Page Title & Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 1: CAPACITY & DEMAND CALIBRATION</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Daily Fleet Planning & Scenario Simulation</h2>
          <p className="text-xs text-[#69716d]">
            Select today's academic timetable scenario to calibrate LightGBM quantile demand projections and dynamic seat re-allocations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-sage text-xs">
            {manifestData?.total_active_buses != null ? `${manifestData.total_active_buses} Active Vehicles` : 'Loading...'}
          </span>
          <span className="badge badge-coral text-xs">
            {activeScenario ? activeScenario.replace('_', ' ') : 'Scenario'}
          </span>
        </div>
      </div>

      {/* Operational Workflow Step 1: Scenario Condition Selector */}
      <div className="card space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
          <div>
            <h3 className="card-title text-base font-bold">Select Today's Academic Timetable Scenario</h3>
            <p className="text-xs text-[#69716d]">Adjusts ridership expectation and priority allocation vectors across zones.</p>
          </div>
          <span className="text-xs text-[#69716d]">Calibrates LightGBM Quantile Surge & Fleet Balancing</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {(SCENARIOS || []).map(sc => (
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

      {/* Dynamic Dispatch Chart & Capacity vs Demand */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-8">
          <ChartContainer
            kicker="DYNAMIC DISPATCH"
            title="Capacity vs. Scenario Demand"
            subtitle="Comparing status-quo baseline against BUSify dynamic allocation"
          >
            {loading ? (
              <div
                aria-busy="true"
                aria-label="Loading capacity and demand chart"
                className="h-80 rounded-[8px] bg-[#f7f8f5] animate-pulse"
              >
                <div className="flex h-full items-end gap-4 px-8 pb-8">
                  {[45, 70, 55, 85, 62].map((height, index) => (
                    <div key={index} className="flex-1 rounded-t bg-[#dfe5df]" style={{ height: `${height}%` }} />
                  ))}
                </div>
              </div>
            ) : !hasComparisonData ? (
              <div className="flex h-80 items-center justify-center rounded-[8px] border border-dashed border-[#dfe5df] bg-[#f7f8f5] px-6 text-center">
                <p className="text-sm text-[#69716d]" role="status">
                  No forecast data available for this date and scenario.
                </p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height={320}>
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
            )}
          </ChartContainer>
        </div>

        <div className="lg:col-span-4 space-y-4">
          <div className="card space-y-3">
            <p className="kicker" style={{ margin: 0 }}>ALLOCATION SUMMARY</p>
            <h4 className="font-bold text-sm text-[#18201d]">Ridership vs Fleet Quota</h4>
            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[#69716d]">Total Expected Riders</span>
                <span className="font-bold text-[#18201d]">
                  {loading ? '—' : (manifestData?.total_expected_riders ?? '—')}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[#69716d]">Total Seats Deployed</span>
                <span className="font-bold text-[#2b6e3b]">
                  {loading ? '—' : (manifestData?.total_seats_deployed ?? '—')}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[#69716d]">Fleet Utilization</span>
                <span className="font-bold text-[#ff6b00]">
                  {loading ? '—' : (manifestData?.overall_utilization_pct != null ? `${manifestData.overall_utilization_pct}%` : '—')}
                </span>
              </div>
              <div className="flex items-center justify-between p-2 rounded bg-[#f7f8f5] border border-[#dfe5df]">
                <span className="text-[#69716d]">Standing Commuters</span>
                <span className="font-bold text-[#18201d]">
                  {loading ? '—' : (manifestData?.total_standing ?? '—')}
                </span>
              </div>
            </div>
          </div>

          <div className="card space-y-2 bg-[#f7f8f5]">
            <span className="kicker" style={{ margin: 0 }}>ZERO-STANDING GUARANTEE</span>
            <p className="text-xs text-[#69716d] leading-relaxed">
              When scenario demand surges (such as placement drives or rain), BUSify shifts idle capacity from low-demand residential zones to prevent dangerous bus overcrowding.
            </p>
          </div>
        </div>
      </div>

      {/* Corridor-by-Corridor Allocation Breakdown Table */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
          <div>
            <p className="kicker" style={{ margin: 0 }}>DETAILED CORRIDOR ALLOCATION</p>
            <h4 className="card-title text-base font-bold">Zone-Level Bus Sizing vs Demand</h4>
          </div>
          <span className="text-xs text-[#69716d]">5 Operational Transit Corridors</span>
        </div>

        <div className="overflow-x-auto">
          <table className="editorial-table text-xs">
            <thead>
              <tr>
                <th>Corridor / Zone</th>
                <th>Assigned Buses</th>
                <th>Optimized Seats</th>
                <th>Static Baseline Seats</th>
                <th>Expected Demand</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {!loading && !hasComparisonData ? (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-[#69716d]">
                    No corridor allocation data is available for this date and scenario.
                  </td>
                </tr>
              ) : (comparisonChartData || []).map((row, idx) => {
                const diff = row.optimized_seats - row.baseline_seats;
                return (
                  <tr key={idx}>
                    <td className="font-bold text-[#18201d]">{row.name}</td>
                    <td>
                      <span className="badge badge-sage font-mono font-bold">{row.buses} Buses</span>
                    </td>
                    <td className="font-mono font-bold text-[#18201d]">{row.optimized_seats} seats</td>
                    <td className="font-mono text-[#69716d]">{row.baseline_seats} seats</td>
                    <td className="font-mono font-semibold text-[#ff6b00]">{row.demand} students</td>
                    <td>
                      {diff > 0 ? (
                        <span className="badge badge-sage text-[10px]">+{diff / 55} Buses Shifted Here</span>
                      ) : diff < 0 ? (
                        <span className="badge badge-coral text-[10px]">{diff / 55} Buses Reallocated</span>
                      ) : (
                        <span className="badge badge-blue text-[10px]">Baseline Stable</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
