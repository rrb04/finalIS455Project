import { NextResponse } from "next/server";
import { apiErrorMessage } from "@/lib/apiError";
import { getSupabaseAdmin } from "@/lib/supabaseAdmin";

export async function GET() {
  try {
    const supabase = getSupabaseAdmin();
    const { data, error } = await supabase
      .from("customers")
      .select("customer_id, full_name, email, city, state, customer_segment")
      .order("customer_id");
    if (error) {
      console.error("GET /api/customers", error);
      return NextResponse.json({ error: apiErrorMessage(error) }, { status: 500 });
    }
    return NextResponse.json({ customers: data ?? [] });
  } catch (e) {
    console.error("GET /api/customers", e);
    return NextResponse.json({ error: apiErrorMessage(e) }, { status: 500 });
  }
}
