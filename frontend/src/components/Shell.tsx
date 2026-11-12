'use client';

import React, { useState } from 'react';
import {
  LayoutDashboard,
  Navigation,
  Package,
  Thermometer,
  FileCheck,
  GitBranch,
  CreditCard,
  ShieldAlert,
  BarChart3,
  FlaskConical,
  FileSpreadsheet,
  Settings,
  ChevronLeft,
  ChevronRight,
  Search,
  Bell,
  RefreshCw,
  Shield,
  CheckCircle2,
  AlertTriangle,
  User,
  ExternalLink,
  Sparkles,
} from 'lucide-react';

export type NavigationTab =
  | 'overview'
  | 'settlement'
  | 'tracking'
  | 'shipments'
  | 'temperature'
  | 'evidence'
  | 'timeline'
  | 'payments'
  | 'investigations'
  | 'carriers'
  | 'demo'
  | 'reports'
  | 'settings';

interface ShellProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  onSearchChange?: (query: string) => void;
  searchQuery?: string;
  onResetScenarios?: () => void;
  isResetting?: boolean;
  children: React.ReactNode;
}

export function Shell({
  currentTab,
  onSelectTab,
  onSearchChange,
  searchQuery = '',
  onResetScenarios,
  isResetting = false,
  children,
}: ShellProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);

  const navigationItems = [
    { id: 'overview' as NavigationTab, label: 'Overview', icon: LayoutDashboard },
    { id: 'settlement' as NavigationTab, label: 'AI Settlement', icon: Sparkles, badge: 'AI CORE' },
    { id: 'tracking' as NavigationTab, label: 'Live Tracking', icon: Navigation, badge: 'HERO' },
    { id: 'shipments' as NavigationTab, label: 'Shipments', icon: Package },
    { id: 'temperature' as NavigationTab, label: 'Temperature Monitor', icon: Thermometer },
    { id: 'evidence' as NavigationTab, label: 'Evidence Vault', icon: FileCheck },
    { id: 'timeline' as NavigationTab, label: 'Journey Timeline', icon: GitBranch },
    { id: 'payments' as NavigationTab, label: 'Payment Control', icon: CreditCard },
    { id: 'investigations' as NavigationTab, label: 'Investigations', icon: ShieldAlert, alert: true },
    { id: 'carriers' as NavigationTab, label: 'Carrier Performance', icon: BarChart3 },
    { id: 'demo' as NavigationTab, label: 'Demo Center', icon: FlaskConical, badge: '4 LABS' },
    { id: 'reports' as NavigationTab, label: 'Reports', icon: FileSpreadsheet },
    { id: 'settings' as NavigationTab, label: 'Settings', icon: Settings },
  ];

  const getPageTitleAndDesc = (tab: NavigationTab) => {
    switch (tab) {
      case 'overview':
        return {
          title: 'Fleet Operations Overview',
          desc: 'High-level logistics intelligence, compliance posture, and real-time shipment health.',
        };
      case 'settlement':
        return {
          title: 'ColdChain AI Settlement Intelligence',
          desc: 'Autonomous contract understanding, multi-factor investigation, and human-approved PayPal execution.',
        };
      case 'tracking':
        return {
          title: 'Live Interactive Tracking',
          desc: 'End-to-end waypoint corridors, real-time temperature conditions, and active transit progress.',
        };
      case 'shipments':
        return {
          title: 'Shipment Registry & Management',
          desc: 'Searchable cold-chain consignments, carrier assignments, and live compliance statuses.',
        };
      case 'temperature':
        return {
          title: 'Thermal Intelligence & Excursions',
          desc: 'Continuous temperature history, 2°C–8°C safe bounds, and real-time excursion duration tracking.',
        };
      case 'evidence':
        return {
          title: 'Cryptographic Evidence Vault',
          desc: 'SHA-256 tamper-proof telemetry files, calibration certs, and independent data integrity verification.',
        };
      case 'timeline':
        return {
          title: 'Chain of Custody Journey',
          desc: 'Verified multi-custodian transfer logs, timestamped signatures, and unbroken custody tracking.',
        };
      case 'payments':
        return {
          title: 'Automated Payment Control',
          desc: 'Condition-gated escrow releases and simulated PayPal Sandbox captures tied strictly to compliance.',
        };
      case 'investigations':
        return {
          title: 'Anomaly & Fraud Investigations',
          desc: 'Case management for thermal breaches, evidence digest discrepancies, and custody gaps.',
        };
      case 'carriers':
        return {
          title: 'Carrier Benchmark & Performance',
          desc: 'Compliance scores, thermal reliability metrics, and historical delivery assurance grades.',
        };
      case 'demo':
        return {
          title: 'Sentinel Challenge Demo Center',
          desc: 'One-click deterministic simulation of all 4 hackathon cold-chain scenarios.',
        };
      case 'reports':
        return {
          title: 'Audit Reports & Compliance Export',
          desc: 'Regulatory 21 CFR Part 11 compliant audit logs, shipment manifests, and verification certificates.',
        };
      case 'settings':
        return {
          title: 'Platform Configuration & Security',
          desc: 'Organization profile, API credentials, webhook endpoints, and backend connectivity settings.',
        };
    }
  };

  const { title, desc } = getPageTitleAndDesc(currentTab);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#070B12] text-slate-100 font-sans">
      {/* 1. LEFT SIDEBAR */}
      <aside
        className={`flex flex-col border-r border-[#162033] bg-[#0A0F1D] transition-all duration-300 z-30 select-none ${
          collapsed ? 'w-20' : 'w-64'
        }`}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center justify-between border-b border-[#162033] px-4">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-cyan-400 via-sky-500 to-blue-600 shadow-glow-cyan text-slate-950 font-bold">
              <Shield className="h-5 w-5 text-slate-950 fill-slate-950" />
            </div>
            {!collapsed && (
              <div className="flex flex-col truncate">
                <span className="text-sm font-bold tracking-wider text-slate-100 flex items-center gap-1.5">
                  COLDCHAIN
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 font-mono">
                    SENTINEL
                  </span>
                </span>
                <span className="text-[10px] text-slate-400 truncate">Logistics Command Center</span>
              </div>
            )}
          </div>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="flex h-7 w-7 items-center justify-center rounded-lg border border-[#1E293B] bg-[#0F172A] text-slate-400 hover:text-slate-200 transition"
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <div className="flex-1 overflow-y-auto py-3 px-2 space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                title={collapsed ? item.label : undefined}
                className={`group relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-xs font-medium transition-all ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/15 via-sky-500/10 to-transparent text-cyan-300 border-l-2 border-cyan-400 font-semibold'
                    : 'text-slate-400 hover:bg-[#11192C] hover:text-slate-200'
                }`}
              >
                <Icon
                  className={`h-4 w-4 shrink-0 transition ${
                    isActive ? 'text-cyan-400 drop-shadow-[0_0_8px_rgba(0,242,254,0.6)]' : 'text-slate-400 group-hover:text-slate-200'
                  }`}
                />
                {!collapsed && (
                  <span className="flex-1 text-left truncate">{item.label}</span>
                )}
                {!collapsed && item.badge && (
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                    {item.badge}
                  </span>
                )}
                {!collapsed && item.alert && (
                  <span className="h-2 w-2 rounded-full bg-rose-500 animate-pulse"></span>
                )}
              </button>
            );
          })}
        </div>

        {/* User / Organization Profile Footer */}
        <div className="border-t border-[#162033] p-3 bg-[#080D1A]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#1A263D] border border-[#233554] text-cyan-400">
              <User className="h-4 w-4" />
            </div>
            {!collapsed && (
              <div className="flex flex-col truncate">
                <span className="text-xs font-semibold text-slate-200 truncate">Global BioPharma Corp</span>
                <span className="text-[10px] text-cyan-400 font-mono">ADMIN / QA AUDITOR</span>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* 2. MAIN CONTENT AREA (TOP BAR + VIEW CANVAS) */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* TOP BAR */}
        <header className="flex h-16 w-full items-center justify-between border-b border-[#162033] bg-[#0A0F1D]/80 backdrop-blur-md px-6 z-20">
          {/* Page Heading & Description */}
          <div className="flex flex-col">
            <h1 className="text-base font-bold tracking-tight text-slate-100 flex items-center gap-2">
              {title}
            </h1>
            <p className="text-xs text-slate-400 hidden sm:block">{desc}</p>
          </div>

          {/* Search & Actions Bar */}
          <div className="flex items-center gap-3">
            {/* Global Search Bar */}
            <div className="relative w-48 md:w-64">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400 pointer-events-none" />
              <input
                type="text"
                placeholder="Search shipments, medicines..."
                value={searchQuery}
                onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
                className="w-full rounded-xl border border-[#1E293B] bg-[#0E1526] py-1.5 pl-8 pr-3 text-xs text-slate-200 placeholder:text-slate-500 focus:border-cyan-500/50 focus:outline-none focus:ring-1 focus:ring-cyan-500/50 transition"
              />
            </div>

            {/* Judge Demo Quick Access Button */}
            <button
              onClick={() => onSelectTab('demo')}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 text-xs font-semibold transition shadow-sm"
              title="Open Hackathon Demo Scenarios (Instant Judge Access)"
            >
              <FlaskConical className="h-3.5 w-3.5 text-emerald-400" />
              <span className="hidden sm:inline">Judge Demo Labs</span>
            </button>

            {/* Scenario Reset Button */}
            {onResetScenarios && (
              <button
                onClick={onResetScenarios}
                disabled={isResetting}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-cyan-500/40 bg-gradient-to-r from-cyan-500/20 to-sky-500/20 text-cyan-300 hover:bg-cyan-500/30 text-xs font-medium transition shadow-sm disabled:opacity-50"
                title="Reset all 4 demo scenarios to clean state"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isResetting ? 'animate-spin' : ''}`} />
                <span className="hidden md:inline">{isResetting ? 'Resetting...' : 'Reset Scenarios'}</span>
              </button>
            )}

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative flex h-8 w-8 items-center justify-center rounded-xl border border-[#1E293B] bg-[#0E1526] text-slate-400 hover:text-slate-200 transition"
              >
                <Bell className="h-4 w-4" />
                <span className="absolute -top-1 -right-1 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-rose-500 text-[8px] font-bold text-white">
                  3
                </span>
              </button>

              {/* Notification Popover */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 rounded-2xl border border-[#1F2E47] bg-[#0E1526] shadow-2xl p-3 z-50 animate-in fade-in slide-in-from-top-2">
                  <div className="flex items-center justify-between border-b border-[#1A253A] pb-2 mb-2">
                    <span className="text-xs font-bold text-slate-200">System Alerts</span>
                    <span className="text-[10px] font-mono text-cyan-400">3 UNRESOLVED</span>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div className="p-2 rounded-lg bg-rose-950/40 border border-rose-500/30">
                      <div className="flex items-center gap-1.5 text-rose-300 font-semibold text-[11px]">
                        <AlertTriangle className="h-3 w-3" />
                        Thermal Breach: CHALLENGE-02
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        14.5°C breach on tarmac. Payment capture held.
                      </p>
                    </div>
                    <div className="p-2 rounded-lg bg-amber-950/40 border border-amber-500/30">
                      <div className="flex items-center gap-1.5 text-amber-300 font-semibold text-[11px]">
                        <Shield className="h-3 w-3" />
                        Tamper Alert: CHALLENGE-03
                      </div>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        SHA-256 hash mismatch detected on logger payload.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Cloud & Service Connectivity Badges */}
            <div className="hidden lg:flex items-center gap-2 border-l border-[#1A253A] pl-3">
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-emerald-950/50 border border-emerald-500/30 text-[10px] font-mono text-emerald-400">
                <CheckCircle2 className="h-3 w-3" />
                <span>API: LIVE</span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/50 border border-cyan-500/30 text-[10px] font-mono text-cyan-400">
                <span>PAYPAL: SANDBOX</span>
              </div>
            </div>
          </div>
        </header>

        {/* DYNAMIC VIEW CONTAINER */}
        <main className="flex-1 overflow-y-auto p-6 bg-[#080C14]">
          {children}
        </main>
      </div>
    </div>
  );
}
