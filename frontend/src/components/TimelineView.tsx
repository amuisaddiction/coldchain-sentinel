'use client';

import React, { useState } from 'react';
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  XCircle,
  MapPin,
  User,
  Building,
  Thermometer,
  FileText,
  ShieldAlert,
  ChevronRight,
  Truck,
  Plane,
  Warehouse,
  Hospital,
  AlertCircle,
} from 'lucide-react';
import { DEMO_SHIPMENTS } from '../lib/mockData';

interface CustodyEvent {
  id: string;
  step_title: string;
  stage_type: 'DISPATCH' | 'AIR_TRANSIT' | 'TARMAC' | 'CUSTOMS' | 'LAST_MILE' | 'DELIVERY';
  timestamp: string;
  actor: string;
  organization: string;
  location: string;
  temp: string;
  temp_status: 'SAFE' | 'WARNING' | 'BREACH';
  status: 'COMPLETED' | 'IN_PROGRESS' | 'GAP_DETECTED' | 'FAILED' | 'UPCOMING';
  evidence_doc?: string;
  remarks?: string;
}

const CUSTODY_EVENTS_BY_SHIPMENT: Record<string, CustodyEvent[]> = {
  'CHALLENGE-01-CLEAN': [
    {
      id: 'c1',
      step_title: 'Cold Storage Release & Packaging Seal',
      stage_type: 'DISPATCH',
      timestamp: '2026-11-10 08:00 UTC',
      actor: 'Marc Baumgartner (Logistics Lead)',
      organization: 'Basel Biopharma Manufacturing AG',
      location: 'Basel, Switzerland',
      temp: '4.2°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'manifest_basel_01.pdf',
      remarks: 'Primary insulated VIP container sealed with dual calibrated loggers.',
    },
    {
      id: 'c2',
      step_title: 'Zurich Airport Hub Acceptance',
      stage_type: 'AIR_TRANSIT',
      timestamp: '2026-11-10 10:30 UTC',
      actor: 'Elena Rossi (Air Cargo Handler)',
      organization: 'Swiss WorldCargo Cold Division',
      location: 'Zurich Airport (ZRH)',
      temp: '4.6°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'nist_calibration_cert.pdf',
      remarks: 'Transferred directly into active temperature-controlled cargo hold.',
    },
    {
      id: 'c3',
      step_title: 'London Heathrow Ramp & Customs Handover',
      stage_type: 'CUSTOMS',
      timestamp: '2026-11-10 14:15 UTC',
      actor: 'David Miller (Customs Agent)',
      organization: 'UK Border Force / Swiss Cargo',
      location: 'London Heathrow (LHR) Pier 4',
      temp: '5.1°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'heathrow_clearance.pdf',
      remarks: 'Expedited customs clearance under cold-chain priority protocol.',
    },
    {
      id: 'c4',
      step_title: 'Destination Pharmacy Verification & Delivery Sign-off',
      stage_type: 'DELIVERY',
      timestamp: '2026-11-10 16:45 UTC',
      actor: 'Dr. Sarah Higgins (Chief Hospital Pharmacist)',
      organization: "Guy's and St Thomas' NHS Foundation Trust",
      location: "London Guy's Hospital Pharmacy Hub",
      temp: '4.5°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'telemetry_log_swiss_cargo_01.csv',
      remarks: 'Full batch temperature lineage inspected and approved. Payment released.',
    },
  ],

  'CHALLENGE-02-EXCURSION': [
    {
      id: 'e1',
      step_title: 'Depot Dispatch & Sensor Activation',
      stage_type: 'DISPATCH',
      timestamp: '2026-11-10 09:30 UTC',
      actor: 'Klaus Weber (Depot Tech)',
      organization: 'Munich Biotech Center',
      location: 'Munich, Germany',
      temp: '4.1°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'munich_dispatch_02.pdf',
      remarks: 'Loaded into thermal active container with 10-minute allowed spike tolerance.',
    },
    {
      id: 'e2',
      step_title: 'Munich Franz Josef Airport Handover',
      stage_type: 'AIR_TRANSIT',
      timestamp: '2026-11-10 11:15 UTC',
      actor: 'Thomas Müller (Ground Staff)',
      organization: 'Alitalia Ground Cargo',
      location: 'Munich Airport (MUC)',
      temp: '4.6°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'air_waybill_muc_fco.pdf',
      remarks: 'Handover complete without temperature anomalies.',
    },
    {
      id: 'e3',
      step_title: 'Tarmac Ramp Transfer — UNPROTECTED EXPOSURE',
      stage_type: 'TARMAC',
      timestamp: '2026-11-10 14:15 UTC',
      actor: 'Gianni Rossi (Ramp Operative)',
      organization: 'Alitalia Cargo Rome Hub',
      location: 'Rome Fiumicino Airport (FCO) Tarmac Bay 12',
      temp: '14.5°C',
      temp_status: 'BREACH',
      status: 'FAILED',
      evidence_doc: 'alitalia_logger_tarmac_b2.csv',
      remarks: 'CRITICAL BREACH: Container left on hot asphalt apron for 15 minutes. Temperature exceeded 8°C ceiling.',
    },
    {
      id: 'e4',
      step_title: 'Final Hospital Receiving Handover',
      stage_type: 'DELIVERY',
      timestamp: '2026-11-10 17:00 UTC (Expected)',
      actor: 'Quarantine Receiving Team',
      organization: 'Policlinico Umberto I Rome',
      location: 'Rome, Italy',
      temp: '--',
      temp_status: 'SAFE',
      status: 'UPCOMING',
      remarks: 'Receiving blocked pending medical safety board destruction or salvage review.',
    },
  ],

  'CHALLENGE-03-TAMPER': [
    {
      id: 't1',
      step_title: 'Insulin Batch Release & Cryptographic Seal',
      stage_type: 'DISPATCH',
      timestamp: '2026-11-11 06:15 UTC',
      actor: 'Frederik Larsen (QA Specialist)',
      organization: 'Copenhagen Biologics Hub',
      location: 'Copenhagen, Denmark',
      temp: '3.8°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'cph_batch_seal.pdf',
      remarks: 'Digital manifest signed and SHA-256 digest registered.',
    },
    {
      id: 't2',
      step_title: 'Oresund Bridge Freight Crossing',
      stage_type: 'LAST_MILE',
      timestamp: '2026-11-11 09:00 UTC',
      actor: 'Nils Lindqvist (Logistics Driver)',
      organization: 'Nordic Express Cold',
      location: 'Malmo Transit Center',
      temp: '4.2°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'transit_log_malmo.csv',
      remarks: 'Vehicle refrigeration verified at 4°C.',
    },
    {
      id: 't3',
      step_title: 'Arlanda Cargo Ingestion — SHA-256 DISCREPANCY',
      stage_type: 'CUSTOMS',
      timestamp: '2026-11-11 13:40 UTC',
      actor: 'Automated Ingestion Gateway',
      organization: 'Stockholm Arlanda Hub',
      location: 'Stockholm Arlanda Airport (ARN)',
      temp: '5.4°C',
      temp_status: 'WARNING',
      status: 'FAILED',
      evidence_doc: 'tampered_telemetry_payload.csv',
      remarks: 'TAMPER DETECTED: Computed file digest differs from original blockchain seal. Modification suspected.',
    },
    {
      id: 't4',
      step_title: 'Karolinska Hospital Pharmacy Intake',
      stage_type: 'DELIVERY',
      timestamp: '2026-11-11 16:00 UTC (Estimated)',
      actor: 'Pharmacy Receiving',
      organization: 'Karolinska University Hospital',
      location: 'Stockholm, Sweden',
      temp: '--',
      temp_status: 'SAFE',
      status: 'UPCOMING',
      remarks: 'Delivery postponed pending forensic integrity verification.',
    },
  ],

  'CHALLENGE-04-CUSTODY': [
    {
      id: 'g1',
      step_title: 'Biopharma Production Seal & Handover',
      stage_type: 'DISPATCH',
      timestamp: '2026-11-11 04:00 UTC',
      actor: 'Min-jun Kim (Cold Chain Dispatcher)',
      organization: 'Seoul Central Biopharma',
      location: 'Seoul, South Korea',
      temp: '3.9°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'seoul_origin_seal.pdf',
      remarks: 'Consignment packaged in certified vacuum insulation containers.',
    },
    {
      id: 'g2',
      step_title: 'Incheon Cargo Flight Departure',
      stage_type: 'AIR_TRANSIT',
      timestamp: '2026-11-11 06:30 UTC',
      actor: 'Ji-won Park (Air Freight Marshall)',
      organization: 'Trans-Asia Cold Express',
      location: 'Incheon International Airport (ICN)',
      temp: '4.0°C',
      temp_status: 'SAFE',
      status: 'COMPLETED',
      evidence_doc: 'flight_manifest_icn_hnd.pdf',
      remarks: 'Air container loaded onto scheduled cargo flight KE-803.',
    },
    {
      id: 'g3',
      step_title: 'Tokyo Haneda Air Cargo Receiving — SIGNATURE MISSING',
      stage_type: 'CUSTOMS',
      timestamp: '2026-11-11 11:00 UTC',
      actor: 'UNKNOWN / MISSING CUSTODIAN',
      organization: 'Tokyo Haneda Cargo Center',
      location: 'Tokyo Haneda International Airport (HND)',
      temp: '4.1°C',
      temp_status: 'SAFE',
      status: 'GAP_DETECTED',
      remarks: 'CUSTODY GAP: No authorized handler digital signature recorded during tarmac-to-warehouse custody transfer. Compliance protocol breached.',
    },
    {
      id: 'g4',
      step_title: 'Todai Medical Hospital Delivery',
      stage_type: 'DELIVERY',
      timestamp: '2026-11-11 15:00 UTC (Estimated)',
      actor: 'Hospital Oncology Department',
      organization: 'Todai Medical Hospital',
      location: 'Tokyo, Japan',
      temp: '--',
      temp_status: 'SAFE',
      status: 'UPCOMING',
      remarks: 'Payment held in escrow until custodian identity is officially authenticated and signed.',
    },
  ],
};

export function TimelineView() {
  const [selectedTracking, setSelectedTracking] = useState<string>('CHALLENGE-01-CLEAN');

  const currentShipment = DEMO_SHIPMENTS.find((s) => s.tracking_number === selectedTracking) || DEMO_SHIPMENTS[0];
  const events = CUSTODY_EVENTS_BY_SHIPMENT[selectedTracking] || CUSTODY_EVENTS_BY_SHIPMENT['CHALLENGE-01-CLEAN'];

  const getStageIcon = (stage: CustodyEvent['stage_type']) => {
    switch (stage) {
      case 'DISPATCH':
        return <Warehouse className="w-4 h-4" />;
      case 'AIR_TRANSIT':
        return <Plane className="w-4 h-4" />;
      case 'TARMAC':
        return <Truck className="w-4 h-4" />;
      case 'CUSTOMS':
        return <Building className="w-4 h-4" />;
      case 'LAST_MILE':
        return <Truck className="w-4 h-4" />;
      case 'DELIVERY':
        return <Hospital className="w-4 h-4" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Shipment Switcher & Context Bar */}
      <div className="p-4 rounded-xl border border-canvas-700/60 bg-canvas-900/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="text-[11px] text-cyan-brand font-mono uppercase tracking-wider block">
            Digital Chain of Custody Lineage
          </span>
          <h2 className="text-base font-bold text-white flex items-center gap-2 mt-0.5">
            Custody Handover Verification
            <span className="text-xs text-canvas-400 font-normal">
              ({events.length} Audited Milestone Handshakes)
            </span>
          </h2>
        </div>

        {/* Shipment Selector Pills */}
        <div className="flex items-center gap-2 overflow-x-auto w-full md:w-auto pb-1 md:pb-0">
          {DEMO_SHIPMENTS.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedTracking(s.tracking_number)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 border ${
                selectedTracking === s.tracking_number
                  ? 'bg-cyan-brand text-canvas-950 border-cyan-brand shadow-glow-cyan'
                  : 'bg-canvas-950 text-canvas-300 border-canvas-700 hover:border-canvas-500'
              }`}
            >
              <span>{s.tracking_number.split('-')[1]}</span>
              <span className="opacity-70 font-mono text-[10px]">({s.tracking_number.split('-')[2]})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Shipment Snapshot Strip */}
      <div className="p-4 rounded-xl border border-canvas-700/50 bg-gradient-to-r from-canvas-900 to-canvas-950 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div>
          <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Medicine / Consignment</span>
          <span className="font-bold text-white text-sm">{currentShipment.medicine_name}</span>
        </div>
        <div>
          <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Origin & Destination</span>
          <span className="font-medium text-canvas-200">
            {currentShipment.origin_city} → {currentShipment.destination_city}
          </span>
        </div>
        <div>
          <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Assigned Carrier</span>
          <span className="font-semibold text-cyan-brand">{currentShipment.carrier_name}</span>
        </div>
        <div>
          <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">Custody Lineage Status</span>
          <span
            className={`font-bold px-2 py-0.5 rounded text-[11px] ${
              currentShipment.status === 'VERIFIED'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                : currentShipment.status === 'FAILED'
                ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
            }`}
          >
            {currentShipment.status === 'VERIFIED'
              ? 'Complete & Unbroken'
              : currentShipment.status === 'FAILED'
              ? 'Critical Chain Violation'
              : 'Custody Review Required'}
          </span>
        </div>
      </div>

      {/* Vertical Timeline */}
      <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-3 sm:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-canvas-700">
        {events.map((event, idx) => {
          const isGap = event.status === 'GAP_DETECTED';
          const isFailed = event.status === 'FAILED';
          const isCompleted = event.status === 'COMPLETED';

          return (
            <div key={event.id} className="relative group">
              {/* Timeline Marker Node */}
              <div
                className={`absolute -left-6 sm:-left-8 top-3 w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-transform group-hover:scale-110 ${
                  isGap
                    ? 'bg-amber-950 text-amber-400 border-amber-500 animate-pulse'
                    : isFailed
                    ? 'bg-rose-950 text-rose-400 border-rose-500'
                    : isCompleted
                    ? 'bg-emerald-950 text-emerald-400 border-emerald-500'
                    : 'bg-canvas-800 text-canvas-400 border-canvas-600'
                }`}
              >
                {isGap ? (
                  <AlertCircle className="w-4 h-4 text-amber-400" />
                ) : isFailed ? (
                  <XCircle className="w-4 h-4 text-rose-400" />
                ) : isCompleted ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Clock className="w-4 h-4 text-canvas-400" />
                )}
              </div>

              {/* Event Card */}
              <div
                className={`p-5 rounded-xl border transition-all duration-200 ${
                  isGap
                    ? 'bg-amber-950/20 border-amber-500/50 shadow-lg shadow-amber-950/20'
                    : isFailed
                    ? 'bg-rose-950/20 border-rose-500/50 shadow-lg shadow-rose-950/20'
                    : isCompleted
                    ? 'bg-canvas-900 border-canvas-750 hover:border-canvas-600'
                    : 'bg-canvas-950 border-canvas-800 opacity-60'
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <div className="p-1.5 rounded-lg bg-canvas-800 border border-canvas-700 text-cyan-brand">
                        {getStageIcon(event.stage_type)}
                      </div>
                      <h3 className="text-sm font-bold text-white tracking-wide">
                        {event.step_title}
                      </h3>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-canvas-400">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5 text-canvas-500" />
                        {event.timestamp}
                      </span>
                      <span className="text-canvas-600">•</span>
                      <span className="flex items-center gap-1 text-canvas-300">
                        <MapPin className="w-3.5 h-3.5 text-cyan-brand" />
                        {event.location}
                      </span>
                    </div>
                  </div>

                  {/* Temperature Pill */}
                  {event.temp !== '--' && (
                    <div
                      className={`shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold border ${
                        event.temp_status === 'BREACH'
                          ? 'bg-rose-500/20 text-rose-300 border-rose-500/40'
                          : event.temp_status === 'WARNING'
                          ? 'bg-amber-500/20 text-amber-300 border-amber-500/40'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      }`}
                    >
                      <Thermometer className="w-3.5 h-3.5" />
                      <span>{event.temp}</span>
                    </div>
                  )}
                </div>

                {/* Handover Custodian Box */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-4 pt-3 border-t border-canvas-800/80 text-xs">
                  <div className="flex items-start gap-2">
                    <User className="w-4 h-4 text-canvas-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">
                        Verified Signatory
                      </span>
                      <span
                        className={`font-semibold ${
                          isGap ? 'text-amber-400 font-bold' : 'text-canvas-200'
                        }`}
                      >
                        {event.actor}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-start gap-2">
                    <Building className="w-4 h-4 text-canvas-400 shrink-0 mt-0.5" />
                    <div>
                      <span className="text-[10px] text-canvas-400 uppercase tracking-wider block">
                        Operating Entity
                      </span>
                      <span className="text-canvas-300">{event.organization}</span>
                    </div>
                  </div>
                </div>

                {/* Remarks & Evidence Chip */}
                {event.remarks && (
                  <p
                    className={`mt-3 text-xs p-2.5 rounded-lg border ${
                      isGap
                        ? 'bg-amber-500/10 border-amber-500/30 text-amber-200'
                        : isFailed
                        ? 'bg-rose-500/10 border-rose-500/30 text-rose-200'
                        : 'bg-canvas-950/60 border-canvas-800 text-canvas-300'
                    }`}
                  >
                    {event.remarks}
                  </p>
                )}

                {event.evidence_doc && (
                  <div className="mt-3 flex items-center justify-between text-xs pt-2">
                    <span className="text-[11px] text-canvas-400 flex items-center gap-1.5 font-mono">
                      <FileText className="w-3.5 h-3.5 text-cyan-brand" />
                      {event.evidence_doc}
                    </span>
                    <span className="text-[11px] text-cyan-brand hover:underline cursor-pointer flex items-center gap-0.5 font-medium">
                      Inspect Signed Digest <ChevronRight className="w-3 h-3" />
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
