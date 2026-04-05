import Link from "next/link";

export function Nav() {
  return (
    <header className="border-b border-zinc-200 bg-white dark:border-zinc-800 dark:bg-zinc-900">
      <div className="mx-auto flex max-w-3xl items-center gap-6 px-4 py-3">
        <Link
          href="/"
          className="font-semibold text-zinc-900 dark:text-zinc-100"
        >
          Shop Ops
        </Link>
        <nav className="flex gap-4 text-sm text-zinc-600 dark:text-zinc-400">
          <Link href="/" className="hover:text-zinc-900 dark:hover:text-zinc-100">
            Select customer
          </Link>
          <Link
            href="/order"
            className="hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            New order
          </Link>
          <Link
            href="/admin"
            className="hover:text-zinc-900 dark:hover:text-zinc-100"
          >
            Admin / history
          </Link>
        </nav>
      </div>
    </header>
  );
}
