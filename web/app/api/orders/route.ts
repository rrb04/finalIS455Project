import { NextResponse } from "next/server";
import { apiErrorMessage } from "@/lib/apiError";
import { getSupabaseAdmin } from "@/lib/supabaseAdmin";

export async function GET() {
  try {
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("orders")
      .select(
        "order_id, customer_id, order_datetime, order_subtotal, shipping_fee, tax_amount, order_total, payment_method, shipping_state, risk_score, needs_review, priority_rank, scored_at",
      )
      .order("order_datetime", { ascending: false })
      .limit(200);
    if (error) throw error;
    return NextResponse.json({ orders: data ?? [] });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Failed to load orders";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const customerId = Number(body.customer_id);
    const orderSubtotal = Number(body.order_subtotal);
    const paymentMethod = String(body.payment_method ?? "card");
    const deviceType = String(body.device_type ?? "mobile");
    const ipCountry = String(body.ip_country ?? "US");
    const promoUsed = body.promo_used ? 1 : 0;
    const promoCode =
      typeof body.promo_code === "string" && body.promo_code.trim()
        ? body.promo_code.trim()
        : null;
    const billingZip = String(body.billing_zip ?? "00000");
    const shippingZip = String(body.shipping_zip ?? "00000");
    const shippingState = String(body.shipping_state ?? "US");

    if (!customerId || Number.isNaN(orderSubtotal) || orderSubtotal <= 0) {
      return NextResponse.json(
        { error: "customer_id and positive order_subtotal are required" },
        { status: 400 },
      );
    }

    const shippingFee = Number(body.shipping_fee ?? 9.99);
    const taxAmount = Number(
      body.tax_amount ?? Math.round(orderSubtotal * 0.08 * 100) / 100,
    );
    const orderTotal =
      Number(body.order_total) ||
      Math.round((orderSubtotal + shippingFee + taxAmount) * 100) / 100;

    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("orders")
      .insert({
        customer_id: customerId,
        order_datetime: new Date().toISOString(),
        billing_zip: billingZip,
        shipping_zip: shippingZip,
        shipping_state: shippingState,
        payment_method: paymentMethod,
        device_type: deviceType,
        ip_country: ipCountry,
        promo_used: promoUsed,
        promo_code: promoCode,
        order_subtotal: orderSubtotal,
        shipping_fee: shippingFee,
        tax_amount: taxAmount,
        order_total: orderTotal,
        risk_score: 0,
        is_fraud: 0,
      })
      .select("order_id")
      .single();
    if (error) {
      console.error("POST /api/orders", error);
      return NextResponse.json({ error: apiErrorMessage(error) }, { status: 500 });
    }
    return NextResponse.json({ ok: true, order_id: data.order_id });
  } catch (e) {
    console.error("POST /api/orders", e);
    return NextResponse.json({ error: apiErrorMessage(e) }, { status: 500 });
  }
}
