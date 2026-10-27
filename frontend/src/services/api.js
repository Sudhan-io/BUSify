import axios from 'axios';
import { getToken, clearSession, setSession } from './auth';

const rawBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api';
const trimmedBase = rawBase.replace(/\/+$/, '');
const API_BASE_URL = trimmedBase.endsWith('/api') ? trimmedBase : `${trimmedBase}/api`;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ─── Auth wiring ─────────────────────────────────────────────────────────────
// A handler registered by the app shell, invoked whenever the API rejects a
// token. Kept as a callback rather than imported app state so this module stays
// free of React dependencies.
let unauthorizedHandler = null;

export const onUnauthorized = (handler) => {
  unauthorizedHandler = handler;
};

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      clearSession();
      unauthorizedHandler?.(error);
    }
    return Promise.reject(error);
  }
);

/**
 * Maps the API's institution shape onto the names the UI already uses.
 *
 * The backend names these fields `campus_code`, `total_fleet_size` and
 * `default_capacity` (see routes_institution.py). The UI reads `short_name`,
 * `fleet_size` and `bus_capacity`. Previously the two sets simply did not
 * match: reads silently fell back to hardcoded defaults, and on write the
 * unknown keys were dropped by Pydantic so every campus was created with the
 * backend's defaults regardless of what the user entered.
 *
 * Normalising here keeps the mismatch in one place instead of at every read site.
 */
export const normalizeInstitution = (raw) => {
  if (!raw || typeof raw !== 'object') return raw;
  return {
    ...raw,
    short_name: raw.short_name ?? raw.campus_code ?? null,
    fleet_size: raw.fleet_size ?? raw.total_fleet_size ?? null,
    bus_capacity: raw.bus_capacity ?? raw.default_capacity ?? null,
  };
};

/** Builds the InstitutionCreateRequest body the backend actually accepts. */
const toInstitutionCreatePayload = (data = {}) => ({
  name: data.name,
  campus_code: data.campus_code ?? data.short_name ?? undefined,
  city: data.city,
  district: data.district || undefined,
  state: data.state || undefined,
  campus_lat: data.campus_lat,
  campus_lng: data.campus_lng,
  depot_address: data.depot_address || undefined,
  total_fleet_size: data.total_fleet_size ?? data.fleet_size,
  default_capacity: data.default_capacity ?? data.bus_capacity,
});

export const api = {
  // Authentication
  login: async (username, password) => {
    const res = await apiClient.post('/auth/token', { username, password });
    setSession(res.data);
    return res.data;
  },

  // Health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Stops and Fleet
  getStops: async () => {
    const res = await apiClient.get('/stops');
    return res.data;
  },

  getBuses: async (areaId = null, isActive = null, search = null) => {
    const params = {};
    if (areaId && areaId !== 'ALL') params.area_id = areaId;
    if (isActive !== null && isActive !== undefined) params.is_active = isActive;
    if (search && search.trim()) params.search = search.trim();
    const res = await apiClient.get('/buses', { params });
    return res.data;
  },

  getDrivers: async (isActive = null, areaId = null, search = null) => {
    const params = {};
    if (isActive !== null && isActive !== undefined) params.is_active = isActive;
    if (areaId && areaId !== 'ALL') params.area_id = areaId;
    if (search && search.trim()) params.search = search.trim();
    const res = await apiClient.get('/buses/drivers', { params });
    return res.data;
  },

  addBus: async (busData) => {
    const res = await apiClient.post('/buses', busData);
    return res.data;
  },

  updateBus: async (busId, busData) => {
    const res = await apiClient.put(`/buses/${busId}`, busData);
    return res.data;
  },

  deleteBus: async (busId) => {
    const res = await apiClient.delete(`/buses/${busId}`);
    return res.data;
  },

  // Demand Forecast (p50 / p90)
  getForecast: async (date) => {
    const params = date ? { date } : {};
    const res = await apiClient.get('/forecast', { params });
    return res.data;
  },

  // OR-Tools Fleet Allocation
  getAllocation: async (date) => {
    const params = date ? { date } : {};
    const res = await apiClient.get('/allocation', { params });
    return res.data;
  },

  // Capacitated VRP Routes
  getRoutes: async (areaId, date, campusLat = null, campusLng = null, direction = 'MORNING_PICKUP') => {
    const params = { area_id: areaId };
    if (date) params.date = date;
    if (campusLat !== null && campusLat !== undefined) params.campus_lat = campusLat;
    if (campusLng !== null && campusLng !== undefined) params.campus_lng = campusLng;
    if (direction) params.direction = direction;
    const res = await apiClient.get('/routes', { params });
    return res.data;
  },

  // Bus Crowding Advisory
  getCrowding: async (busId, date) => {
    const params = { bus_id: busId };
    if (date) params.date = date;
    const res = await apiClient.get('/crowding', { params });
    return res.data;
  },

  // Backtesting Simulator
  simulate: async (sampleDays = 7) => {
    const res = await apiClient.post('/simulate', { sample_days: sampleDays });
    return res.data;
  },

  // Operational Workflow (College Office & Student Pass)
  getOperationalManifest: async (date, scenario = 'REGULAR') => {
    const params = { scenario };
    if (date) params.date = date;
    const res = await apiClient.get('/workflow/operational-manifest', { params });
    return res.data;
  },

  approvePlan: async (date, scenario = 'REGULAR', slot = 'morning') => {
    const res = await apiClient.post('/workflow/plan/approve', {
      date,
      scenario,
      slot,
    });
    return res.data;
  },

  getPlanStatus: async (date, slot = 'morning') => {
    const params = { date, slot };
    const res = await apiClient.get('/workflow/plan/status', { params });
    return res.data;
  },

  // Student Registrations & Demand Summary
  getStudentRegistrations: async (areaId = null, stopId = null, search = null, page = 1, pageSize = 50) => {
    const params = { page, page_size: pageSize };
    if (areaId && areaId !== 'ALL') params.area_id = areaId;
    if (stopId) params.stop_id = stopId;
    if (search && search.trim()) params.search = search.trim();
    const res = await apiClient.get('/workflow/students/registrations', { params });
    return res.data;
  },

  getDemandSummary: async (date = null) => {
    const params = date ? { date } : {};
    const res = await apiClient.get('/workflow/demand-summary', { params });
    return res.data;
  },

  getStudents: async () => {
    const res = await apiClient.get('/workflow/students');
    return res.data?.students || [];
  },

  getStudentProfile: async (rollNo, date) => {
    const params = { roll_no: rollNo };
    if (date) params.date = date;
    const res = await apiClient.get('/workflow/student-profile', { params });
    return res.data;
  },

  toggleStudentOptOut: async (rollNo, travelingToday, date) => {
    const res = await apiClient.post('/workflow/student-opt-out', {
      student_roll: rollNo,
      traveling_today: travelingToday,
      // Omitting this made the backend default to today, so the navbar date
      // picker was silently ignored and the toggle applied to the wrong day.
      ...(date ? { date } : {}),
    });
    return res.data;
  },

  // Suggestion 1 & 2: CSV Upload & Comparative Benchmark with College Anchor
  uploadStopsCsv: async (fileOrText, campusLat, campusLng, institutionName) => {
    const params = {};
    if (campusLat !== undefined) params.campus_lat = campusLat;
    if (campusLng !== undefined) params.campus_lng = campusLng;
    if (institutionName !== undefined) params.institution_name = institutionName;

    let res;
    if (typeof fileOrText === 'string') {
      const formData = new FormData();
      formData.append('csv_text', fileOrText);
      res = await apiClient.post('/workflow/upload-stops-csv', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } else if (fileOrText instanceof File) {
      const formData = new FormData();
      formData.append('file', fileOrText);
      res = await apiClient.post('/workflow/upload-stops-csv', formData, {
        params,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    } else {
      res = await apiClient.post('/workflow/upload-stops-csv', {}, { params });
    }
    return res.data;
  },

  downloadTemplateCsv: async () => {
    const res = await apiClient.get('/workflow/template-csv', {
      responseType: 'blob',
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'college_stops_template.csv');
    document.body.appendChild(link);
    link.click();
    link.parentNode.removeChild(link);
    return true;
  },

  // Multi-Institution & College Scalability API
  getDistricts: async () => {
    const res = await apiClient.get('/institutions/districts');
    return res.data?.districts || [];
  },

  getInstitutions: async (district = null, search = null) => {
    const params = {};
    if (district && district !== 'All Districts') params.district = district;
    if (search && search.trim()) params.search = search.trim();
    const res = await apiClient.get('/institutions', { params });
    return (res.data?.institutions || []).map(normalizeInstitution);
  },

  getActiveInstitution: async () => {
    const res = await apiClient.get('/institutions/active');
    return normalizeInstitution(res.data);
  },

  setActiveInstitution: async (institutionId) => {
    const res = await apiClient.post('/institutions/active', {
      institution_id: institutionId,
    });
    return normalizeInstitution(res.data?.active_institution);
  },

  createInstitution: async (institutionData) => {
    const res = await apiClient.post('/institutions', toInstitutionCreatePayload(institutionData));
    // The endpoint wraps the created campus as { success, message, institution }.
    // Returning the wrapper here made every caller read `created.id` as undefined.
    return normalizeInstitution(res.data?.institution);
  },
};

export default api;

