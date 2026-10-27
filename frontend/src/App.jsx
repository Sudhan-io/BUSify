import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import OfficeLayout from './layouts/OfficeLayout';
import OfficeOverview from './pages/office/OfficeOverview';
import DailyPlanning from './pages/office/DailyPlanning';
import RoutesAndMap from './pages/office/RoutesAndMap';
import DispatchManifest from './pages/office/DispatchManifest';
import FleetAndDrivers from './pages/office/FleetAndDrivers';
import StudentsAndDemand from './pages/office/StudentsAndDemand';
import ReportsAndHistory from './pages/office/ReportsAndHistory';
import StudentView from './views/StudentView';
import NotFound from './pages/NotFound';
import api, { onUnauthorized } from './services/api';
import { statusColor, BACKEND_STATUS } from './constants/status';
import {
  isAuthenticated,
  getRole,
  getDisplayName,
  clearSession,
} from './services/auth';
import LoginModal from './components/LoginModal';
import { DEFAULT_INSTITUTION } from './constants/institution';

/**
 * Single source of truth for backend status -> colour.
 *
 * The previous footer used a hardcoded green and the health check set
 * 'HEALTHY' inside its own catch block, so an unreachable backend was
 * reported as fully operational on a dispatch console.
 */
function AppShell() {
  const [activeRole, setActiveRole] = useState('office');
  const [selectedDate, setSelectedDate] = useState('2026-10-15');
  const [backendStatus, setBackendStatus] = useState(BACKEND_STATUS.CHECKING);
  const [activeInstitution, setActiveInstitution] = useState(DEFAULT_INSTITUTION);
  const [institutionsList, setInstitutionsList] = useState([DEFAULT_INSTITUTION]);

  // Transport-officer session. Read-only endpoints and the student view stay
  // public, so this gates privileged actions rather than the whole app.
  const [session, setSession] = useState(() => ({
    authenticated: isAuthenticated(),
    role: getRole(),
    name: getDisplayName(),
  }));
  const [showLogin, setShowLogin] = useState(false);
  const [sessionNotice, setSessionNotice] = useState(null);

  // Any 401 from the API tears down the session and prompts re-auth.
  useEffect(() => {
    onUnauthorized(() => {
      setSession({ authenticated: false, role: null, name: null });
      setSessionNotice('Your session expired. Please sign in again.');
      setShowLogin(true);
    });
  }, []);

  // Load backend health and active institution presets
  useEffect(() => {
    async function initPlatform() {
      try {
        const health = await api.getHealth();
        setBackendStatus(health.status === 'DEGRADED' ? BACKEND_STATUS.DEGRADED : BACKEND_STATUS.HEALTHY);
      } catch {
        // NOT a graceful fallback: the backend is unreachable, so say so.
        setBackendStatus(BACKEND_STATUS.OFFLINE);
      }

      try {
        const [insts, active] = await Promise.all([
          api.getInstitutions(),
          api.getActiveInstitution()
        ]);
        if (insts && insts.length > 0) {
          setInstitutionsList(insts);
        }
        if (active) {
          setActiveInstitution(active);
        }
      } catch (err) {
        console.warn('Using default institution config:', err);
      }
    }
    initPlatform();
  }, []);

  const handleLogin = async (username, password) => {
    const result = await api.login(username, password);
    setSession({
      authenticated: true,
      role: result.role,
      name: result.name,
    });
    setSessionNotice(null);
    return result;
  };

  const handleLogout = () => {
    clearSession();
    setSession({ authenticated: false, role: null, name: null });
    setSessionNotice('Signed out.');
  };

  /**
   * Gate for privileged actions. Returns true when the caller may proceed;
   * otherwise prompts for sign-in and returns false.
   */
  const requireSession = () => {
    if (session.authenticated) return true;
    setShowLogin(true);
    return false;
  };

  const handleSelectInstitution = async (inst) => {
    if (!requireSession()) return;
    try {
      const active = await api.setActiveInstitution(inst.id);
      setActiveInstitution(active?.id ? active : inst);
    } catch (err) {
      console.error('Failed to set active institution:', err);
      setActiveInstitution(inst); // Fallback optimistic update
    }
  };

  const handleCreateInstitution = async (instData) => {
    if (!requireSession()) return null;
    const created = await api.createInstitution(instData);
    if (!created || !created.id) {
      throw new Error('Campus registration returned no institution record.');
    }
    setInstitutionsList(prev =>
      prev.some(i => i.id === created.id) ? prev : [...prev, created]
    );
    setActiveInstitution(created);
    return created;
  };

  return (
    <div className="app-shell">
      {/* Global Editorial Navigation Header */}
      <Navbar
        activeRole={activeRole}
        setActiveRole={setActiveRole}
        selectedDate={selectedDate}
        setSelectedDate={setSelectedDate}
        backendStatus={backendStatus}
        activeInstitution={activeInstitution}
        institutionsList={institutionsList}
        onSelectInstitution={handleSelectInstitution}
        onCreateInstitution={handleCreateInstitution}
        session={session}
        onRequestSignIn={() => setShowLogin(true)}
        onLogout={handleLogout}
      />

      {sessionNotice && (
        <div
          role="status"
          className="fixed bottom-4 left-1/2 -translate-x-1/2 z-[1100] rounded-lg border border-[#f5c6c2]
                     bg-[#fdecea] px-4 py-2 text-xs text-[#c0392b] shadow-lg"
        >
          {sessionNotice}
        </div>
      )}

      <LoginModal
        open={showLogin}
        onClose={() => setShowLogin(false)}
        onAuthenticated={handleLogin}
      />

      {/* Main Editorial Page Content */}
      <main className="page-wrap">
        <Routes>
          <Route path="/" element={<Navigate to="/office/overview" replace />} />
          <Route path="/office" element={<Navigate to="/office/overview" replace />} />
          <Route
            path="/office"
            element={
              <OfficeLayout
                selectedDate={selectedDate}
                activeInstitution={activeInstitution}
                onSelectInstitution={handleSelectInstitution}
                institutionsList={institutionsList}
                isAuthenticated={session.authenticated}
                onRequestSignIn={() => setShowLogin(true)}
              />
            }
          >
            <Route path="overview" element={<OfficeOverview />} />
            <Route path="planning" element={<DailyPlanning />} />
            <Route path="routes" element={<RoutesAndMap />} />
            <Route path="manifest" element={<DispatchManifest />} />
            <Route path="fleet" element={<FleetAndDrivers />} />
            <Route path="students" element={<StudentsAndDemand />} />
            <Route path="reports" element={<ReportsAndHistory />} />
          </Route>
          <Route
            path="/student"
            element={
              <StudentView
                selectedDate={selectedDate}
                activeInstitution={activeInstitution}
                onSelectInstitution={handleSelectInstitution}
                institutionsList={institutionsList}
              />
            }
          />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>

      {/* Editorial Footer */}
      <footer className="border-t border-[#dfe5df] bg-[#f7f8f5] px-[4vw] py-6 text-xs text-[#69716d] flex flex-col sm:flex-row items-center justify-between max-w-[1280px] mx-auto w-full gap-3">
        <span>BUSify Platform &bull; {activeInstitution?.name || 'VSB Engineering College'} Transit Network</span>
        <span className="flex items-center gap-2">
          <span
            className="status-dot"
            style={{ background: statusColor(backendStatus) }}
            role="status"
            aria-label={`Backend status: ${backendStatus}`}
          />
          <span>Fulfilling UN Sustainable Development Goals 10 (Reduced Inequalities) & 11 (Sustainable Cities)</span>
        </span>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  );
}
