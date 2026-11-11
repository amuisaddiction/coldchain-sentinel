'use client';

import React, { useState } from 'react';
import {
  Award,
  Truck,
  Plane,
  ShieldCheck,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  ChevronRight,
  BarChart3,
  Calendar,
  CheckCircle2,
  XCircle,
  FileText,
} from 'lucide-react';
import { DEMO_CARRIERS } from '../lib/mockData';

export function CarriersView() {
  const [carriers] = useState(DEMO_CARRIERS);
  const [selectedCarrier, setSelectedCarrier] = useState(DEMO_CARRIERS[0]);

  const getGradeBadge = (grade: string) => {
    if (grade.startsWith('A')) {
      return (
        <span className="px-2.5 py-1 rounded-md text-xs font-black bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 font-mono">
          {grade}
        </span>
      );
    }
    if (grade.startsWith('B')) {
      return (
        <span className="px-2.5 py-1 rounded-md text-xs font-black bg-blue-500/20 text-blue-400 border border-blue-500/30 font-mono">
          {grade}
        </span>
      );
    }
    return (
      <span className="px-2.5 py-1 rounded-md text-xs font-black bg-rose-500/20 text-rose-400 border border-rose-500/30 font-mono">
        {grade}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-canvas-700/60 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Carrier Intelligence & Cold Chain Compliance Benchmarks
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Live Rating Matrix
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Real-time telemetry and forensic audits automatically calculate carrier SLA reliability scores. High-performing carriers earn priority consignment allocation and immediate payment clearance.
            </p>
          </div>
        </div>
      </div>

      {/* Carrier Leaderboard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {carriers.map((c) => {
          const isSelected = c.name === selectedCarrier.name;
          const isFailing = c.grade.startsWith('F');

          return (
            <div
              key={c.name}
              onClick={() => setSelectedCarrier(c)}
              className={`p-5 rounded-xl border cursor-pointer transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-cyan-brand bg-gradient-to-b from-canvas-900 to-canvas-850 shadow-glow-cyan'
                  : 'border-canvas-800 bg-canvas-900/80 hover:border-canvas-700'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="p-2 rounded-lg bg-canvas-800 text-cyan-brand border border-canvas-700">
                    {c.fleet_type.includes('Air') ? (
                      <Plane className="w-4 h-4" />
                    ) : (
                      <Truck className="w-4 h-4" />
                    )}
                  </div>
                  {getGradeBadge(c.grade)}
                </div>

                <h3 className="text-sm font-bold text-white mt-3">{c.name}</h3>
                <span className="text-[11px] text-canvas-400 block mt-0.5">{c.fleet_type}</span>

                {/* Compliance Bar */}
                <div className="mt-4">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-canvas-400 text-[11px]">Compliance Rate</span>
                    <span className="font-mono font-bold text-white">{c.compliance_score}%</span>
                  </div>
                  <div className="w-full h-1.5 rounded-full bg-canvas-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        isFailing ? 'bg-rose-500' : 'bg-gradient-to-r from-cyan-brand to-emerald-400'
                      }`}
                      style={{ width: `${c.compliance_score}%` }}
                    />
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-2 mt-4 pt-3 border-t border-canvas-800/80 text-xs">
                  <div>
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Shipments</span>
                    <span className="font-mono font-bold text-white">{c.total_shipments}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Avg Temp Var</span>
                    <span className="font-mono font-bold text-canvas-200">±{c.avg_temp_variance}°C</span>
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-3 border-t border-canvas-850 flex items-center justify-between text-[11px]">
                <span className={`${c.incidents === 0 ? 'text-emerald-400' : 'text-rose-400'} font-semibold`}>
                  {c.incidents === 0 ? 'Zero Breaches' : `${c.incidents} Incidents Logged`}
                </span>
                <span className="text-cyan-brand flex items-center gap-0.5 font-medium">
                  Details <ChevronRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Detailed Carrier Intelligence Dossier */}
      <div className="p-6 rounded-xl border border-canvas-700/70 bg-canvas-900 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-canvas-800">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white">{selectedCarrier.name}</h3>
              {getGradeBadge(selectedCarrier.grade)}
            </div>
            <p className="text-xs text-canvas-400 mt-1">
              Active Partner SLA Agreement • Operating Sector: {selectedCarrier.fleet_type}
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Overall Rating</span>
              <span className="text-lg font-black text-cyan-brand font-mono">
                {selectedCarrier.compliance_score} / 100
              </span>
            </div>
          </div>
        </div>

        {/* Detailed KPI breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl bg-canvas-950 border border-canvas-800">
            <span className="text-xs text-canvas-400 block mb-1">Temperature Stability SLA</span>
            <div className="text-xl font-bold font-mono text-emerald-400">±{selectedCarrier.avg_temp_variance}°C</div>
            <p className="text-[11px] text-canvas-400 mt-1">Acceptable tolerance ceiling: ±1.0°C</p>
          </div>

          <div className="p-4 rounded-xl bg-canvas-950 border border-canvas-800">
            <span className="text-xs text-canvas-400 block mb-1">On-Time Delivery SLA</span>
            <div className="text-xl font-bold font-mono text-white">{selectedCarrier.success_rate}%</div>
            <p className="text-[11px] text-canvas-400 mt-1">Calculated over {selectedCarrier.total_shipments} flights/transits</p>
          </div>

          <div className="p-4 rounded-xl bg-canvas-950 border border-canvas-800">
            <span className="text-xs text-canvas-400 block mb-1">Escrow Payout Clearance</span>
            <div className="text-xl font-bold font-mono text-cyan-brand">
              {selectedCarrier.grade.startsWith('F') ? 'Suspended' : 'Instant (<15m)'}
            </div>
            <p className="text-[11px] text-canvas-400 mt-1">Automated PayPal capture enabled</p>
          </div>
        </div>

        {/* Audit Remarks */}
        <div className="p-4 rounded-xl bg-canvas-950/60 border border-canvas-800 text-xs text-canvas-300 leading-relaxed">
          <h4 className="font-bold text-white mb-1.5 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-cyan-brand" />
            Carrier Quality Assurance Evaluation Note
          </h4>
          {selectedCarrier.grade.startsWith('A') ? (
            <p>
              Swiss WorldCargo and Tier-1 partners consistently exhibit exceptional thermal containment performance in long-haul pharmaceutical routes. Active dry-ice pod telemetry confirms strict adherence to WHO GDP protocols. Recommended for critical vaccine batches.
            </p>
          ) : (
            <p className="text-rose-300">
              WARNING: Alitalia Cargo currently operates under active Quality Hold due to recurring apron thermal excursions during Rome Fiumicino transfers. Standard SLA penalties are applied and payments are held in smart escrow.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
