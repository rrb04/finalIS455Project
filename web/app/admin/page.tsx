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

export default function AdminPage() {
  const [orders, setOrders] = useState<OrderRow[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [scoreMsg, setScoreMsg] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setErr(null);
    fetch("/api/orders")
      .then((r) => r.json())
      .then((d) => {
        if (d.error) setErr(d.error);
        else setOrders(d.orders ?? []);
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
            Administrator — order history
          </h1>
          <p className="mt-1 text-sm text-zinc-600">
            Risk scores use the same 0–100 scale as <code className="text-xs">shop.db</code>.
            Higher score = higher priority to verify before fulfilling.
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
        <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          {scoreMsg}
        </p>
      )}
      {err && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {err}
        </p>
      )}

      <section>
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-zinc-500">
          Priority queue (verify before fulfilling)
        </h2>
        <div className="overflow-x-auto rounded-lg border border-zinc-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-zinc-100 text-zinc-700">
              <tr>
                <th className="px-3 py-2">Rank</th>
                <th className="px-3 py-2">Order</th>
                <th className="px-3 py-2">Customer</th>
                <th className="px-3 py-2">Total</th>
                <th className="px-3 py-2">Risk score</th>
                <th className="px-3 py-2">Needs review</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-3 py-6 text-zinc-500">
                    Loading…
                  </td>
                </tr>
              ) : (
                queue.map((o) => (
                  <tr key={o.order_id} className="border-t border-zinc-100">
                    <td className="px-3 py-2">{o.priority_rank ?? "—"}</td>
                    <td className="px-3 py-2">{o.order_id}</td>
                    <td className="px-3 py-2">{o.customer_id}</td>
                    <td className="px-3 py-2">${Number(o.order_total).toFixed(2)}</td>
                    <td className="px-3 py-2">
                      {o.risk_score != null ? Number(o.risk_score).toFixed(1) : "—"}
                    </td>
                    <td className="px-3 py-2">
                      {o.needs_review ? (
                        <span className="rounded bg-red-100 px-2 py-0.5 text-red-800">
                          yes
                        </span>
                      ) : (
                        <span className="text-zinc-500">no</span>
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
