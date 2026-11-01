import { BookOpenCheck, FileSearch, CircleCheckBig, Clock, ShieldAlert } from "lucide-react";
import { ragChunks } from "@/lib/ecopulse-data";
import { cn } from "@/lib/utils";

export function RagInspector() {
  return (
    <section className="surface-card">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <BookOpenCheck className="size-4.5 text-primary" />
          <h2 className="text-sm font-semibold uppercase tracking-[0.14em]">Agent 3: Policy &amp; Compliance RAG Inspector</h2>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-md bg-muted px-2.5 py-1 text-xs text-muted-foreground">
          <FileSearch className="size-3.5" /> Carbon Policies Vector Store · {ragChunks.length} chunks retrieved
        </span>
      </header>

      <div className="grid gap-4 p-5 lg:grid-cols-2 xl:grid-cols-4">
        {ragChunks.map((c) => {
          const verified = c.mandate === "VERIFIED";
          return (
            <article key={c.docId} className="flex flex-col justify-between rounded-xl border border-border bg-surface-2 p-4">
              <div>
                <div className="flex items-center justify-between">
                  <span className="num text-[11px] font-semibold text-primary">[DOC_ID: {c.docId}]</span>
                  <span className="text-[10px] font-mono rounded bg-accent px-1.5 py-0.5 text-accent-foreground">
                    RAG Vector
                  </span>
                </div>
                <h3 className="mt-1.5 text-xs font-bold leading-snug">{c.title}</h3>
                <p className="mt-2 text-xs leading-relaxed text-muted-foreground">{c.body}</p>
              </div>

              <div className="mt-4 space-y-2 border-t border-border/60 pt-3">
                <div className="flex items-center justify-between text-[11px] uppercase tracking-wider text-muted-foreground">
                  <span>Cosine Similarity</span>
                  <span className="num font-bold text-foreground">Score: {c.score.toFixed(2)}</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn("h-full rounded-full", c.score >= 0.85 ? "bg-success" : "bg-warning")}
                    style={{ width: `${c.score * 100}%` }}
                  />
                </div>
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-[10px] font-bold tracking-wide",
                    verified ? "bg-success/15 text-success" : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30",
                  )}
                >
                  {verified ? <CircleCheckBig className="size-3.5" /> : <ShieldAlert className="size-3.5" />}
                  MANDATE: {c.mandate}
                </span>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
