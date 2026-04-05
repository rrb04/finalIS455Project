import { NextResponse } from "next/server";
import { apiErrorMessage } from "@/lib/apiError";
import { getSupabaseAdmin } from "@/lib/supabaseAdmin";
import {
  isValidScoringConfig,
  riskScoreFromConfig,
} from "@/lib/scoringFromConfig";

/**
 * Risk scoring without Python on Vercel.
 * If `ml_scoring_config` has a row (from daily `train_from_supabase.py`), uses
 * those logistic coefficients; otherwise falls back to a static heuristic.
 */
const MAX_TOTAL = 2053.11;

function scoreRowHeuristic(orderTotal: number, segment: string | null): number {
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

    const { data: cfgRow, error: cfgErr } = await supabase
      .from("ml_scoring_config")
      .select("config")
      .eq("id", 1)
      .maybeSingle();
    let mlCfg: unknown;
    if (cfgErr) {
      const hint = apiErrorMessage(cfgErr);
      if (/does not exist|schema cache|Could not find the table/i.test(hint)) {
        console.warn("POST /api/score: ml_scoring_config unavailable, using heuristic:", hint);
      } else {
        console.error("POST /api/score ml_scoring_config", cfgErr);
        return NextResponse.json({ error: hint }, { status: 500 });
      }
    } else {
      mlCfg = cfgRow?.config;
    }

    const { data: orders, error: oErr } = await supabase
      .from("orders")
      .select("order_id, customer_id, order_total");
    if (oErr) {
      console.error("POST /api/score orders", oErr);
      return NextResponse.json({ error: apiErrorMessage(oErr) }, { status: 500 });
    }
    const { data: customers, error: cErr } = await supabase
      .from("customers")
      .select("customer_id, customer_segment");
    if (cErr) {
      console.error("POST /api/score customers", cErr);
      return NextResponse.json({ error: apiErrorMessage(cErr) }, { status: 500 });
    }
    const segById = new Map(
      (customers ?? []).map((c) => [c.customer_id, c.customer_segment as string]),
    );

    const scored = (orders ?? []).map((o) => {
      const total = Number(o.order_total);
      const segment = segById.get(o.customer_id) ?? null;
      if (isValidScoringConfig(mlCfg)) {
        const { risk_score, needs_review } = riskScoreFromConfig(
          total,
          segment,
          mlCfg,
        );
        return { order_id: o.order_id, risk_score, needs_review };
      }
      const risk_score = scoreRowHeuristic(total, segment);
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
      if (error) {
        console.error("POST /api/score update", error);
        return NextResponse.json({ error: apiErrorMessage(error) }, { status: 500 });
      }
    }

    return NextResponse.json({
      ok: true,
      updated: withRank.length,
      top: withRank.slice(0, 5),
    });
  } catch (e) {
    console.error("POST /api/score", e);
    return NextResponse.json({ error: apiErrorMessage(e) }, { status: 500 });
  }
}
