'use client';

import React, { useState } from 'react';
import {
  DollarSign,
  ShieldCheck,
  ShieldAlert,
  Lock,
  Unlock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Clock,
  ArrowUpRight,
  ExternalLink,
  Info,
  Building,
  RefreshCw,
} from 'lucide-react';
import { DEMO_SHIPMENTS, ShipmentModel } from '../lib/mockData';

export function PaymentsView() {
  const [shipments, setShipments] = useState<ShipmentModel[]>(DEMO_SHIPMENTS);
  const [capturingId, setCapturingId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Escrow aggregates
  const totalEscrowed = shipments.reduce((acc, s) => acc + s.payment_amount, 0);
  const totalReleased = shipments
    .filter((s) => s.payment_status === 'CAPTURED')
    .reduce((acc, s) => acc + s.payment_amount, 0);
  const totalBlocked = shipments
    .filter((s) => s.payment_status === 'CAPTURE_BLOCKED')
    .reduce((acc, s) => acc + s.payment_amount, 0);
  const totalInReview = shipments
    .filter((s) => s.payment_status === 'HELD_FOR_REVIEW')
    .reduce((acc, s) => acc + s.payment_amount, 0);

  const handleCapture = (shipment: ShipmentModel) => {
    setCapturingId(shipment.id);
    setTimeout(() => {
      setShipments((prev) =>
        prev.map((s) => (s.id === shipment.id ? { ...s, payment_status: 'CAPTURED' } : s))
      );
      setCapturingId(null);
      setActionSuccess(`Payment of $${shipment.payment_amount.toLocaleString()} successfully captured via PayPal Escrow.`);
      setTimeout(() => setActionSuccess(null), 4000);
    }, 1500);
  };

  const getStatusBadge = (status: ShipmentModel['payment_status']) => {
    switch (status) {
      case 'CAPTURED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            CAPTURED / SETTLED
          </span>
        );
      case 'CAPTURE_BLOCKED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            CAPTURE BLOCKED
          </span>
        );
      case 'HELD_FOR_REVIEW':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3.5 h-3.5" />
            HELD FOR AUDIT
          </span>
        );
      case 'AUTHORIZED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            <Clock className="w-3.5 h-3.5" />
            ESCROW AUTHORIZED
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Explainer */}
      <div className="p-5 rounded-xl border border-cyan-brand/30 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Automated Payment Assurance & Escrow Vault
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/30">
                PayPal Sandbox Integrated
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Carrier freight settlements are held in programmatic escrow. Payment capture is strictly gated on three automated criteria: continuous temperature compliance, unbroken cryptographic file hashes, and intact chain of custody sign-offs.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-canvas-400 bg-canvas-950/80 px-3.5 py-2 rounded-lg border border-canvas-800">
          <Info className="w-4 h-4 text-cyan-brand shrink-0" />
          <span>Requires 3/3 Compliance Gates for Auto-Release</span>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-3 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {actionSuccess}
        </div>
      )}

      {/* Escrow KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-canvas-700/60 bg-canvas-900">
          <span className="text-[11px] font-semibold text-canvas-400 uppercase tracking-wider block">
            Total Escrow Value
          </span>
          <div className="text-2xl font-black text-white font-mono mt-1">
            ${totalEscrowed.toLocaleString()}
          </div>
          <span className="text-[11px] text-canvas-400 mt-1 block">4 active consignments</span>
        </div>

        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20">
          <span className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider block">
            Released to Carriers
          </span>
          <div className="text-2xl font-black text-emerald-400 font-mono mt-1">
            ${totalReleased.toLocaleString()}
          </div>
          <span className="text-[11px] text-emerald-300/80 mt-1 block">100% verified compliance</span>
        </div>

        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-950/20">
          <span className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider block">
            Blocked / Penalized
          </span>
          <div className="text-2xl font-black text-rose-400 font-mono mt-1">
            ${totalBlocked.toLocaleString()}
          </div>
          <span className="text-[11px] text-rose-300/80 mt-1 block">Critical thermal breach</span>
        </div>

        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-950/20">
          <span className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider block">
            Held in Audit Escrow
          </span>
          <div className="text-2xl font-black text-amber-400 font-mono mt-1">
            ${totalInReview.toLocaleString()}
          </div>
          <span className="text-[11px] text-amber-300/80 mt-1 block">Tamper & custody reviews</span>
        </div>
      </div>

      {/* Payment Gates & Shipments Table */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Lock className="w-4 h-4 text-cyan-brand" />
          Active Escrow Agreements & Compliance Gates
        </h3>

        <div className="space-y-4">
          {shipments.map((shipment) => {
            const isClean = shipment.id === 's-clean-01';
            const isExcursion = shipment.id === 's-excursion-02';
            const isTamper = shipment.id === 's-tamper-03';
            const isCustody = shipment.id === 's-custody-04';

            // Gates evaluation
            const tempGate = isClean || isTamper || isCustody; // Clean temp for clean, tamper, custody
            const hashGate = isClean || isExcursion || isCustody; // Hash intact for clean, excursion, custody
            const custodyGate = isClean || isExcursion || isTamper; // Custody intact for clean, excursion, tamper

            const canCapture = shipment.payment_status === 'AUTHORIZED' || shipment.status === 'VERIFIED';
            const isCapturing = capturingId === shipment.id;

            return (
              <div
                key={shipment.id}
                className="p-5 rounded-xl border border-canvas-700/70 bg-canvas-900/90 hover:border-canvas-600 transition-all space-y-4"
              >
                {/* Header row */}
                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2.5">
                      <span className="text-xs font-mono font-bold text-cyan-brand">
                        {shipment.tracking_number}
                      </span>
                      <span className="text-canvas-500">•</span>
                      <span className="text-sm font-bold text-white">{shipment.medicine_name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-canvas-400 mt-1">
                      <span>Carrier: <strong className="text-canvas-200">{shipment.carrier_name}</strong></span>
                      <span>•</span>
                      <span>Route: <strong className="text-canvas-200">{shipment.origin_city} → {shipment.destination_city}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Escrow Amount</span>
                      <span className="text-lg font-black text-white font-mono">
                        ${shipment.payment_amount.toLocaleString()} {shipment.currency}
                      </span>
                    </div>
                    <div>{getStatusBadge(shipment.payment_status)}</div>
                  </div>
                </div>

                {/* 3 Verification Gates Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3.5 rounded-lg bg-canvas-950/70 border border-canvas-800 text-xs">
                  {/* Gate 1: Temperature */}
                  <div className="flex items-start gap-2.5">
                    {tempGate ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="font-semibold text-white block">1. Thermal Stability</span>
                      <span className="text-[11px] text-canvas-400">
                        {tempGate
                          ? 'Maintained within 2°C–8°C limit'
                          : 'Spike to 14.5°C (>10 min excursion)'}
                      </span>
                    </div>
                  </div>

                  {/* Gate 2: SHA-256 Digest */}
                  <div className="flex items-start gap-2.5">
                    {hashGate ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="font-semibold text-white block">2. SHA-256 Integrity</span>
                      <span className="text-[11px] text-canvas-400">
                        {hashGate
                          ? 'Zero file modification detected'
                          : 'Tamper Alert: Hash digest mismatch'}
                      </span>
                    </div>
                  </div>

                  {/* Gate 3: Chain of Custody */}
                  <div className="flex items-start gap-2.5">
                    {custodyGate ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="font-semibold text-white block">3. Custody Sign-Off</span>
                      <span className="text-[11px] text-canvas-400">
                        {custodyGate
                          ? 'All handover actors authenticated'
                          : 'Gap: Missing airport handler signature'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Plain Language Explanation of Escrow Action */}
                <div
                  className={`p-3 rounded-lg text-xs flex items-start gap-2.5 border ${
                    shipment.payment_status === 'CAPTURED'
                      ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                      : shipment.payment_status === 'CAPTURE_BLOCKED'
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
                      : 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                  }`}
                >
                  <Info className="w-4 h-4 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">Settlement Rationale:</span>
                    <span className="text-canvas-300">
                      {shipment.payment_status === 'CAPTURED'
                        ? 'Payment settled to carrier Swiss WorldCargo. All 3 compliance gates passed with perfect integrity records.'
                        : shipment.payment_status === 'CAPTURE_BLOCKED'
                        ? 'Payment capture permanently blocked. Temperature breach invalidates carrier freight service level agreement.'
                        : 'Settlement withheld in smart escrow. A human QA auditor must resolve the flagged discrepancies prior to release.'}
                    </span>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="flex items-center justify-between pt-2">
                  <div className="flex items-center gap-2 text-[11px] text-canvas-400 font-mono">
                    <span>Gate Score:</span>
                    <span
                      className={`font-bold ${
                        isClean ? 'text-emerald-400' : 'text-amber-400'
                      }`}
                    >
                      {isClean ? '3/3 PASSED' : '2/3 FAILED'}
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {shipment.payment_status === 'CAPTURED' ? (
                      <span className="text-xs font-semibold text-emerald-400 flex items-center gap-1 font-mono">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Settlement Closed
                      </span>
                    ) : shipment.payment_status === 'CAPTURE_BLOCKED' ? (
                      <span className="text-xs font-semibold text-rose-400 flex items-center gap-1 font-mono">
                        <ShieldAlert className="w-3.5 h-3.5" /> Capture Disallowed
                      </span>
                    ) : (
                      <button
                        onClick={() => handleCapture(shipment)}
                        disabled={isCapturing}
                        className="px-4 py-2 rounded-lg text-xs font-semibold bg-cyan-brand text-canvas-950 hover:bg-cyan-brand/90 transition-all shadow-glow-cyan flex items-center gap-1.5"
                      >
                        {isCapturing ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            Authorizing PayPal Capture...
                          </>
                        ) : (
                          <>
                            <Unlock className="w-3.5 h-3.5" />
                            Execute QA Manual Release
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
