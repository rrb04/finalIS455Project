/** Supabase PostgREST errors are plain objects, not `Error` instances. */
export function apiErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  if (typeof err === "object" && err !== null && "message" in err) {
    const o = err as { message?: string; details?: string; hint?: string };
    const parts = [o.message, o.details, o.hint].filter(Boolean);
    if (parts.length) return parts.join(" — ");
  }
  return typeof err === "string" ? err : "Unknown error";
}
