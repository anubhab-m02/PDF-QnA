"use client";

import { use, useEffect, useState } from "react";
import { toast } from "sonner";
import { DocumentNav } from "@/components/documents/document-nav";
import { QuizQuestionCard } from "@/components/quiz/quiz-question-card";
import { ScoreRing } from "@/components/quiz/score-ring";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { apiFetch, authHeaders, ApiError, NetworkError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Quiz, QuizAttempt } from "@/lib/quiz";

type ViewState = "idle" | "generating" | "taking" | "results";

export default function DocumentQuizPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const documentId = Number(id);
  const { token } = useAuth();

  const [view, setView] = useState<ViewState>("idle");
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [activeQuiz, setActiveQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [loadingList, setLoadingList] = useState(true);

  useEffect(() => {
    if (!token || Number.isNaN(documentId)) return;
    (async () => {
      try {
        const list = await apiFetch<Quiz[]>(
          `/api/quizzes?document_id=${documentId}`,
          { headers: authHeaders(token) }
        );
        setQuizzes(list);
      } catch (err) {
        if (err instanceof ApiError || err instanceof NetworkError) toast.error(err.message);
      } finally {
        setLoadingList(false);
      }
    })();
  }, [token, documentId]);

  async function generateQuiz() {
    if (!token) return;
    setView("generating");
    try {
      const quiz = await apiFetch<Quiz>(`/api/documents/${documentId}/quizzes`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ num_questions: 5 }),
      });
      setQuizzes((prev) => [quiz, ...prev]);
      startQuiz(quiz);
    } catch (err) {
      setView("idle");
      if (err instanceof ApiError || err instanceof NetworkError) {
        toast.error(err.message);
      } else {
        toast.error("Failed to generate quiz");
      }
    }
  }

  function startQuiz(quiz: Quiz) {
    setActiveQuiz(quiz);
    setAnswers(new Array(quiz.questions.length).fill(null));
    setCurrentIndex(0);
    setAttempt(null);
    setView("taking");
  }

  function selectAnswer(index: number) {
    setAnswers((prev) => {
      const next = [...prev];
      next[currentIndex] = index;
      return next;
    });
  }

  async function submitQuiz() {
    if (!token || !activeQuiz) return;
    try {
      const result = await apiFetch<QuizAttempt>(`/api/quizzes/${activeQuiz.id}/attempts`, {
        method: "POST",
        headers: authHeaders(token),
        body: JSON.stringify({ answers: answers.map((a) => a ?? -1) }),
      });
      setAttempt(result);
      setView("results");
    } catch (err) {
      if (err instanceof ApiError || err instanceof NetworkError) {
        toast.error(err.message);
      } else {
        toast.error("Failed to submit quiz");
      }
    }
  }

  const currentQuestion = activeQuiz?.questions[currentIndex];
  const isLastQuestion = activeQuiz ? currentIndex === activeQuiz.questions.length - 1 : false;

  return (
    <div className="h-full overflow-y-auto">
      <DocumentNav documentId={documentId} />
      <div className="mx-auto max-w-2xl px-6 py-8">
        {view === "idle" && (
          <div className="flex flex-col gap-6">
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <p className="text-lg font-medium">Test your knowledge</p>
              <p className="text-sm text-muted-foreground">
                Generate a quiz from this document to check your understanding
              </p>
              <Button onClick={generateQuiz}>Generate quiz</Button>
            </div>

            {!loadingList && quizzes.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-sm font-medium text-muted-foreground">Previous quizzes</p>
                <div className="flex flex-col divide-y rounded-md border">
                  {quizzes.map((quiz) => (
                    <button
                      key={quiz.id}
                      type="button"
                      onClick={() => startQuiz(quiz)}
                      className="flex items-center justify-between px-3 py-2 text-left text-sm hover:bg-accent/50"
                    >
                      <span>{quiz.topic || `Quiz · ${quiz.questions.length} questions`}</span>
                      <span className="text-xs text-muted-foreground">
                        {new Date(quiz.created_at).toLocaleDateString()}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {view === "generating" && (
          <div className="flex flex-col gap-3 pt-4">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
        )}

        {view === "taking" && activeQuiz && currentQuestion && (
          <div className="flex flex-col gap-6 pt-4">
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted-foreground">
                Question {currentIndex + 1} of {activeQuiz.questions.length}
              </p>
              <Progress
                value={((currentIndex + 1) / activeQuiz.questions.length) * 100}
              />
            </div>

            <QuizQuestionCard
              question={currentQuestion}
              selectedIndex={answers[currentIndex]}
              onSelect={selectAnswer}
            />

            <div className="flex justify-end gap-2">
              {isLastQuestion ? (
                <Button disabled={answers[currentIndex] === null} onClick={submitQuiz}>
                  Submit
                </Button>
              ) : (
                <Button
                  disabled={answers[currentIndex] === null}
                  onClick={() => setCurrentIndex((i) => i + 1)}
                >
                  Next
                </Button>
              )}
            </div>
          </div>
        )}

        {view === "results" && activeQuiz && attempt && (
          <div className="flex flex-col gap-6 pt-4" aria-live="polite">
            <div className="flex flex-col items-center gap-2 py-4">
              <ScoreRing score={attempt.score} total={attempt.total} />
              <p className="text-sm text-muted-foreground">Quiz complete</p>
            </div>

            <div className="flex flex-col gap-6">
              {activeQuiz.questions.map((q, i) => (
                <QuizQuestionCard
                  key={i}
                  question={q}
                  selectedIndex={answers[i]}
                  onSelect={() => {}}
                  revealed
                />
              ))}
            </div>

            <div className="flex justify-center gap-2">
              <Button variant="outline" onClick={generateQuiz}>
                New quiz
              </Button>
              <Button variant="outline" onClick={() => setView("idle")}>
                Back to quizzes
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
