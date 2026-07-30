import React from "react";
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ApprovalGate } from './ApprovalGate';
import type { ApprovalStatus } from '@/lib/types';

describe('ApprovalGate', () => {
  it('renders pending status correctly', () => {
    render(<ApprovalGate status="pending" />);
    expect(screen.getByText('Plan approval')).toBeInTheDocument();
    expect(screen.getByText('pending')).toBeInTheDocument();
  });

  it('renders approved status correctly', () => {
    render(<ApprovalGate status="approved" />);
    expect(screen.getByText('approved')).toBeInTheDocument();
  });

  it('renders rejected status correctly', () => {
    render(<ApprovalGate status="rejected" />);
    expect(screen.getByText('rejected')).toBeInTheDocument();
  });

  it('renders changes_requested status correctly', () => {
    render(<ApprovalGate status="changes_requested" />);
    expect(screen.getByText('changes requested')).toBeInTheDocument();
  });

  it('calls onDecision with "approved" when Approve button is clicked', () => {
    const handleDecision = vi.fn();
    render(<ApprovalGate status="pending" onDecision={handleDecision} />);

    const approveButton = screen.getByRole('button', { name: /approve/i });
    fireEvent.click(approveButton);

    expect(handleDecision).toHaveBeenCalledWith('approved');
  });

  it('calls onDecision with "changes_requested" when Changes button is clicked', () => {
    const handleDecision = vi.fn();
    render(<ApprovalGate status="pending" onDecision={handleDecision} />);

    const changesButton = screen.getByRole('button', { name: /changes/i });
    fireEvent.click(changesButton);

    expect(handleDecision).toHaveBeenCalledWith('changes_requested');
  });

  it('calls onDecision with "rejected" when Reject button is clicked', () => {
    const handleDecision = vi.fn();
    render(<ApprovalGate status="pending" onDecision={handleDecision} />);

    const rejectButton = screen.getByRole('button', { name: /reject/i });
    fireEvent.click(rejectButton);

    expect(handleDecision).toHaveBeenCalledWith('rejected');
  });

  it('disables all buttons when disabled prop is true', () => {
    const handleDecision = vi.fn();
    render(<ApprovalGate status="pending" disabled onDecision={handleDecision} />);

    const approveButton = screen.getByRole('button', { name: /approve/i });
    const changesButton = screen.getByRole('button', { name: /changes/i });
    const rejectButton = screen.getByRole('button', { name: /reject/i });

    expect(approveButton).toBeDisabled();
    expect(changesButton).toBeDisabled();
    expect(rejectButton).toBeDisabled();

    // Verify click doesn't trigger callback when disabled
    fireEvent.click(approveButton);
    expect(handleDecision).not.toHaveBeenCalled();
  });
});
