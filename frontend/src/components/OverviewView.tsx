'use client';

import React from 'react';
import {
  Package,
  Navigation,
  CheckCircle2,
  AlertTriangle,
  Lock,
  ArrowRight,
  TrendingUp,
  Thermometer,
  Shield,
  Activity,
  CreditCard,
  Building,
  Sparkles,
} from 'lucide-react';
import { ShipmentModel, DEMO_SHIPMENTS } from '@/lib/mockData';
import { InteractiveMap } from './InteractiveMap';

interface OverviewViewProps {
  shipments: ShipmentModel[];
  onSelectShipment: (shipment: ShipmentModel) => void;
  onNavigateTab: (tab: any) => void;
}

export function OverviewView({ shipments, onSelectShipment, onNavigateTab }: OverviewViewProps) {
  const activeShipments = shipments.length > 0 ? shipments : DEMO_SHIPMENTS;
  const inTransitCount = activeShipments.filter((s) => s.status === 'IN_TRANSIT' || s.progress_pct < 100).length;
  const verifiedCount = activeShipments.filter((s) => s.status === 'VERIFIED').length;
  const breachCount = activeShipments.filter((s) => s.temp_status === 'BREACH' || s.status === 'FAILED').length;
  const blockedPaymentCount = activeShipments.filter((s) => s.payment_status === 'CAPTURE_BLOCKED' || s.payment_status === 'HELD_FOR_REVIEW').length;

  const heroShipment = activeShipments[0] || DEMO_SHIPMENTS[0];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* SIGNATURE AI SETTLEMENT INTELLIGENCE CALLOUT */}
      <div className="p-4 rounded-xl border border-cyan-brand/40 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide">ColdChain AI Settlement Intelligence</h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-brand/20 text-cyan-brand border border-cyan-brand/30 font-mono">NEW SIGNATURE FEATURE</span>
            </div>
            <p className="text-xs text-canvas-300 mt-0.5">
              Autonomous contract understanding, multi-factor investigation, and human-approved PayPal execution.
            </p>
          </div>
        </div>
        <button
          onClick={() => onNavigateTab('settlement')}
          className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-cyan-brand text-canvas-950 font-bold text-xs hover:bg-cyan-brand/90 transition-all shadow-glow-cyan shrink-0"
        >
          <span>Launch AI Settlement</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* 1. TOP 5 PROMINENT KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1 */}
        <div className="panel-card p-4 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Consignments</span>
            <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <Package className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold font-mono text-slate-100">{activeShipments.length}</div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-slate-400">
              <span className="text-emerald-400 font-semibold">100% Tracked</span>
              <span>across Europe/Asia</span>
            </div>
          </div>
        </div>

        {/* KPI 2 */}
        <div className="panel-card p-4 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">In Transit</span>
            <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
              <Navigation className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold font-mono text-sky-400">{inTransitCount}</div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-slate-400">
              <span className="text-sky-400 font-semibold">Live GPS & Nodes</span>
              <span>moving now</span>
            </div>
          </div>
        </div>

        {/* KPI 3 */}
        <div className="panel-card p-4 flex flex-col justify-between relative overflow-hidden group">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Verified & Released</span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold font-mono text-emerald-400">{verifiedCount}</div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-emerald-400/90 font-medium">
              <span>All 2°C–8°C rules passed</span>
            </div>
          </div>
        </div>

        {/* KPI 4 */}
        <div className="panel-card p-4 flex flex-col justify-between relative overflow-hidden group border-rose-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Critical Excursions</span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold font-mono text-rose-400">{breachCount}</div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-rose-400 font-semibold">
              <span>14.5°C Tarmac Spike Detected</span>
            </div>
          </div>
        </div>

        {/* KPI 5 */}
        <div className="panel-card p-4 flex flex-col justify-between relative overflow-hidden group border-amber-500/30">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Payments Blocked</span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Lock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-4">
            <div className="text-2xl font-bold font-mono text-amber-400">{blockedPaymentCount}</div>
            <div className="flex items-center gap-1.5 mt-1 text-[11px] text-amber-400 font-semibold">
              <span>Fraud & Compliance Escrow</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. SHIPMENT MAP PREVIEW & CRITICAL ALERTS PANEL */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Live Map Preview */}
        <div className="lg:col-span-2 panel-card p-5 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
                  Active Transit Corridor
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30">
                  {heroShipment.tracking_number}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                {heroShipment.origin} → {heroShipment.destination}
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('tracking')}
              className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition"
            >
              <span>Expand Map</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>

          <div className="h-[320px] w-full rounded-xl overflow-hidden">
            <InteractiveMap shipment={heroShipment} />
          </div>
        </div>

        {/* Right 1 Col: Urgent Attention & Alerts Feed */}
        <div className="panel-card p-5 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3 border-b border-[#1A263D] pb-3">
              <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-400" />
                <span>Urgent Interventions</span>
              </h2>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                2 ACTIONS NEEDED
              </span>
            </div>

            <div className="space-y-3 mt-3">
              {/* Alert 1 */}
              <div
                onClick={() => onNavigateTab('temperature')}
                className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 cursor-pointer hover:border-rose-400 transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-rose-300">Thermal Excursion Breach</span>
                  <span className="text-[10px] font-mono text-rose-400">CHALLENGE-02</span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  14.5°C breach (&gt;8.0°C limit) recorded for 15 mins. Automated payment release strictly blocked.
                </p>
                <div className="flex items-center gap-1 mt-2 text-[10px] font-semibold text-rose-400">
                  <span>View temperature telemetry</span>
                  <ArrowRight className="h-3 w-3" />
                </div>
              </div>

              {/* Alert 2 */}
              <div
                onClick={() => onNavigateTab('evidence')}
                className="p-3 rounded-xl bg-amber-950/30 border border-amber-500/40 cursor-pointer hover:border-amber-400 transition"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-amber-300">Evidence SHA-256 Mismatch</span>
                  <span className="text-[10px] font-mono text-amber-400">CHALLENGE-03</span>
                </div>
                <p className="text-xs text-slate-300 mt-1">
                  Telemetry CSV digest differs from uploaded blockchain record. Tamper case opened.
                </p>
                <div className="flex items-center gap-1 mt-2 text-[10px] font-semibold text-amber-400">
                  <span>Inspect evidence vault</span>
                  <ArrowRight className="h-3 w-3" />
                </div>
              </div>
            </div>
          </div>

          {/* Quick Compliance Summary */}
          <div className="mt-4 pt-3 border-t border-[#1A263D] flex items-center justify-between text-xs">
            <span className="text-slate-400 font-mono">GATEWAY:</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <CheckCircle2 className="h-3.5 w-3.5" />
              PayPal Sandbox Automated
            </span>
          </div>
        </div>
      </div>

      {/* 3. RECENT CONSIGNMENTS & SETTLEMENT ACTIVITY */}
      <div className="panel-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              Active Shipments & Compliance Status
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Live temperature sensors, automated verification decisions, and escrow settlements.
            </p>
          </div>
          <button
            onClick={() => onNavigateTab('shipments')}
            className="flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium transition"
          >
            <span>View All Shipments</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-[#1E293B] text-slate-400 text-[11px] font-mono uppercase tracking-wider">
                <th className="pb-3 font-medium">Tracking Ref</th>
                <th className="pb-3 font-medium">Medicine & Cargo</th>
                <th className="pb-3 font-medium">Route Corridor</th>
                <th className="pb-3 font-medium">Current Temp</th>
                <th className="pb-3 font-medium">Verification</th>
                <th className="pb-3 font-medium">Payment State</th>
                <th className="pb-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1A253A]">
              {activeShipments.map((s) => (
                <tr
                  key={s.tracking_number}
                  className="hover:bg-[#121A2D] transition group cursor-pointer"
                  onClick={() => {
                    onSelectShipment(s);
                    onNavigateTab('tracking');
                  }}
                >
                  <td className="py-3 font-mono font-medium text-cyan-400 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-cyan-400"></span>
                    {s.tracking_number}
                  </td>
                  <td className="py-3 font-medium text-slate-200">
                    <div>{s.medicine_name}</div>
                    <div className="text-[10px] text-slate-500 font-mono">{s.batch_number}</div>
                  </td>
                  <td className="py-3 text-slate-300">
                    <div className="truncate max-w-[200px]">
                      {s.origin_city} → {s.destination_city}
                    </div>
                    <div className="text-[10px] text-slate-500">{s.carrier_name}</div>
                  </td>
                  <td className="py-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium ${
                        s.temp_status === 'SAFE'
                          ? 'bg-emerald-950/60 text-emerald-300 border border-emerald-500/30'
                          : s.temp_status === 'WARNING'
                          ? 'bg-amber-950/60 text-amber-300 border border-amber-500/30'
                          : 'bg-rose-950/60 text-rose-300 border border-rose-500/30'
                      }`}
                    >
                      <Thermometer className="h-3 w-3" />
                      {s.current_temp}°C
                    </span>
                  </td>
                  <td className="py-3">
                    <span
                      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold ${
                        s.status === 'VERIFIED'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : s.status === 'FAILED'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
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
                  <td className="py-3 font-mono text-slate-200">
                    <div className="flex items-center gap-1">
                      <CreditCard className="h-3.5 w-3.5 text-slate-400" />
                      <span>
                        ${s.payment_amount.toLocaleString()} {s.currency}
                      </span>
                    </div>
                    <div
                      className={`text-[10px] font-medium ${
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
                  <td className="py-3 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectShipment(s);
                        onNavigateTab('shipments');
                      }}
                      className="px-2.5 py-1 rounded-lg border border-[#233554] bg-[#141E33] text-slate-300 hover:text-cyan-300 hover:border-cyan-500/50 text-xs transition"
                    >
                      Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
