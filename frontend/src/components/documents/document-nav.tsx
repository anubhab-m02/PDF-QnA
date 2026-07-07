"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function DocumentNav({ documentId }: { documentId: number }) {
  const pathname = usePathname();

  const tabs = [
    { label: "Chat", href: `/documents/${documentId}/chat` },
    { label: "Quiz", href: `/documents/${documentId}/quiz` },
    { label: "Flashcards", href: `/documents/${documentId}/flashcards` },
  ];

  return (
    <nav className="flex gap-1 px-4 pt-2">
      {tabs.map((tab) => {
        const active = pathname === tab.href;
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "rounded-t-md px-3 py-1.5 text-sm font-medium transition-colors",
              active
                ? "border-x border-t bg-background text-foreground"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
