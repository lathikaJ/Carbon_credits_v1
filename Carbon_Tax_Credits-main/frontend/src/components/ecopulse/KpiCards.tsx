import { Activity, ArrowDownRight, ArrowUpRight, Coins, Factory, ShieldCheck, TriangleAlert } from "lucide-react";
import { summary } from "@/lib/ecopulse-data";
import { cn } from "@/lib/utils";

function Trend({ value, invert = false }: { value: number; invert?: boolean }) {
  const good = invert ? value > 0 : value < 0;
  const Icon = value < 0 ? ArrowDownRight : ArrowUpRight;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
        good ? "bg-success/15 text-success" : "bg-warning/15 text-warning",
      )}
    >
      <Icon className="size-3.5" />
      {Math.abs(value).toFixed(1)}%
    </span>
  );
}

function Shell({
  title,
  icon,
  children,
  footer,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  footer: React.ReactNode;
}) {
  return (
    <div className="surface-card p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted-foreground">{title}</p>
        <span className="grid size-9 place-items-center rounded-lg bg-accent text-accent-foreground">{icon}</span>
      </div>
      <div className="mt-4">{children}</div>
      <div className="mt-4 flex items-center gap-2 border-t border-border pt-3 text-xs text-muted-foreground">
        {footer}
      </div>
    </div>
  );
}

export function KpiCards() {
  const isPending = summary.complianceStatus === "PENDING_AUDIT";
  const confidencePct = Math.round(summary.confidenceScore * 100);

  return (
    <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Shell
        title="Plant Carbon Emissions"
        icon={<Factory className="size-4.5" />}
        footer={
          <>
            <Trend value={summary.emissionsTrendPct} /> <span>vs 30-day baseline (26 lines)</span>
          </>
        }
      >
        <p className="num text-3xl font-semibold">
          {summary.totalEmissionsKg.toLocaleString()}
          <span className="ml-1.5 text-base font-medium text-muted-foreground">kg CO₂ ({summary.totalEmissionsTons} tCO₂)</span>
        </p>
      </Shell>

      <Shell
        title="Potential Carbon Credits"
        icon={<Coins className="size-4.5" />}
        footer={
          <>
            <Trend value={summary.creditsTrendPct} invert /> <span>9 lines with reduction potential</span>
          </>
        }
      >
        <p className="num text-3xl font-semibold">
          {summary.potentialCreditsTco2e.toFixed(3)}
          <span className="ml-1.5 text-base font-medium text-muted-foreground">tCO₂e</span>
        </p>
      </Shell>

      <Shell
        title="Composite Confidence Score"
        icon={<Activity className="size-4.5" />}
        footer={<span className="text-amber-500 font-medium">Unmetered Proxy Cap: CS &le; 0.45</span>}
      >
        <div className="flex items-baseline justify-between">
          <p className="num text-3xl font-semibold text-amber-500">
            {confidencePct}
            <span className="ml-1 text-base font-medium">%</span>
          </p>
          <span className="rounded-full bg-amber-500/15 px-2.5 py-0.5 text-[10px] font-bold text-amber-600 dark:text-amber-400">
            LOW (PROXY CAP)
          </span>
        </div>
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-amber-500" style={{ width: `${confidencePct}%` }} />
        </div>
      </Shell>

      <Shell
        title="Compliance Status"
        icon={<TriangleAlert className="size-4.5 text-amber-500" />}
        footer={<span>Grid EF {summary.gridFactor} kg CO₂/kWh</span>}
      >
        <span
          className={cn(
            "inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-base font-bold tracking-wide",
            isPending ? "bg-amber-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/30" : "bg-success text-success-foreground",
          )}
        >
          <TriangleAlert className="size-4.5" />
          {summary.complianceStatus}
        </span>
        <p className="mt-2 text-xs text-muted-foreground">
          Pending physical line sub-meter audit
        </p>
      </Shell>
    </section>
  );
}
