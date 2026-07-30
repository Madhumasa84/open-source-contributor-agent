import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { SemanticSearchPanel } from '@/components/SemanticSearchPanel'
import { semanticSearch } from '@/lib/api'
import type { SearchResult } from '@/lib/types'

vi.mock('@/lib/api', () => ({
  semanticSearch: vi.fn(),
}))

describe('SemanticSearchPanel', () => {
  const mockWorkflowId = 'test-workflow-123'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders initially in a closed state', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    expect(screen.getByText('Semantic Code Search')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/Search concepts/)).not.toBeInTheDocument()
  })

  it('expands when clicked', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    const toggleButton = screen.getByRole('button', { name: /Semantic Code Search/i })
    fireEvent.click(toggleButton)

    expect(screen.getByPlaceholderText(/Search concepts/)).toBeInTheDocument()
    expect(screen.getAllByRole('button')).toHaveLength(2)
  })

  it('updates the search query when typed', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/)
    fireEvent.change(input, { target: { value: 'auth middleware' } })

    expect(input).toHaveValue('auth middleware')
  })

  it('performs a successful search and displays results', async () => {
    const mockResults: SearchResult[] = [
      {
        file_path: 'backend/auth.py',
        score: 0.95,
        start_line: 10,
        end_line: 15,
        content: 'def authenticate(req):\n  # handle auth\n  pass',
      },
    ]
    vi.mocked(semanticSearch).mockResolvedValueOnce(mockResults)

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))
    fireEvent.change(screen.getByPlaceholderText(/Search concepts/), { target: { value: 'auth' } })

    const searchButton = screen.getAllByRole('button').find(b => b.getAttribute('type') === 'submit')!
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('backend/auth.py')).toBeInTheDocument()
    })

    expect(screen.getByText(/Score: 0.95/)).toBeInTheDocument()
    expect(screen.getByText(/Lines 10 - 15/)).toBeInTheDocument()
    expect(semanticSearch).toHaveBeenCalledWith(mockWorkflowId, 'auth')
  })

  it('displays loading state during search', async () => {
    vi.mocked(semanticSearch).mockImplementationOnce(() => new Promise((resolve) => setTimeout(() => resolve([]), 100)))

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))
    fireEvent.change(screen.getByPlaceholderText(/Search concepts/), { target: { value: 'auth' } })

    const searchButton = screen.getAllByRole('button').find(b => b.getAttribute('type') === 'submit')!
    fireEvent.click(searchButton)
    expect(searchButton).toBeDisabled()

    await waitFor(() => {
      expect(searchButton).not.toBeDisabled()
    })
  })

  it('displays error message when search fails', async () => {
    vi.mocked(semanticSearch).mockRejectedValueOnce(new Error('API Error'))

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))
    fireEvent.change(screen.getByPlaceholderText(/Search concepts/), { target: { value: 'auth' } })

    const searchButton = screen.getAllByRole('button').find(b => b.getAttribute('type') === 'submit')!
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('API Error')).toBeInTheDocument()
    })
  })

  it('displays no results message when search returns empty', async () => {
    vi.mocked(semanticSearch).mockResolvedValueOnce([])

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))
    fireEvent.change(screen.getByPlaceholderText(/Search concepts/), { target: { value: 'unknown concept' } })

    const searchButton = screen.getAllByRole('button').find(b => b.getAttribute('type') === 'submit')!
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('No results found.')).toBeInTheDocument()
    })
  })
})
