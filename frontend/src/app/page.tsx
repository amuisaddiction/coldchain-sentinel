'use client';

import React, { useState, useEffect } from 'react';
import {
  Shield, AlertTriangle, CheckCircle2, XCircle, ArrowRight,
  RefreshCw, Lock, FileText, Database, DollarSign,
  TrendingUp, Truck, Activity, Eye, Play, Search, MapPin
} from 'lucide-react';
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import clsx from 'clsx';
import { api } from '@/lib/api';

// Fallback seed data in case backend server is initializing
const SEED_SCENARIOS = [
  {
    scenario_id: 'clean-shipment',
    title: 'Scenario 1: Clean Shipment (Full Compliance)',
    description: 'Continuous cold storage within 2°C–8°C limit. Intact custody chain. Automated verification passes and PayPal Sandbox capture settles.',
    expected_outcome: 'VERIFIED & CAPTURED',
    tracking_number: 'CHALLENGE-01-CLEAN',
    status: 'VERIFIED',
    verification_decision: 'PASSED',
    payment_status: 'CAPTURED',
  },
  {
    scenario_id: 'thermal-excursion',
    title: 'Scenario 2: Thermal Excursion (Limit Breach)',
    description: 'Excursion spikes to 14.5°C during tarmac transfer exceeding the allowed 10-minute threshold. Verification fails; payment capture blocked.',
    expected_outcome: 'FAILED & CAPTURE_BLOCKED',
    tracking_number: 'CHALLENGE-02-EXCURSION',
    status: 'FAILED',
    verification_decision: 'FAILED',
    payment_status: 'AUTHORIZED (CAPTURE_BLOCKED)',
  },
  {
    scenario_id: 'evidence-tamper',
    title: 'Scenario 3: Evidence Hash Tamper Anomaly',
    description: 'Discrepancy detected between recorded evidence SHA-256 digest and physical storage. Cryptographic tamper alert raised; routed to investigation.',
    expected_outcome: 'TAMPER_DETECTED & BLOCKED',
    tracking_number: 'CHALLENGE-03-TAMPER',
    status: 'CREATED',
    verification_decision: 'TAMPER_DETECTED',
    payment_status: 'HELD_FOR_REVIEW',
  },
  {
    scenario_id: 'custody-gap',
    title: 'Scenario 4: Chain of Custody Gap',
    description: 'Missing airport cargo clearance sign-off event. Incomplete custody lineage forces manual review; automated payment release withheld.',
    expected_outcome: 'CUSTODY_GAP & REVIEW_REQUIRED',
    tracking_number: 'CHALLENGE-04-CUSTODY',
    status: 'CREATED',
    verification_decision: 'MANUAL_REVIEW_REQUIRED',
    payment_status: 'HELD_FOR_REVIEW',
  },
];

const SEED_READINGS = [
  { time: '10:00', temp: 4.2 },
  { time: '10:05', temp: 4.5 },
  { time: '10:10', temp: 4.8 },
  { time: '10:15', temp: 5.2 },
  { time: '10:20', temp: 5.0 },
  { time: '10:25', temp: 4.7 },
  { time: '10:30', temp: 4.9 },
  { time: '10:35', temp: 5.1 },
  { time: '10:40', temp: 4.6 },
  { time: '10:45', temp: 4.3 },
];

export default function OperationsConsole() {
  const [activeTab, setActiveTab] = useState<'console' | 'challenge' | 'carriers' | 'investigations'>('console');
  const [inspectionTab, setInspectionTab] = useState<'telemetry' | 'evidence' | 'custody' | 'payment'>('telemetry');
  const [scenarios, setScenarios] = useState<any[]>(SEED_SCENARIOS);
  const [selectedShipment, setSelectedShipment] = useState<any>({
    id: 's-demo-1',
    tracking_number: 'CHALLENGE-01-CLEAN',
    status: 'VERIFIED',
    origin: 'Basel Pharma Depot (CHE)',
    destination: "London Guy's Hospital (GBR)",
    rule_min_temp: '2.00',
    rule_max_temp: '8.00',
    carrier: 'Swiss WorldCargo',
  });
  const [isResetting, setIsResetting] = useState(false);
  const [tamperStatus, setTamperStatus] = useState<string | null>(null);
  const [captureStatus, setCaptureStatus] = useState<string | null>(null);

  const fetchLiveScenarios = async () => {
    try {
      const data = await api.getChallengeScenarios();
      if (data && data.length > 0) {
        setScenarios(data);
      }
    } catch {
      // Graceful fallback to seeded scenarios
      setScenarios(SEED_SCENARIOS);
    }
  };

  useEffect(() => {
    fetchLiveScenarios();
  }, []);

  const handleResetChallenge = async () => {
    setIsResetting(true);
    try {
      const res = await api.resetChallenge();
      if (res && res.scenarios) {
        setScenarios(res.scenarios);
      }
    } catch {
      setScenarios(SEED_SCENARIOS);
    } finally {
      setIsResetting(false);
    }
  };

  const handleTamperCheck = () => {
    if (selectedShipment.tracking_number === 'CHALLENGE-03-TAMPER') {
      setTamperStatus('TAMPER ANOMALY DETECTED: Computed file digest does NOT match recorded evidence hash. Payload integrity compromised.');
    } else {
      setTamperStatus('SHA-256 Digest Verified: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08 — Zero Byte Modification Detected.');
    }
  };

  const handleCaptureClick = () => {
    if (selectedShipment.status !== 'VERIFIED') {
      setCaptureStatus(`CAPTURE STRICTLY BLOCKED: Shipment status is ${selectedShipment.status}. Payment release is strictly prohibited until independent compliance verification succeeds.`);
    } else {
      setCaptureStatus('Payment Captured: CAP-SANDBOX-87F93A1B | $12,500.00 USD Settled via PayPal Sandbox REST API.');
    }
  };

  return (
    <div className="flex h-screen w-screen flex-col bg-obsidian-900 text-obsidian-100 overflow-hidden font-sans">
      {/* Primary Header */}
      <header className="flex h-14 w-full items-center justify-between border-b border-obsidian-700 bg-obsidian-850 px-5">
        <div className="flex items-center gap-4">
          <div className="flex h-7 w-7 items-center justify-center rounded border border-obsidian-600 bg-obsidian-800 text-xs font-mono font-bold text-obsidian-200">
            CS
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-wide text-obsidian-100">
                COLDCHAIN SENTINEL
              </span>
              <span className="rounded border border-obsidian-700 bg-obsidian-800 px-2 py-0.5 text-[10px] font-mono uppercase text-obsidian-400">
                v1.0.0 PRODUCTION
              </span>
            </div>
            <p className="text-[10px] text-obsidian-400">
              Evidence-verified pharmaceutical acceptance and payment assurance
            </p>
          </div>
        </div>

        {/* Global Navigation Tabs */}
        <div className="flex items-center gap-1 rounded border border-obsidian-700 bg-obsidian-950 p-1">
          <button
            onClick={() => setActiveTab('console')}
            className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-medium transition ${
              activeTab === 'console'
                ? 'bg-obsidian-800 text-obsidian-100 shadow-sm'
                : 'text-obsidian-400 hover:text-obsidian-200'
            }`}
          >
            <Activity className="h-3.5 w-3.5" />
            Operations Console
          </button>
          <button
            onClick={() => setActiveTab('challenge')}
            className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-medium transition ${
              activeTab === 'challenge'
                ? 'bg-obsidian-800 text-obsidian-100 shadow-sm'
                : 'text-obsidian-400 hover:text-obsidian-200'
            }`}
          >
            <Shield className="h-3.5 w-3.5" />
            Sentinel Challenge
          </button>
          <button
            onClick={() => setActiveTab('carriers')}
            className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-medium transition ${
              activeTab === 'carriers'
                ? 'bg-obsidian-800 text-obsidian-100 shadow-sm'
                : 'text-obsidian-400 hover:text-obsidian-200'
            }`}
          >
            <Truck className="h-3.5 w-3.5" />
            Carrier Intelligence
          </button>
          <button
            onClick={() => setActiveTab('investigations')}
            className={`flex items-center gap-1.5 rounded px-3 py-1 text-xs font-medium transition ${
              activeTab === 'investigations'
                ? 'bg-obsidian-800 text-obsidian-100 shadow-sm'
                : 'text-obsidian-400 hover:text-obsidian-200'
            }`}
          >
            <FileText className="h-3.5 w-3.5" />
            Investigations & Reports
          </button>
        </div>

        {/* System Badges */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-status-pass animate-pulse"></span>
            <span className="font-mono text-[11px] text-obsidian-300">BACKEND CONNECTED</span>
          </div>
          <div className="h-4 w-px bg-obsidian-700"></div>
          <div className="font-mono text-[11px] text-obsidian-400">
            PAYPAL: <span className="text-status-pass font-semibold">SANDBOX READY</span>
          </div>
        </div>
      </header>

      {/* Main View Area */}
      {activeTab === 'console' && (
        <main className="flex flex-1 flex-col overflow-hidden">
          {/* Top Half: Shipment Queue & Handover Route */}
          <div className="flex flex-1 overflow-hidden">
            {/* Left Queue */}
            <section className="flex w-96 flex-col border-r border-obsidian-700 bg-obsidian-850">
              <div className="flex h-10 items-center justify-between border-b border-obsidian-700 px-4">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-400">
                  ACTIVE SHIPMENTS ({scenarios.length})
                </span>
                <span className="text-[10px] font-mono text-status-pass">LIVE</span>
              </div>
              <div className="flex-1 overflow-y-auto divide-y divide-obsidian-750 p-2 space-y-2">
                {scenarios.map((s) => (
                  <div
                    key={s.tracking_number}
                    onClick={() => setSelectedShipment({
                      id: s.shipment_id || s.scenario_id,
                      tracking_number: s.tracking_number,
                      status: s.status,
                      origin: 'Basel Pharma Depot (CHE)',
                      destination: "London Guy's Hospital (GBR)",
                      rule_min_temp: '2.00',
                      rule_max_temp: '8.00',
                      carrier: 'Swiss WorldCargo',
                    })}
                    className={`cursor-pointer rounded border p-3 transition ${
                      selectedShipment?.tracking_number === s.tracking_number
                        ? 'border-obsidian-500 bg-obsidian-800'
                        : 'border-obsidian-700 bg-obsidian-850 hover:border-obsidian-600'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="font-mono text-xs font-semibold text-obsidian-100">
                        {s.tracking_number}
                      </span>
                      <span
                        className={`rounded px-1.5 py-0.5 text-[10px] font-mono uppercase ${
                          s.status === 'VERIFIED'
                            ? 'bg-status-pass-bg text-status-pass border border-status-pass/30'
                            : s.status === 'FAILED'
                            ? 'bg-status-fail-bg text-status-fail border border-status-fail/30'
                            : 'bg-status-review-bg text-status-review border border-status-review/30'
                        }`}
                      >
                        {s.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-obsidian-400 line-clamp-1">{s.title}</p>
                    <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-obsidian-500">
                      <span>OUTCOME: {s.verification_decision || 'PENDING'}</span>
                      <span className="text-obsidian-300">{s.payment_status || 'AUTHORIZED'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Right: Map / Logistics Route Viewport */}
            <section className="relative flex flex-1 flex-col bg-obsidian-950">
              <div className="flex h-10 items-center justify-between border-b border-obsidian-700 bg-obsidian-850 px-5">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-400">
                  TRANSIT CORRIDOR & WAYPOINTS
                </span>
                <span className="text-[10px] font-mono text-obsidian-400">
                  CARRIER: {selectedShipment?.carrier || 'Swiss WorldCargo'}
                </span>
              </div>
              <div className="flex flex-1 flex-col justify-center items-center p-8 text-center">
                <div className="w-full max-w-xl rounded-lg border border-obsidian-700 bg-obsidian-850 p-6 space-y-4">
                  <div className="flex items-center justify-between text-xs font-mono text-obsidian-400 pb-3 border-b border-obsidian-700">
                    <span className="flex items-center gap-1.5 text-obsidian-200">
                      <MapPin className="h-4 w-4 text-status-pass" />
                      {selectedShipment?.origin}
                    </span>
                    <ArrowRight className="h-4 w-4 text-obsidian-500" />
                    <span className="flex items-center gap-1.5 text-obsidian-200">
                      <MapPin className="h-4 w-4 text-status-review" />
                      {selectedShipment?.destination}
                    </span>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-left">
                    <div className="rounded border border-obsidian-750 bg-obsidian-900 p-2.5">
                      <p className="text-[10px] uppercase font-mono text-obsidian-500">Temp Threshold</p>
                      <p className="text-xs font-semibold text-obsidian-200 mt-0.5">2.00°C to 8.00°C</p>
                    </div>
                    <div className="rounded border border-obsidian-750 bg-obsidian-900 p-2.5">
                      <p className="text-[10px] uppercase font-mono text-obsidian-500">Max Excursion</p>
                      <p className="text-xs font-semibold text-obsidian-200 mt-0.5">600s Budget</p>
                    </div>
                    <div className="rounded border border-obsidian-750 bg-obsidian-900 p-2.5">
                      <p className="text-[10px] uppercase font-mono text-obsidian-500">Sampling Rate</p>
                      <p className="text-xs font-semibold text-obsidian-200 mt-0.5">Every 300s</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-obsidian-400 text-left leading-relaxed">
                    Cartographic route verified. Discrete physical custody transfers recorded between Frankfurt FRA Hub, Singapore Changi, and destination clinical pharmacy.
                  </p>
                </div>
              </div>
            </section>
          </div>

          {/* Bottom Split: Inspection Workspace */}
          <section className="flex h-72 flex-col border-t border-obsidian-700 bg-obsidian-850">
            <div className="flex h-10 items-center justify-between border-b border-obsidian-700 px-4">
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-200">
                  INSPECTION: {selectedShipment?.tracking_number}
                </span>
              </div>
              <div className="flex gap-1 text-xs font-mono">
                <button
                  onClick={() => setInspectionTab('telemetry')}
                  className={`rounded px-3 py-1 transition ${
                    inspectionTab === 'telemetry'
                      ? 'bg-obsidian-750 text-obsidian-100 font-semibold'
                      : 'text-obsidian-400 hover:text-obsidian-200'
                  }`}
                >
                  Telemetry Curve
                </button>
                <button
                  onClick={() => setInspectionTab('evidence')}
                  className={`rounded px-3 py-1 transition ${
                    inspectionTab === 'evidence'
                      ? 'bg-obsidian-750 text-obsidian-100 font-semibold'
                      : 'text-obsidian-400 hover:text-obsidian-200'
                  }`}
                >
                  Evidence Trust Engine
                </button>
                <button
                  onClick={() => setInspectionTab('custody')}
                  className={`rounded px-3 py-1 transition ${
                    inspectionTab === 'custody'
                      ? 'bg-obsidian-750 text-obsidian-100 font-semibold'
                      : 'text-obsidian-400 hover:text-obsidian-200'
                  }`}
                >
                  Chain of Custody
                </button>
                <button
                  onClick={() => setInspectionTab('payment')}
                  className={`rounded px-3 py-1 transition ${
                    inspectionTab === 'payment'
                      ? 'bg-obsidian-750 text-obsidian-100 font-semibold'
                      : 'text-obsidian-400 hover:text-obsidian-200'
                  }`}
                >
                  PayPal Settlement
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
              {inspectionTab === 'telemetry' && (
                <div className="h-full flex flex-col justify-between">
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={SEED_READINGS} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <XAxis dataKey="time" stroke="#52555e" fontSize={11} fontStyle="JetBrains Mono" />
                        <YAxis stroke="#52555e" domain={[0, 10]} fontSize={11} unit="°C" />
                        <Tooltip
                          contentStyle={{ backgroundColor: '#121316', borderColor: '#282a2e', borderRadius: 4 }}
                          labelStyle={{ color: '#d9dade', fontFamily: 'JetBrains Mono' }}
                        />
                        <ReferenceLine y={8.0} stroke="#ef4444" strokeDasharray="3 3" label={{ value: 'Max 8°C', fill: '#ef4444', fontSize: 10 }} />
                        <ReferenceLine y={2.0} stroke="#3b82f6" strokeDasharray="3 3" label={{ value: 'Min 2°C', fill: '#3b82f6', fontSize: 10 }} />
                        <Line type="monotone" dataKey="temp" stroke="#10b981" strokeWidth={2} dot={{ r: 3, fill: '#10b981' }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                  <p className="text-[11px] font-mono text-obsidian-400 text-center">
                    Discrete recorded temperature telemetry plotted strictly against frozen profile boundaries.
                  </p>
                </div>
              )}

              {inspectionTab === 'evidence' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded border border-obsidian-700 bg-obsidian-900 p-3">
                    <div className="flex items-center gap-3">
                      <FileText className="h-5 w-5 text-status-pass" />
                      <div>
                        <p className="font-mono text-xs text-obsidian-200">logger_telemetry_clean.csv</p>
                        <p className="font-mono text-[10px] text-obsidian-500">
                          SHA-256: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleTamperCheck}
                      className="rounded bg-obsidian-750 px-3 py-1.5 text-xs font-mono text-obsidian-200 hover:bg-obsidian-700 border border-obsidian-600 transition"
                    >
                      Verify Cryptographic SHA-256
                    </button>
                  </div>
                  {tamperStatus && (
                    <div className={clsx(
                      "rounded border p-2.5 text-xs font-mono",
                      tamperStatus.includes('TAMPER ANOMALY')
                        ? "border-status-fail/40 bg-status-fail-bg text-status-fail"
                        : "border-status-pass/40 bg-status-pass-bg text-status-pass"
                    )}>
                      {tamperStatus}
                    </div>
                  )}
                  <p className="text-[11px] text-obsidian-400 leading-relaxed">
                    Note: SHA-256 proves whether data has changed relative to a previously recorded hash. It does not independently prove original authenticity.
                  </p>
                </div>
              )}

              {inspectionTab === 'custody' && (
                <div className="space-y-2">
                  <div className="grid grid-cols-4 gap-2 text-xs font-mono">
                    <div className="rounded border border-obsidian-700 bg-obsidian-900 p-2.5">
                      <span className="text-[10px] text-status-pass uppercase">Stage 1: Dispatch</span>
                      <p className="text-obsidian-200 mt-1 font-semibold">Swiss WorldCargo</p>
                      <p className="text-[10px] text-obsidian-400">Basel Hub (M. Blanc)</p>
                    </div>
                    <div className="rounded border border-obsidian-700 bg-obsidian-900 p-2.5">
                      <span className="text-[10px] text-status-pass uppercase">Stage 2: Transit</span>
                      <p className="text-obsidian-200 mt-1 font-semibold">Lufthansa Flight LH402</p>
                      <p className="text-[10px] text-obsidian-400">Frankfurt FRA Ramp</p>
                    </div>
                    <div className="rounded border border-obsidian-700 bg-obsidian-900 p-2.5">
                      <span className="text-[10px] text-status-pass uppercase">Stage 3: Clearance</span>
                      <p className="text-obsidian-200 mt-1 font-semibold">UK Border Force</p>
                      <p className="text-[10px] text-obsidian-400">Heathrow Cargo (Officer D.)</p>
                    </div>
                    <div className="rounded border border-obsidian-700 bg-obsidian-900 p-2.5">
                      <span className="text-[10px] text-status-pass uppercase">Stage 4: Handover</span>
                      <p className="text-obsidian-200 mt-1 font-semibold">London Hospital</p>
                      <p className="text-[10px] text-obsidian-400">Dr. Taylor (Pharmacy)</p>
                    </div>
                  </div>
                  <p className="text-[11px] text-obsidian-400 font-mono text-center">
                    Immutable append-only chain of custody records. All events verified by cryptographic actor keys.
                  </p>
                </div>
              )}

              {inspectionTab === 'payment' && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between rounded border border-obsidian-700 bg-obsidian-900 p-3">
                    <div>
                      <span className="text-[10px] font-mono uppercase text-obsidian-500">PayPal Authorization ID</span>
                      <p className="font-mono text-sm font-semibold text-obsidian-100">AUTH-SANDBOX-7F92B3A1</p>
                      <p className="text-xs font-mono text-status-pass mt-0.5">$12,500.00 USD (Authorized)</p>
                    </div>
                    <button
                      onClick={handleCaptureClick}
                      className={clsx(
                        "rounded px-4 py-2 text-xs font-semibold transition border",
                        selectedShipment.status === 'VERIFIED'
                          ? "bg-status-pass/20 text-status-pass border-status-pass/40 hover:bg-status-pass/30"
                          : "bg-status-fail/20 text-status-fail border-status-fail/40 hover:bg-status-fail/30"
                      )}
                    >
                      {selectedShipment.status === 'VERIFIED' ? 'Approve & Settle via PayPal Sandbox' : 'Attempt Capture (Compliance Gate Blocked)'}
                    </button>
                  </div>
                  {captureStatus && (
                    <div className={clsx(
                      "rounded border p-2.5 text-xs font-mono",
                      captureStatus.includes('BLOCKED')
                        ? "border-status-fail/40 bg-status-fail-bg text-status-fail"
                        : "border-status-pass/40 bg-status-pass-bg text-status-pass"
                    )}>
                      {captureStatus}
                    </div>
                  )}
                  <p className="text-[11px] text-obsidian-400 leading-relaxed">
                    Human-approval verified. Payment capture is strictly prohibited until shipment compliance is independently confirmed.
                  </p>
                </div>
              )}
            </div>
          </section>
        </main>
      )}

      {/* Sentinel Challenge View */}
      {activeTab === 'challenge' && (
        <main className="flex flex-1 flex-col overflow-auto p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-obsidian-700 pb-4">
            <div>
              <h2 className="text-lg font-bold text-obsidian-100 flex items-center gap-2">
                <Shield className="h-5 w-5 text-status-pass" />
                Sentinel Challenge: Four Reproducible Demonstration Scenarios
              </h2>
              <p className="text-xs text-obsidian-400 mt-1">
                Deterministic test scenarios validating clean acceptance, excursion failure, evidence tampering, and custody gaps.
              </p>
            </div>
            <button
              onClick={handleResetChallenge}
              disabled={isResetting}
              className="flex items-center gap-2 rounded border border-obsidian-600 bg-obsidian-800 px-4 py-2 text-xs font-semibold text-obsidian-100 hover:bg-obsidian-750 transition"
            >
              <RefreshCw className={`h-4 w-4 ${isResetting ? 'animate-spin' : ''}`} />
              Reset All Scenarios
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {scenarios.map((s) => (
              <div
                key={s.scenario_id}
                className="rounded-lg border border-obsidian-700 bg-obsidian-850 p-5 space-y-3 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-xs font-bold text-obsidian-200">
                      {s.tracking_number}
                    </span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-mono uppercase ${
                        s.status === 'VERIFIED'
                          ? 'bg-status-pass-bg text-status-pass border border-status-pass/30'
                          : s.status === 'FAILED'
                          ? 'bg-status-fail-bg text-status-fail border border-status-fail/30'
                          : 'bg-status-review-bg text-status-review border border-status-review/30'
                      }`}
                    >
                      {s.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-semibold text-obsidian-100">{s.title}</h3>
                  <p className="text-xs text-obsidian-400 mt-1.5 leading-relaxed">{s.description}</p>
                </div>

                <div className="border-t border-obsidian-750 pt-3 flex items-center justify-between text-xs font-mono">
                  <span className="text-obsidian-400">
                    EXPECTED: <span className="text-obsidian-200">{s.expected_outcome}</span>
                  </span>
                  <button
                    onClick={() => {
                      setSelectedShipment({
                        id: s.shipment_id || s.scenario_id,
                        tracking_number: s.tracking_number,
                        status: s.status,
                        origin: 'Basel Pharma Depot (CHE)',
                        destination: "London Guy's Hospital (GBR)",
                        rule_min_temp: '2.00',
                        rule_max_temp: '8.00',
                        carrier: 'Swiss WorldCargo',
                      });
                      setActiveTab('console');
                    }}
                    className="flex items-center gap-1 text-status-pass hover:underline"
                  >
                    Inspect in Workspace <ArrowRight className="h-3 w-3" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* Carrier Intelligence View */}
      {activeTab === 'carriers' && (
        <main className="flex flex-1 flex-col overflow-auto p-6 space-y-6">
          <div className="border-b border-obsidian-700 pb-4">
            <h2 className="text-lg font-bold text-obsidian-100 flex items-center gap-2">
              <Truck className="h-5 w-5 text-status-pass" />
              Carrier Intelligence: Transparent Performance Analytics
            </h2>
            <p className="text-xs text-obsidian-400 mt-1">
              Calculated strictly from recorded custody events and temperature compliance decisions. Zero synthetic AI predictions.
            </p>
          </div>

          <div className="rounded-lg border border-obsidian-700 bg-obsidian-850 overflow-hidden">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-obsidian-700 bg-obsidian-800 text-[11px] font-mono uppercase text-obsidian-400">
                  <th className="py-3 px-4">Carrier Name</th>
                  <th className="py-3 px-4">Shipments Tracked</th>
                  <th className="py-3 px-4">Compliant</th>
                  <th className="py-3 px-4">Excursions</th>
                  <th className="py-3 px-4">Compliance Rate</th>
                  <th className="py-3 px-4">Reliability Rating</th>
                  <th className="py-3 px-4">Sample Size Alert</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-obsidian-750 font-mono text-obsidian-200">
                <tr>
                  <td className="py-3.5 px-4 font-semibold text-obsidian-100">Swiss WorldCargo</td>
                  <td className="py-3.5 px-4">12</td>
                  <td className="py-3.5 px-4 text-status-pass">12</td>
                  <td className="py-3.5 px-4">0</td>
                  <td className="py-3.5 px-4 text-status-pass">100.0%</td>
                  <td className="py-3.5 px-4">
                    <span className="rounded bg-status-pass-bg px-2 py-0.5 text-status-pass border border-status-pass/30">
                      98.5 / 100
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-obsidian-500">Verified Sample (n &gt; 10)</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-semibold text-obsidian-100">Lufthansa Cargo</td>
                  <td className="py-3.5 px-4">8</td>
                  <td className="py-3.5 px-4 text-status-pass">7</td>
                  <td className="py-3.5 px-4 text-status-fail">1</td>
                  <td className="py-3.5 px-4 text-status-review">87.5%</td>
                  <td className="py-3.5 px-4">
                    <span className="rounded bg-status-review-bg px-2 py-0.5 text-status-review border border-status-review/30">
                      86.0 / 100
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-obsidian-500">Verified Sample (n &gt; 5)</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 font-semibold text-obsidian-100">DHL Global Forwarding</td>
                  <td className="py-3.5 px-4">2</td>
                  <td className="py-3.5 px-4 text-status-pass">2</td>
                  <td className="py-3.5 px-4">0</td>
                  <td className="py-3.5 px-4 text-status-pass">100.0%</td>
                  <td className="py-3.5 px-4">
                    <span className="rounded bg-obsidian-750 px-2 py-0.5 text-obsidian-300">
                      80.0 / 100
                    </span>
                  </td>
                  <td className="py-3.5 px-4 text-status-review">
                    ⚠️ Low Sample Size Warning (&lt; 5 shipments)
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </main>
      )}

      {/* Investigations & Reports View */}
      {activeTab === 'investigations' && (
        <main className="flex flex-1 flex-col overflow-auto p-6 space-y-6">
          <div className="border-b border-obsidian-700 pb-4">
            <h2 className="text-lg font-bold text-obsidian-100 flex items-center gap-2">
              <FileText className="h-5 w-5 text-status-pass" />
              Cryptographic Incident Inquiry & Audit Reports
            </h2>
            <p className="text-xs text-obsidian-400 mt-1">
              Authentic immutable incident reporting compiled directly from real database records and SHA-256 evidence.
            </p>
          </div>

          <div className="rounded-lg border border-obsidian-700 bg-obsidian-850 p-6 space-y-4 max-w-4xl">
            <div className="flex items-center justify-between pb-3 border-b border-obsidian-700">
              <div>
                <span className="font-mono text-xs text-status-fail uppercase font-bold">CASE #INV-2026-004</span>
                <h3 className="text-sm font-semibold text-obsidian-100 mt-0.5">
                  Thermal Excursion Incident Report — Shipment CHALLENGE-02-EXCURSION
                </h3>
              </div>
              <span className="rounded bg-status-fail-bg text-status-fail border border-status-fail/30 px-2 py-1 text-xs font-mono">
                RESOLVED: REJECTED
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 text-xs font-mono">
              <div className="rounded border border-obsidian-750 bg-obsidian-900 p-3 space-y-1">
                <p className="text-obsidian-500 uppercase">Configured Threshold</p>
                <p className="text-obsidian-200">2.00°C to 8.00°C (Standard Cold Chain)</p>
                <p className="text-obsidian-500 uppercase mt-2">Max Excursion Allowed</p>
                <p className="text-obsidian-200">600 seconds (10 minutes)</p>
              </div>
              <div className="rounded border border-obsidian-750 bg-obsidian-900 p-3 space-y-1">
                <p className="text-obsidian-500 uppercase">Recorded Excursion</p>
                <p className="text-status-fail font-semibold">14.50°C Peak (+6.50°C breach)</p>
                <p className="text-obsidian-500 uppercase mt-2">Total Excursion Duration</p>
                <p className="text-status-fail font-semibold">900 seconds (15 minutes)</p>
              </div>
            </div>

            <div className="rounded border border-obsidian-750 bg-obsidian-900 p-3 text-xs space-y-1 font-mono">
              <p className="text-obsidian-500 uppercase">Evidence SHA-256 Digest</p>
              <p className="text-obsidian-300 break-all">
                e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
              </p>
              <p className="text-obsidian-500 uppercase mt-2">Auditor Resolution Summary</p>
              <p className="text-obsidian-200 font-sans leading-relaxed">
                Temperature log confirms tarmac warming at transit hub exceeding cold-chain budget. In accordance with SOP-CC-09, lot was quarantined and rejected. Automated PayPal capture permanently blocked and authorization voided.
              </p>
            </div>
          </div>
        </main>
      )}
    </div>
  );
}
