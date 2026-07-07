"use client";

import { ChevronDown, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ChatSession } from "@/lib/chat";

export function SessionSwitcher({
  sessions,
  activeSessionId,
  onSelect,
  onCreate,
}: {
  sessions: ChatSession[];
  activeSessionId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
}) {
  const active = sessions.find((s) => s.id === activeSessionId);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button variant="outline" size="sm">
            {active?.title ?? "Select session"}
            <ChevronDown className="size-4" />
          </Button>
        }
      />
      <DropdownMenuContent align="end">
        {sessions.map((session) => (
          <DropdownMenuItem key={session.id} onClick={() => onSelect(session.id)}>
            {session.title}
          </DropdownMenuItem>
        ))}
        {sessions.length > 0 && <DropdownMenuSeparator />}
        <DropdownMenuItem onClick={onCreate}>
          <Plus className="size-4" />
          New session
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
