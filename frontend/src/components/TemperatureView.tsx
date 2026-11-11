'use client';

import React, { useState } from 'react';
import {
  Thermometer,
  AlertTriangle,
  CheckCircle2,
  Clock,
  TrendingDown,
  TrendingUp,
  Activity,
  Layers,
  Info,
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { ShipmentModel, DEMO_SHIPMENTS, DEMO_TELEMETRY } from '@/lib/mockData';

interface TemperatureViewProps {
  shipments: ShipmentModel[];
  selectedShipment: ShipmentModel;
  onSelectShipment: (shipment: ShipmentModel) => void;
}

export function TemperatureView({
  shipments,
  selectedShipment,
  onSelectShipment,
}: TemperatureViewProps) {
  const current = selectedShipment || shipments[0] || DEMO_SHIPMENTS[0];
  const chartData = DEMO_TELEMETRY[current.tracking_number] || DEMO_TELEMETRY['CHALLENGE-01-CLEAN'];

  // Compute metrics
  const temps = chartData.map((d) => d.temp);
  const minTemp = Math.min(...temps);
  const maxTemp = Math.max(...temps);
  const avgTemp = (temps.reduce((a, b) => a + b, 0) / (temps.length || 1)).toFixed(1);

  const isExcursion = maxTemp > current.max_allowed_temp || minTemp < current.min_allowed_temp;
  const excursionDurationMins = current.tracking_number === 'CHALLENGE-02-EXCURSION' ? 15 : 0;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Shipment Switcher */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 panel-card p-3">
        <span className="text-xs font-mono font-medium text-slate-400 shrink-0">SELECT SENSOR STREAM:</span>
        {(shipments.length > 0 ? shipments : DEMO_SHIPMENTS).map((s) => {
          const isSelected = s.tracking_number === current.tracking_number;
          return (
            <button
              key={s.tracking_number}
              onClick={() => onSelectShipment(s)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-medium transition shrink-0 border ${
                isSelected
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200'
                  : 'bg-[#0E1524] border-[#1E293B] text-slate-400 hover:text-slate-200'
              }`}
            >
              <span
                className={`h-2 w-2 rounded-full ${
                  s.temp_status === 'SAFE' ? 'bg-emerald-400' : 'bg-rose-400'
                }`}
              ></span>
              <span className="font-mono">{s.tracking_number}</span>
            </button>
          );
        })}
      </div>

      {/* Plain Language Temperature Banner */}
      <div
        className={`p-4 rounded-2xl border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-lg ${
          !isExcursion
            ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-200'
            : 'bg-rose-950/30 border-rose-500/40 text-rose-200'
        }`}
      >
        <div className="flex items-center gap-3">
          <div
            className={`p-2.5 rounded-xl ${
              !isExcursion ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
            }`}
          >
            {!isExcursion ? <CheckCircle2 className="h-5 w-5" /> : <AlertTriangle className="h-5 w-5" />}
          </div>
          <div>
            <h2 className="text-sm font-bold tracking-tight">
              {!isExcursion
                ? 'Temperature stayed within the safe range (+2.0°C to +8.0°C).'
                : `Temperature crossed the allowed safe limit for ${excursionDurationMins} minutes.`}
            </h2>
            <p className="text-xs opacity-80 mt-0.5">
              {!isExcursion
                ? 'Certified NIST logger data confirms 100% thermal compliance throughout all custody handovers.'
                : 'Sensor recorded a thermal spike up to 14.5°C during tarmac transit. Automated payment capture is blocked.'}
            </p>
          </div>
        </div>

        <div className="text-xs font-mono px-3 py-1.5 rounded-xl bg-black/40 border border-white/10 shrink-0">
          <span>STATUS: </span>
          <span className="font-bold">{!isExcursion ? 'COMPLIANT' : 'BREACH DETECTED'}</span>
        </div>
      </div>

      {/* Temperature Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Current Sensor Reading */}
        <div className="panel-card p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Latest Reading</span>
            <Activity className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-slate-100">{current.current_temp}°C</div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Updated live from sensor</div>
          </div>
        </div>

        {/* Minimum Recorded Temp */}
        <div className="panel-card p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Minimum Temperature</span>
            <TrendingDown className="h-4 w-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <div className="text-2xl font-bold font-mono text-cyan-300">{minTemp}°C</div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Safe floor: +2.00°C</div>
          </div>
        </div>

        {/* Maximum Recorded Temp */}
        <div className="panel-card p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Maximum Temperature</span>
            <TrendingUp className={`h-4 w-4 ${maxTemp > 8.0 ? 'text-rose-400' : 'text-emerald-400'}`} />
          </div>
          <div className="mt-3">
            <div
              className={`text-2xl font-bold font-mono ${
                maxTemp > 8.0 ? 'text-rose-400' : 'text-emerald-400'
              }`}
            >
              {maxTemp}°C
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Safe ceiling: +8.00°C</div>
          </div>
        </div>

        {/* Excursion Duration */}
        <div className="panel-card p-4">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>Excursion Duration</span>
            <Clock className={`h-4 w-4 ${excursionDurationMins > 0 ? 'text-rose-400' : 'text-emerald-400'}`} />
          </div>
          <div className="mt-3">
            <div
              className={`text-2xl font-bold font-mono ${
                excursionDurationMins > 0 ? 'text-rose-400' : 'text-emerald-400'
              }`}
            >
              {excursionDurationMins} min
            </div>
            <div className="text-[10px] text-slate-400 font-mono mt-0.5">Allowed ceiling: 10 mins</div>
          </div>
        </div>
      </div>

      {/* Main Temperature Curve Chart */}
      <div className="panel-card p-5">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-6">
          <div>
            <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wide">
              Continuous Thermal Curve ({current.tracking_number})
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Target band: +2.0°C to +8.0°C. Points outside the shaded region constitute non-compliant thermal excursions.
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-cyan-400"></span>
              <span className="text-slate-300">Sensor Logger</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-0.5 w-4 bg-emerald-500"></span>
              <span className="text-emerald-400">Safe Limits (+2°C/+8°C)</span>
            </div>
          </div>
        </div>

        {/* Recharts Area Container */}
        <div className="h-[360px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00F2FE" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#00F2FE" stopOpacity={0.0} />
                </linearGradient>
              </defs>

              <XAxis dataKey="time" stroke="#475569" tick={{ fill: '#94A3B8', fontSize: 11 }} />
              <YAxis
                stroke="#475569"
                domain={[0, 16]}
                ticks={[0, 2, 4, 6, 8, 10, 12, 14, 16]}
                tick={{ fill: '#94A3B8', fontSize: 11 }}
                unit="°C"
              />

              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    const isBreach = data.temp > 8.0 || data.temp < 2.0;
                    return (
                      <div className="rounded-xl border border-[#1E293B] bg-[#0E1526]/95 backdrop-blur-md p-3 shadow-xl text-xs font-mono">
                        <div className="text-slate-400">{data.time} UTC</div>
                        <div
                          className={`text-sm font-bold mt-1 ${
                            isBreach ? 'text-rose-400' : 'text-cyan-300'
                          }`}
                        >
                          Temperature: {data.temp}°C
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          Safe range: +2.0°C to +8.0°C
                        </div>
                        <div
                          className={`mt-1 font-semibold text-[10px] ${
                            isBreach ? 'text-rose-400' : 'text-emerald-400'
                          }`}
                        >
                          {isBreach ? 'EXCURSION BREACH' : 'COMPLIANT'}
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />

              {/* Safe bounds reference lines */}
              <ReferenceLine y={8} stroke="#10B981" strokeDasharray="4 4" strokeWidth={1.5} label={{ value: 'MAX 8°C', fill: '#10B981', fontSize: 10, position: 'right' }} />
              <ReferenceLine y={2} stroke="#10B981" strokeDasharray="4 4" strokeWidth={1.5} label={{ value: 'MIN 2°C', fill: '#10B981', fontSize: 10, position: 'right' }} />

              {/* Shaded Area & Line */}
              <Area type="monotone" dataKey="temp" stroke="#00F2FE" strokeWidth={2.5} fillOpacity={1} fill="url(#tempGradient)" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
