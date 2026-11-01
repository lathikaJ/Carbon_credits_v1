import React from "react";
import ReactDOM from "react-dom/client";
import { Leaf, RefreshCw, Building2 } from "lucide-react";
import { KpiCards } from "@/components/ecopulse/KpiCards";
import { TelemetrySection } from "@/components/ecopulse/TelemetrySection";
import { RagInspector } from "@/components/ecopulse/RagInspector";
import { IncentivePanel } from "@/components/ecopulse/IncentivePanel";
import { ReportSection } from "@/components/ecopulse/ReportSection";
import { summary } from "@/lib/ecopulse-data";
import "@/styles.css";

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4 px-5 py-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-xl bg-emerald-500 text-slate-950 font-bold">
              <Leaf className="size-6" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-slate-50">EcoPulse AI</h1>
              <p className="text-xs text-emerald-400">
                Industrial Decarbonization &amp; Carbon Credit Intelligence
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-slate-300">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-2 border border-slate-700">
              <Building2 className="size-4 text-emerald-400" /> Plant M5 · Pune Works
            </span>
            <span className="num inline-flex items-center gap-1.5 rounded-lg bg-slate-800/80 px-3 py-2 border border-slate-700">
              <RefreshCw className="size-4 text-emerald-400" /> {summary.lastRun}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-6 px-5 py-6 lg:px-8">
        <KpiCards />
        <TelemetrySection />
        <RagInspector />
        <IncentivePanel />
        <ReportSection />
        <p className="pb-4 text-center text-xs text-slate-500">
          EcoPulse AI multi-agent pipeline · figures illustrative for screening purposes only
        </p>
      </main>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
