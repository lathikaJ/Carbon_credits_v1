import { createFileRoute } from "@tanstack/react-router";
import { Leaf, RefreshCw, Building2 } from "lucide-react";
import { KpiCards } from "@/components/ecopulse/KpiCards";
import { TelemetrySection } from "@/components/ecopulse/TelemetrySection";
import { RagInspector } from "@/components/ecopulse/RagInspector";
import { IncentivePanel } from "@/components/ecopulse/IncentivePanel";
import { ReportSection } from "@/components/ecopulse/ReportSection";
import { summary } from "@/lib/ecopulse-data";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "EcoPulse AI — Industrial Decarbonization Dashboard" },
      {
        name: "description",
        content:
          "Executive dashboard for industrial carbon emissions, carbon credit headroom, policy RAG compliance and green tax incentive screening.",
      },
      { property: "og:title", content: "EcoPulse AI — Industrial Decarbonization Dashboard" },
      {
        property: "og:description",
        content:
          "Multi-agent carbon intelligence: line-level emissions telemetry, policy compliance retrieval, credit monetization and audit-ready reporting.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  return (
    <div className="min-h-screen bg-background">
      <header className="hero-gradient border-b border-border">
        <div className="mx-auto flex max-w-[1500px] flex-wrap items-center justify-between gap-4 px-5 py-6 lg:px-8">
          <div className="flex items-center gap-3">
            <span className="grid size-11 place-items-center rounded-xl bg-primary text-primary-foreground">
              <Leaf className="size-6" />
            </span>
            <div>
              <h1 className="text-xl font-bold text-primary-foreground/95">EcoPulse AI</h1>
              <p className="text-xs text-primary-foreground/70">
                Industrial Decarbonization &amp; Carbon Credit Intelligence
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 text-xs text-primary-foreground/80">
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-primary-foreground/10 px-3 py-2">
              <Building2 className="size-4" /> Plant M5 · Pune Works
            </span>
            <span className="num inline-flex items-center gap-1.5 rounded-lg bg-primary-foreground/10 px-3 py-2">
              <RefreshCw className="size-4" /> {summary.lastRun}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1500px] space-y-5 px-5 py-6 lg:px-8">
        <KpiCards />
        <TelemetrySection />
        <RagInspector />
        <IncentivePanel />
        <ReportSection />
        <p className="pb-4 text-center text-xs text-muted-foreground">
          EcoPulse AI multi-agent pipeline · figures illustrative for screening purposes only
        </p>
      </main>
    </div>
  );
}
