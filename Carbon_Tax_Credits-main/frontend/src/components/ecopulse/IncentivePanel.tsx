import { BadgeIndianRupee, Info, CircleCheckBig, CircleSlash, AlertTriangle } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { incentives } from "@/lib/ecopulse-data";
import { cn } from "@/lib/utils";

const split = [
  { name: "Financial Rebate Objective", value: 45.0 },
  { name: "Green Manufacturing Allowance", value: 30.0 },
  { name: "Accelerated Depreciation", value: 25.0 },
];
const palette = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)"];

export function IncentivePanel() {
  return (
    <section className="surface-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <BadgeIndianRupee className="size-4.5 text-primary" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Agent 4: Green Tax Incentive &amp; Financial Rebate Optimization</h2>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-amber-500/15 border border-amber-500/30 px-2.5 py-1 text-xs font-semibold text-amber-600 dark:text-amber-400">
          <AlertTriangle className="size-3.5" /> REQUIRES_LOCATION_CONFIRMATION (Rule 2)
        </span>
      </header>

      <div className="flex items-start gap-2.5 border-b border-amber-500/30 bg-amber-500/10 px-5 py-3">
        <Info className="mt-0.5 size-4 shrink-0 text-amber-500" />
        <p className="text-xs font-medium leading-relaxed text-amber-600 dark:text-amber-400">
          <strong>MANDATORY DISCLAIMER:</strong> ILLUSTRATIVE SCREENING ONLY -- NOT TAX ADVICE. Flags are based purely on operational KPI thresholds (OEE &ge; 85% and Carbon Intensity &lt; Plant Mean). Automated rebate issuance blocked until plant location is confirmed.
        </p>
      </div>

      <div className="grid gap-5 p-5 lg:grid-cols-3">
        <div className="space-y-3 lg:col-span-2">
          {incentives.map((i) => (
            <div
              key={i.name}
              className={cn(
                "flex flex-wrap items-center justify-between gap-3 rounded-xl border p-4",
                i.eligible ? "border-success/25 bg-success/8" : "border-amber-500/30 bg-amber-500/5",
              )}
            >
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  {i.eligible ? (
                    <CircleCheckBig className="size-4 text-success" />
                  ) : (
                    <CircleSlash className="size-4 text-amber-500" />
                  )}
                  <p className="text-xs font-bold">{i.name}</p>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{i.ref} · {i.basis}</p>
              </div>
              <span className={cn("num text-xs font-bold rounded-lg px-2.5 py-1", i.eligible ? "bg-success/15 text-success" : "bg-amber-500/15 text-amber-600 dark:text-amber-400")}>
                {i.value}
              </span>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-border bg-surface-2 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Rebate Objective Split</p>
          <div className="h-[190px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={split} dataKey="value" innerRadius={48} outerRadius={72} paddingAngle={3} stroke="none">
                  {split.map((_, idx) => (
                    <Cell key={idx} fill={palette[idx]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "0.6rem",
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <p className="num text-center text-xl font-bold">26 Lines Evaluated</p>
          <p className="text-center text-xs text-muted-foreground">Screening Candidate Status</p>
        </div>
      </div>
    </section>
  );
}
