"use client";

import { useCallback, useEffect, useState } from "react";

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

export default function AdminPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [customersById, setCustomersById] = useState<Map<number, string>>(
    new Map(),
  );
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [scoreMsg, setScoreMsg] = useState<string | null>(null);

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

  const queue = [...orders].sort((a, b) => {
    const pa = a.priority_rank ?? 999999;
    const pb = b.priority_rank ?? 999999;
    return pa - pb;
  });

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
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          All orders — sorted by review priority (lowest rank = check first)
        </h2>
        <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white shadow-sm">
          <table className="min-w-full text-left text-base text-zinc-900">
            <thead className="bg-zinc-100 text-xs font-semibold uppercase tracking-wide text-zinc-600">
              <tr>
                <th className="px-4 py-3 text-right">Rank</th>
                <th className="px-4 py-3 text-right">Order #</th>
                <th className="px-4 py-3 text-left">Customer</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-right">Risk</th>
                <th className="px-4 py-3 text-center">Review</th>
              </tr>
            </thead>
            <tbody className="tabular-nums">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-zinc-500">
                    Loading…
                  </td>
                </tr>
              ) : (
                queue.map((o) => (
                  <tr
                    key={o.order_id}
                    className="border-t border-zinc-100 hover:bg-zinc-50/80"
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
                      {o.needs_review ? (
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
