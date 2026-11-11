'use client';

import React, { useState } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  CheckCircle2,
  Clock,
  Printer,
  FileCheck,
  Shield,
  Share2,
} from 'lucide-react';

export function ReportsView() {
  const [downloading, setDownloading] = useState<string | null>(null);

  const reports = [
    {
      id: 'REP-2026-Q4-01',
      title: 'GDP Pharma Cold Chain Compliance Audit (Monthly Summary)',
      date: '2026-11-10',
      period: 'October 1 - November 10, 2026',
      size: '3.8 MB',
      type: 'PDF / Audit Ready',
      status: 'VERIFIED',
      description: 'Comprehensive Good Distribution Practice (GDP) audit covering temperature excursions, carrier metrics, and cryptographic custody verification.',
    },
    {
      id: 'REP-2026-Q4-02',
      title: 'Carrier SLA & Thermal Integrity Performance Benchmarking',
      date: '2026-11-08',
      period: 'Q3 - Q4 2026',
      size: '2.1 MB',
      type: 'PDF / Financial & Ops',
      status: 'GENERATED',
      description: 'Carrier comparison rankings, breach incidence rates, on-time arrivals, and escrow release compliance percentages.',
    },
    {
      id: 'REP-2026-Q4-03',
      title: 'Forensic Cryptographic Hash Ledger Export (SHA-256 Manifests)',
      date: '2026-11-05',
      period: 'All Active Batches',
      size: '840 KB',
      type: 'JSON / Raw Ledger',
      status: 'IMMUTABLE',
      description: 'Cryptographic proof log linking logger digests to cloud storage objects, designed for regulatory inspection and legal dispute protection.',
    },
  ];

  const handleDownload = (id: string) => {
    setDownloading(id);
    setTimeout(() => {
      setDownloading(null);
      alert(`Report ${id} successfully downloaded to your workstation.`);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-canvas-700/60 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Regulatory Audit & Compliance Reports
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                FDA 21 CFR Part 11 Compliant
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Export validated audit documentation, GDP temperature compliance packages, and carrier settlement balance sheets with single-click cryptographic proof.
            </p>
          </div>
        </div>

        <button
          onClick={() => alert('Compiling on-demand audit manifest for all 4 demo scenarios...')}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-cyan-brand text-canvas-950 font-bold text-xs hover:bg-cyan-brand/90 shadow-glow-cyan"
        >
          <FileCheck className="w-4 h-4" />
          Generate Instant Audit Package
        </button>
      </div>

      {/* Reports List */}
      <div className="space-y-4">
        {reports.map((report) => (
          <div
            key={report.id}
            className="p-5 rounded-xl border border-canvas-750 bg-canvas-900/90 hover:border-canvas-600 transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4"
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-2.5">
                <span className="text-xs font-mono font-bold text-cyan-brand">{report.id}</span>
                <span className="text-canvas-500">•</span>
                <span className="text-xs font-semibold text-emerald-400 font-mono">{report.type}</span>
              </div>
              <h3 className="text-sm font-bold text-white tracking-wide">{report.title}</h3>
              <p className="text-xs text-canvas-300 max-w-3xl leading-relaxed">{report.description}</p>
              <div className="flex items-center gap-4 text-[11px] text-canvas-400 pt-1 font-mono">
                <span>Period: {report.period}</span>
                <span>•</span>
                <span>Size: {report.size}</span>
                <span>•</span>
                <span>Generated: {report.date}</span>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => handleDownload(report.id)}
                disabled={downloading === report.id}
                className="flex items-center gap-2 px-3.5 py-2 rounded-lg bg-canvas-800 hover:bg-canvas-700 text-canvas-200 hover:text-white text-xs font-semibold border border-canvas-700 transition-all"
              >
                <Download className={`w-4 h-4 text-cyan-brand ${downloading === report.id ? 'animate-bounce' : ''}`} />
                {downloading === report.id ? 'Exporting...' : 'Download Export'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
