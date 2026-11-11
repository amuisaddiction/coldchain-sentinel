'use client';

import React, { useState } from 'react';
import {
  AlertOctagon,
  AlertTriangle,
  ShieldAlert,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ArrowRight,
  FileText,
  User,
  DollarSign,
  Download,
  Share2,
  ChevronRight,
  X,
  Thermometer,
} from 'lucide-react';
import { DEMO_INVESTIGATIONS, DEMO_SHIPMENTS } from '../lib/mockData';

export function InvestigationsView() {
  const [investigations, setInvestigations] = useState(DEMO_INVESTIGATIONS);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(DEMO_INVESTIGATIONS[0].id);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  const currentCase = investigations.find((c) => c.id === selectedCaseId) || investigations[0];
  const relatedShipment = DEMO_SHIPMENTS.find((s) => s.tracking_number === currentCase.shipment_tracking);

  const filteredCases = investigations.filter((item) => {
    const matchesSeverity = filterSeverity === 'ALL' || item.priority === filterSeverity;
    const matchesSearch =
      item.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.shipment_tracking.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.assigned_to.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  const handleResolveCase = (caseId: string) => {
    setInvestigations((prev) =>
      prev.map((c) => (c.id === caseId ? { ...c, status: 'RESOLVED' } : c))
    );
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
            HIGH
          </span>
        );
      case 'MEDIUM':
      default:
        return (
          <span className="px-2.5 py-0.5 rounded text-[11px] font-bold bg-blue-500/20 text-blue-400 border border-blue-500/30">
            MEDIUM
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-canvas-700/60 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-rose-950/20 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400">
            <AlertOctagon className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Quality Assurance & Forensic Investigations
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
                {investigations.filter((c) => c.status !== 'RESOLVED').length} Active Cases
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Automated anomaly triggers flag thermal breaches, cryptographic hash mismatches, and custody gaps. QA officers conduct forensic audits and hold or release escrow settlements accordingly.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => alert('Forensic incident audit report generated (PDF).')}
            className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-canvas-800 hover:bg-canvas-700 text-canvas-200 text-xs font-semibold border border-canvas-700"
          >
            <Download className="w-4 h-4 text-cyan-brand" />
            Export Audit Log
          </button>
        </div>
      </div>

      {/* Main Grid: Cases List (40%) + Detailed Case Dossier (60%) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Cases List */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-3.5 rounded-xl border border-canvas-700/60 bg-canvas-900 flex items-center justify-between gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-canvas-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search incident ID, carrier, title..."
                className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-canvas-950 border border-canvas-800 text-xs text-white placeholder-canvas-400 focus:outline-none focus:border-cyan-brand"
              />
            </div>
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-canvas-950 border border-canvas-800 text-xs text-canvas-300"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
            </select>
          </div>

          <div className="space-y-3">
            {filteredCases.map((item) => {
              const isSelected = item.id === currentCase.id;
              const isResolved = item.status === 'RESOLVED';

              return (
                <div
                  key={item.id}
                  onClick={() => setSelectedCaseId(item.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-cyan-brand bg-gradient-to-r from-canvas-900 to-canvas-850 shadow-glow-cyan'
                      : 'border-canvas-800 bg-canvas-900/80 hover:border-canvas-700'
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-xs font-mono font-bold text-cyan-brand">{item.id}</span>
                    <div className="flex items-center gap-2">
                      {getPriorityBadge(item.priority)}
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          isResolved
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-canvas-800 text-canvas-300'
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>
                  </div>

                  <h3 className="text-sm font-semibold text-white mt-2 line-clamp-1">
                    {item.title}
                  </h3>

                  <div className="flex items-center justify-between text-xs text-canvas-400 mt-3 pt-2 border-t border-canvas-800">
                    <span className="font-mono text-canvas-300">{item.shipment_tracking}</span>
                    <span className="flex items-center gap-1 text-[11px]">
                      <Clock className="w-3 h-3" />
                      {item.opened_at.split(' ')[0]}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Detailed Case Dossier */}
        <div className="lg:col-span-7">
          <div className="p-6 rounded-xl border border-canvas-700/70 bg-canvas-900 space-y-6">
            {/* Dossier Header */}
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-canvas-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-bold text-cyan-brand">
                    {currentCase.id}
                  </span>
                  <span className="text-canvas-500">•</span>
                  <span className="text-xs text-canvas-400 uppercase tracking-wider font-semibold">
                    Category: {currentCase.category.replace('_', ' ')}
                  </span>
                </div>
                <h2 className="text-lg font-bold text-white mt-1">
                  {currentCase.title}
                </h2>
                <span className="text-xs text-canvas-400 mt-1 block">
                  Opened {currentCase.opened_at} by Automated Compliance Daemon
                </span>
              </div>

              <div className="flex items-center gap-2">
                {getPriorityBadge(currentCase.priority)}
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-canvas-800 text-white border border-canvas-700">
                  {currentCase.status}
                </span>
              </div>
            </div>

            {/* Affected Product & Consignment Strip */}
            {relatedShipment && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 rounded-lg bg-canvas-950/70 border border-canvas-800 text-xs">
                <div>
                  <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Pharmaceutical</span>
                  <span className="font-bold text-white truncate block">{relatedShipment.medicine_name}</span>
                </div>
                <div>
                  <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Batch Number</span>
                  <span className="font-mono text-cyan-brand font-semibold block">{relatedShipment.batch_number}</span>
                </div>
                <div>
                  <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Carrier</span>
                  <span className="text-canvas-200 block">{relatedShipment.carrier_name}</span>
                </div>
                <div>
                  <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Escrow Hold</span>
                  <span className="font-mono font-bold text-rose-400 block">${relatedShipment.payment_amount.toLocaleString()}</span>
                </div>
              </div>
            )}

            {/* Forensic Findings */}
            <div>
              <h4 className="text-xs font-bold text-canvas-300 uppercase tracking-wider mb-2">
                Forensic Investigation Findings
              </h4>
              <div className="p-4 rounded-xl bg-canvas-950 border border-canvas-800 text-xs text-canvas-200 leading-relaxed space-y-2">
                <p>{currentCase.findings}</p>
                <div className="pt-2 border-t border-canvas-850 flex items-center gap-2 text-cyan-brand font-mono text-[11px]">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Audit trail cryptographically signed by Sentinel Guardian v2.4
                </div>
              </div>
            </div>

            {/* Assigned Investigator */}
            <div className="flex items-center justify-between p-3.5 rounded-lg bg-canvas-950/50 border border-canvas-800 text-xs">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-canvas-800 text-cyan-brand">
                  <User className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Lead Investigator</span>
                  <span className="font-semibold text-white">{currentCase.assigned_to}</span>
                </div>
              </div>
              <span className="text-xs text-canvas-400 font-mono">ID: QA-AUDITOR-881</span>
            </div>

            {/* Corrective Action Buttons */}
            <div className="pt-4 border-t border-canvas-800 flex flex-wrap items-center justify-between gap-3">
              <button
                onClick={() => alert(`Escalating incident ${currentCase.id} to Chief Medical Safety Officer.`)}
                className="px-4 py-2 rounded-lg bg-canvas-800 hover:bg-canvas-700 text-canvas-200 text-xs font-semibold border border-canvas-700"
              >
                Escalate to CMO
              </button>

              <div className="flex items-center gap-3">
                {currentCase.status === 'RESOLVED' ? (
                  <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5 font-mono">
                    <CheckCircle2 className="w-4 h-4" />
                    Case Fully Resolved & Archived
                  </span>
                ) : (
                  <button
                    onClick={() => handleResolveCase(currentCase.id)}
                    className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-canvas-950 text-xs font-bold transition-all shadow-lg flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    Sign Off & Mark Case Resolved
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
