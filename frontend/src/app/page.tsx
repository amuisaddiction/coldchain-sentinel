export default function HomePage() {
  return (
    <div className="flex h-screen w-screen flex-col bg-obsidian-900 text-obsidian-100 overflow-hidden font-sans">
      {/* Header Bar */}
      <header className="flex h-12 w-full items-center justify-between border-b border-obsidian-700 bg-obsidian-850 px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-6 w-6 items-center justify-center rounded border border-obsidian-600 bg-obsidian-800 text-xs font-mono font-bold text-obsidian-200">
            CS
          </div>
          <span className="text-sm font-semibold tracking-wide text-obsidian-100">
            COLDCHAIN SENTINEL
          </span>
          <span className="rounded border border-obsidian-700 bg-obsidian-800 px-2 py-0.5 text-[10px] font-mono uppercase text-obsidian-400">
            OPS CONSOLE
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-status-pass"></span>
            <span className="font-mono text-[11px] text-obsidian-300">SYSTEM READY</span>
          </div>
          <div className="h-4 w-px bg-obsidian-700"></div>
          <div className="font-mono text-[11px] text-obsidian-400">
            PAYPAL SANDBOX: <span className="text-obsidian-200">STANDBY</span>
          </div>
        </div>
      </header>

      {/* Main Operations Grid */}
      <main className="flex flex-1 flex-col overflow-hidden">
        {/* Top Split: Left Shipment Queue, Right Geographic View */}
        <div className="flex flex-1 overflow-hidden">
          {/* Left: Shipment List (Compact cards) */}
          <section className="flex w-96 flex-col border-r border-obsidian-700 bg-obsidian-850">
            <div className="flex h-9 items-center justify-between border-b border-obsidian-700 px-3">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-400">
                ACTIVE SHIPMENTS (0)
              </span>
              <span className="text-[10px] font-mono text-obsidian-500">FILTER: ALL</span>
            </div>
            <div className="flex flex-1 items-center justify-center p-6 text-center">
              <div className="space-y-1">
                <p className="text-xs font-medium text-obsidian-300">Phase 1 Architecture Active</p>
                <p className="text-[11px] text-obsidian-500">
                  Ready for Phase 2 database & API integration.
                </p>
              </div>
            </div>
          </section>

          {/* Right: Geographical Map Area */}
          <section className="relative flex flex-1 flex-col bg-obsidian-950">
            <div className="flex h-9 items-center justify-between border-b border-obsidian-700 bg-obsidian-850 px-4">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-400">
                TRANSIT MAP & HANDOVER ROUTE
              </span>
              <span className="text-[10px] font-mono text-obsidian-400">
                LAYER: NATURAL TERRAIN
              </span>
            </div>
            <div className="flex flex-1 items-center justify-center p-6 text-center">
              <div className="max-w-md rounded border border-obsidian-700 bg-obsidian-850 p-6 space-y-2">
                <p className="text-xs font-semibold tracking-wide text-obsidian-200 uppercase">
                  Natural Cartography Viewport
                </p>
                <p className="text-[11px] text-obsidian-400 leading-relaxed">
                  Natural land/ocean tones only. Zero neon filters or artificial GPS traces. Renders discrete recorded custody handover waypoints and destination acceptance.
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Bottom Split: Selected Shipment Detail Drawer */}
        <section className="flex h-56 flex-col border-t border-obsidian-700 bg-obsidian-850">
          <div className="flex h-8 items-center border-b border-obsidian-700 px-3 gap-4">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-obsidian-200">
              INSPECTION WORKSPACE
            </span>
            <div className="flex gap-1 text-[11px] font-mono text-obsidian-400">
              <span className="rounded bg-obsidian-750 px-2 py-0.5 text-obsidian-200">Summary</span>
              <span className="px-2 py-0.5 hover:text-obsidian-200">Telemetry Curve</span>
              <span className="px-2 py-0.5 hover:text-obsidian-200">Evidence Trust</span>
              <span className="px-2 py-0.5 hover:text-obsidian-200">Chain of Custody</span>
              <span className="px-2 py-0.5 hover:text-obsidian-200">PayPal Settlement</span>
              <span className="px-2 py-0.5 hover:text-obsidian-200">Audit Log</span>
            </div>
          </div>
          <div className="flex flex-1 items-center justify-center p-4">
            <p className="text-[11px] font-mono text-obsidian-500">
              Select a shipment above to inspect cryptographic hashes, temperature bounds, and settlement status.
            </p>
          </div>
        </section>
      </main>
    </div>
  );
}
