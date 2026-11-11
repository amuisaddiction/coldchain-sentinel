'use client';

import React, { useState } from 'react';
import {
  FileCheck,
  FileCode,
  FileText,
  AlertTriangle,
  ShieldCheck,
  ShieldAlert,
  Copy,
  Check,
  UploadCloud,
  Search,
  Filter,
  ExternalLink,
  Info,
  Lock,
} from 'lucide-react';
import { DEMO_EVIDENCE, DEMO_SHIPMENTS } from '../lib/mockData';

export function EvidenceView() {
  const [evidenceList, setEvidenceList] = useState(DEMO_EVIDENCE);
  const [selectedShipment, setSelectedShipment] = useState<string>('ALL');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const [verifiedMap, setVerifiedMap] = useState<Record<string, boolean>>({});
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSimulateVerify = (id: string) => {
    setVerifyingId(id);
    setTimeout(() => {
      setVerifyingId(null);
      setVerifiedMap((prev) => ({ ...prev, [id]: true }));
    }, 1200);
  };

  const filteredEvidence = evidenceList.filter((item) => {
    const matchesShipment = selectedShipment === 'ALL' || item.shipment_tracking === selectedShipment;
    const matchesQuery =
      item.file_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.recorded_sha256.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.uploaded_by.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.shipment_tracking.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesShipment && matchesQuery;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner / Explainer */}
      <div className="p-5 rounded-xl border border-cyan-brand/30 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                Cryptographic Evidence & SHA-256 Assurance
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Tamper-Evident Ledger
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Every temperature logger CSV, NIST calibration certificate, and custody handover manifest is cryptographically hashed with SHA-256 upon ingestion. Automated verification guarantees proof of zero alteration before payment escrow release.
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3 w-full md:w-auto">
          <button
            onClick={() => setShowUploadModal(true)}
            className="flex-1 md:flex-initial flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-cyan-brand text-canvas-950 font-semibold text-xs hover:bg-cyan-brand/90 transition-all shadow-glow-cyan"
          >
            <UploadCloud className="w-4 h-4" />
            Upload New Evidence
          </button>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-xl border border-canvas-700/60 bg-canvas-900/80 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-canvas-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search hash, filename, carrier..."
            className="w-full pl-9 pr-3 py-2 rounded-lg bg-canvas-950 border border-canvas-700/80 text-xs text-white placeholder-canvas-400 focus:outline-none focus:border-cyan-brand"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs text-canvas-400 flex items-center gap-1 shrink-0">
            <Filter className="w-3.5 h-3.5" /> Shipment:
          </span>
          <select
            value={selectedShipment}
            onChange={(e) => setSelectedShipment(e.target.value)}
            className="px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-700/80 text-xs text-canvas-200 focus:outline-none focus:border-cyan-brand"
          >
            <option value="ALL">All Active Shipments (4)</option>
            {DEMO_SHIPMENTS.map((s) => (
              <option key={s.id} value={s.tracking_number}>
                {s.tracking_number} ({s.medicine_name.split(' ')[0]})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Evidence Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredEvidence.map((item) => {
          const isTampered = item.integrity_status === 'HASH_MISMATCH';
          const isVerified = verifiedMap[item.id] || item.integrity_status === 'VERIFIED';
          const isVerifying = verifyingId === item.id;

          return (
            <div
              key={item.id}
              className={`p-5 rounded-xl border transition-all duration-200 flex flex-col justify-between ${
                isTampered
                  ? 'border-rose-500/50 bg-gradient-to-b from-rose-950/20 to-canvas-900/90 shadow-lg shadow-rose-950/30'
                  : 'border-canvas-700/70 bg-gradient-to-b from-canvas-900 to-canvas-950/90 hover:border-canvas-600'
              }`}
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2.5 rounded-lg border ${
                        item.file_type === 'LOGGER_CSV'
                          ? 'bg-blue-500/10 border-blue-500/30 text-blue-400'
                          : 'bg-purple-500/10 border-purple-500/30 text-purple-400'
                      }`}
                    >
                      {item.file_type === 'LOGGER_CSV' ? (
                        <FileCode className="w-5 h-5" />
                      ) : (
                        <FileText className="w-5 h-5" />
                      )}
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-white tracking-wide truncate max-w-xs sm:max-w-sm">
                        {item.file_name}
                      </h3>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[11px] text-canvas-400 font-mono">{item.file_size}</span>
                        <span className="text-canvas-500">•</span>
                        <span className="text-[11px] font-semibold text-cyan-brand font-mono">
                          {item.shipment_tracking}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Integrity Badge */}
                  {isTampered ? (
                    <span className="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
                      <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                      HASH MISMATCH
                    </span>
                  ) : (
                    <span className="shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      INTEGRITY INTACT
                    </span>
                  )}
                </div>

                {/* Plain Language Status Explanation Banner */}
                <div
                  className={`mt-4 p-3 rounded-lg border text-xs flex items-start gap-2.5 ${
                    isTampered
                      ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
                      : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                  }`}
                >
                  {isTampered ? (
                    <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                  ) : (
                    <FileCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                  )}
                  <div>
                    <span className="font-semibold block">
                      {isTampered
                        ? 'CRITICAL TAMPER WARNING:'
                        : 'Verified Assurance:'}
                    </span>
                    <span className="text-canvas-300">
                      {isTampered
                        ? 'Computed file hash does not match original manifest digest. Telemetry numbers were altered post-capture. Payment capture blocked.'
                        : 'Verified — file has not changed since recorded hash. Cryptographically identical to source logger.'}
                    </span>
                  </div>
                </div>

                {/* SHA-256 Digest Box */}
                <div className="mt-4 p-3 rounded-lg bg-canvas-950/80 border border-canvas-800">
                  <div className="flex items-center justify-between text-[11px] text-canvas-400 mb-1.5">
                    <span className="font-semibold uppercase tracking-wider flex items-center gap-1">
                      <Lock className="w-3 h-3 text-cyan-brand" />
                      Recorded SHA-256 Digest
                    </span>
                    <button
                      onClick={() => copyToClipboard(item.recorded_sha256, item.id)}
                      className="flex items-center gap-1 text-canvas-300 hover:text-white transition-colors"
                    >
                      {copiedId === item.id ? (
                        <>
                          <Check className="w-3 h-3 text-emerald-400" />
                          <span className="text-emerald-400 font-sans">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3" />
                          <span>Copy Hash</span>
                        </>
                      )}
                    </button>
                  </div>
                  <div className="font-mono text-xs text-canvas-200 break-all select-all bg-canvas-900/60 p-2 rounded border border-canvas-800/80">
                    {item.recorded_sha256}
                  </div>
                </div>

                {/* Metadata Details */}
                <div className="grid grid-cols-2 gap-2 mt-4 text-xs text-canvas-300">
                  <div className="p-2 rounded bg-canvas-950/50 border border-canvas-800/60">
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Uploaded By</span>
                    <span className="font-medium text-white truncate block">{item.uploaded_by}</span>
                  </div>
                  <div className="p-2 rounded bg-canvas-950/50 border border-canvas-800/60">
                    <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Timestamp</span>
                    <span className="font-medium text-white block">{item.uploaded_at}</span>
                  </div>
                </div>
              </div>

              {/* Bottom Actions */}
              <div className="mt-5 pt-4 border-t border-canvas-800 flex items-center justify-between gap-3">
                <span className="text-[11px] text-canvas-400 flex items-center gap-1">
                  <Info className="w-3.5 h-3.5 text-cyan-brand" />
                  Supabase Private Bucket Storage
                </span>

                <button
                  onClick={() => handleSimulateVerify(item.id)}
                  disabled={isVerifying}
                  className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                    isTampered
                      ? 'bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30'
                      : 'bg-canvas-800 hover:bg-canvas-700 text-canvas-200 hover:text-white border border-canvas-700'
                  }`}
                >
                  {isVerifying ? (
                    <>
                      <div className="w-3 h-3 border-2 border-cyan-brand border-t-transparent rounded-full animate-spin" />
                      Computing SHA-256...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-3.5 h-3.5 text-cyan-brand" />
                      Re-Verify Integrity
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload Evidence Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="w-full max-w-lg p-6 rounded-2xl bg-canvas-900 border border-canvas-700 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-canvas-800 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-cyan-brand" />
                Upload New Evidence File
              </h3>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-canvas-400 hover:text-white text-lg font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-canvas-300 leading-relaxed">
              Files are streamed directly to secure Supabase storage. A cryptographic SHA-256 hash is computed in real time before persistence to establish the immutable root of custody.
            </p>

            <div className="border-2 border-dashed border-canvas-700 hover:border-cyan-brand rounded-xl p-8 text-center cursor-pointer transition-colors bg-canvas-950/60">
              <UploadCloud className="w-10 h-10 text-cyan-brand mx-auto mb-2 animate-bounce" />
              <p className="text-sm font-semibold text-white">Click or drag loggers, certs, or photos</p>
              <p className="text-xs text-canvas-400 mt-1">Accepts .CSV, .PDF, .PNG (Max 25MB)</p>
            </div>

            <div className="space-y-3 pt-2">
              <div>
                <label className="text-xs text-canvas-300 font-semibold mb-1 block">Associated Shipment</label>
                <select className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-700 text-xs text-white">
                  {DEMO_SHIPMENTS.map((s) => (
                    <option key={s.id} value={s.tracking_number}>
                      {s.tracking_number} — {s.medicine_name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-canvas-300 font-semibold mb-1 block">Evidence Category</label>
                <select className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-700 text-xs text-white">
                  <option value="LOGGER_CSV">Temperature Logger CSV Dump</option>
                  <option value="CALIBRATION_CERT">NIST Traceable Calibration Certificate</option>
                  <option value="WAYBILL">Air Waybill / Customs Clearance Manifest</option>
                  <option value="PHOTO_PROOF">Tarmac Packaging Inspection Photo</option>
                </select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-4 border-t border-canvas-800">
              <button
                onClick={() => setShowUploadModal(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-canvas-300 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowUploadModal(false);
                  alert('Evidence uploaded successfully. SHA-256 digest registered.');
                }}
                className="px-4 py-2 rounded-lg text-xs font-semibold bg-cyan-brand text-canvas-950 hover:bg-cyan-brand/90 shadow-glow-cyan"
              >
                Calculate Digest & Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
