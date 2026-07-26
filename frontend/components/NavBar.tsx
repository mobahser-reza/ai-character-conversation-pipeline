"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearToken } from "@/lib/api";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/characters", label: "Characters" },
  { href: "/voices", label: "Voices" },
  { href: "/api-keys", label: "API Keys" },
  { href: "/scripts", label: "Scripts" },
  { href: "/jobs", label: "Jobs" },
  { href: "/docs", label: "Docs" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav className="flex items-center justify-between border-b border-slate-800 px-6 py-4">
      <div className="flex gap-6">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`text-sm ${
              pathname === link.href ? "text-white font-semibold" : "text-slate-400 hover:text-slate-200"
            }`}
          >
            {link.label}
          </Link>
        ))}
      </div>
      <button
        onClick={() => {
          clearToken();
          window.location.href = "/login";
        }}
        className="text-sm text-slate-400 hover:text-red-400"
      >
        Log out
      </button>
    </nav>
  );
}
