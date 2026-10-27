import React from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Plus,
  Edit2,
  Trash2,
  Phone,
  CheckCircle2,
  X,
  RefreshCw,
  Check
} from 'lucide-react';
import usePageTitle from '../../hooks/usePageTitle';

export default function FleetAndDrivers() {
  usePageTitle('Fleet & Drivers');
  const {
    busesList,
    showBusModal,
    setShowBusModal,
    editingBus,
    busSaveLoading,
    busSuccessMessage,
    busError,
    setBusError,
    busFormData,
    setBusFormData,
    handleOpenAddBus,
    handleOpenEditBus,
    handleSaveBus,
    handleDeleteBus
  } = useOutletContext();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#edf1ed] pb-4">
        <div>
          <p className="kicker" style={{ margin: 0 }}>FLEET & VEHICLE INVENTORY</p>
          <h2 className="text-xl font-serif font-bold text-[#18201d]">College Bus Fleet & Driver Management</h2>
          <p className="text-xs text-[#69716d]">
            Directly configure college bus inventory, seating capacity, assigned drivers, emergency contacts, and corridor routes.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            id="btn-add-bus-page"
            onClick={handleOpenAddBus}
            className="coral-button text-xs whitespace-nowrap flex items-center gap-1.5"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add New Bus</span>
          </button>
        </div>
      </div>

      {/* Success & Error Banners */}
      {busSuccessMessage && (
        <div className="p-3 bg-[#eef5ee] border border-[#cbe3cb] rounded-[7px] text-xs text-[#2b6e3b] flex items-center gap-2 font-medium">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{busSuccessMessage}</span>
        </div>
      )}

      {busError && (
        <div role="alert" className="p-3 bg-[#fdecea] border border-[#f5c6c2] rounded-[7px] text-xs text-[#c0392b] flex items-center justify-between font-medium">
          <span>{busError}</span>
          <button onClick={() => setBusError(null)} className="text-[#c0392b] hover:opacity-75 p-0.5" title="Dismiss error">
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Fleet Table Card */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between border-b border-[#edf1ed] pb-3">
          <div>
            <h3 className="card-title text-base font-bold">Active Fleet Specifications</h3>
            <p className="text-xs text-[#69716d]">Physical vehicle sizing and driver assignments.</p>
          </div>
          <span className="badge badge-sage text-xs">{busesList.length} Registered Buses</span>
        </div>

        <div className="overflow-x-auto">
          <table className="editorial-table">
            <thead>
              <tr>
                <th>Bus Code</th>
                <th>Vehicle Reg No</th>
                <th>Capacity</th>
                <th>Assigned Driver</th>
                <th>Phone Number</th>
                <th>Designated Corridor / Route</th>
                <th>Depot Station</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {busesList.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-6 text-xs text-[#69716d]">
                    No buses registered in fleet.
                  </td>
                </tr>
              ) : (
                busesList.map((bus) => (
                  <tr key={bus.bus_id}>
                    <td className="font-bold text-[#18201d] font-mono">{bus.bus_id}</td>
                    <td className="font-mono text-xs text-[#69716d]">{bus.registration_no || 'TN 47 B 2026'}</td>
                    <td>
                      <span className="badge badge-sage text-[11px] font-bold">{bus.seats} Seats</span>
                    </td>
                    <td className="font-semibold text-[#18201d]">{bus.driver_name || 'Assigned Driver'}</td>
                    <td className="font-mono text-xs text-[#69716d]">
                      <span className="flex items-center gap-1">
                        <Phone className="h-3 w-3 text-[#2b6e3b]" />
                        <span>{bus.driver_phone || '+91 98421 10293'}</span>
                      </span>
                    </td>
                    <td className="text-xs text-[#18201d]">
                      <span className="badge badge-blue text-[10px] mr-1">{bus.default_area_id || 'Zone A'}</span>
                      <span>{bus.route_name || 'Karudayampalayam & Kovai Road Express'}</span>
                    </td>
                    <td className="text-xs text-[#69716d]">{bus.depot_location || 'VSB Main Campus, Karudayampalayam'}</td>
                    <td>
                      <span className={`badge ${bus.is_active !== false ? 'badge-sage' : 'badge-coral'} text-[10px]`}>
                        {bus.is_active !== false ? 'Active Dispatch' : 'Maintenance'}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <button
                          onClick={() => handleOpenEditBus(bus)}
                          className="p-1.5 rounded hover:bg-[#ebeee8] text-[#18201d] transition-colors"
                          title="Edit Bus Details"
                        >
                          <Edit2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteBus(bus.bus_id)}
                          className="p-1.5 rounded hover:bg-[#fee2e2] text-[#d9381e] transition-colors"
                          title="Remove Bus"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Bus Modal */}
      {showBusModal && (
        <div className="fixed inset-0 bg-[#18201d]/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] overflow-y-auto">
          <div className="bg-white rounded-[12px] border border-[#18201d] max-w-xl w-full p-6 shadow-2xl space-y-4 my-8 animate-fade-in">
            <div className="flex items-start justify-between border-b border-[#edf1ed] pb-3">
              <div>
                <p className="kicker" style={{ margin: 0 }}>FLEET SPECIFICATION</p>
                <h3 className="card-title text-base font-bold">
                  {editingBus ? `Edit Specifications: ${editingBus.bus_id}` : 'Register New Bus into College Fleet'}
                </h3>
                <p className="text-xs text-[#69716d]">
                  Configure vehicle capacity, assigned driver, emergency contact, and corridor route.
                </p>
              </div>
              <button
                onClick={() => setShowBusModal(false)}
                className="text-[#69716d] hover:text-[#18201d] p-1"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <form onSubmit={handleSaveBus} className="space-y-3.5 text-xs">
              {busError && (
                <div role="alert" className="p-2.5 bg-[#fdecea] border border-[#f5c6c2] rounded-[6px] text-xs text-[#c0392b]">
                  {busError}
                </div>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Bus Code / ID *</label>
                  <input
                    type="text"
                    required
                    disabled={!!editingBus}
                    value={busFormData.bus_id}
                    onChange={(e) => setBusFormData({ ...busFormData, bus_id: e.target.value })}
                    placeholder="e.g. BUS-11"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Vehicle Registration Number</label>
                  <input
                    type="text"
                    value={busFormData.registration_no}
                    onChange={(e) => setBusFormData({ ...busFormData, registration_no: e.target.value })}
                    placeholder="e.g. TN 47 V 1998"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Seating Capacity (Seats) *</label>
                  <input
                    type="number"
                    required
                    min={15}
                    max={100}
                    value={busFormData.seats}
                    onChange={(e) => setBusFormData({ ...busFormData, seats: parseInt(e.target.value) || 55 })}
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Default Transit Corridor</label>
                  <select
                    value={busFormData.default_area_id}
                    onChange={(e) => setBusFormData({ ...busFormData, default_area_id: e.target.value })}
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  >
                    <option value="AREA_A">Zone A: Karudayampalayam & Kovai Road</option>
                    <option value="AREA_B">Zone B: Gandhigramam & South Hub</option>
                    <option value="AREA_C">Zone C: Thanthonimalai & Collectorate</option>
                    <option value="AREA_D">Zone D: Velur & North Corridor</option>
                    <option value="AREA_E">Zone E: Paramathi & West Rural</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Assigned Driver Name *</label>
                  <input
                    type="text"
                    required
                    value={busFormData.driver_name}
                    onChange={(e) => setBusFormData({ ...busFormData, driver_name: e.target.value })}
                    placeholder="e.g. R. Murugan"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
                <div>
                  <label className="font-semibold text-[#18201d] block mb-1">Driver Phone Number *</label>
                  <input
                    type="text"
                    required
                    value={busFormData.driver_phone}
                    onChange={(e) => setBusFormData({ ...busFormData, driver_phone: e.target.value })}
                    placeholder="e.g. +91 98421 10293"
                    className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white font-mono text-xs focus:border-[#18201d] outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-[#18201d] block mb-1">Route Name / Description</label>
                <input
                  type="text"
                  value={busFormData.route_name}
                  onChange={(e) => setBusFormData({ ...busFormData, route_name: e.target.value })}
                  placeholder="e.g. Karudayampalayam - Kovai Road - Central Bus Stand Express"
                  className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                />
              </div>

              <div>
                <label className="font-semibold text-[#18201d] block mb-1">Depot / Parking Station</label>
                <input
                  type="text"
                  value={busFormData.depot_location}
                  onChange={(e) => setBusFormData({ ...busFormData, depot_location: e.target.value })}
                  placeholder="e.g. VSB Main Campus Depot, Karudayampalayam"
                  className="w-full px-3 py-2 rounded border border-[#dfe5df] bg-white text-xs focus:border-[#18201d] outline-none"
                />
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="chk-bus-active-page"
                  checked={busFormData.is_active}
                  onChange={(e) => setBusFormData({ ...busFormData, is_active: e.target.checked })}
                  className="rounded text-[#ff6b00]"
                />
                <label htmlFor="chk-bus-active-page" className="text-xs text-[#18201d] font-semibold cursor-pointer">
                  Vehicle is active and available for daily dispatch
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#edf1ed]">
                <button
                  type="button"
                  onClick={() => setShowBusModal(false)}
                  className="outline-button text-xs py-1.5 px-3"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busSaveLoading}
                  className="coral-button text-xs py-1.5 px-4 font-bold flex items-center gap-1.5"
                >
                  {busSaveLoading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Check className="h-3.5 w-3.5" />}
                  <span>{editingBus ? 'Save Changes' : 'Register Bus'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
