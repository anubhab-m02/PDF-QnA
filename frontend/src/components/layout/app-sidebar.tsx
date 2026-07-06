import { FileStack, LayoutGrid, User } from "lucide-react";
import { NavLink } from "@/components/layout/nav-link";

export function AppSidebar() {
  return (
    <aside className="flex h-full w-60 shrink-0 flex-col border-r bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 border-b px-4">
        <FileStack className="size-5 text-primary" />
        <span className="font-semibold">PDF-QnA</span>
      </div>

      <nav className="flex flex-col gap-1 p-3">
        <NavLink href="/library" label="Library" icon={<LayoutGrid className="size-4" />} />
        <NavLink href="/profile" label="Profile" icon={<User className="size-4" />} />
      </nav>

      <div className="flex-1 overflow-y-auto px-3">
        <p className="px-3 pt-4 text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Current document
        </p>
        <p className="px-3 pt-2 text-sm text-muted-foreground">
          Select a document from your library to chat, quiz, or study flashcards.
        </p>
      </div>

      <div className="border-t p-3">
        <div className="rounded-md px-3 py-2 text-sm text-muted-foreground">
          Not signed in
        </div>
      </div>
    </aside>
  );
}
