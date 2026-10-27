/**
 * Authoritative campus depot coordinates and institution defaults (M-02).
 * Canonical source matching backend settings: 10.95488, 77.95462.
 */

export const CANONICAL_CAMPUS_COORDINATES = {
  lat: 10.95488,
  lng: 77.95462,
};

export const DEFAULT_INSTITUTION = {
  id: 'VSB_KARUR',
  name: 'VSB Engineering College',
  campus_code: 'VSBEC',
  short_name: 'VSB Karur',
  city: 'Karudayampalayam, Karur',
  district: 'Karur',
  campus_lat: CANONICAL_CAMPUS_COORDINATES.lat,
  campus_lng: CANONICAL_CAMPUS_COORDINATES.lng,
  total_fleet_size: 45,
  fleet_size: 45,
  default_capacity: 55,
  bus_capacity: 55,
};
