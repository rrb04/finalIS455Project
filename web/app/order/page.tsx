"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

function OrderForm() {
  const search = useSearchParams();
  const initialId = search.get("customer_id") ?? "";

  const [customerId, setCustomerId] = useState(initialId);
  const [orderSubtotal, setOrderSubtotal] = useState("99.00");
  const [paymentMethod, setPaymentMethod] = useState("card");
  const [deviceType, setDeviceType] = useState("mobile");
  const [ipCountry, setIpCountry] = useState("US");
  const [shippingZip, setShippingZip] = useState("");
  const [billingZip, setBillingZip] = useState("");
  const [shippingState, setShippingState] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setMsg(null);
    setLoading(true);
    try {
      const payload: Record<string, unknown> = {
        customer_id: Number(customerId),
        order_subtotal: Number(orderSubtotal),
        payment_method: paymentMethod,
        device_type: deviceType,
        ip_country: ipCountry,
      };
      if (shippingZip.trim()) payload.shipping_zip = shippingZip.trim();
      if (billingZip.trim()) payload.billing_zip = billingZip.trim();
      if (shippingState.trim()) payload.shipping_state = shippingState.trim();

      const res = await fetch("/api/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Save failed");
      setMsg(`Order #${data.order_id} saved.`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">New order</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Matches <code className="text-xs">shop.db</code> columns: subtotal, fees/tax
          computed on the server unless you add overrides later.
        </p>
      </div>

      <form onSubmit={submit} className="flex flex-col gap-4">
        <label className="flex flex-col gap-1 text-sm font-medium">
          Customer ID
          <input
            required
            type="number"
            min={1}
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={customerId}
            onChange={(e) => setCustomerId(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Order subtotal (before tax &amp; shipping)
          <input
            required
            step="0.01"
            type="number"
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={orderSubtotal}
            onChange={(e) => setOrderSubtotal(e.target.value)}
          />
        </label>
        <p className="text-xs text-zinc-500">
          Default: shipping $9.99, tax 8% of subtotal, total = subtotal + shipping + tax.
        </p>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Payment method
          <select
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
          >
            <option value="card">card</option>
            <option value="paypal">paypal</option>
            <option value="bank">bank</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Device type
          <select
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={deviceType}
            onChange={(e) => setDeviceType(e.target.value)}
          >
            <option value="mobile">mobile</option>
            <option value="desktop">desktop</option>
            <option value="tablet">tablet</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          IP country (ISO)
          <input
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={ipCountry}
            onChange={(e) => setIpCountry(e.target.value)}
            maxLength={2}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Shipping ZIP (optional)
          <input
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={shippingZip}
            onChange={(e) => setShippingZip(e.target.value)}
            placeholder="defaults to 00000"
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Billing ZIP (optional)
          <input
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={billingZip}
            onChange={(e) => setBillingZip(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1 text-sm font-medium">
          Shipping state (optional)
          <input
            className="rounded-md border border-zinc-300 px-3 py-2"
            value={shippingState}
            onChange={(e) => setShippingState(e.target.value)}
            placeholder="e.g. CO"
            maxLength={2}
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="mt-2 rounded-md bg-zinc-900 px-4 py-2 text-sm font-medium text-white hover:bg-zinc-800 disabled:opacity-60"
        >
          {loading ? "Saving…" : "Save order"}
        </button>
      </form>

      {msg && (
        <p className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-900">
          {msg}
        </p>
      )}
      {err && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {err}
        </p>
      )}
    </main>
  );
}

export default function OrderPage() {
  return (
    <Suspense fallback={<main className="p-10 text-sm text-zinc-600">Loading…</main>}>
      <OrderForm />
    </Suspense>
  );
}
