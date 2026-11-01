import { useState } from "react";
import {
  Bar,
  CartesianGrid,
  Legend,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CircuitBoard, Gauge, Search } from "lucide-react";
import { emissionSeries, lines } from "@/lib/ecopulse-data";
import { cn } from "@/lib/utils";

function LineageBadge({ lineage }: { lineage: "METERED" | "ESTIMATED_PROXY" }) {
  const metered = lineage === "METERED";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-semibold tracking-wide",
        metered
          ? "border-success/30 bg-success/12 text-success"
          : "border-warning/35 bg-warning/12 text-warning",
      )}
    >
      {lineage}
    </span>
  );
}

const tooltipStyle = {
  backgroundColor: "var(--popover)",
  border: "1px solid var(--border)",
  borderRadius: "0.6rem",
  color: "var(--popover-foreground)",
  fontSize: 12,
};

export function TelemetrySection() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredLines = lines.filter(
    (l) =>
      l.line.toLowerCase().includes(searchTerm.toLowerCase()) ||
      l.product.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <section className="grid gap-4 xl:grid-cols-5">
      <div className="surface-card xl:col-span-3">
        <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
          <div className="flex items-center gap-2">
            <CircuitBoard className="size-4.5 text-primary" />
            <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Line-by-Line Telemetry (26 Lines)</h2>
          </div>
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search line or product..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="h-8 rounded-lg border border-border bg-background pl-8 pr-3 text-xs outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
        </header>
        <div className="max-h-[380px] overflow-y-auto overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-background border-b border-border text-left text-[11px] uppercase tracking-wider text-muted-foreground z-10">
              <tr>
                <th className="px-5 py-3 font-semibold">Line</th>
                <th className="px-3 py-3 font-semibold">Energy (kWh)</th>
                <th className="px-3 py-3 font-semibold">CO₂ (kg)</th>
                <th className="px-3 py-3 font-semibold">CI / unit</th>
                <th className="px-3 py-3 font-semibold">OEE</th>
                <th className="px-5 py-3 font-semibold">Lineage</th>
              </tr>
            </thead>
            <tbody>
              {filteredLines.map((l) => (
                <tr key={l.line} className="border-b border-border/60 last:border-0 hover:bg-muted/40">
                  <td className="px-5 py-2.5">
                    <p className="num font-semibold">{l.line}</p>
                    <p className="text-xs text-muted-foreground">{l.product}</p>
                  </td>
                  <td className="num px-3 py-2.5">{l.energyKwh.toLocaleString()}</td>
                  <td className="num px-3 py-2.5">{l.co2Kg.toLocaleString()}</td>
                  <td className="num px-3 py-2.5">
                    <span className={cn(l.ci > 0.45 ? "text-warning font-semibold" : "text-success")}>{l.ci.toFixed(3)}</span>
                  </td>
                  <td className="num px-3 py-2.5">{l.oee.toFixed(1)}%</td>
                  <td className="px-5 py-2.5">
                    <LineageBadge lineage={l.lineage} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="surface-card xl:col-span-2">
        <header className="flex items-center gap-2 border-b border-border px-5 py-4">
          <Gauge className="size-4.5 text-primary" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Emissions vs Baseline (kg CO₂)</h2>
        </header>
        <div className="h-[360px] p-4">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={emissionSeries.slice(0, 10)} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
              <XAxis dataKey="line" tick={{ fontSize: 10, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "var(--muted-foreground)" }} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "var(--muted)", opacity: 0.4 }} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="actual" name="Actual CO₂ (kg)" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="baseline" name="Baseline (kg)" fill="var(--chart-4)" opacity={0.4} radius={[4, 4, 0, 0]} />
              <Line type="monotone" dataKey="actual" name="Trend" stroke="var(--chart-3)" strokeWidth={2} dot={false} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}
