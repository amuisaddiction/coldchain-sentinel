'use client';

import React, { useState } from 'react';
import { MapPin, Navigation, Compass, AlertTriangle, CheckCircle2, ShieldAlert, Clock, Layers } from 'lucide-react';
import { ShipmentModel } from '@/lib/mockData';

interface InteractiveMapProps {
  shipment: ShipmentModel;
  onSelectWaypoint?: (wpName: string) => void;
  className?: string;
}

export function InteractiveMap({ shipment, onSelectWaypoint, className = '' }: InteractiveMapProps) {
  const [activeWaypointIndex, setActiveWaypointIndex] = useState<number | null>(null);
  const [mapMode, setMapMode] = useState<'standard' | 'thermal'>('standard');

  const waypoints = shipment.waypoints || [];
  const origin = waypoints[0];
  const destination = waypoints[waypoints.length - 1];

  // Coordinate projection helper for SVG container (500 x 300 viewBox)
  // Maps waypoints into proportional SVG space across Europe/Asia
  const getCoordinates = (index: number, total: number) => {
    const paddingX = 80;
    const paddingY = 60;
    const usableWidth = 500 - paddingX * 2;
    const usableHeight = 300 - paddingY * 2;

    const x = paddingX + (index / (total - 1 || 1)) * usableWidth;
    // Slight organic vertical curve for flight/route corridor
    const curveOffsets = [0, -35, -20, 0];
    const y = paddingY + usableHeight / 2 + (curveOffsets[index % curveOffsets.length] || 0);

    return { x, y };
  };

  const points = waypoints.map((wp, i) => ({
    ...wp,
    ...getCoordinates(i, waypoints.length),
  }));

  // Build SVG bezier path string connecting the waypoints
  let pathD = '';
  if (points.length >= 2) {
    pathD = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const cx1 = prev.x + (curr.x - prev.x) / 2;
      const cy1 = prev.y;
      const cx2 = prev.x + (curr.x - prev.x) / 2;
      const cy2 = curr.y;
      pathD += ` C ${cx1} ${cy1}, ${cx2} ${cy2}, ${curr.x} ${curr.y}`;
    }
  }

  // Current position on the path
  const currentIdx = Math.min(
    Math.floor((shipment.progress_pct / 100) * (points.length - 1)),
    points.length - 1
  );
  const currentPos = points[currentIdx] || points[0];

  return (
    <div className={`relative flex flex-col h-full w-full bg-[#080D18] border border-[#182338] rounded-2xl overflow-hidden shadow-2xl ${className}`}>
      {/* Map Control HUD Bar */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#0F172A]/90 border border-[#1E293B] backdrop-blur-md shadow-lg">
          <div className="h-2 w-2 rounded-full bg-cyan-400 animate-ping"></div>
          <span className="text-xs font-mono font-medium text-slate-200">
            RADAR: {shipment.origin_city.toUpperCase()} → {shipment.destination_city.toUpperCase()}
          </span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">
            {shipment.progress_pct}% COMPLETED
          </span>
        </div>

        {/* Heatmap/Thermal Toggle */}
        <div className="flex items-center rounded-lg bg-[#0F172A]/90 border border-[#1E293B] p-0.5 backdrop-blur-md">
          <button
            onClick={() => setMapMode('standard')}
            className={`px-2 py-1 text-xs font-medium rounded ${
              mapMode === 'standard' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Route Corridor
          </button>
          <button
            onClick={() => setMapMode('thermal')}
            className={`px-2 py-1 text-xs font-medium rounded ${
              mapMode === 'thermal' ? 'bg-cyan-500/20 text-cyan-300' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Thermal Overlay
          </button>
        </div>
      </div>

      {/* Map Top-Right Status Badge */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
        <div
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border backdrop-blur-md shadow-lg text-xs font-medium ${
            shipment.temp_status === 'SAFE'
              ? 'bg-emerald-950/80 border-emerald-500/40 text-emerald-300'
              : shipment.temp_status === 'WARNING'
              ? 'bg-amber-950/80 border-amber-500/40 text-amber-300'
              : 'bg-rose-950/80 border-rose-500/40 text-rose-300'
          }`}
        >
          {shipment.temp_status === 'SAFE' ? (
            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <AlertTriangle className="h-3.5 w-3.5 text-rose-400" />
          )}
          <span>
            {shipment.current_temp}°C ({shipment.temp_status})
          </span>
        </div>
      </div>

      {/* SVG Canvas Map Surface */}
      <div className="relative flex-1 w-full min-h-[380px] flex items-center justify-center p-4">
        {/* Synthetic Map Background Grid */}
        <div className="absolute inset-0 opacity-20 pointer-events-none">
          <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <pattern id="grid-pattern" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#253552" strokeWidth="0.75" />
                <circle cx="40" cy="40" r="1" fill="#38BDF8" opacity="0.4" />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid-pattern)" />
          </svg>
        </div>

        {/* Dynamic Route SVG Layer */}
        <svg
          viewBox="0 0 500 300"
          className="w-full h-full max-h-[460px] drop-shadow-2xl overflow-visible select-none"
        >
          <defs>
            <linearGradient id="route-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00F2FE" stopOpacity="0.9" />
              <stop offset="50%" stopColor="#38BDF8" stopOpacity="0.8" />
              <stop
                offset="100%"
                stopColor={shipment.temp_status === 'BREACH' ? '#EF4444' : '#10B981'}
                stopOpacity="0.9"
              />
            </linearGradient>

            {/* Glowing filter */}
            <filter id="cyan-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Background Corridor Halo */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke={mapMode === 'thermal' && shipment.temp_status === 'BREACH' ? '#EF4444' : '#00F2FE'}
              strokeWidth="10"
              strokeOpacity="0.12"
              strokeLinecap="round"
            />
          )}

          {/* Planned Path Line */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="#1E293B"
              strokeWidth="3"
              strokeDasharray="4 4"
            />
          )}

          {/* Active Completed Route Segment */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="url(#route-gradient)"
              strokeWidth="3.5"
              strokeLinecap="round"
              filter="url(#cyan-glow)"
            />
          )}

          {/* Waypoint Nodes */}
          {points.map((pt, idx) => {
            const isOrigin = idx === 0;
            const isDest = idx === points.length - 1;
            const isBreachNode = shipment.temp_status === 'BREACH' && idx === 2;

            return (
              <g
                key={pt.name}
                className="cursor-pointer transition-transform hover:scale-110"
                onClick={() => {
                  setActiveWaypointIndex(idx);
                  if (onSelectWaypoint) onSelectWaypoint(pt.name);
                }}
              >
                {/* Node Outer Radar Ring */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isOrigin || isDest ? '14' : '10'}
                  fill={isBreachNode ? '#7F1D1D' : '#0F172A'}
                  stroke={isBreachNode ? '#EF4444' : isDest ? '#10B981' : '#38BDF8'}
                  strokeWidth="2"
                  strokeOpacity={pt.status === 'completed' ? '1' : '0.4'}
                />

                {/* Node Center Core */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isOrigin || isDest ? '6' : '4'}
                  fill={isBreachNode ? '#EF4444' : isDest ? '#10B981' : '#00F2FE'}
                />

                {/* Node Label Text */}
                <text
                  x={pt.x}
                  y={idx % 2 === 0 ? pt.y - 20 : pt.y + 26}
                  textAnchor="middle"
                  className="text-[11px] font-sans font-medium fill-slate-200 select-none drop-shadow"
                >
                  {pt.name.split(' (')[0]}
                </text>

                {pt.time && (
                  <text
                    x={pt.x}
                    y={idx % 2 === 0 ? pt.y - 8 : pt.y + 38}
                    textAnchor="middle"
                    className="text-[9px] font-mono fill-cyan-400 select-none opacity-80"
                  >
                    {pt.time} UTC
                  </text>
                )}
              </g>
            );
          })}

          {/* Current Active Vehicle Marker */}
          {currentPos && (
            <g transform={`translate(${currentPos.x}, ${currentPos.y})`}>
              {/* Radar pulse ripples */}
              <circle r="18" fill="none" stroke="#00F2FE" strokeWidth="1.5" className="radar-ping" />
              <circle r="8" fill="#00F2FE" stroke="#0F172A" strokeWidth="2" />
            </g>
          )}
        </svg>
      </div>

      {/* Map Bottom Information Footer Bar */}
      <div className="z-10 flex items-center justify-between border-t border-[#182338] bg-[#0A101D]/95 px-5 py-3 text-xs">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Compass className="h-3.5 w-3.5 text-cyan-400" />
            <span className="font-mono text-slate-400">CARRIER:</span>
            <span className="font-medium text-slate-200">{shipment.carrier_name}</span>
          </div>
          <div className="h-3 w-px bg-slate-800"></div>
          <div className="flex items-center gap-1.5 text-slate-300">
            <Clock className="h-3.5 w-3.5 text-cyan-400" />
            <span className="font-mono text-slate-400">EST. ARRIVAL:</span>
            <span className="font-medium text-slate-200">{shipment.estimated_arrival}</span>
          </div>
        </div>

        {/* Certified illustrative disclaimer to avoid misleading GPS fabrication */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-wider">
            Verified Waypoint Lineage • Illustrative GIS Corridor
          </span>
        </div>
      </div>
    </div>
  );
}
