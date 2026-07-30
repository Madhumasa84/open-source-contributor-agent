import React from "react";
import { render, screen, within } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { WorkflowRail } from "./WorkflowRail";
import type { WorkflowStage } from "@/lib/types";

// Helper for testing
const stepsList = [
  "Issue",
  "Analyze",
  "Plan",
  "Approve",
  "Change",
  "Tests",
  "Security",
  "Review",
  "Draft PR"
];

describe("WorkflowRail", () => {
  it("renders correctly with initial stage", () => {
    const { container } = render(<WorkflowRail stage="created" />);

    const items = container.querySelectorAll('li');
    expect(items).toHaveLength(stepsList.length);

    const issueStep = items[0].querySelector('div');
    expect(issueStep).toHaveClass("bg-mint");
    expect(issueStep).toHaveTextContent("Issue");

    const analyzeStep = items[1].querySelector('div');
    expect(analyzeStep).not.toHaveClass("bg-mint");
    expect(analyzeStep).toHaveClass("text-ink/70");
  });

  it("renders correctly with intermediate stage", () => {
    const { container } = render(<WorkflowRail stage="plan_approved" />);

    const items = container.querySelectorAll('li');

    const approveStep = items[3].querySelector('div');
    expect(approveStep).toHaveClass("bg-mint");
    expect(approveStep).toHaveTextContent("Approve");

    const issueStep = items[0].querySelector('div');
    expect(issueStep).not.toHaveClass("bg-mint");
    expect(issueStep).toHaveClass("text-ink/70");
    expect(issueStep?.querySelector('svg')?.getAttribute('class')).toContain('lucide-check');

    const reviewStep = items[7].querySelector('div');
    expect(reviewStep).not.toHaveClass("bg-mint");
    expect(reviewStep).toHaveClass("text-ink/70");
    expect(reviewStep?.querySelector('svg')?.getAttribute('class')).toContain('lucide-circle');
  });

  it("renders correctly with final stage", () => {
    const { container } = render(<WorkflowRail stage="draft_pr_ready" />);

    const items = container.querySelectorAll('li');

    const draftPrStep = items[8].querySelector('div');
    expect(draftPrStep).toHaveClass("bg-mint");
    expect(draftPrStep).toHaveTextContent("Draft PR");

    const reviewStep = items[7].querySelector('div');
    expect(reviewStep).not.toHaveClass("bg-mint");
    expect(reviewStep).toHaveClass("text-ink/70");
    expect(reviewStep?.querySelector('svg')?.getAttribute('class')).toContain('lucide-check');
  });

  it("defaults to first step if unknown stage is provided", () => {
    const { container } = render(<WorkflowRail stage={"unknown_stage" as WorkflowStage} />);

    const items = container.querySelectorAll('li');

    const issueStep = items[0].querySelector('div');
    expect(issueStep).toHaveClass("bg-mint");
    expect(issueStep).toHaveTextContent("Issue");
  });
});
