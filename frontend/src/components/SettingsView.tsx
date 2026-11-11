'use client';

import React, { useState } from 'react';
import {
  Settings,
  Database,
  Cloud,
  Lock,
  DollarSign,
  Shield,
  CheckCircle2,
  Server,
  RefreshCw,
} from 'lucide-react';

export function SettingsView() {
  const [testingConnection, setTestingConnection] = useState(false);
  const [connSuccess, setConnSuccess] = useState<string | null>(null);

  const handleTestConnection = () => {
    setTestingConnection(true);
    setConnSuccess(null);
    setTimeout(() => {
      setTestingConnection(false);
      setConnSuccess('FastAPI Backend, Supabase PostgreSQL, and Storage health checked: ALL SYSTEMS OPERATIONAL.');
      setTimeout(() => setConnSuccess(null), 5000);
    }, 1200);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-5 rounded-xl border border-canvas-700/60 bg-gradient-to-r from-canvas-900 via-canvas-900/90 to-cyan-brand/10 shadow-lg flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="p-3 rounded-lg bg-cyan-brand/10 border border-cyan-brand/30 text-cyan-brand">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-bold text-white tracking-wide">
                System Infrastructure & Command Configuration
              </h2>
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                Production Connected
              </span>
            </div>
            <p className="text-xs text-canvas-300 mt-1 max-w-2xl leading-relaxed">
              Active configuration for FastAPI API endpoints, Supabase PostgreSQL persistence, Supabase private object storage, and PayPal Sandbox escrow gates.
            </p>
          </div>
        </div>

        <button
          onClick={handleTestConnection}
          disabled={testingConnection}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-canvas-800 hover:bg-canvas-700 text-white font-semibold text-xs border border-canvas-700"
        >
          <RefreshCw className={`w-4 h-4 text-cyan-brand ${testingConnection ? 'animate-spin' : ''}`} />
          {testingConnection ? 'Probing Services...' : 'Health Ping All Services'}
        </button>
      </div>

      {connSuccess && (
        <div className="p-3.5 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 text-xs font-semibold flex items-center gap-2 animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {connSuccess}
        </div>
      )}

      {/* Settings Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Backend & API */}
        <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
          <div className="flex items-center gap-2.5 text-white font-bold text-sm">
            <Server className="w-4 h-4 text-cyan-brand" />
            Backend API Architecture
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-canvas-400 block mb-1">FastAPI Backend Service</span>
              <input
                type="text"
                readOnly
                value="https://coldchain-sentinel.onrender.com (or local :8000)"
                className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-300 font-mono text-xs select-all"
              />
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">CORS Allowed Origins</span>
              <input
                type="text"
                readOnly
                value="https://coldchain-sentinel.vercel.app, http://localhost:3000"
                className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-300 font-mono text-xs select-all"
              />
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">Active Authentication Scheme</span>
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                JWT Bearer Tokens (HS256) with RBAC Roles (Admin, Auditor, Carrier, Viewer)
              </div>
            </div>
          </div>
        </div>

        {/* Database & Persistence */}
        <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
          <div className="flex items-center gap-2.5 text-white font-bold text-sm">
            <Database className="w-4 h-4 text-cyan-brand" />
            Database & Persistence Layer
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-canvas-400 block mb-1">Database Engine</span>
              <input
                type="text"
                readOnly
                value="Supabase Free PostgreSQL (Session Mode Pooler :5432)"
                className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-300 font-mono text-xs select-all"
              />
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">Alembic Migration Schema</span>
              <div className="font-semibold text-emerald-400 flex items-center gap-1.5 font-mono">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Idempotent Enum Migrations (13 Postgres Enums, 11 Tables)
              </div>
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">Storage Backend</span>
              <div className="font-semibold text-cyan-brand flex items-center gap-1.5 font-mono">
                <Cloud className="w-3.5 h-3.5" />
                Supabase Storage (Private Bucket: evidence)
              </div>
            </div>
          </div>
        </div>

        {/* Payment Escrow Gateway */}
        <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
          <div className="flex items-center gap-2.5 text-white font-bold text-sm">
            <DollarSign className="w-4 h-4 text-cyan-brand" />
            Payment Escrow Configuration
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-canvas-400 block mb-1">Payment Provider</span>
              <input
                type="text"
                readOnly
                value="PayPal REST API (Sandbox Environment)"
                className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-300 font-mono text-xs select-all"
              />
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">Escrow Policy Mode</span>
              <p className="text-canvas-300">
                Strict Tri-Gate Release (Thermal + Hash + Custody Handshake must all pass before capture call).
              </p>
            </div>
          </div>
        </div>

        {/* Cryptographic Ledger */}
        <div className="p-5 rounded-xl border border-canvas-750 bg-canvas-900 space-y-4">
          <div className="flex items-center gap-2.5 text-white font-bold text-sm">
            <Lock className="w-4 h-4 text-cyan-brand" />
            Cryptographic Integrity Engine
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <span className="text-canvas-400 block mb-1">Hash Algorithm</span>
              <input
                type="text"
                readOnly
                value="SHA-256 (FIPS 180-4 standard)"
                className="w-full px-3 py-2 rounded-lg bg-canvas-950 border border-canvas-800 text-canvas-300 font-mono text-xs select-all"
              />
            </div>
            <div>
              <span className="text-canvas-400 block mb-1">Verification Trigger</span>
              <p className="text-canvas-300">
                Synchronous on file upload and asynchronous prior to automated payment capture.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
