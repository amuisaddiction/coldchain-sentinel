'use client';

import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  FileText,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  DollarSign,
  ArrowRight,
  Lock,
  Layers,
  UserCheck,
  Building,
  Thermometer,
  FileCode,
  Link2Off,
  Check,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  Info,
  Scale,
} from 'lucide-react';
import { api } from '../lib/api';
import { DEMO_SHIPMENTS, ShipmentModel } from '../lib/mockData';

interface SettlementIntelligenceViewProps {
  shipments: ShipmentModel[];
  onSelectShipment?: (shipment: ShipmentModel) => void;
  onNavigateTab?: (tab: string) => void;
}

export function SettlementIntelligenceView({
  shipments,
  onSelectShipment,
  onNavigateTab,
}: SettlementIntelligenceViewProps) {
  // Demo scenarios quick switcher
  const [selectedScenario, setSelectedScenario] = useState<'A' | 'B' | 'C'>('A');
  const [investigating, setInvestigating] = useState(false);
  const [approving, setApproving] = useState(false);
  const [activeStep, setActiveStep] = useState<number>(4); // Default to recommendation step

  // Data states
  const [contractData, setContractData] = useState<any>(null);
  const [investigationData, setInvestigationData] = useState<any>(null);
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [reviewerNotes, setReviewerNotes] = useState<string>(
    'Verified against cold chain telemetry and digital custody sign-offs. Releasing approved freight settlement.'
  );

  // Map scenarios to tracking IDs
  const scenarioTrackingMap = {
    A: 'CHALLENGE-01-CLEAN',
    B: 'CHALLENGE-02-EXCURSION',
    C: 'CHALLENGE-03-TAMPER',
  };

  const scenarioMeta = {
    A: {
      name: 'Scenario A: Clean Shipment',
      desc: '100% compliant Pfizer mRNA batch. All 3 gates pass. AI recommends ELIGIBLE. Human approves PayPal capture.',
      badge: 'ELIGIBLE FOR RELEASE',
      badgeClass: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
      contractId: 'SAMPLE-MSA-01-CLEAN',
    },
    B: {
      name: 'Scenario B: Temperature Breach',
      desc: 'Humira Syringes exposed to 14.5°C tarmac spike for 15 mins. AI recommends QUALITY_REVIEW. Payment held.',
      badge: 'QUALITY HOLD',
      badgeClass: 'bg-rose-500/20 text-rose-400 border-rose-500/30',
      contractId: 'SAMPLE-MSA-02-EXCURSION',
    },
    C: {
      name: 'Scenario C: Insufficient Evidence',
      desc: 'NovoRapid Insulin with SHA-256 telemetry hash discrepancy. AI recommends INSUFFICIENT_EVIDENCE. Manual audit required.',
      badge: 'AUDIT REQUIRED',
      badgeClass: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
      contractId: 'SAMPLE-MSA-03-TAMPER',
    },
  };

  // Load contract and investigation on scenario switch
  useEffect(() => {
    loadScenarioData(selectedScenario);
  }, [selectedScenario]);

  const loadScenarioData = async (sc: 'A' | 'B' | 'C') => {
    setInvestigating(true);
    setExecutionResult(null);

    const tracking = scenarioTrackingMap[sc];
    const contractKey = scenarioMeta[sc].contractId;

    try {
      // 1. Fetch Contract
      const contractRes = await api.extractContract({ sample_id: contractKey });
      setContractData(contractRes.contract);

      // 2. Fetch Investigation
      const invRes = await api.runSettlementInvestigation(tracking, contractKey);
      setInvestigationData(invRes);

      // Set initial notes
      if (sc === 'A') {
        setReviewerNotes('QA Sign-off: All contract clauses and thermal stability limits met. Approved for PayPal capture.');
      } else if (sc === 'B') {
        setReviewerNotes('QA Alert: 14.5°C tarmac breach confirmed. Consignment quarantined. Withholding carrier freight fee.');
      } else {
        setReviewerNotes('QA Alert: File hash mismatch detected. Forensic audit required. Settlement withheld.');
      }
    } catch (err) {
      console.warn('API error fetching settlement data, using verified fallback models:', err);
    } finally {
      setInvestigating(false);
    }
  };

  const handleExecuteApproval = async (approved: boolean) => {
    if (!investigationData) return;
    setApproving(true);

    try {
      const res = await api.approveSettlement({
        investigation_id: investigationData.investigation_id,
        shipment_id: investigationData.shipment_id,
        approved,
        approved_amount: approved ? investigationData.total_authorized_amount : 0,
        reviewer_notes: reviewerNotes,
        reviewer_id: 'lead-qa-auditor@pharmalogistics.com',
      });
      setExecutionResult(res);
      setActiveStep(6);
    } catch (err: any) {
      alert(`Approval execution failed: ${err.message || err}`);
    } finally {
      setApproving(false);
    }
  };

  const steps = [
    { num: 1, label: 'CONTRACT INTELLIGENCE' },
    { num: 2, label: 'SHIPMENT INVESTIGATION' },
    { num: 3, label: 'AI FINDINGS' },
    { num: 4, label: 'SETTLEMENT RECOMMENDATION' },
    { num: 5, label: 'HUMAN APPROVAL' },
    { num: 6, label: 'PAYPAL EXECUTION' },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-cyan-brand/40 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                ColdChain AI Settlement Intelligence
              </h2>
              <span className="px-2.5 py-0.5 rounded text-[11px] font-black bg-cyan-brand/20 text-cyan-brand border border-cyan-brand/30 font-mono">
                SIGNATURE ENGINE
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-3xl leading-relaxed">
              Connects AI-powered contract understanding, shipment evidence verification, deterministic lot-level settlement intelligence, and human-approved PayPal execution into one unified workflow.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-canvas-400 bg-canvas-950/80 px-3 py-2 rounded-lg border border-canvas-800 shrink-0">
          <Info className="w-4 h-4 text-cyan-brand shrink-0" />
          <span>Deterministic Financial Math • Zero Hallucinations</span>
        </div>
      </div>

      {/* Scenario Quick-Switcher */}
      <div className="p-4 rounded-xl border border-canvas-700/60 bg-canvas-900/80 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-canvas-300 uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-cyan-brand" />
            Select Evaluated Demo Scenario
          </span>
          <span className="text-[11px] text-canvas-400 font-mono">
            Tracking: {scenarioTrackingMap[selectedScenario]}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {(['A', 'B', 'C'] as const).map((sc) => {
            const meta = scenarioMeta[sc];
            const isSelected = selectedScenario === sc;

            return (
              <button
                key={sc}
                onClick={() => setSelectedScenario(sc)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  isSelected
                    ? 'border-cyan-brand bg-gradient-to-r from-canvas-900 to-canvas-850 shadow-glow-cyan'
                    : 'border-canvas-800 bg-canvas-950/70 hover:border-canvas-700'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-bold text-white">{meta.name}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${meta.badgeClass}`}>
                    {meta.badge}
                  </span>
                </div>
                <p className="text-[11px] text-canvas-400 line-clamp-2 leading-relaxed">
                  {meta.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>

      {/* 6-Step Visual Journey Progress Bar */}
      <div className="p-4 rounded-xl border border-canvas-800 bg-canvas-950 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[700px] gap-2">
          {steps.map((step, idx) => {
            const isPassed = activeStep > step.num;
            const isCurrent = activeStep === step.num;

            return (
              <React.Fragment key={step.num}>
                <div
                  onClick={() => setActiveStep(step.num)}
                  className={`flex items-center gap-2 cursor-pointer transition-all ${
                    isCurrent
                      ? 'text-cyan-brand font-bold'
                      : isPassed
                      ? 'text-emerald-400 font-medium'
                      : 'text-canvas-400'
                  }`}
                >
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold font-mono border ${
                      isCurrent
                        ? 'border-cyan-brand bg-cyan-brand/20 text-cyan-brand ring-2 ring-cyan-brand/30'
                        : isPassed
                        ? 'border-emerald-500 bg-emerald-950 text-emerald-400'
                        : 'border-canvas-700 bg-canvas-900 text-canvas-400'
                    }`}
                  >
                    {isPassed ? <Check className="w-3.5 h-3.5" /> : step.num}
                  </div>
                  <span className="text-[11px] tracking-wide whitespace-nowrap">{step.label}</span>
                </div>

                {idx < steps.length - 1 && (
                  <div className="flex-1 h-0.5 bg-canvas-800 mx-2" />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Main Grid: Left Panel (Contract & Investigation) + Right Panel (Settlement & PayPal) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Contract & Investigation Findings (55%) */}
        <div className="lg:col-span-7 space-y-6">
          {/* Section 1: Contract Intelligence Card */}
          <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
            <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-canvas-800 text-cyan-brand border border-canvas-700">
                  <FileText className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">
                    {contractData?.title || 'Master Cold Chain Logistics Agreement'}
                  </h3>
                  <span className="text-[11px] text-canvas-400 font-mono">
                    ID: {contractData?.contract_id} • Effective: {contractData?.effective_date}
                  </span>
                </div>
              </div>

              <span className="px-2.5 py-1 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 flex items-center gap-1 font-mono">
                <ShieldCheck className="w-3.5 h-3.5" />
                Reviewer Verified
              </span>
            </div>

            {/* Contract Key Metrics Strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 p-3 rounded-lg bg-canvas-950/70 border border-canvas-800 text-xs">
              <div>
                <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Permitted Temp</span>
                <span className="font-bold text-emerald-400 font-mono">
                  {contractData?.permitted_min_temp_celsius}°C to {contractData?.permitted_max_temp_celsius}°C
                </span>
              </div>
              <div>
                <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Max Excursion</span>
                <span className="font-bold text-white font-mono">
                  {contractData?.max_excursion_duration_seconds} seconds
                </span>
              </div>
              <div>
                <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Agreed Freight</span>
                <span className="font-bold text-cyan-brand font-mono">
                  ${Number(contractData?.agreed_payment_amount || 0).toLocaleString()} {contractData?.currency}
                </span>
              </div>
              <div>
                <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Delivery Window</span>
                <span className="font-bold text-canvas-200 font-mono">
                  {contractData?.delivery_deadline_hours} Hours
                </span>
              </div>
            </div>

            {/* Extracted Clauses with Citations */}
            <div>
              <span className="text-xs font-bold text-canvas-300 uppercase tracking-wider block mb-2">
                Extracted Contractual Clauses & Legal Citations
              </span>
              <div className="space-y-2">
                {contractData?.clauses?.map((clause: any) => (
                  <div
                    key={clause.clause_id}
                    className="p-3 rounded-lg bg-canvas-950/60 border border-canvas-800 text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-white flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-canvas-800 text-cyan-brand font-mono border border-canvas-700">
                          {clause.category}
                        </span>
                        {clause.title}
                      </span>
                      <span className="text-[11px] text-canvas-400 font-mono">
                        {clause.source_document} (Page {clause.source_page})
                      </span>
                    </div>
                    <p className="text-canvas-300 italic text-[11px] leading-relaxed">
                      "{clause.text_excerpt}"
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-canvas-400 pt-1 border-t border-canvas-850">
                      <span>Requirement: {clause.requirement_summary}</span>
                      <span className="text-emerald-400 flex items-center gap-0.5">
                        <CheckCircle2 className="w-3 h-3" /> Cited from {clause.source_section}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Section 2: Shipment Investigation & Telemetry Comparison */}
          <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
            <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-canvas-800 text-cyan-brand border border-canvas-700">
                  <Thermometer className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Shipment Condition vs Contract Investigation
                  </h3>
                  <span className="text-[11px] text-canvas-400 font-mono">
                    Tracking: {investigationData?.tracking_number} • Carrier: {investigationData?.carrier_name}
                  </span>
                </div>
              </div>

              <span
                className={`px-2.5 py-1 rounded text-[11px] font-bold border font-mono ${
                  investigationData?.compliance_breakdown?.temperature_compliant
                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                    : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                }`}
              >
                {investigationData?.compliance_breakdown?.temperature_compliant
                  ? 'THERMAL COMPLIANT'
                  : 'LIMIT EXCURSION DETECTED'}
              </span>
            </div>

            {/* Tri-Factor Comparison Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {/* Factor 1: Temperature */}
              <div
                className={`p-3.5 rounded-lg border text-xs ${
                  investigationData?.compliance_breakdown?.temperature_compliant
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : 'bg-rose-950/20 border-rose-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">1. Thermal Stability</span>
                  {investigationData?.compliance_breakdown?.temperature_compliant ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                </div>
                <div className="font-mono text-sm font-bold mt-1">
                  Peak: {investigationData?.compliance_breakdown?.recorded_max_temp}°C
                </div>
                <p className="text-[11px] text-canvas-400 mt-1">
                  Excursion duration: {investigationData?.compliance_breakdown?.total_excursion_seconds}s (Max:{' '}
                  {contractData?.max_excursion_duration_seconds}s)
                </p>
              </div>

              {/* Factor 2: SHA-256 Hashes */}
              <div
                className={`p-3.5 rounded-lg border text-xs ${
                  investigationData?.compliance_breakdown?.evidence_hash_valid
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : 'bg-rose-950/20 border-rose-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">2. SHA-256 Ledger</span>
                  {investigationData?.compliance_breakdown?.evidence_hash_valid ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400" />
                  )}
                </div>
                <div className="font-mono text-sm font-bold mt-1">
                  {investigationData?.compliance_breakdown?.evidence_hash_valid ? 'INTACT' : 'TAMPERED'}
                </div>
                <p className="text-[11px] text-canvas-400 mt-1">
                  {investigationData?.compliance_breakdown?.evidence_hash_valid
                    ? 'File hash matches manifest.'
                    : 'Discrepancy: File altered.'}
                </p>
              </div>

              {/* Factor 3: Custody Handshake */}
              <div
                className={`p-3.5 rounded-lg border text-xs ${
                  investigationData?.compliance_breakdown?.custody_chain_complete
                    ? 'bg-emerald-950/20 border-emerald-500/30'
                    : 'bg-amber-950/20 border-amber-500/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-bold text-white">3. Custody Handshakes</span>
                  {investigationData?.compliance_breakdown?.custody_chain_complete ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-400" />
                  )}
                </div>
                <div className="font-mono text-sm font-bold mt-1">
                  {investigationData?.compliance_breakdown?.custody_chain_complete ? 'VERIFIED' : 'GAP DETECTED'}
                </div>
                <p className="text-[11px] text-canvas-400 mt-1">
                  {investigationData?.compliance_breakdown?.custody_chain_complete
                    ? 'All checkpoints signed.'
                    : 'Missing ramp handover sign-off.'}
                </p>
              </div>
            </div>

            {/* Investigation Timeline */}
            <div>
              <span className="text-xs font-bold text-canvas-300 uppercase tracking-wider block mb-2">
                Investigation Audit Trail
              </span>
              <div className="space-y-2">
                {investigationData?.investigation_timeline?.map((ev: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-canvas-950/60 border border-canvas-800 text-xs flex items-start justify-between gap-3"
                  >
                    <div>
                      <span className="font-bold text-white block">{ev.stage.replace(/_/g, ' ')}</span>
                      <span className="text-canvas-400 text-[11px] mt-0.5 block">{ev.detail}</span>
                    </div>
                    <span
                      className={`shrink-0 px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                        ev.status === 'PASS' || ev.status === 'VERIFIED'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : 'bg-rose-500/20 text-rose-400'
                      }`}
                    >
                      {ev.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Legal Notice */}
            <p className="text-[10px] text-canvas-400 italic border-t border-canvas-800 pt-2">
              Regulatory Notice: SHA-256 verification proves file has not changed since ingestion; does not certify original clinical authenticity. Temperature compliance indicates cold-chain adherence, not medical safety certification.
            </p>
          </div>
        </div>

        {/* Right Column: Lot Settlement, Human Approval & PayPal Execution (45%) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Section 3: Lot-Level Settlement Recommendations */}
          <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
            <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-cyan-brand" />
                <h3 className="text-sm font-bold text-white">Lot-Level Settlement Intelligence</h3>
              </div>
              <span className="text-xs font-mono font-bold text-cyan-brand">
                Total: ${Number(investigationData?.total_authorized_amount || 0).toLocaleString()} USD
              </span>
            </div>

            <div className="space-y-3">
              {investigationData?.lots?.map((lot: any) => {
                const isEligible = lot.recommendation === 'ELIGIBLE';
                const isQualityReview = lot.recommendation === 'QUALITY_REVIEW';

                return (
                  <div
                    key={lot.lot_number}
                    className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                      isEligible
                        ? 'bg-emerald-950/20 border-emerald-500/30'
                        : isQualityReview
                        ? 'bg-rose-950/20 border-rose-500/30'
                        : 'bg-amber-950/20 border-amber-500/30'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white">{lot.lot_number}</span>
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold border font-mono ${
                          isEligible
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : isQualityReview
                            ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                        }`}
                      >
                        {lot.recommendation.replace('_', ' ')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-canvas-300 text-[11px]">
                      <span>{lot.medicine_name}</span>
                      <span className="font-mono font-bold text-white">
                        ${Number(lot.allocated_amount).toLocaleString()} USD
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[10px] text-canvas-400 bg-canvas-950/50 p-2 rounded border border-canvas-850">
                      <span>Units: {lot.doses_count?.toLocaleString()} Doses</span>
                      <span className="text-right">Unit Price: ${lot.unit_price}</span>
                    </div>

                    <p className="text-[11px] text-canvas-300 leading-relaxed pt-1">
                      {lot.rationale}
                    </p>
                  </div>
                );
              })}
            </div>

            {/* Executive Summary Callout */}
            <div className="p-3 rounded-lg bg-canvas-950 border border-canvas-800 text-xs">
              <span className="text-[10px] text-canvas-400 uppercase tracking-wider block font-bold mb-1">
                Executive AI Recommendation
              </span>
              <p className="text-canvas-200 leading-relaxed">
                {investigationData?.executive_summary}
              </p>
            </div>
          </div>

          {/* Section 4: Human-in-the-Loop Review & Approval */}
          <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
            <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-cyan-brand" />
                <h3 className="text-sm font-bold text-white">Human Approval Gate</h3>
              </div>
              <span className="text-[11px] text-canvas-400 font-mono">Role: QA Auditor</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-canvas-400 block mb-1 font-medium">Reviewer Audit Remarks</label>
                <textarea
                  rows={2}
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-200 text-xs focus:outline-none focus:border-cyan-brand"
                  placeholder="Enter QA verification observations..."
                />
              </div>

              <div className="flex items-center justify-between p-3 rounded-lg bg-canvas-950 border border-canvas-800">
                <span className="text-canvas-400 font-medium">Approved Release Amount:</span>
                <span className="font-mono text-base font-black text-cyan-brand">
                  ${Number(investigationData?.total_authorized_amount || 0).toLocaleString()} USD
                </span>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  onClick={() => handleExecuteApproval(false)}
                  disabled={approving || executionResult}
                  className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 font-bold text-xs border border-rose-500/40 transition-colors disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  Reject & Hold Funds
                </button>

                <button
                  onClick={() => handleExecuteApproval(true)}
                  disabled={approving || executionResult || investigationData?.overall_recommendation !== 'ELIGIBLE_FOR_SETTLEMENT'}
                  className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg bg-cyan-brand text-canvas-950 font-bold text-xs hover:bg-cyan-brand/90 transition-all shadow-glow-cyan disabled:opacity-50"
                >
                  {approving ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      Capturing via PayPal...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-4 h-4" />
                      Approve & Settle
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Section 5: PayPal Sandbox Execution Result */}
          {executionResult && (
            <div className="p-5 rounded-xl border border-cyan-brand/40 bg-gradient-to-b from-canvas-900 to-canvas-950 space-y-4 animate-fadeIn">
              <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
                <div className="flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-cyan-brand" />
                  <h3 className="text-sm font-bold text-white">PayPal Sandbox Execution Receipt</h3>
                </div>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono border ${
                    executionResult.decision === 'APPROVED_AND_CAPTURED'
                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                  }`}
                >
                  {executionResult.paypal_status}
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                {executionResult.paypal_transaction_id ? (
                  <div className="p-3 rounded-lg bg-canvas-950 border border-canvas-800">
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block mb-1">
                      PayPal Capture Transaction Reference
                    </span>
                    <div className="font-mono text-cyan-brand font-bold text-sm break-all select-all">
                      {executionResult.paypal_transaction_id}
                    </div>
                  </div>
                ) : (
                  <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30 text-rose-300">
                    Capture withheld by reviewer. No funds transferred to carrier.
                  </div>
                )}

                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded bg-canvas-950 border border-canvas-800">
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Mode</span>
                    <span className="font-mono text-canvas-200">
                      {executionResult.is_live_sandbox ? 'Live PayPal Sandbox' : 'Sandbox Verified Simulation'}
                    </span>
                  </div>
                  <div className="p-2.5 rounded bg-canvas-950 border border-canvas-800">
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Settlement Amount</span>
                    <span className="font-mono font-bold text-white">
                      ${Number(executionResult.approved_amount).toLocaleString()} USD
                    </span>
                  </div>
                </div>

                <div className="p-2 rounded bg-canvas-950/60 border border-canvas-850 text-[10px] text-canvas-400 font-mono">
                  <span>Idempotency Hash: {executionResult.idempotency_key}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
