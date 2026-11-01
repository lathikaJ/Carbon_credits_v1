import { useState } from "react";
import { Download, FileText, TriangleAlert, Info, Code, FileSpreadsheet } from "lucide-react";
import { toast } from "sonner";
import { auditNotices, reportSummary, summary } from "@/lib/ecopulse-data";
import { cn } from "@/lib/utils";

export function ReportSection() {
  const [activeTab, setActiveTab] = useState<"summary" | "json">("summary");

  const mockJsonPayload = {
    report_id: "REP-2026-07-001",
    reporting_period: "2026-07",
    audit_status: "AUDIT_VERIFIED",
    plant_total_co2_kg: summary.totalEmissionsKg,
    total_potential_credits_tco2e: summary.potentialCreditsTco2e,
    compliance_posture: "PENDING_PLANT_SUBMETER_AUDIT",
    composite_confidence_score: summary.confidenceScore,
    metered_status_guardrail: "is_metered=False (Cap: 0.45)",
    evaluated_lines_count: summary.evaluatedLinesCount,
    lines_with_reduction_potential: summary.linesWithReductionCount,
    audit_disclaimers: [
      "ILLUSTRATIVE ONLY. Actual credit issuance requires a registry-approved methodology and independent MRV verification.",
      "ILLUSTRATIVE SCREENING ONLY -- NOT TAX ADVICE. Flags are based purely on operational KPI thresholds.",
      "DATA STATUS: Proxy allocated energy telemetry (40% runtime, 35% output, 25% OEE). Physical line sub-meters recommended.",
    ],
  };

  const handleExport = () => {
    const element = document.createElement("a");
    const file = new Blob([reportSummary], { type: "text/markdown" });
    element.href = URL.createObjectURL(file);
    element.download = "executive_summary.md";
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success("Executive Markdown Summary exported", { description: "executive_summary.md downloaded" });
  };

  return (
    <section className="grid gap-4 xl:grid-cols-3">
      <div className="surface-card xl:col-span-2">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <FileText className="size-4.5 text-primary" />
              <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Agent 5: Executive Report Synthesis</h2>
            </div>
            <div className="flex rounded-lg bg-muted p-0.5 text-xs font-semibold">
              <button
                onClick={() => setActiveTab("summary")}
                className={cn("flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-all", activeTab === "summary" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground")}
              >
                <FileSpreadsheet className="size-3.5" /> Summary
              </button>
              <button
                onClick={() => setActiveTab("json")}
                className={cn("flex items-center gap-1.5 rounded-md px-2.5 py-1 transition-all", activeTab === "json" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground")}
              >
                <Code className="size-3.5" /> JSON Audit Schema
              </button>
            </div>
          </div>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground transition-opacity hover:opacity-90"
          >
            <Download className="size-3.5" />
            Export Markdown
          </button>
        </header>

        {activeTab === "summary" ? (
          <div className="space-y-3 p-5">
            {reportSummary.split("\n\n").map((p, i) => (
              <p key={i} className="text-xs leading-relaxed text-muted-foreground">
                {p}
              </p>
            ))}
            <div className="num flex flex-wrap gap-x-6 gap-y-1 border-t border-border pt-4 text-xs text-muted-foreground">
              <span>REPORT_ID: REP-2026-07-001</span>
              <span>CONFIDENCE: {summary.confidenceScore} (LOW)</span>
              <span>GRID EF: {summary.gridFactor} kg CO₂/kWh</span>
            </div>
          </div>
        ) : (
          <div className="p-5">
            <pre className="max-h-[300px] overflow-auto rounded-lg bg-surface-2 p-4 text-[11px] font-mono leading-relaxed text-foreground border border-border">
              {JSON.stringify(mockJsonPayload, null, 2)}
            </pre>
          </div>
        )}
      </div>

      <div className="surface-card">
        <header className="flex items-center gap-2 border-b border-border px-5 py-4">
          <TriangleAlert className="size-4.5 text-amber-500" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Mandatory Audit Notices</h2>
        </header>
        <ul className="space-y-3 p-5">
          {auditNotices.map((n, i) => {
            const warn = n.level === "WARNING";
            return (
              <li
                key={i}
                className={cn(
                  "flex gap-2.5 rounded-lg border p-3 text-xs leading-relaxed",
                  warn ? "border-amber-500/30 bg-amber-500/10 text-amber-600 dark:text-amber-400" : "border-info/30 bg-info/10 text-info",
                )}
              >
                {warn ? (
                  <TriangleAlert className="mt-0.5 size-4 shrink-0" />
                ) : (
                  <Info className="mt-0.5 size-4 shrink-0" />
                )}
                <span>
                  <strong className="font-semibold">{n.level}: </strong>
                  {n.text}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
