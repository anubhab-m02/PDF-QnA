import { cn } from "@/lib/utils";
import { scoreTier } from "@/lib/quiz";

const TIER_STYLE = {
  high: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400",
  mid: "bg-amber-500/15 text-amber-600 dark:text-amber-400",
  low: "bg-red-500/15 text-red-600 dark:text-red-400",
};

export function ScoreBadge({ score, total }: { score: number; total: number }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const tier = scoreTier(pct);

  return (
    <span className={cn("rounded-full px-2 py-0.5 text-xs font-medium", TIER_STYLE[tier])}>
      {score}/{total} ({pct}%)
    </span>
  );
}
