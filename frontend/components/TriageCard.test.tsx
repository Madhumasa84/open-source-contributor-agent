import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { TriageCard } from "./TriageCard";
import type { TriageData } from "@/lib/types";

const mockTriageData: TriageData = {
  issue_id: 1,
  difficulty_score: 2,
  fixability_score: 8,
  good_first_issue: true,
  contributor_level: "beginner",
  triage_reasoning: "This is a simple issue perfect for beginners.",
};

describe("TriageCard", () => {
  it("renders triage data correctly", () => {
    render(<TriageCard data={mockTriageData} />);

    expect(screen.getByText("Issue Triage")).toBeInTheDocument();
    expect(screen.getByText("Good First Issue")).toBeInTheDocument();
    expect(screen.getByText("beginner")).toBeInTheDocument();
    expect(screen.getByText("2 / 10")).toBeInTheDocument(); // Difficulty
    expect(screen.getByText("8 / 10")).toBeInTheDocument(); // Fixability
  });

  it("does not render Good First Issue tag when false", () => {
    const data = { ...mockTriageData, good_first_issue: false };
    render(<TriageCard data={data} />);

    expect(screen.queryByText("Good First Issue")).not.toBeInTheDocument();
  });

  it("applies correct color for intermediate contributor level", () => {
    const data: TriageData = { ...mockTriageData, contributor_level: "intermediate" };
    render(<TriageCard data={data} />);

    const levelSpan = screen.getByText("intermediate");
    expect(levelSpan).toHaveClass("bg-amber-100", "text-amber-700");
  });

  it("applies correct color for advanced contributor level", () => {
    const data: TriageData = { ...mockTriageData, contributor_level: "advanced" };
    render(<TriageCard data={data} />);

    const levelSpan = screen.getByText("advanced");
    expect(levelSpan).toHaveClass("bg-rose-100", "text-rose-700");
  });

  it("applies correct colors for difficulty scores", () => {
    const { container, rerender } = render(<TriageCard data={{ ...mockTriageData, difficulty_score: 2 }} />);
    // difficulty_score <= 3 -> bg-emerald-500
    let bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[0]).toHaveClass("bg-emerald-500");

    rerender(<TriageCard data={{ ...mockTriageData, difficulty_score: 5 }} />);
    // difficulty_score <= 7 -> bg-amber-500
    bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[0]).toHaveClass("bg-amber-500");

    rerender(<TriageCard data={{ ...mockTriageData, difficulty_score: 9 }} />);
    // difficulty_score > 7 -> bg-rose-500
    bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[0]).toHaveClass("bg-rose-500");
  });

  it("applies correct colors for fixability scores", () => {
    const { container, rerender } = render(<TriageCard data={{ ...mockTriageData, fixability_score: 8 }} />);
    // fixability_score >= 7 -> bg-emerald-500
    let bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[1]).toHaveClass("bg-emerald-500");

    rerender(<TriageCard data={{ ...mockTriageData, fixability_score: 5 }} />);
    // fixability_score >= 4 -> bg-amber-500
    bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[1]).toHaveClass("bg-amber-500");

    rerender(<TriageCard data={{ ...mockTriageData, fixability_score: 2 }} />);
    // fixability_score < 4 -> bg-rose-500
    bars = container.querySelectorAll('.bg-panel > div');
    expect(bars[1]).toHaveClass("bg-rose-500");
  });

  it("toggles triage reasoning visibility on button click", () => {
    render(<TriageCard data={mockTriageData} />);

    // Initial state: hidden
    expect(screen.queryByText(mockTriageData.triage_reasoning)).not.toBeInTheDocument();

    // Click to expand
    const toggleButton = screen.getByText("Triage Reasoning");
    fireEvent.click(toggleButton);
    expect(screen.getByText(mockTriageData.triage_reasoning)).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(toggleButton);
    expect(screen.queryByText(mockTriageData.triage_reasoning)).not.toBeInTheDocument();
  });
});
