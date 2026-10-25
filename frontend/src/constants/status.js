/**
 * Backend health status presentation.
 *
 * Kept in one module because the previous implementation was duplicated and
 * had drifted: the footer used a hardcoded green regardless of status, and the
 * navbar collapsed DEGRADED and OFFLINE into a single "Connecting" label.
 *
 * Status vocabulary:
 *   CHECKING — health request in flight
 *   HEALTHY  — backend reachable, database connected
 *   DEGRADED — backend reachable, database NOT connected
 *   OFFLINE  — backend unreachable
 */
export const BACKEND_STATUS = {
  CHECKING: 'CHECKING',
  HEALTHY: 'HEALTHY',
  DEGRADED: 'DEGRADED',
  OFFLINE: 'OFFLINE',
};

const PRESENTATION = {
  [BACKEND_STATUS.CHECKING]: { color: '#9aa3a0', label: 'Checking…' },
  [BACKEND_STATUS.HEALTHY]: { color: '#48a15b', label: 'Dispatch Active' },
  [BACKEND_STATUS.DEGRADED]: { color: '#d98324', label: 'Database Unavailable' },
  [BACKEND_STATUS.OFFLINE]: { color: '#c0392b', label: 'Backend Offline' },
};

const FALLBACK = PRESENTATION[BACKEND_STATUS.CHECKING];

export const statusColor = (status) => PRESENTATION[status]?.color ?? FALLBACK.color;
export const statusLabel = (status) => PRESENTATION[status]?.label ?? FALLBACK.label;