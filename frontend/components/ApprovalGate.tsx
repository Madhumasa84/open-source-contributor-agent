import { Ban, Check, PauseCircle, RotateCcw } from "lucide-react";
import type { ApprovalStatus } from "@/lib/types";

export function ApprovalGate({
  status,
  disabled,
  onDecision
}: {
  status: ApprovalStatus;
  disabled?: boolean;
  onDecision?: (decision: ApprovalStatus) => void;
}) {
  const icon =
    status === "approved" ? (
      <Check aria-hidden className="h-4 w-4 text-pine" />
    ) : status === "rejected" ? (
      <Ban aria-hidden className="h-4 w-4 text-danger" />
    ) : (
      <PauseCircle aria-hidden className="h-4 w-4 text-amber" />
    );

  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="mb-3 flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          {icon}
          <span className="truncate text-sm font-medium">Plan approval</span>
        </div>
        <span className="rounded-md bg-panel px-2 py-1 text-xs capitalize text-ink/70">
          {status.replace("_", " ")}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-2">
        <GateButton
          label="Approve"
          disabled={disabled}
          icon={<Check aria-hidden className="h-3.5 w-3.5" />}
          onClick={() => onDecision?.("approved")}
        />
        <GateButton
          label="Changes"
          disabled={disabled}
          icon={<RotateCcw aria-hidden className="h-3.5 w-3.5" />}
          onClick={() => onDecision?.("changes_requested")}
        />
        <GateButton
          label="Reject"
          disabled={disabled}
          icon={<Ban aria-hidden className="h-3.5 w-3.5" />}
          onClick={() => onDecision?.("rejected")}
        />
      </div>
    </div>
  );
}

function GateButton({
  label,
  icon,
  disabled,
  onClick
}: {
  label: string;
  icon: React.ReactNode;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className="inline-flex h-8 min-w-0 items-center justify-center gap-1 rounded-md border border-line bg-panel px-2 text-xs font-medium text-ink/70 hover:border-pine/50 disabled:cursor-not-allowed disabled:opacity-50"
    >
      {icon}
      <span className="truncate">{label}</span>
    </button>
  );
}
