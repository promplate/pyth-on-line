import { render, screen } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import GitHubUser from '../lib/components/GitHubUser.svelte';

describe('GitHubUser Component', () => {
  it('renders user avatar with correct alt text', () => {
    const props = {
      url: 'https://github.com/testuser.png',
      login: 'testuser',
      name: 'Test User'
    };

    render(GitHubUser, props);
    
    const avatar = screen.getByAltText('Test User');
    expect(avatar).toBeInTheDocument();
    expect(avatar).toHaveAttribute('src', 'https://github.com/testuser.png');
  });

  it('renders with login as alt text when name is null', () => {
    const props = {
      url: 'https://github.com/testuser.png',
      login: 'testuser',
      name: null
    };

    render(GitHubUser, props);
    
    const avatar = screen.getByAltText('@testuser');
    expect(avatar).toBeInTheDocument();
  });

  it('renders fallback text correctly for full name', () => {
    const props = {
      url: 'https://github.com/testuser.png',
      login: 'testuser',
      name: 'John Doe'
    };

    render(GitHubUser, props);
    
    // The fallback should show "JD" for "John Doe"
    const fallback = screen.getByText('JD');
    expect(fallback).toBeInTheDocument();
  });

  it('renders fallback text correctly for single name', () => {
    const props = {
      url: 'https://github.com/testuser.png',
      login: 'testuser',
      name: 'John'
    };

    render(GitHubUser, props);
    
    // The fallback should show "Jo" for "John"
    const fallback = screen.getByText('Jo');
    expect(fallback).toBeInTheDocument();
  });

  it('renders fallback text using login when name is null', () => {
    const props = {
      url: 'https://github.com/testuser.png',
      login: 'testuser',
      name: null
    };

    render(GitHubUser, props);
    
    // The fallback should show "te" for "testuser"
    const fallback = screen.getByText('te');
    expect(fallback).toBeInTheDocument();
  });
});