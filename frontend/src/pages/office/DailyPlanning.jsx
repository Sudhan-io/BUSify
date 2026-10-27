import React, { useState } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import ChartContainer from '../../components/ChartContainer';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import {
  Check,
  Calendar,
  Sliders,
  BarChart3,
  Send,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  HelpCircle,
  Bus,
  Users,
  Scale
} from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function DailyPlanning() {
  usePageTitle('Daily Planning');
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);

  const {
    selectedDate,
    activeScenario,
    setActiveScenario,
    SCENARIOS,
    comparisonChartData,
    manifestData,
    loading
  } = useOutletContext();

  const hasComparisonData = comparisonChartData && comparisonChartData.length > 0;

  const STEPS = [
    { num: 1, label: 'Date & Scenario', icon: Calendar, desc: 'Calibrate academic timetable' },
    { num: 2, label: 'Solver Constraints', icon: Sliders, desc: 'Review fleet boundaries & policy' },
    { num: 3, label: 'Capacity & Equity', icon: BarChart3, desc: 'Analyze projections & equity' },
    { num: 4, label: 'Confirm & Dispatch', icon: Send, desc: 'Audit and proceed to manifest' },
  ];

  return (
    <div className="space-y-6">
      {/* Page Title & Context Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>GUIDED DISPATCH WORKFLOW</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">Daily Fleet Planning & Scenario Simulation</h2>
          <p className="text-xs text-[#69716d]">
            Configure today's operational conditions, verify fleet constraints, and approve dynamic bus re-allocations.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge badge-sage text-xs">
            {manifestData?.total_active_buses != null ? `${manifestData.total_active_buses} Active Vehicles` : 'Loading...'}
          </span>
          <span className="badge badge-coral text-xs">
            {activeScenario ? activeScenario.replace(/_/g, ' ') : 'Scenario'}
          </span>
        </div>
      </div>

      {/* Guided 4-Step Progress Stepper */}
      <div className="card p-3 bg-white border border-[#dfe5df]" role="navigation" aria-label="Planning Workflow Steps">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {STEPS.map((s) => {
            const Icon = s.icon;
            const isActive = currentStep === s.num;
            const isCompleted = currentStep > s.num;
            return (
              <button
                key={s.num}
                type="button"
                onClick={() => setCurrentStep(s.num)}
                className={`flex items-start gap-3 p-3 rounded-[8px] text-left border transition-all ${
                  isActive
                    ? 'bg-[#18201d] text-white border-[#18201d] shadow-sm'
                    : isCompleted
                    ? 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
                    : 'bg-white text-[#69716d] border-[#edf1ed] hover:border-[#dfe5df]'
                }`}
                aria-current={isActive ? 'step' : undefined}
              >
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                    isActive
                      ? 'bg-white text-[#18201d]'
                      : isCompleted
                      ? 'bg-[#2b6e3b] text-white'
                      : 'bg-[#edf1ed] text-[#69716d]'
                  }`}
                >
                  {isCompleted ? <Check className="h-4 w-4" /> : s.num}
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5">
                    <Icon className="h-3.5 w-3.5 shrink-0" />
                    <span className="font-bold text-xs truncate">{s.label}</span>
                  </div>
                  <p className={`text-[11px] truncate ${isActive ? 'text-[#dfe5df]' : 'text-[#69716d]'}`}>
                    {s.desc}
                  </p>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* STEP 1: DATE & SCENARIO SELECTION */}
      {currentStep === 1 && (
        <div className="card space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
            <div>
              <p className="kicker" style={{ margin: 0 }}>STEP 1 OF 4</p>
              <h3 className="card-title text-base font-bold">Select Date & Academic Timetable Scenario</h3>
              <p className="text-xs text-[#69716d]">
                Ridership projections and fleet allocations dynamically recalibrate based on academic schedule and weather conditions.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-[#18201d] bg-[#f7f8f5] px-2.5 py-1 rounded border border-[#dfe5df]">
                Target Date: <strong>{selectedDate || 'Today'}</strong>
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
            {(SCENARIOS || []).map((sc) => (
              <button
                key={sc.id}
                type="button"
                onClick={() => setActiveScenario(sc.id)}
                className={`p-4 rounded-[8px] text-left border transition-all flex flex-col justify-between ${
                  activeScenario === sc.id
                    ? 'bg-[#18201d] text-white border-[#18201d] shadow-sm'
                    : 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-xs">{sc.label}</span>
                    {activeScenario === sc.id && <Check className="h-4 w-4 text-white" />}
                  </div>
                  <p className={`text-[11px] pt-2 leading-relaxed ${activeScenario === sc.id ? 'text-[#dfe5df]' : 'text-[#69716d]'}`}>
                    {sc.desc}
                  </p>
                </div>
                <div className="pt-3">
                  <span
                    className={`text-[10px] uppercase font-mono tracking-wider px-2 py-0.5 rounded ${
                      activeScenario === sc.id
                        ? 'bg-white/20 text-white'
                        : 'bg-[#dfe5df] text-[#18201d]'
                    }`}
                  >
                    {sc.id === 'REGULAR'
                      ? 'Standard Load'
                      : sc.id === 'EXAM_DAY'
                      ? 'Morning Surge'
                      : sc.id === 'PLACEMENT_DRIVE'
                      ? 'Priority Corridors'
                      : '+35% Weather Shift'}
                  </span>
                </div>
              </button>
            ))}
          </div>

          <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] flex items-start gap-3">
            <HelpCircle className="h-4 w-4 text-[#69716d] shrink-0 mt-0.5" />
            <div className="text-xs text-[#69716d] leading-relaxed">
              <strong className="text-[#18201d]">How Scenario Calibration Works:</strong> Switching the scenario updates the LightGBM quantile demand forecaster (p90) and re-executes the OR-Tools CP-SAT integer programming solver to shift surplus buses from low-density zones to surge corridors.
            </div>
          </div>

          <div className="flex justify-end pt-2 border-t border-[#edf1ed]">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="btn btn-primary flex items-center gap-2 text-xs"
            >
              Continue to Solver Constraints
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: SOLVER CONSTRAINTS & POLICY */}
      {currentStep === 2 && (
        <div className="card space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
            <div>
              <p className="kicker" style={{ margin: 0 }}>STEP 2 OF 4</p>
              <h3 className="card-title text-base font-bold">Review Fleet Boundaries & Solver Constraints</h3>
              <p className="text-xs text-[#69716d]">
                Mathematical bounds and penalty weights enforced by the OR-Tools CP-SAT optimization engine.
              </p>
            </div>
            <span className="badge badge-sage text-xs">OR-Tools CP-SAT v9.11</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-2">
              <div className="flex items-center justify-between text-xs text-[#69716d]">
                <span className="font-semibold uppercase tracking-wider">Total Fleet Budget</span>
                <Bus className="h-4 w-4 text-[#18201d]" />
              </div>
              <div className="text-2xl font-serif font-bold text-[#18201d]">
                {manifestData?.total_active_buses ?? 50} <span className="text-xs font-sans font-normal text-[#69716d]">Buses</span>
              </div>
              <p className="text-[11px] text-[#69716d] leading-tight">
                Global fleet upper bound constraint (sum of buses &le; total fleet size). All active depot vehicles.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-2">
              <div className="flex items-center justify-between text-xs text-[#69716d]">
                <span className="font-semibold uppercase tracking-wider">Minimum Coverage</span>
                <ShieldCheck className="h-4 w-4 text-[#2b6e3b]" />
              </div>
              <div className="text-2xl font-serif font-bold text-[#18201d]">
                &ge; 2 <span className="text-xs font-sans font-normal text-[#69716d]">Buses / Zone</span>
              </div>
              <p className="text-[11px] text-[#69716d] leading-tight">
                Hard floor constraint ensuring every radial corridor retains scheduled student transit service.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-2">
              <div className="flex items-center justify-between text-xs text-[#69716d]">
                <span className="font-semibold uppercase tracking-wider">Bus Capacity</span>
                <Users className="h-4 w-4 text-[#ff6b00]" />
              </div>
              <div className="text-2xl font-serif font-bold text-[#18201d]">
                {manifestData?.bus_capacity ?? 55} <span className="text-xs font-sans font-normal text-[#69716d]">Seats / Bus</span>
              </div>
              <p className="text-[11px] text-[#69716d] leading-tight">
                Standard seated vehicle capacity across active college transit fleet.
              </p>
            </div>

            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-2">
              <div className="flex items-center justify-between text-xs text-[#69716d]">
                <span className="font-semibold uppercase tracking-wider">Standing Penalty</span>
                <Scale className="h-4 w-4 text-[#ff6b00]" />
              </div>
              <div className="text-2xl font-serif font-bold text-[#18201d]">
                10.0 &times; <span className="text-xs font-sans font-normal text-[#69716d]">Objective Weight</span>
              </div>
              <p className="text-[11px] text-[#69716d] leading-tight">
                Penalty minimization: heavily penalizes overcrowding (standing weight 10.0 vs empty seat weight 1.0).
              </p>
            </div>
          </div>

          <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-2">
            <h4 className="font-bold text-xs text-[#18201d] uppercase tracking-wider">
              Mathematical Optimization Formulation:
            </h4>
            <p className="text-xs text-[#69716d] font-mono leading-relaxed bg-white p-3 rounded border border-[#dfe5df]">
              Minimize: 10.0 &times; &sum; Standing(a) + 1.0 &times; &sum; EmptySeats(a) + 0.5 &times; &sum; |Allocation(a) - Baseline(a)|<br />
              Subject to: &sum; Buses(a) &le; 50, Buses(a) &ge; 2 for all zones a &isin; &#123;A, B, C, D, E&#125;
            </p>
            <p className="text-[11px] text-[#69716d]">
              *Note: Zero standing is a high-penalty objective target. If scenario ridership surges beyond physical fleet capacity, standing students physically occur.
            </p>
          </div>

          <div className="flex justify-between pt-2 border-t border-[#edf1ed]">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="btn btn-secondary flex items-center gap-2 text-xs"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Date & Scenario
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="btn btn-primary flex items-center gap-2 text-xs"
            >
              Review Allocation & Equity
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: ALLOCATION REVIEW & EQUITY */}
      {currentStep === 3 && (
        <div className="space-y-6">
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
                    <span className="text-[#69716d]">Seating Equity</span>
                    <span className="font-bold text-[#2b6e3b]">
                      {loading ? '—' : (manifestData?.seating_equity_pct != null ? `${manifestData.seating_equity_pct}%` : '100%')}
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
                <span className="kicker" style={{ margin: 0 }}>DYNAMIC LOAD BALANCING</span>
                <p className="text-xs text-[#69716d] leading-relaxed">
                  BUSify shifts idle capacity from low-demand residential zones to high-density corridors to achieve equal seat availability and eliminate standing.
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
                    const busCap = manifestData?.bus_capacity || 55;
                    const diffBuses = Math.round(diff / busCap);
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
                          {diffBuses > 0 ? (
                            <span className="badge badge-sage text-[10px]">+{diffBuses} Buses Shifted Here</span>
                          ) : diffBuses < 0 ? (
                            <span className="badge badge-coral text-[10px]">{diffBuses} Buses Reallocated</span>
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

          <div className="flex justify-between pt-2 border-t border-[#edf1ed]">
            <button
              type="button"
              onClick={() => setCurrentStep(2)}
              className="btn btn-secondary flex items-center gap-2 text-xs"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Constraints
            </button>
            <button
              type="button"
              onClick={() => setCurrentStep(4)}
              className="btn btn-primary flex items-center gap-2 text-xs"
            >
              Proceed to Confirmation
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 4: CONFIRMATION & DISPATCH HANDOFF */}
      {currentStep === 4 && (
        <div className="card space-y-5">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
            <div>
              <p className="kicker" style={{ margin: 0 }}>STEP 4 OF 4</p>
              <h3 className="card-title text-base font-bold">Confirm Daily Plan & Handoff to Dispatch</h3>
              <p className="text-xs text-[#69716d]">
                Verify readiness checklist before opening operational driver trip sheets and GPS manifests.
              </p>
            </div>
            <span className="badge badge-sage text-xs">Plan Ready for Approval</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-3">
              <h4 className="font-bold text-xs uppercase tracking-wider text-[#18201d]">
                Operational Readiness Checklist
              </h4>
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#2b6e3b]" />
                  <span>
                    Academic Scenario: <strong>{activeScenario ? activeScenario.replace(/_/g, ' ') : 'Regular'}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#2b6e3b]" />
                  <span>
                    Target Date: <strong>{selectedDate || 'Today'}</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#2b6e3b]" />
                  <span>
                    Forecast Demand: <strong>{manifestData?.total_expected_riders ?? '—'} students</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#2b6e3b]" />
                  <span>
                    Fleet Deployed: <strong>{manifestData?.total_active_buses ?? 50} buses ({manifestData?.total_seats_deployed ?? '—'} seats)</strong>
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4 text-[#2b6e3b]" />
                  <span>
                    Seating Equity Metric: <strong>{manifestData?.seating_equity_pct ?? 100}% achieved</strong>
                  </span>
                </div>
              </div>
            </div>

            <div className="p-4 rounded-[8px] bg-[#f7f8f5] border border-[#dfe5df] space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <h4 className="font-bold text-xs uppercase tracking-wider text-[#18201d]">
                  Next Operational Phase: Dispatch Manifest
                </h4>
                <p className="text-xs text-[#69716d] leading-relaxed">
                  Approving this daily plan advances to the Dispatch Manifest tab, where bus-to-driver assignments, boarding stop sequences, and departure trip sheets can be printed or broadcast to drivers.
                </p>
              </div>
              <button
                type="button"
                onClick={() => navigate('/office/manifest')}
                className="btn btn-primary w-full flex items-center justify-center gap-2 text-xs py-2.5 font-bold"
              >
                Approve Planning & Open Dispatch Manifest
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="flex justify-start pt-2 border-t border-[#edf1ed]">
            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="btn btn-secondary flex items-center gap-2 text-xs"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              Back to Allocation Review
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
