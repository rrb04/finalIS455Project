"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

type Customer = {
  customer_id: number;
  full_name: string | null;
  email: string | null;
  city: string | null;
  state: string | null;
  customer_segment: string | null;
};

export default function Home() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selected, setSelected] = useState<number | "">("");
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/customers")
      .then(async (r) => {
        const d = await r.json();
        if (!r.ok) {
          setErr(d.error ?? `Request failed (${r.status})`);
          return;
        }
        setErr(null);
        setCustomers(d.customers ?? []);
      })
      .catch(() => setErr("Network error: could not reach /api/customers."));
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col gap-6 px-4 py-10">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Select customer</h1>
        <p className="mt-1 text-sm text-zinc-600">
          Pick who is placing an order (no login required for this demo).
        </p>
      </div>

      {err && (
        <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800">
          {err}
        </p>
      )}

      <label className="flex flex-col gap-2 text-sm font-medium text-zinc-800">
        Customer
        <select
          className="rounded-md border border-zinc-300 bg-white px-3 py-2 text-base font-normal"
          value={selected === "" ? "" : String(selected)}
          onChange={(e) =>
            setSelected(e.target.value === "" ? "" : Number(e.target.value))
          }
        >
          <option value="">Choose a customer…</option>
          {customers.map((c) => (
            <option key={c.customer_id} value={c.customer_id}>
              {c.full_name ?? `Customer ${c.customer_id}`} — {c.city}, {c.state}{" "}
              ({c.customer_segment})
            </option>
          ))}
        </select>
      </label>

      <div className="flex flex-wrap gap-3">
        <Link
          href={selected === "" ? "#" : `/order?customer_id=${selected}`}
          className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium text-white ${
            selected === ""
              ? "cursor-not-allowed bg-zinc-300"
              : "bg-zinc-900 hover:bg-zinc-800"
          }`}
          aria-disabled={selected === ""}
          onClick={(e) => {
            if (selected === "") e.preventDefault();
          }}
        >
          Place new order
        </Link>
        <Link
          href="/admin"
          className="inline-flex items-center justify-center rounded-md border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-800 hover:bg-zinc-100"
        >
          Administrator: order history
        </Link>
      </div>
    </main>
  );
}
