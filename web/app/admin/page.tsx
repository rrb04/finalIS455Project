"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type OrderRow = {
  order_id: number;
  customer_id: number;
  order_datetime: string;
  order_subtotal: number;
  shipping_fee: number;
  tax_amount: number;
  order_total: number;
  payment_method: string | null;
  shipping_state: string | null;
  risk_score: number | null;
  needs_review: boolean | null;
  priority_rank: number | null;
  scored_at: string | null;
};

type CustomerRow = { customer_id: number; full_name: string | null };

type SortColumn = "rank" | "order" | "customer" | "total" | "risk" | "review";
type SortDirection = "asc" | "desc";

/** First click on a column uses this direction (rank asc = priority queue: 1 first). */
const DEFAULT_SORT_DIRECTION: Record<SortColumn, SortDirection> = {
  rank: "asc",
  order: "desc",
  customer: "asc",
  total: "desc",
  risk: "desc",
  review: "desc",
};

/** Same rule as batch scoring: prob >= 0.42 → risk display >= 42 (see scripts/score_supabase_orders.py). */
function orderNeedsReview(o: OrderRow): boolean {
  const r = o.risk_score != null ? Number(o.risk_score) : NaN;
  if (!Number.isNaN(r) && r >= 42) return true;
  return o.needs_review === true;
}

function compareOrders(
  a: OrderRow,
  b: OrderRow,
  column: SortColumn,
  direction: SortDirection,
  customerName: (id: number) => string,
): number {
  const mult = direction === "asc" ? 1 : -1;
  let cmp = 0;

  switch (column) {
    case "rank": {
      const va = a.priority_rank ?? 999_999;
      const vb = b.priority_rank ?? 999_999;
      cmp = va - vb;
      break;
    }
    case "order": {
      cmp = a.order_id - b.order_id;
      break;
    }
    case "customer": {
      const sa = customerName(a.customer_id).toLowerCase();
      const sb = customerName(b.customer_id).toLowerCase();
      cmp = sa.localeCompare(sb, undefined, { sensitivity: "base" });
      break;
    }
    case "total": {
      cmp = Number(a.order_total) - Number(b.order_total);
      break;
    }
    case "risk": {
      const ra =
        a.risk_score != null && !Number.isNaN(Number(a.risk_score))
          ? Number(a.risk_score)
          : null;
      const rb =
        b.risk_score != null && !Number.isNaN(Number(b.risk_score))
          ? Number(b.risk_score)
          : null;
      if (ra === null && rb === null) return 0;
      if (ra === null) return 1;
      if (rb === null) return -1;
      return (ra - rb) * mult;
    }
    case "review": {
      const na = orderNeedsReview(a) ? 1 : 0;
      const nb = orderNeedsReview(b) ? 1 : 0;
      cmp = na - nb;
      break;
    }
  }

  return cmp * mult;
}

export default function AdminPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [customersById, setCustomersById] = useState<Map<number, string>>(
    new Map(),
  );
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [scoreMsg, setScoreMsg] = useState<string | null>(null);
  const [sortColumn, setSortColumn] = useState<SortColumn>("rank");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  const load = useCallback(() => {
    setLoading(true);
    setErr(null);
    Promise.all([
      fetch("/api/orders").then((r) => r.json()),
      fetch("/api/customers").then((r) => r.json()),
    ])
      .then(([ordersJson, custJson]) => {
        if (ordersJson.error) setErr(ordersJson.error);
        else setOrders(ordersJson.orders ?? []);
        if (!custJson.error && Array.isArray(custJson.customers)) {
          const m = new Map<number, string>();
          for (const c of custJson.customers as CustomerRow[]) {
            m.set(
              c.customer_id,
              c.full_name?.trim() || `Customer #${c.customer_id}`,
            );
          }
          setCustomersById(m);
        }
      })
      .catch(() => setErr("Could not load orders."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function runScoring() {
    setScoring(true);
    setScoreMsg(null);
    setErr(null);
    try {
      const res = await fetch("/api/score", { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Scoring failed");
      setScoreMsg(`Scoring finished. Updated ${data.updated} orders.`);
      await load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Scoring failed");
    } finally {
      setScoring(false);
    }
  }

  const customerName = useCallback(
    (id: number) => customersById.get(id)?.trim() || `Customer #${id}`,
    [customersById],
  );

  const sortedOrders = useMemo(() => {
    const arr = [...orders];
    arr.sort((a, b) => {
      const c = compareOrders(a, b, sortColumn, sortDirection, customerName);
      if (c !== 0) return c;
      return a.order_id - b.order_id;
    });
    return arr;
  }, [orders, sortColumn, sortDirection, customerName]);

  const onSortHeaderClick = useCallback((col: SortColumn) => {
    if (col === sortColumn) {
      setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortColumn(col);
      setSortDirection(DEFAULT_SORT_DIRECTION[col]);
    }
  }, [sortColumn]);

  const sortHint = useMemo(() => {
    const labels: Record<SortColumn, string> = {
      rank: "Rank",
      order: "Order #",
      customer: "Customer",
      total: "Total",
      risk: "Risk",
      review: "Review",
    };
    return `${labels[sortColumn]} · ${sortDirection === "asc" ? "ascending" : "descending"}`;
  }, [sortColumn, sortDirection]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-4 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Administrator — fraud review queue
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            Risk is on a 0–100 scale (higher = more suspicious). New orders are
            saved first; scores are filled when you run the model below.
          </p>
        </div>
        <button
          type="button"
          onClick={runScoring}
          disabled={scoring}
          className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-60"
        >
          {scoring ? "Running…" : "Run scoring"}
        </button>
      </div>

      {scoreMsg && (
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm font-medium text-amber-950 tabular-nums">
          {scoreMsg}
        </p>
      )}
      {err && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {err}
        </p>
      )}

      <section
        className="rounded-lg border border-zinc-200 bg-zinc-50 px-4 py-3 text-sm text-zinc-800"
        aria-labelledby="how-it-works-heading"
      >
        <h2 id="how-it-works-heading" className="font-semibold text-zinc-900">
          How this page works
        </h2>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-zinc-700">
          <li>
            <strong>Place orders</strong> from the home page — each order is
            stored with a placeholder risk score until you score.
          </li>
          <li>
            <strong>Run scoring</strong> applies the latest fraud model (from
            Supabase <code className="text-xs">ml_scoring_config</code> when
            present, otherwise a simple rule). It updates every order&apos;s
            risk, review flag, and rank.
          </li>
          <li>
            <strong>Priority queue</strong> lists orders by rank (1 = highest
            risk). &quot;Needs review&quot; flags cases to check before
            shipping. Ranks show &quot;—&quot; until you&apos;ve run scoring at
            least once.
          </li>
        </ol>
        <p className="mt-2 text-xs text-zinc-600">
          Training new model weights is separate (e.g. GitHub Actions); this
          button only <em>applies</em> the saved model to orders.
        </p>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
          Order history —{" "}
          <span className="normal-case text-zinc-600 dark:text-zinc-300">
            {sortHint}
            {sortColumn === "rank" && sortDirection === "asc" ? (
              <span className="block text-xs font-normal normal-case text-zinc-500 dark:text-zinc-500">
                Priority queue: rank 1 = highest risk (review first)
              </span>
            ) : null}
          </span>
        </h2>
        <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm dark:border-zinc-800 dark:bg-zinc-950">
          <table className="min-w-full text-left text-base text-zinc-900 dark:text-zinc-100">
            <thead className="bg-zinc-100 text-xs font-semibold uppercase tracking-wide text-zinc-600 dark:bg-zinc-900 dark:text-zinc-400">
              <tr>
                {(
                  [
                    {
                      id: "rank" as const,
                      label: "Rank",
                      align: "right" as const,
                    },
                    {
                      id: "order" as const,
                      label: "Order #",
                      align: "right" as const,
                    },
                    {
                      id: "customer" as const,
                      label: "Customer",
                      align: "left" as const,
                    },
                    {
                      id: "total" as const,
                      label: "Total",
                      align: "right" as const,
                    },
                    {
                      id: "risk" as const,
                      label: "Risk",
                      align: "right" as const,
                    },
                    {
                      id: "review" as const,
                      label: "Review",
                      align: "center" as const,
                    },
                  ] as const
                ).map((col) => {
                  const active = sortColumn === col.id;
                  const caret = active
                    ? sortDirection === "asc"
                      ? "↑"
                      : "↓"
                    : "";
                  return (
                    <th
                      key={col.id}
                      scope="col"
                      aria-sort={
                        active
                          ? sortDirection === "asc"
                            ? "ascending"
                            : "descending"
                          : "none"
                      }
                      className={`px-2 py-2 sm:px-4 sm:py-3 ${
                        col.align === "right"
                          ? "text-right"
                          : col.align === "center"
                            ? "text-center"
                            : "text-left"
                      }`}
                    >
                      <button
                        type="button"
                        onClick={() => onSortHeaderClick(col.id)}
                        className={`inline-flex w-full min-w-0 items-center gap-1 rounded-md px-1.5 py-1 text-left transition-colors hover:bg-zinc-200/80 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-amber-600 dark:hover:bg-zinc-800 ${
                          col.align === "right"
                            ? "justify-end"
                            : col.align === "center"
                              ? "justify-center"
                              : "justify-start"
                        } ${active ? "text-zinc-900 dark:text-zinc-100" : ""}`}
                      >
                        <span>{col.label}</span>
                        <span
                          className="inline-flex w-4 shrink-0 justify-center font-normal tabular-nums text-amber-700 dark:text-amber-500"
                          aria-hidden
                        >
                          {active ? caret : "\u00a0"}
                        </span>
                      </button>
                    </th>
                  );
                })}
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {loading ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-4 py-6 text-zinc-500 dark:text-zinc-400"
                  >
                    Loading…
                  </td>
                </tr>
              ) : (
                sortedOrders.map((o) => (
                  <tr
                    key={o.order_id}
                    className="border-t border-zinc-100 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-zinc-900/60"
                  >
                    <td className="px-4 py-3 text-right align-middle">
                      <span className="inline-block min-w-[2rem] text-lg font-bold text-zinc-950">
                        {o.priority_rank ?? "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right align-middle">
                      <span className="text-lg font-semibold text-zinc-950">
                        {o.order_id}
                      </span>
                    </td>
                    <td className="px-4 py-3 align-middle">
                      <span className="font-medium text-zinc-900">
                        {customersById.get(o.customer_id) ?? "—"}
                      </span>
                      <span className="mt-0.5 block text-sm font-semibold tabular-nums text-zinc-600">
                        ID {o.customer_id}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right align-middle">
                      <span className="text-lg font-semibold text-zinc-950">
                        ${Number(o.order_total).toFixed(2)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right align-middle">
                      <span
                        className={`inline-block min-w-[3.25rem] text-xl font-bold ${
                          o.risk_score != null && Number(o.risk_score) >= 42
                            ? "text-amber-700"
                            : "text-zinc-950"
                        }`}
                      >
                        {o.risk_score != null
                          ? Number(o.risk_score).toFixed(1)
                          : "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center align-middle">
                      {orderNeedsReview(o) ? (
                        <span className="inline-block min-w-[2.5rem] rounded-md bg-red-100 px-2.5 py-1 text-sm font-bold text-red-900">
                          Yes
                        </span>
                      ) : (
                        <span className="text-sm font-semibold text-zinc-500">
                          No
                        </span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
