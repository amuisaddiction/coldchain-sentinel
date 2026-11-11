'use client';

import React, { useState } from 'react';
import {
  Package,
  Search,
  Filter,
  CheckCircle2,
  AlertTriangle,
  CreditCard,
  Thermometer,
  ArrowRight,
  Shield,
  FileText,
  Clock,
  ExternalLink,
  ChevronRight,
  X,
} from 'lucide-react';
import { ShipmentModel, DEMO_SHIPMENTS } from '@/lib/mockData';

interface ShipmentsViewProps {
  shipments: ShipmentModel[];
  onSelectShipment: (shipment: ShipmentModel) => void;
  onNavigateTab: (tab: any) => void;
}

export function ShipmentsView({ shipments, onSelectShipment, onNavigateTab }: ShipmentsViewProps) {
  const allShipments = shipments.length > 0 ? shipments : DEMO_SHIPMENTS;
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [activeDetailShipment, setActiveDetailShipment] = useState<ShipmentModel | null>(null);
  const [detailTab, setDetailTab] = useState<'overview' | 'telemetry' | 'custody' | 'payment'>('overview');

  const filtered = allShipments.filter((s) => {
    const matchesFilter =
      filterStatus === 'ALL'
        ? true
        : filterStatus === 'VERIFIED'
        ? s.status === 'VERIFIED'
        : filterStatus === 'BREACH'
        ? s.temp_status === 'BREACH'
        : filterStatus === 'REVIEW'
        ? s.status === 'REVIEW_REQUIRED'
        : true;

    const matchesSearch =
      s.tracking_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.medicine_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.carrier_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.origin_city.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.destination_city.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesFilter && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Filter & Search HUD */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 panel-card p-4">
        {/* Search */}
        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400 pointer-events-none" />
          <input
            type="text"
            placeholder="Filter by tracking, medicine, city..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl border border-[#1E293B] bg-[#0A0F1D] py-2 pl-9 pr-3 text-xs text-slate-200 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition"
          />
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto">
          {[
            { id: 'ALL', label: 'All Shipments' },
            { id: 'VERIFIED', label: 'Verified Safe' },
            { id: 'BREACH', label: 'Thermal Breaches' },
            { id: 'REVIEW', label: 'Manual Review' },
          ].map((f) => (
            <button
              key={f.id}
              onClick={() => setFilterStatus(f.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition shrink-0 ${
                filterStatus === f.id
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                  : 'bg-[#0E1526] text-slate-400 hover:text-slate-200 border border-[#1A253A]'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Registry Table */}
      <div className="panel-card p-5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1E293B] text-slate-400 text-[11px] font-mono uppercase tracking-wider">
                <th className="pb-3 font-medium">Consignment ID</th>
                <th className="pb-3 font-medium">Medicine & Batch</th>
                <th className="pb-3 font-medium">Route Corridor</th>
                <th className="pb-3 font-medium">Carrier</th>
                <th className="pb-3 font-medium">Temperature Condition</th>
                <th className="pb-3 font-medium">Compliance Decision</th>
                <th className="pb-3 font-medium">Payment State</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#182338]">
              {filtered.map((s) => (
                <tr
                  key={s.tracking_number}
                  onClick={() => {
                    setActiveDetailShipment(s);
                    onSelectShipment(s);
                  }}
                  className="hover:bg-[#11192C] transition cursor-pointer group"
                >
                  <td className="py-3.5 font-mono font-semibold text-cyan-400 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
                    {s.tracking_number}
                  </td>
                  <td className="py-3.5">
                    <div className="font-semibold text-slate-200">{s.medicine_name}</div>
                    <div className="text-[10px] text-slate-400 font-mono">{s.batch_number}</div>
                  </td>
                  <td className="py-3.5 text-slate-300">
                    <div className="font-medium">
                      {s.origin_city} → {s.destination_city}
                    </div>
                    <div className="text-[10px] text-slate-500">{s.origin.split(',')[0]}</div>
                  </td>
                  <td className="py-3.5 text-slate-300 font-medium">
                    {s.carrier_name}
                  </td>
                  <td className="py-3.5">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-lg text-xs font-mono font-medium ${
                        s.temp_status === 'SAFE'
                          ? 'bg-emerald-950/40 text-emerald-300 border border-emerald-500/30'
                          : s.temp_status === 'WARNING'
                          ? 'bg-amber-950/40 text-amber-300 border border-amber-500/30'
                          : 'bg-rose-950/40 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      <Thermometer className="h-3.5 w-3.5" />
                      {s.current_temp}°C
                    </span>
                  </td>
                  <td className="py-3.5">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold ${
                        s.status === 'VERIFIED'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                          : s.status === 'FAILED'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/40'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/40'
                      }`}
                    >
                      {s.status === 'VERIFIED' ? (
                        <CheckCircle2 className="h-3 w-3" />
                      ) : (
                        <AlertTriangle className="h-3 w-3" />
                      )}
                      {s.status}
                    </span>
                  </td>
                  <td className="py-3.5">
                    <div className="font-mono text-slate-200">
                      ${s.payment_amount.toLocaleString()} {s.currency}
                    </div>
                    <div
                      className={`text-[10px] font-semibold ${
                        s.payment_status === 'CAPTURED'
                          ? 'text-emerald-400'
                          : s.payment_status === 'CAPTURE_BLOCKED'
                          ? 'text-rose-400'
                          : 'text-amber-400'
                      }`}
                    >
                      {s.payment_status}
                    </div>
                  </td>
                  <td className="py-3.5 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveDetailShipment(s);
                        onSelectShipment(s);
                      }}
                      className="px-3 py-1 rounded-lg border border-[#233554] bg-[#141E33] text-slate-300 hover:text-cyan-300 hover:border-cyan-500 text-xs transition"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Slide-over Inspection Drawer when a shipment is selected */}
      {activeDetailShipment && (
        <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/60 backdrop-blur-sm">
          <div className="h-full w-full max-w-xl bg-[#0B101D] border-l border-[#1F2E47] p-6 overflow-y-auto space-y-6 animate-in slide-in-from-right duration-300 shadow-2xl">
            {/* Drawer Header */}
            <div className="flex items-center justify-between border-b border-[#1A253A] pb-4">
              <div>
                <span className="text-xs font-mono font-semibold text-cyan-400">
                  {activeDetailShipment.tracking_number}
                </span>
                <h3 className="text-lg font-bold text-slate-100">{activeDetailShipment.medicine_name}</h3>
                <p className="text-xs text-slate-400">{activeDetailShipment.batch_number}</p>
              </div>
              <button
                onClick={() => setActiveDetailShipment(null)}
                className="h-8 w-8 rounded-lg bg-[#141E33] border border-[#233554] flex items-center justify-center text-slate-400 hover:text-white transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Inspection Tabs */}
            <div className="flex items-center gap-1 border-b border-[#1A253A] pb-2 text-xs">
              {(['overview', 'telemetry', 'custody', 'payment'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setDetailTab(tab)}
                  className={`px-3 py-1.5 rounded-lg capitalize font-medium transition ${
                    detailTab === tab
                      ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Tab 1: Overview */}
            {detailTab === 'overview' && (
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl bg-[#090E1A] border border-[#182338] space-y-2">
                  <span className="text-slate-400 uppercase tracking-wider font-mono text-[10px]">
                    Transit Corridor
                  </span>
                  <div className="text-sm font-semibold text-slate-200">
                    {activeDetailShipment.origin} → {activeDetailShipment.destination}
                  </div>
                  <div className="text-slate-400">Carrier: {activeDetailShipment.carrier_name}</div>
                  <div className="text-slate-400 font-mono">Dispatched: {activeDetailShipment.dispatched_at}</div>
                </div>

                <div className="p-4 rounded-xl bg-[#090E1A] border border-[#182338] space-y-2">
                  <span className="text-slate-400 uppercase tracking-wider font-mono text-[10px]">
                    Temperature Compliance Limits
                  </span>
                  <div className="grid grid-cols-3 gap-2 pt-1 font-mono">
                    <div className="p-2 rounded-lg bg-[#121B2F] border border-[#1D2B47]">
                      <span className="text-[10px] text-slate-400 block">Min Threshold</span>
                      <span className="text-sm font-bold text-slate-200">+{activeDetailShipment.min_allowed_temp}°C</span>
                    </div>
                    <div className="p-2 rounded-lg bg-[#121B2F] border border-[#1D2B47]">
                      <span className="text-[10px] text-slate-400 block">Max Threshold</span>
                      <span className="text-sm font-bold text-slate-200">+{activeDetailShipment.max_allowed_temp}°C</span>
                    </div>
                    <div className="p-2 rounded-lg bg-[#121B2F] border border-[#1D2B47]">
                      <span className="text-[10px] text-slate-400 block">Recorded Temp</span>
                      <span
                        className={`text-sm font-bold ${
                          activeDetailShipment.temp_status === 'SAFE' ? 'text-emerald-400' : 'text-rose-400'
                        }`}
                      >
                        +{activeDetailShipment.current_temp}°C
                      </span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-[#090E1A] border border-[#182338]">
                  <span className="text-slate-400 uppercase tracking-wider font-mono text-[10px] block mb-1">
                    Automated Assessment
                  </span>
                  <p className="text-slate-300 leading-relaxed text-xs">{activeDetailShipment.description}</p>
                </div>
              </div>
            )}

            {/* Tab 2: Telemetry Quick Links */}
            {detailTab === 'telemetry' && (
              <div className="space-y-4 text-xs">
                <p className="text-slate-300">
                  Continuous sensor readings recorded by certified NIST temperature data loggers.
                </p>
                <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30 text-cyan-300 flex items-center justify-between">
                  <span>View comprehensive temperature curves</span>
                  <button
                    onClick={() => onNavigateTab('temperature')}
                    className="px-3 py-1.5 rounded-lg bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 transition"
                  >
                    Open Monitor
                  </button>
                </div>
              </div>
            )}

            {/* Tab 3: Custody */}
            {detailTab === 'custody' && (
              <div className="space-y-4 text-xs">
                <p className="text-slate-300">
                  Full custody handover events recorded across ground dispatch, air carrier, and hospital delivery.
                </p>
                <button
                  onClick={() => onNavigateTab('timeline')}
                  className="w-full py-2.5 rounded-xl bg-[#141E33] border border-[#233554] text-cyan-300 font-semibold hover:border-cyan-500 transition text-center"
                >
                  View Vertical Custody Timeline →
                </button>
              </div>
            )}

            {/* Tab 4: Payment */}
            {detailTab === 'payment' && (
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-xl bg-[#090E1A] border border-[#182338]">
                  <span className="text-slate-400 font-mono uppercase text-[10px]">Payment Escrow Status</span>
                  <div className="text-lg font-bold font-mono text-slate-100 mt-1">
                    ${activeDetailShipment.payment_amount.toLocaleString()} {activeDetailShipment.currency}
                  </div>
                  <div
                    className={`text-xs font-semibold mt-1 ${
                      activeDetailShipment.payment_status === 'CAPTURED'
                        ? 'text-emerald-400'
                        : activeDetailShipment.payment_status === 'CAPTURE_BLOCKED'
                        ? 'text-rose-400'
                        : 'text-amber-400'
                    }`}
                  >
                    Status: {activeDetailShipment.payment_status}
                  </div>
                </div>
                <button
                  onClick={() => onNavigateTab('payments')}
                  className="w-full py-2.5 rounded-xl bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 font-semibold hover:bg-cyan-500/30 transition text-center"
                >
                  Manage Escrow & Sandbox Release →
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
