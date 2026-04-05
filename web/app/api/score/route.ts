import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabaseAdmin";

/**
 * Deployment-friendly risk scoring (no Python on Vercel).
 * Outputs 0–100 to match shop.db `risk_score` scale.
 * Train the real model in pipeline.ipynb; this keeps the live app working.
 */
const MAX_TOTAL = 2053.11;

function scoreRow(orderTotal: number, segment: string | null): number {
  const amt = Math.min(70, (orderTotal / MAX_TOTAL) * 70);
  const seg = (segment ?? "").toLowerCase();
  let segPart = 22;
  if (seg === "premium") segPart = 30;
  if (seg === "budget") segPart = 34;
  if (seg === "standard") segPart = 24;
  const raw = amt * 0.62 + segPart * 0.38;
  return Math.min(100, Math.max(0.1, Math.round(raw * 10) / 10));
}

export async function POST() {
  try {
    const supabase = getSupabaseAdmin();
    const { data: orders, error: oErr } = await supabase
      .from("orders")
      .select("order_id, customer_id, order_total");
    if (oErr) throw oErr;
    const { data: customers, error: cErr } = await supabase
      .from("customers")
      .select("customer_id, customer_segment");
    if (cErr) throw cErr;
    const segById = new Map(
      (customers ?? []).map((c) => [c.customer_id, c.customer_segment as string]),
    );

    const scored = (orders ?? []).map((o) => {
      const risk_score = scoreRow(
        Number(o.order_total),
        segById.get(o.customer_id) ?? null,
      );
      return {
        order_id: o.order_id,
        risk_score,
        needs_review: risk_score >= 42,
      };
    });

    scored.sort((a, b) => b.risk_score - a.risk_score);
    const withRank = scored.map((s, i) => ({
      ...s,
      priority_rank: i + 1,
      scored_at: new Date().toISOString(),
    }));

    for (const row of withRank) {
      const { error } = await supabase
        .from("orders")
        .update({
          risk_score: row.risk_score,
          needs_review: row.needs_review,
          priority_rank: row.priority_rank,
          scored_at: row.scored_at,
        })
        .eq("order_id", row.order_id);
      if (error) throw error;
    }

    return NextResponse.json({
      ok: true,
      updated: withRank.length,
      top: withRank.slice(0, 5),
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Scoring failed";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
