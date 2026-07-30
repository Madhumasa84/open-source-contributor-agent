import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { SemanticSearchPanel } from '../../components/SemanticSearchPanel'
import { semanticSearch } from '../../lib/api'

// Mock the API and icons
vi.mock('../../lib/api', () => ({
  semanticSearch: vi.fn(),
}))

vi.mock('lucide-react', () => ({
  Search: () => <div data-testid="search-icon" />,
  ChevronDown: () => <div data-testid="chevron-down" />,
  ChevronUp: () => <div data-testid="chevron-up" />,
  Loader2: () => <div data-testid="loader" />,
}))

describe('SemanticSearchPanel', () => {
  const mockWorkflowId = 'test-workflow-123'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders collapsed state by default', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    expect(screen.getByText('Semantic Code Search')).toBeInTheDocument()
    expect(screen.getByTestId('chevron-down')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/Search concepts/)).not.toBeInTheDocument()
  })

  it('expands and collapses when clicking the header', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    const headerButton = screen.getByRole('button', { name: /Semantic Code Search/i })

    // Expand
    fireEvent.click(headerButton)
    expect(screen.getByTestId('chevron-up')).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search concepts/)).toBeInTheDocument()

    // Collapse
    fireEvent.click(headerButton)
    expect(screen.getByTestId('chevron-down')).toBeInTheDocument()
    expect(screen.queryByPlaceholderText(/Search concepts/)).not.toBeInTheDocument()
  })

  it('updates input value on typing', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)

    // Expand
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/i) as HTMLInputElement
    fireEvent.change(input, { target: { value: 'authentication' } })

    expect(input.value).toBe('authentication')
  })

  it('disables search button when input is empty', () => {
    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const searchButton = screen.getByRole('button', { name: "Search" })
    expect(searchButton).toBeDisabled()

    const input = screen.getByPlaceholderText(/Search concepts/i)
    fireEvent.change(input, { target: { value: ' ' } })

    expect(searchButton).toBeDisabled() // Still disabled with only whitespace
  })

  it('handles successful search and displays results', async () => {
    const mockResults = [
      {
        file_path: 'src/auth.ts',
        start_line: 10,
        end_line: 15,
        content: 'function login() {\n  return true;\n}',
        score: 0.95
      }
    ];

    (semanticSearch as any).mockResolvedValueOnce(mockResults)

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/i)
    fireEvent.change(input, { target: { value: 'login' } })

    const searchButton = screen.getByRole('button', { name: "Search" })
    fireEvent.click(searchButton)

    // Check loading state
    expect(screen.getByTestId('loader')).toBeInTheDocument()
    expect(searchButton).toBeDisabled()

    // Wait for results
    await waitFor(() => {
      expect(screen.queryByTestId('loader')).not.toBeInTheDocument()
    })

    expect(semanticSearch).toHaveBeenCalledWith(mockWorkflowId, 'login')
    expect(semanticSearch).toHaveBeenCalledTimes(1)

    // Verify results are displayed
    expect(screen.getByText('src/auth.ts')).toBeInTheDocument()
    expect(screen.getByText('Score: 0.95')).toBeInTheDocument()
    expect(screen.getByText('Lines 10 - 15')).toBeInTheDocument()
    expect(screen.getByText(/function login/)).toBeInTheDocument()
  })

  it('handles search error', async () => {
    const errorMessage = 'API rate limit exceeded';
    (semanticSearch as any).mockRejectedValueOnce(new Error(errorMessage))

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/i)
    fireEvent.change(input, { target: { value: 'error case' } })

    const searchButton = screen.getByRole('button', { name: "Search" })
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })

    expect(screen.queryByTestId('loader')).not.toBeInTheDocument()
  })

  it('displays no results message when search returns empty array', async () => {
    (semanticSearch as any).mockResolvedValueOnce([])

    render(<SemanticSearchPanel workflowId={mockWorkflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/i)
    fireEvent.change(input, { target: { value: 'nonexistent' } })

    const searchButton = screen.getByRole('button', { name: "Search" })
    fireEvent.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('No results found.')).toBeInTheDocument()
    })
  })
})
