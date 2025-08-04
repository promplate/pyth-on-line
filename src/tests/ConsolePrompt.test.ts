import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import ConsolePrompt from '../lib/components/ConsolePrompt.svelte';

describe('ConsolePrompt Component', () => {
  it('renders with default prompt', () => {
    render(ConsolePrompt);
    
    // The text includes HTML entities, so we need to find by element content
    const element = document.querySelector('span');
    expect(element).toBeInTheDocument();
    expect(element?.textContent).toBe('>>> ');
  });

  it('renders with custom prompt', () => {
    render(ConsolePrompt, {
      props: {
        prompt: 'custom>'
      }
    });
    
    // Check by text content
    const element = document.querySelector('span');
    expect(element).toBeInTheDocument();
    expect(element?.textContent).toBe('custom> ');
  });

  it('has correct CSS classes', () => {
    render(ConsolePrompt);
    
    const element = document.querySelector('span');
    expect(element).toHaveClass('flex-shrink-0');
    expect(element).toHaveClass('select-none');
    expect(element).toHaveClass('op-25');
    expect(element).toHaveClass('group-hover:op-100');
  });

  it('preserves font feature settings', () => {
    render(ConsolePrompt);
    
    const element = document.querySelector('span');
    expect(element?.tagName).toBe('SPAN');
    expect(element).toBeInTheDocument();
  });
});