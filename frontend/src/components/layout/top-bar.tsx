"use client";

import { usePathname } from "next/navigation";
import { ThemeToggle } from "@/components/layout/theme-toggle";

function titleFromPathname(pathname: string): string {
  if (pathname.startsWith("/library")) return "Library";
  if (pathname.startsWith("/profile")) return "Profile";
  if (pathname.includes("/chat")) return "Chat";
  if (pathname.includes("/quiz")) return "Quiz";
  if (pathname.includes("/flashcards")) return "Flashcards";
  return "PDF-QnA";
}

export function TopBar() {
  const pathname = usePathname();

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b px-6">
      <h1 className="text-2xl font-semibold">{titleFromPathname(pathname)}</h1>
      <ThemeToggle />
    </header>
  );
}
