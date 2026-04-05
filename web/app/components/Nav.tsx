import Link from "next/link";

export function Nav() {
  return (
    <header className="border-b border-zinc-200 bg-white">
      <div className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3">
        <Link href="/" className="font-semibold text-zinc-900">
          Shop Ops
        </Link>
        <nav className="flex gap-4 text-sm text-zinc-600">
          <Link href="/" className="hover:text-zinc-900">
            Select customer
          </Link>
          <Link href="/order" className="hover:text-zinc-900">
            New order
          </Link>
          <Link href="/admin" className="hover:text-zinc-900">
            Admin / history
          </Link>
        </nav>
      </div>
    </header>
  );
}
