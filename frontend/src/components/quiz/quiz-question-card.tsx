import { cn } from "@/lib/utils";
import type { QuizQuestion } from "@/lib/quiz";

export function QuizQuestionCard({
  question,
  selectedIndex,
  onSelect,
  revealed,
}: {
  question: QuizQuestion;
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  revealed?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-lg font-medium">{question.question}</p>
      <div role="radiogroup" aria-label={question.question} className="flex flex-col gap-2">
        {question.options.map((option, i) => {
          const isSelected = selectedIndex === i;
          const isCorrect = revealed && i === question.answer_index;
          const isChosenWrong = revealed && isSelected && i !== question.answer_index;

          return (
            <button
              key={i}
              type="button"
              role="radio"
              aria-checked={isSelected}
              disabled={revealed}
              onClick={() => onSelect(i)}
              className={cn(
                "rounded-md border px-3 py-2 text-left text-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                isSelected && !revealed && "border-primary bg-primary/5",
                isCorrect && "border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
                isChosenWrong && "border-red-500 bg-red-500/10 text-red-700 dark:text-red-400",
                !isSelected && !isCorrect && !isChosenWrong && "border-border hover:bg-accent/50"
              )}
            >
              {option}
            </button>
          );
        })}
      </div>
      {revealed && (
        <p className="rounded-md bg-muted p-3 text-sm text-muted-foreground">
          {question.explanation}
        </p>
      )}
    </div>
  );
}
