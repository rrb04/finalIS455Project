/**
 * Applies logistic coefficients stored by scripts/train_from_supabase.py.
 * Risk is probability of fraud × 100 (0–100), matching shop.db scale.
 */
export type MlScoringConfig = {
  version: number;
  intercept: number;
  scaler_mean: number;
  scaler_scale: number;
  coef_order_total: number;
  segment_coef: Record<string, number>;
  /** Probability above which an order is flagged for review (default 0.42). */
  review_threshold_prob?: number;
};

function sigmoid(x: number): number {
  if (x > 40) return 1;
  if (x < -40) return 0;
  return 1 / (1 + Math.exp(-x));
}

export function riskScoreFromConfig(
  orderTotal: number,
  segment: string | null,
  cfg: MlScoringConfig,
): { risk_score: number; needs_review: boolean } {
  const scale = cfg.scaler_scale || 1;
  const z = (orderTotal - cfg.scaler_mean) / scale;
  const seg = (segment ?? "").toLowerCase();
  const segCoef =
    cfg.segment_coef[seg] ??
    cfg.segment_coef["unknown"] ??
    cfg.segment_coef["other"] ??
    0;
  const logit =
    cfg.intercept + cfg.coef_order_total * z + segCoef;
  const p = sigmoid(logit);
  const risk_score = Math.min(
    99.9,
    Math.max(0.1, Math.round(p * 1000) / 10),
  );
  const needs_review = p >= (cfg.review_threshold_prob ?? 0.42);
  return { risk_score, needs_review };
}

export function isValidScoringConfig(raw: unknown): raw is MlScoringConfig {
  if (!raw || typeof raw !== "object") return false;
  const o = raw as Record<string, unknown>;
  return (
    o.version === 2 &&
    typeof o.intercept === "number" &&
    typeof o.scaler_mean === "number" &&
    typeof o.scaler_scale === "number" &&
    typeof o.coef_order_total === "number" &&
    typeof o.segment_coef === "object" &&
    o.segment_coef !== null
  );
}
