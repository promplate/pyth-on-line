import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import Details from '../lib/components/Details.svelte';

describe('Details Component', () => {
  it('renders details element without summary', () => {
    render(Details);
    
    const details = screen.getByRole('group');
    expect(details).toBeInTheDocument();
    expect(details.tagName).toBe('DETAILS');
  });

  it('renders with summary when provided', () => {
    render(Details, {
      props: {
        summary: 'Click to expand'
      }
    });
    
    const summary = screen.getByText('Click to expand');
    expect(summary).toBeInTheDocument();
    expect(summary.tagName).toBe('SUMMARY');
  });

  it('does not render summary when empty', () => {
    render(Details, {
      props: {
        summary: ''
      }
    });
    
    // Should not find a summary element when summary is empty
    const summaryElement = document.querySelector('summary');
    expect(summaryElement).not.toBeInTheDocument();
  });

  it('can be expanded and collapsed', async () => {
    render(Details, {
      props: {
        summary: 'Toggle content'
      }
    });
    
    const details = screen.getByRole('group') as HTMLDetailsElement;
    expect(details.open).toBe(false);
    
    // Click the summary to open
    const summary = screen.getByText('Toggle content');
    summary.click();
    
    // Should be open after clicking
    expect(details.open).toBe(true);
  });
});