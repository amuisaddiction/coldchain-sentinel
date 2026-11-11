'use client';

import React, { useState } from 'react';
import {
  Navigation,
  MapPin,
  Clock,
  Thermometer,
  ShieldCheck,
  AlertTriangle,
  CreditCard,
  Truck,
  Building,
  CheckCircle2,
  Calendar,
  Layers,
  Info,
} from 'lucide-react';
import { ShipmentModel, DEMO_SHIPMENTS } from '@/lib/mockData';
import { InteractiveMap } from './InteractiveMap';

interface LiveTrackingViewProps {
  shipments: ShipmentModel[];
  selectedShipment: ShipmentModel;
  onSelectShipment: (shipment: ShipmentModel) => void;
  onNavigateTab: (tab: any) => void;
}

export function LiveTrackingView({
  shipments,
  selectedShipment,
  onSelectShipment,
  onNavigateTab,
}: LiveTrackingViewProps) {
  const current = selectedShipment || shipments[0] || DEMO_SHIPMENTS[0];
  const [selectedWaypointInfo, setSelectedWaypointInfo] = useState<string | null>(null);

  return (
    <div className="flex flex-col h-[calc(100vh-8.5rem)] space-y-4 max-w-7xl mx-auto">
      {/* Top Consignment Selector Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0">
        <span className="text-xs font-mono font-medium text-slate-400 shrink-0">SELECT ROUTE:</span>
        {(shipments.length > 0 ? shipments : DEMO_SHIPMENTS).map((s) => {
          const isSelected = s.tracking_number === current.tracking_number;
          return (
            <button
              key={s.tracking_number}
              onClick={() => onSelectShipment(s)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition shrink-0 border ${
                isSelected
                  ? 'bg-cyan-500/20 border-cyan-400/60 text-cyan-200 shadow-glow-cyan'
                  : 'bg-[#0E1524] border-[#1E293B] text-slate-400 hover:border-slate-600 hover:text-slate-200'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  s.temp_status === 'SAFE'
                    ? 'bg-emerald-400'
                    : s.temp_status === 'WARNING'
                    ? 'bg-amber-400'
                    : 'bg-rose-400'
                }`}
              ></span>
              <span className="font-mono">{s.tracking_number}</span>
              <span className="text-[10px] opacity-75">
                ({s.origin_city} → {s.destination_city})
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Hero Layout: 68% Left Map + 32% Right Telemetry & Condition Panel */}
      <div className="flex flex-col lg:flex-row flex-1 gap-6 overflow-hidden">
        {/* LEFT 68%: Large Interactive GIS Vector Map */}
        <div className="lg:w-[68%] flex flex-col h-full rounded-2xl overflow-hidden relative">
          <InteractiveMap
            shipment={current}
            onSelectWaypoint={(name) => setSelectedWaypointInfo(name)}
            className="flex-1"
          />
        </div>

        {/* RIGHT 32%: Live Telemetry & Custody Inspection Panel */}
        <div className="lg:w-[32%] flex flex-col h-full panel-card p-5 overflow-y-auto space-y-5">
          {/* Shipment Identification Card */}
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-cyan-400 font-semibold flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse"></span>
                {current.tracking_number}
              </span>
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                  current.status === 'VERIFIED'
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : current.status === 'FAILED'
                    ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                    : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                }`}
              >
                {current.status}
              </span>
            </div>

            <h3 className="text-base font-bold text-slate-100 mt-2">{current.medicine_name}</h3>
            <p className="text-xs font-mono text-slate-400">{current.batch_number}</p>
          </div>

          {/* Route Progress Bar */}
          <div className="space-y-1.5 p-3 rounded-xl bg-[#090E1A] border border-[#182338]">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-slate-400">Transit Progress</span>
              <span className="text-cyan-400 font-bold">{current.progress_pct}%</span>
            </div>
            <div className="w-full h-2 rounded-full bg-[#162035] overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  current.temp_status === 'BREACH'
                    ? 'bg-gradient-to-r from-cyan-400 to-rose-500'
                    : 'bg-gradient-to-r from-cyan-400 to-emerald-400'
                }`}
                style={{ width: `${current.progress_pct}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 font-mono pt-1">
              <span>{current.origin_city}</span>
              <span>{current.destination_city}</span>
            </div>
          </div>

          {/* Current Condition Sensors */}
          <div className="grid grid-cols-2 gap-3">
            <div
              className={`p-3 rounded-xl border flex flex-col justify-between ${
                current.temp_status === 'SAFE'
                  ? 'bg-emerald-950/20 border-emerald-500/30'
                  : current.temp_status === 'WARNING'
                  ? 'bg-amber-950/20 border-amber-500/30'
                  : 'bg-rose-950/20 border-rose-500/30'
              }`}
            >
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Temperature</span>
                <Thermometer
                  className={`h-4 w-4 ${
                    current.temp_status === 'SAFE'
                      ? 'text-emerald-400'
                      : current.temp_status === 'WARNING'
                      ? 'text-amber-400'
                      : 'text-rose-400'
                  }`}
                />
              </div>
              <div className="mt-2">
                <div
                  className={`text-xl font-bold font-mono ${
                    current.temp_status === 'SAFE'
                      ? 'text-emerald-300'
                      : current.temp_status === 'WARNING'
                      ? 'text-amber-300'
                      : 'text-rose-300'
                  }`}
                >
                  {current.current_temp}°C
                </div>
                <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                  Allowed: {current.min_allowed_temp}°C–{current.max_allowed_temp}°C
                </div>
              </div>
            </div>

            <div className="p-3 rounded-xl bg-[#090E1A] border border-[#182338] flex flex-col justify-between">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Escrow State</span>
                <CreditCard className="h-4 w-4 text-cyan-400" />
              </div>
              <div className="mt-2">
                <div className="text-xl font-bold font-mono text-slate-200">
                  ${current.payment_amount.toLocaleString()}
                </div>
                <div
                  className={`text-[10px] font-semibold font-mono mt-0.5 ${
                    current.payment_status === 'CAPTURED'
                      ? 'text-emerald-400'
                      : current.payment_status === 'CAPTURE_BLOCKED'
                      ? 'text-rose-400'
                      : 'text-amber-400'
                  }`}
                >
                  {current.payment_status}
                </div>
              </div>
            </div>
          </div>

          {/* Custody Chain Waypoints List */}
          <div className="space-y-2">
            <span className="text-xs font-mono uppercase tracking-wider text-slate-400">
              Verified Handover Stops
            </span>
            <div className="space-y-2">
              {current.waypoints.map((wp, idx) => (
                <div
                  key={wp.name}
                  className={`flex items-start gap-2.5 p-2 rounded-lg text-xs border ${
                    wp.status === 'completed'
                      ? 'bg-emerald-950/20 border-emerald-500/30 text-slate-300'
                      : wp.status === 'active'
                      ? 'bg-cyan-950/30 border-cyan-400/40 text-cyan-200'
                      : 'bg-[#090E1A] border-[#182338] text-slate-500'
                  }`}
                >
                  <div className="mt-0.5">
                    {wp.status === 'completed' ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <div className="h-3.5 w-3.5 rounded-full border border-cyan-400 flex items-center justify-center">
                        <div className="h-1.5 w-1.5 rounded-full bg-cyan-400"></div>
                      </div>
                    )}
                  </div>
                  <div className="flex-1 truncate">
                    <div className="font-medium text-slate-200 truncate">{wp.name}</div>
                    {wp.time && <div className="text-[10px] text-cyan-400 font-mono">{wp.time} UTC Handover</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Plain-Language Condition Explanation */}
          <div className="p-3 rounded-xl bg-[#090E1A] border border-[#182338] text-xs space-y-1">
            <span className="font-semibold text-slate-200 flex items-center gap-1.5">
              <Info className="h-3.5 w-3.5 text-cyan-400" />
              Automated Sentinel Assessment
            </span>
            <p className="text-slate-400 text-[11px] leading-relaxed">{current.description}</p>
          </div>

          {/* Action Quick Buttons */}
          <div className="grid grid-cols-2 gap-2 pt-2">
            <button
              onClick={() => onNavigateTab('temperature')}
              className="px-3 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/20 text-xs font-medium transition text-center"
            >
              Analyze Telemetry
            </button>
            <button
              onClick={() => onNavigateTab('payments')}
              className="px-3 py-2 rounded-xl bg-[#141E33] border border-[#233554] text-slate-300 hover:text-white hover:border-slate-500 text-xs font-medium transition text-center"
            >
              Manage Payment
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
