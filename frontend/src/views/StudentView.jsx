import React, { useState, useEffect } from 'react';
import LeafletMap from '../components/LeafletMap';
import StatusBadge from '../components/StatusBadge';
import { Bus, MapPin, Clock, Calendar, Check, ShieldCheck, User, Phone, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import api from '../services/api';
import { describeError } from '../services/auth';

const SAMPLE_STUDENTS_FALLBACK = [
  { roll_no: '21CS104', name: 'K. Vignesh', department: 'CSE - Final Year' },
];

export default function StudentView({ selectedDate, activeInstitution, onSelectInstitution, institutionsList }) {
  const [studentRoll, setStudentRoll] = useState('21CS104');
  const [studentProfile, setStudentProfile] = useState(null);
  // Roster comes from the API; the backend is the source of truth for which
  // roll numbers exist. The fallback only covers a cold first paint.
  const [sampleStudents, setSampleStudents] = useState(SAMPLE_STUDENTS_FALLBACK);
  const [routeInfo, setRouteInfo] = useState(null);
  const [stops, setStops] = useState([]);
  const [optOutMessage, setOptOutMessage] = useState(null);
  const [loading, setLoading] = useState(false);
  const [profileError, setProfileError] = useState(null);
  const [toggling, setToggling] = useState(false);
  const [optOutError, setOptOutError] = useState(null);

  // Load student profile on roll number or date change
  useEffect(() => {
    let cancelled = false;
    async function loadProfile() {
      setLoading(true);
      setProfileError(null);
      try {
        const [prof, st, roster] = await Promise.all([
          api.getStudentProfile(studentRoll, selectedDate),
          api.getStops(),
          api.getStudents(),
        ]);
        if (cancelled) return;
        setStudentProfile(prof);
        setStops(st);
        if (Array.isArray(roster) && roster.length) {
          setSampleStudents(roster);
        }

        // Fetch routes for assigned area
        if (prof?.assigned_stop?.area_id) {
          const rt = await api.getRoutes(
            prof.assigned_stop.area_id,
            selectedDate,
            activeInstitution?.campus_lat,
            activeInstitution?.campus_lng
          );
          if (!cancelled) setRouteInfo(rt);
        }
      } catch (err) {
        if (cancelled) return;
        // Previously console-only: an unknown roll or an API failure rendered
        // an empty-looking pass with no indication anything had failed.
        setProfileError(describeError(err));
        setStudentProfile(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadProfile();
    return () => { cancelled = true; };
  }, [studentRoll, selectedDate, activeInstitution?.campus_lat, activeInstitution?.campus_lng]);

  // Handle opt-out toggle (taking leave vs traveling)
  const handleToggleAttendance = async () => {
    if (!studentProfile) return;
    setToggling(true);
    setOptOutError(null);
    const newStatus = !studentProfile.traveling_today;
    try {
      await api.toggleStudentOptOut(studentRoll, newStatus, selectedDate);
      // Re-read the profile instead of patching it locally. The local patch
      // hardcoded occupancy 78/74 and crowd levels, which disagreed with the
      // server's authoritative values.
      const refreshed = await api.getStudentProfile(studentRoll, selectedDate);
      setStudentProfile(refreshed);
      setOptOutMessage(
        newStatus
          ? `Seat re-confirmed for ${studentRoll}.`
          : `Absence recorded for ${studentRoll}. Seat released for peers.`
      );
      setTimeout(() => setOptOutMessage(null), 6000);
    } catch (err) {
      setOptOutError(describeError(err));
    } finally {
      setToggling(false);
    }
  };

  const assignedStop = studentProfile?.assigned_stop;

  return (
    <div className="space-y-8">
      {/* Editorial Hero Section */}
      <section className="hero">
        <div>
          <p className="kicker">
            <span className="pulse"></span> STUDENT COMMUTER CONSOLE / BUS PASS PORTAL
          </p>
          <h1>
            Morning commute,<br />
            <em>guaranteed confirmed seat.</em>
          </h1>
          <p className="hero-copy">
            Every registered commuter has a confirmed seat on their assigned college bus. Check your morning pickup time, track vehicle occupancy, or release your seat if you are taking leave today.
          </p>
        </div>
        <div className="hero-note">
          <span className="note-label">Seating Policy</span>
          <strong>Confirmed Seat.</strong>
          <span>Zero Standing Travel Guarantee &bull; UN SDG 10</span>
        </div>
      </section>

      {/* Operational Step 1: Student Roll Number Lookup */}
      <div className="card space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#edf1ed] pb-3">
          <div>
            <p className="kicker" style={{ margin: 0 }}>WORKFLOW STEP 1: VERIFIED COMMUTER LOOKUP</p>
            <h3 className="card-title text-base font-bold">Select or Enter Student Roll Number</h3>
          </div>
          <span className="text-xs text-[#69716d]">SHA-256 Salted Anonymized Transit Profile</span>
        </div>

        <div className="flex flex-wrap items-center gap-2 pt-1">
          {sampleStudents.map(s => (
            <button
              key={s.roll_no}
              onClick={() => setStudentRoll(s.roll_no)}
              className={`px-3 py-1.5 rounded-[7px] text-xs font-semibold border transition-all ${
                studentRoll === s.roll_no
                  ? 'bg-[#18201d] text-white border-[#18201d]'
                  : 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df] hover:border-[#18201d]'
              }`}
            >
              <span className="font-mono">{s.roll_no}</span> &bull; <span>{s.name} ({s.department})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Notification Banner when seat is released or confirmed */}
      {optOutMessage && (
        <div className="banner">
          <div className="banner-icon">
            <Check className="h-4 w-4" />
          </div>
          <div className="banner-body">
            <strong>Daily Attendance Status Updated</strong>
            <span>{optOutMessage}</span>
          </div>
          <span className="badge badge-sage">Synced</span>
        </div>
      )}

      {/* Opt-out failure — was console-only, so a rejected toggle looked like success */}
      {optOutError && (
        <div
          role="alert"
          className="rounded-lg border border-[#f5c6c2] bg-[#fdecea] px-3 py-2 text-xs text-[#c0392b]"
        >
          Could not update attendance status: {optOutError}
        </div>
      )}

      {/* Main Student Console Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Digital Boarding Pass Ticket */}
        <div className="lg:col-span-5 space-y-6">
          <div className="card space-y-5 border-[#dfe5df]">
            {/* Error banner — an empty pass must never be mistaken for a valid one */}
            {profileError && (
              <div
                role="alert"
                className="rounded-lg border border-[#f5c6c2] bg-[#fdecea] px-3 py-2 text-xs text-[#c0392b]"
              >
                {profileError}
              </div>
            )}

            {/* Loading indicator */}
            {loading && (
              <div
                className="rounded-lg border border-[#dfe5df] bg-[#f7f8f5] px-3 py-2 text-xs text-[#69716d] flex items-center gap-2 animate-pulse"
              >
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-[#ff6b00]" />
                <span>Loading commuter boarding pass...</span>
              </div>
            )}

            {/* Ticket Header */}
            <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>DIGITAL BOARDING PASS</p>
                <h4 className="card-title text-xl font-bold">
                  {/* Was `|| 'BUS-02'`, which rendered a plausible-looking bus code
                      on total API failure. */}
                  {studentProfile?.assigned_bus_code || (loading ? 'Loading...' : 'Unavailable')}
                </h4>
                <p className="text-xs text-[#69716d]">
                  Roll No: <span className="font-mono font-bold text-[#18201d]">{studentRoll}</span>
                  {studentProfile?.student_hash && (
                    <> &bull; ID: <span className="font-mono">{studentProfile.student_hash}</span></>
                  )}
                </p>
              </div>
              <StatusBadge status={studentProfile?.crowd_level || (loading ? 'CHECKING' : 'UNKNOWN')} size="lg" />
            </div>

            {/* Guaranteed Seat & Timings */}
            <div className="grid grid-cols-2 gap-3 bg-[#f7f8f5] p-3.5 rounded-[8px] border border-[#dfe5df]">
              <div>
                <span className="kicker" style={{ margin: '0 0 2px' }}>ASSIGNED SEAT</span>
                <div className="stat-number text-xl text-[#18201d]">
                  {loading ? '—' : (studentProfile?.seat_number ?? '—')}
                </div>
                <span className={`text-[10px] font-bold block ${
                  loading || !studentProfile
                    ? 'text-[#69716d]'
                    : studentProfile.traveling_today
                    ? 'text-[#2b6e3b]'
                    : 'text-[#c0392b]'
                }`}>
                  {loading
                    ? 'Checking seating status...'
                    : !studentProfile
                    ? 'Unavailable'
                    : studentProfile.traveling_today
                    ? 'Confirmed • No Standing'
                    : 'Seat Released • On Leave'}
                </span>
              </div>
              <div>
                <span className="kicker" style={{ margin: '0 0 2px' }}>PICKUP DEPARTURE</span>
                <div className="stat-number text-xl text-[#18201d]">
                  {loading ? '—' : (studentProfile?.pickup_time ?? '—')}
                </div>
                <span className="text-[10px] text-[#69716d] block">Be at stop 5 min early</span>
              </div>
            </div>

            {/* Boarding Location & Driver Information */}
            <div className="space-y-2 text-xs">
              <div className="flex items-start justify-between border-b border-[#edf1ed] pb-2">
                <div>
                  <span className="text-[#69716d] block">Pickup Location</span>
                  <span className="font-bold text-[#18201d] text-sm">{loading ? 'Loading stop...' : (assignedStop?.name || '—')}</span>
                  <span className="text-[11px] text-[#69716d] block">Zone: {assignedStop?.area_id} ({assignedStop?.campus_distance_km} km to campus)</span>
                </div>
                <span className="badge badge-blue">{assignedStop?.stop_id}</span>
              </div>

              <div className="flex items-center justify-between pt-1">
                <div>
                  <span className="text-[#69716d] block">Bus Captain (Driver)</span>
                  <span className="font-bold text-[#18201d]">{loading ? '—' : (studentProfile?.driver_name || '—')}</span>
                </div>
                <a
                  href={`tel:${studentProfile?.driver_phone}`}
                  className="outline-button py-1 px-2.5 text-xs"
                >
                  <Phone className="h-3 w-3" />
                  <span className="font-mono">{studentProfile?.driver_phone}</span>
                </a>
              </div>
            </div>

            {/* Capacity Meter */}
            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-[#18201d]">Expected Occupancy</span>
                <span className="font-bold text-[#18201d]">
                  {loading ? '—' : (studentProfile?.occupancy_pct != null ? `${studentProfile.occupancy_pct}% Full (55 Seats)` : 'Unavailable')}
                </span>
              </div>
              <div className="w-full bg-[#dfe5df] rounded-full h-2 overflow-hidden">
                <div
                  className="bg-[#18201d] h-2 rounded-full transition-all duration-500"
                  style={{ width: `${studentProfile?.occupancy_pct || 0}%` }}
                />
              </div>
            </div>

            {/* WORKFLOW STEP 2: Attendance Opt-Out Toggle */}
            <div className="border-t border-[#edf1ed] pt-4 space-y-2">
              <div className="flex items-center justify-between">
                <div>
                  <span className="font-bold text-xs text-[#18201d] block">Commuting Schedule Action</span>
                  <span className="text-[11px] text-[#69716d]">
                    {loading
                      ? 'Checking attendance status...'
                      : !studentProfile
                      ? 'Status unavailable'
                      : studentProfile.traveling_today
                      ? 'Traveling today on morning route'
                      : 'Taking leave / private vehicle'}
                  </span>
                </div>
                <button
                  onClick={handleToggleAttendance}
                  disabled={toggling}
                  className={`py-1.5 px-3 rounded-[6px] text-xs font-bold transition-all ${
                    studentProfile?.traveling_today
                      ? 'bg-[#f7f8f5] text-[#a82e20] border border-[#f8ded9] hover:bg-[#f8ded9]'
                      : 'bg-[#18201d] text-white hover:bg-[#2a3632]'
                  }`}
                >
                  {toggling ? (
                    <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  ) : studentProfile?.traveling_today ? (
                    'Not Riding Today'
                  ) : (
                    'Re-confirm Seat'
                  )}
                </button>
              </div>
              <p className="text-[10px] text-[#69716d]">
                Toggling "Not Riding Today" releases your seat to prevent bus overcrowding for your regional peers.
              </p>
            </div>
          </div>
        </div>

        {/* Right Column: Route Map & Live Sequential Itinerary */}
        <div className="lg:col-span-7 card space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="kicker" style={{ margin: '0 0 4px' }}>GEOSPATIAL ROUTE PATH</p>
              <h3 className="card-title">Pickup Route to College Campus</h3>
              <p className="text-xs text-[#69716d]">
                Scheduled morning path from {assignedStop?.name} to VSB Engineering College Hub.
              </p>
            </div>
            <span className="badge badge-sage">Arrival 08:30 AM</span>
          </div>

          <div className="h-[380px] w-full rounded-[9px] overflow-hidden">
            <LeafletMap
              stops={stops.filter(s => s.area_id === assignedStop?.area_id)}
              activeRoutes={routeInfo?.routes || []}
              selectedStop={assignedStop}
              campusCenter={[activeInstitution?.campus_lat || 10.95485, activeInstitution?.campus_lng || 77.95463]}
              campusName={activeInstitution?.name || 'VSB Engineering College Transit Hub'}
              activeInstitution={activeInstitution}
              onSelectInstitution={onSelectInstitution}
              institutionsList={institutionsList}
            />
          </div>

          {/* Sequential Itinerary Stops */}
          <div className="space-y-2 pt-2">
            <p className="kicker" style={{ margin: '0 0 4px' }}>SCHEDULED ROUTE STOPS</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {(routeInfo?.routes?.[0]?.itinerary || []).slice(0, 6).map((step, idx) => {
                const isSelected = step.stop_id === assignedStop?.stop_id || step.name?.includes(assignedStop?.name);
                return (
                  <div
                    key={idx}
                    className={`p-2.5 rounded-[7px] border text-xs flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#18201d] text-white border-[#18201d]'
                        : 'bg-[#f7f8f5] text-[#18201d] border-[#dfe5df]'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className={`h-4 w-4 rounded-full flex items-center justify-center text-[10px] font-bold ${isSelected ? 'bg-white text-[#18201d]' : 'bg-[#dfe5df] text-[#18201d]'}`}>
                        {idx + 1}
                      </span>
                      <span className="font-medium truncate max-w-[140px]">{step.name}</span>
                    </div>
                    <span className="font-mono text-[11px] font-bold">{step.time}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
