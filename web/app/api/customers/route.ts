import { NextResponse } from "next/server";
import { getSupabaseAdmin } from "@/lib/supabaseAdmin";

export async function GET() {
  try {
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("customers")
      .select("customer_id, full_name, email, city, state, customer_segment")
      .order("customer_id");
    if (error) throw error;
    return NextResponse.json({ customers: data ?? [] });
  } catch (e) {
    const msg = e instanceof Error ? e.message : "Failed to load customers";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
