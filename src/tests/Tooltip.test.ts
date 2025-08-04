import { render, screen } from '@testing-library/svelte';
import { describe, it, expect, beforeEach } from 'vitest';
import Tooltip from '../lib/components/Tooltip.svelte';

describe('Tooltip Component', () => {
  let target: HTMLElement;
  
  beforeEach(() => {
    // Create a mock target element
    target = document.createElement('div');
    target.style.position = 'absolute';
    target.style.top = '100px';
    target.style.left = '100px';
    target.style.width = '50px';
    target.style.height = '20px';
    document.body.appendChild(target);
    
    // Mock getBoundingClientRect
    target.getBoundingClientRect = () => ({
      top: 100,
      left: 100,
      right: 150,
      bottom: 120,
      width: 50,
      height: 20,
      x: 100,
      y: 100,
      toJSON: () => {}
    });
  });

  it('renders tooltip content when show is true', () => {
    render(Tooltip, {
      props: {
        target,
        show: true
      }
    });
    
    // Since the tooltip uses Portal, we need to check in the document
    const tooltipElement = document.querySelector('.fixed.transition-opacity');
    expect(tooltipElement).toBeInTheDocument();
  });

  it('does not render tooltip content when show is false', () => {
    render(Tooltip, {
      props: {
        target,
        show: false
      }
    });
    
    // When show is false, tooltip might still render but be hidden
    const tooltipElement = document.querySelector('.fixed.transition-opacity');
    if (tooltipElement) {
      expect(tooltipElement).toHaveClass('op-0');
      expect(tooltipElement).toHaveClass('pointer-events-none');
    }
  });

  it('applies opacity classes correctly based on show prop', () => {
    render(Tooltip, {
      props: {
        target,
        show: false
      }
    });
    
    // When show is false, tooltip should have opacity 0
    const tooltipElement = document.querySelector('.fixed.transition-opacity');
    if (tooltipElement) {
      expect(tooltipElement).toHaveClass('op-0');
      expect(tooltipElement).toHaveClass('pointer-events-none');
    }
  });

  it('positions tooltip correctly', async () => {
    render(Tooltip, {
      props: {
        target,
        show: true
      }
    });
    
    // Wait for position calculation
    await new Promise(resolve => setTimeout(resolve, 10));
    
    const tooltipElement = document.querySelector('.fixed.transition-opacity') as HTMLElement;
    expect(tooltipElement).toBeInTheDocument();
    // Position should be calculated based on target position
    expect(tooltipElement.style.left).toBe('100px');
  });
});