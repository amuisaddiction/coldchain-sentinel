'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  ArrowRight,
  ExternalLink,
  Flame,
  FileCode,
  Link2Off,
  Play,
  Layers,
  Info,
} from 'lucide-react';
import { api } from '../lib/api';
import { DEMO_SHIPMENTS, ShipmentModel } from '../lib/mockData';

interface DemoCenterViewProps {
  onSelectShipment: (shipment: ShipmentModel) => void;
  onNavigateTab: (tabId: string) => void;
  onResetSuccess?: () => void;
}

export function DemoCenterView({
  onSelectShipment,
  onNavigateTab,
  onResetSuccess,
}: DemoCenterViewProps) {
  const [resetting, setResetting] = useState(false);
  const [resetFeedback, setResetFeedback] = useState<string | null>(null);

  const handleResetChallenge = async () => {
    setResetting(true);
    setResetFeedback(null);
    try {
      await api.resetChallenge();
      setResetFeedback('Challenge scenarios successfully reset to clean default states in PostgreSQL.');
      if (onResetSuccess) onResetSuccess();
    } catch (err: any) {
      console.warn('Backend reset call encountered error or offline mode, applying frontend state reset:', err);
      setResetFeedback('Local mock challenge state restored. Ready for demonstration.');
      if (onResetSuccess) onResetSuccess();
    } finally {
      setResetting(false);
      setTimeout(() => setResetFeedback(null), 4500);
    }
  };

  const scenarios = [
    {
      id: 'CHALLENGE-01-CLEAN',
      title: 'Scenario 1: Clean Shipment',
      subtitle: 'Pfizer Comirnaty Bivalent mRNA Vaccines',
      medicine: 'Pfizer Comirnaty (LOT-CH-9921)',
      route: 'Basel, Switzerland → London, UK',
      carrier: 'Swiss WorldCargo',
      tests: 'Strict 2°C–8°C thermal bounds throughout 8-hour flight and transit, unbroken SHA-256 evidence chain, full digital sign-offs.',
      expected: 'All 3 compliance gates PASS with zero deviations. Automated PayPal smart escrow capture release executes immediately.',
      badge: '100% COMPLIANT',
      badgeColor: 'emerald',
      icon: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
      shipment: DEMO_SHIPMENTS[0],
      targetTab: 'payments',
    },
    {
      id: 'CHALLENGE-02-EXCURSION',
      title: 'Scenario 2: Thermal Excursion Breach',
      subtitle: 'Humira (Adalimumab) Prefilled Syringes',
      medicine: 'Humira (LOT-DE-4412)',
      route: 'Munich, Germany → Rome, Italy',
      carrier: 'Alitalia Cargo',
      tests: 'Tarmac ramp exposure at Rome Fiumicino Airport exceeding 8°C ceiling for 15 consecutive minutes (14.5°C peak).',
      expected: 'Thermal compliance fails, critical breach alert generated, shipment automatically quarantined, payment capture permanently BLOCKED.',
      badge: 'BREACH DETECTED',
      badgeColor: 'rose',
      icon: <Flame className="w-5 h-5 text-rose-400" />,
      shipment: DEMO_SHIPMENTS[1],
      targetTab: 'telemetry',
    },
    {
      id: 'CHALLENGE-03-TAMPER',
      title: 'Scenario 3: Evidence File Tampering',
      subtitle: 'NovoRapid Insulin Multi-Dose Vials',
      medicine: 'NovoRapid (LOT-DK-7703)',
      route: 'Copenhagen, Denmark → Stockholm, Sweden',
      carrier: 'Nordic Express Cold',
      tests: 'Physical telemetry CSV payload computed SHA-256 hash does not match original digital manifest ledger digest.',
      expected: 'Forensic integrity alarm sounds, SHA-256 mismatch flagged, incident dossier opened, payment held in audit escrow.',
      badge: 'TAMPER DETECTED',
      badgeColor: 'amber',
      icon: <FileCode className="w-5 h-5 text-amber-400" />,
      shipment: DEMO_SHIPMENTS[2],
      targetTab: 'evidence',
    },
    {
      id: 'CHALLENGE-04-CUSTODY',
      title: 'Scenario 4: Broken Custody Lineage',
      subtitle: 'Keytruda (Pembrolizumab) Biologics',
      medicine: 'Keytruda (LOT-KR-1209)',
      route: 'Seoul, South Korea → Tokyo, Japan',
      carrier: 'Trans-Asia Cold Express',
      tests: 'Missing mandatory airport cargo handler digital signature during international air freight tarmac-to-warehouse handover.',
      expected: 'Incomplete custody chain detected, regulatory compliance hold enacted, automated payment release blocked until audited.',
      badge: 'CUSTODY GAP',
      badgeColor: 'amber',
      icon: <Link2Off className="w-5 h-5 text-amber-400" />,
      shipment: DEMO_SHIPMENTS[3],
      targetTab: 'timeline',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-cyan-brand/30 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Interactive Challenge & Hackathon Demo Center
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-brand/20 text-cyan-brand border border-cyan-brand/30 font-mono">
                4 Evaluated Scenarios
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Explore the four core pharmaceutical cold-chain test cases. Each scenario demonstrates automated compliance detection, cryptographic ledger validation, and conditional escrow settlement.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={handleResetChallenge}
            disabled={resetting}
            className="w-full md:w-auto flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-canvas-800 hover:bg-canvas-750 text-white font-semibold text-xs border border-canvas-700 transition-all shadow-md"
          >
            <RotateCcw className={`w-4 h-4 text-cyan-brand ${resetting ? 'animate-spin' : ''}`} />
            {resetting ? 'Resetting Database...' : 'Reset All Scenarios'}
          </button>
        </div>
      </div>

      {resetFeedback && (
        <div className="p-3.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {resetFeedback}
        </div>
      )}

      {/* 4 Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {scenarios.map((sc) => {
          const isEmerald = sc.badgeColor === 'emerald';
          const isRose = sc.badgeColor === 'rose';

          return (
            <div
              key={sc.id}
              className={`p-6 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                isEmerald
                  ? 'bg-gradient-to-b from-canvas-900 to-canvas-950 border-emerald-500/30 hover:border-emerald-500/60'
                  : isRose
                  ? 'bg-gradient-to-b from-canvas-900 to-canvas-950 border-rose-500/30 hover:border-rose-500/60'
                  : 'bg-gradient-to-b from-canvas-900 to-canvas-950 border-amber-500/30 hover:border-amber-500/60'
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-lg bg-canvas-800 border border-canvas-700">
                      {sc.icon}
                    </div>
                    <div>
                      <span className="text-[11px] font-mono font-bold text-cyan-brand block">
                        {sc.id}
                      </span>
                      <h3 className="text-base font-bold text-white tracking-wide">
                        {sc.title}
                      </h3>
                    </div>
                  </div>

                  <span
                    className={`px-2.5 py-1 rounded text-[11px] font-bold border font-mono ${
                      isEmerald
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                        : isRose
                        ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                        : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                    }`}
                  >
                    {sc.badge}
                  </span>
                </div>

                <div className="mt-3 text-xs text-canvas-300 font-medium">
                  {sc.subtitle}
                </div>

                {/* Route & Carrier Strip */}
                <div className="mt-3 p-3 rounded-lg bg-canvas-950/70 border border-canvas-800 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Route</span>
                    <span className="text-canvas-200 font-medium truncate block">{sc.route}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Carrier</span>
                    <span className="text-cyan-brand font-semibold truncate block">{sc.carrier}</span>
                  </div>
                </div>

                {/* What it tests */}
                <div className="mt-4 space-y-2 text-xs">
                  <div>
                    <span className="text-[11px] font-bold text-canvas-400 uppercase tracking-wider block">
                      Verification Test Case:
                    </span>
                    <p className="text-canvas-300 leading-relaxed mt-0.5">{sc.tests}</p>
                  </div>

                  <div>
                    <span className="text-[11px] font-bold text-canvas-400 uppercase tracking-wider block">
                      Expected System Outcome:
                    </span>
                    <p className="text-canvas-200 font-medium leading-relaxed mt-0.5">{sc.expected}</p>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="mt-6 pt-4 border-t border-canvas-800 flex items-center justify-between gap-3">
                <button
                  onClick={() => {
                    onSelectShipment(sc.shipment);
                    onNavigateTab('live-tracking');
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-canvas-800 hover:bg-canvas-700 text-canvas-200 text-xs font-semibold border border-canvas-700 transition-colors"
                >
                  <Play className="w-3.5 h-3.5 text-cyan-brand" />
                  Load into Map
                </button>

                <button
                  onClick={() => {
                    onSelectShipment(sc.shipment);
                    onNavigateTab(sc.targetTab);
                  }}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-cyan-brand text-canvas-950 text-xs font-bold hover:bg-cyan-brand/90 transition-all shadow-glow-cyan"
                >
                  Inspect Analysis
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
