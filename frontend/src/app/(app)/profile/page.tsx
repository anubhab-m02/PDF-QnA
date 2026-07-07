"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, authHeaders, ApiError, NetworkError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { ProfileStats } from "@/lib/profile";

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <Card className="gap-1 p-4">
      <CardHeader className="p-0">
        <CardTitle className="text-xs font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent className="p-0 text-2xl font-semibold">{value}</CardContent>
    </Card>
  );
}

export default function ProfilePage() {
  const { token, user } = useAuth();
  const [stats, setStats] = useState<ProfileStats | null>(null);

  useEffect(() => {
    if (!token) return;
    (async () => {
      try {
        const data = await apiFetch<ProfileStats>("/api/profile/stats", {
          headers: authHeaders(token),
        });
        setStats(data);
      } catch (err) {
        if (err instanceof ApiError || err instanceof NetworkError) toast.error(err.message);
      }
    })();
  }, [token]);

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-8">
        <p className="text-lg font-medium">{user?.username}</p>

        {stats === null ? (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Documents" value={stats.ready_document_count} />
            <StatCard label="Quizzes taken" value={stats.quiz_attempt_count} />
            <StatCard
              label="Average score"
              value={
                stats.average_quiz_score_pct === null
                  ? "—"
                  : `${Math.round(stats.average_quiz_score_pct)}%`
              }
            />
            <StatCard label="Flashcard decks" value={stats.flashcard_deck_count} />
          </div>
        )}
      </div>
    </div>
  );
}
