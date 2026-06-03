import { Check, Circle, ShieldCheck } from "lucide-react";
import clsx from "clsx";
import type { WorkflowStage } from "@/lib/types";

const steps: Array<{ id: WorkflowStage; label: string }> = [
  { id: "created", label: "Issue" },
  { id: "repository_analyzed", label: "Analyze" },
  { id: "plan_generated", label: "Plan" },
  { id: "plan_approved", label: "Approve" },
  { id: "changes_generated", label: "Change" },
  { id: "tests_completed", label: "Tests" },
  { id: "security_completed", label: "Security" },
  { id: "review_ready", label: "Review" },
  { id: "draft_pr_ready", label: "Draft PR" }
];

export function WorkflowRail({ stage }: { stage: WorkflowStage }) {
  const currentIndex = Math.max(
    0,
    steps.findIndex((step) => step.id === stage)
  );

  return (
    <nav className="border-b border-line bg-white xl:border-b-0 xl:border-r">
      <div className="flex h-14 items-center gap-2 border-b border-line px-4">
        <ShieldCheck aria-hidden className="h-5 w-5 text-pine" />
        <span className="text-sm font-semibold tracking-normal">OSCA</span>
      </div>
      <ol className="scrollbar-thin flex gap-1 overflow-x-auto p-3 xl:block xl:space-y-1 xl:overflow-visible">
        {steps.map((step, index) => {
          const done = index < currentIndex;
          const current = index === currentIndex;
          return (
            <li key={step.id}>
              <div
                className={clsx(
                  "flex h-10 min-w-28 items-center gap-3 rounded-md px-3 text-sm xl:min-w-0",
                  current && "bg-mint text-pine",
                  !current && "text-ink/70"
                )}
              >
                {done ? (
                  <Check aria-hidden className="h-4 w-4 text-pine" />
                ) : (
                  <Circle aria-hidden className={clsx("h-4 w-4", current ? "fill-pine text-pine" : "text-ink/30")} />
                )}
                <span className="truncate">{step.label}</span>
              </div>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
