import { cn } from "@/lib/utils";
import { scoreTier } from "@/lib/quiz";

const TIER_COLOR = {
  high: "text-emerald-500",
  mid: "text-amber-500",
  low: "text-red-500",
};

export function ScoreRing({ score, total }: { score: number; total: number }) {
  const pct = total > 0 ? Math.round((score / total) * 100) : 0;
  const tier = scoreTier(pct);
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="relative inline-flex size-24 items-center justify-center">
      <svg viewBox="0 0 96 96" className="size-24 -rotate-90">
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          strokeWidth="8"
          className="stroke-muted"
        />
        <circle
          cx="48"
          cy="48"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={cn("transition-all duration-500 ease-out", TIER_COLOR[tier], "stroke-current")}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-semibold">{pct}%</span>
        <span className="text-xs text-muted-foreground">
          {score}/{total}
        </span>
      </div>
    </div>
  );
}
