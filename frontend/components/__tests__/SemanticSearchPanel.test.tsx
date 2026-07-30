import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import { SemanticSearchPanel } from '../SemanticSearchPanel'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { semanticSearch } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  semanticSearch: vi.fn(),
}))

describe('SemanticSearchPanel', () => {
  const workflowId = 'test-workflow-id'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('renders closed by default', () => {
    render(<SemanticSearchPanel workflowId={workflowId} />)
    expect(screen.getByText('Semantic Code Search')).toBeInTheDocument()
    // The input should not be visible when closed
    expect(screen.queryByPlaceholderText(/Search concepts/)).not.toBeInTheDocument()
  })

  it('expands when clicked', () => {
    render(<SemanticSearchPanel workflowId={workflowId} />)
    const toggleButton = screen.getByRole('button', { name: /Semantic Code Search/i })

    fireEvent.click(toggleButton)

    expect(screen.getByPlaceholderText(/Search concepts/)).toBeInTheDocument()
  })

  it('disables search button when query is empty', () => {
    render(<SemanticSearchPanel workflowId={workflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const searchButton = screen.getByRole('button', { name: 'Search' })
    expect(searchButton).toBeDisabled()

    const input = screen.getByPlaceholderText(/Search concepts/)
    fireEvent.change(input, { target: { value: 'test' } })

    expect(searchButton).not.toBeDisabled()
  })

  it('shows loading state during search and handles successful search', async () => {
    const mockResults = [
      {
        file_path: 'test.ts',
        score: 0.9,
        start_line: 1,
        end_line: 5,
        content: 'const test = true;',
      }
    ]

    // Delay resolution to check loading state
    let resolveSearch: (value: any) => void;
    const searchPromise = new Promise(resolve => {
      resolveSearch = resolve
    })

    ;(semanticSearch as any).mockReturnValue(searchPromise)

    render(<SemanticSearchPanel workflowId={workflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/)
    fireEvent.change(input, { target: { value: 'auth' } })

    const searchButton = screen.getByRole('button', { name: 'Search' })
    fireEvent.click(searchButton)

    // Check loading state
    expect(semanticSearch).toHaveBeenCalledWith(workflowId, 'auth')
    expect(searchButton).toBeDisabled() // button is disabled during loading

    // Need to use class/svg to find loading spinner since button text is gone
    const loaders = document.querySelectorAll('.animate-pulse')
    expect(loaders.length).toBeGreaterThan(0)

    // Resolve search
    resolveSearch!(mockResults)

    // Wait for results
    await waitFor(() => {
      expect(screen.getByText('test.ts')).toBeInTheDocument()
    })

    expect(screen.getByText('Score: 0.90')).toBeInTheDocument()
    expect(screen.getByText('const test = true;')).toBeInTheDocument()
  })

  it('shows error state on failure', async () => {
    ;(semanticSearch as any).mockRejectedValue(new Error('Test error message'))

    render(<SemanticSearchPanel workflowId={workflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/)
    fireEvent.change(input, { target: { value: 'auth' } })

    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() => {
      expect(screen.getByText('Test error message')).toBeInTheDocument()
    })
  })

  it('shows no results message when search returns empty array', async () => {
    ;(semanticSearch as any).mockResolvedValue([])

    render(<SemanticSearchPanel workflowId={workflowId} />)
    fireEvent.click(screen.getByRole('button', { name: /Semantic Code Search/i }))

    const input = screen.getByPlaceholderText(/Search concepts/)
    fireEvent.change(input, { target: { value: 'does_not_exist' } })

    fireEvent.click(screen.getByRole('button', { name: 'Search' }))

    await waitFor(() => {
      expect(screen.getByText('No results found.')).toBeInTheDocument()
    })
  })
})
