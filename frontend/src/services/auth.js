/**
 * auth.js — transport-officer session handling.
 *
 * Storage choice: `sessionStorage`, NOT `localStorage`.
 * The access token lives for 8 hours (JWT_ACCESS_TOKEN_EXPIRE_MINUTES). In
 * localStorage it would survive the browser closing and be readable by any
 * script injected on the origin; sessionStorage clears with the tab and is
 * scoped away from long-lived persistence.
 *
 * Note this is still XSS-readable. The real mitigation is a CSP plus not
 * rendering untrusted values as HTML (see open item C-12).
 */

const TOKEN_KEY = 'busify.session.token';
const ROLE_KEY = 'busify.session.role';
const NAME_KEY = 'busify.session.name';

/** Roles accepted by require_admin on the backend. Keep in sync. */
export const ADMIN_ROLES = ['admin', 'transport_officer'];

export const getToken = () => sessionStorage.getItem(TOKEN_KEY);
export const getRole = () => sessionStorage.getItem(ROLE_KEY);
export const getDisplayName = () => sessionStorage.getItem(NAME_KEY);

export const isAuthenticated = () => Boolean(getToken());

export const hasAdminRole = () => ADMIN_ROLES.includes(getRole());

export function setSession({ access_token, role, name }) {
  sessionStorage.setItem(TOKEN_KEY, access_token);
  sessionStorage.setItem(ROLE_KEY, role ?? '');
  sessionStorage.setItem(NAME_KEY, name ?? '');
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(ROLE_KEY);
  sessionStorage.removeItem(NAME_KEY);
}

/** Normalises axios/FastAPI error shapes into a message safe to render. */
export function describeError(err) {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  // FastAPI validation errors arrive as a list of {loc, msg, type}
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => d?.msg || JSON.stringify(d)).join('; ');
  }
  if (detail) return JSON.stringify(detail);
  if (err?.code === 'ECONNABORTED') return 'Request timed out.';
  if (err?.message === 'Network Error') return 'Cannot reach the BUSify API.';
  return err?.message || 'Unexpected error.';
}