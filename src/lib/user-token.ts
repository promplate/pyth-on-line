import { persisted } from "svelte-persisted-store";
import { derived } from "svelte/store";

// Store for user-provided GitHub personal access token
export const userGitHubToken = persisted<string>("user-github-token", "");

// Derived store to check if user token is available
export const hasUserToken = derived(userGitHubToken, $token => Boolean($token && $token.trim()));

// Validate GitHub token format (basic validation)
export function isValidTokenFormat(token: string): boolean {
  // GitHub personal access tokens follow these patterns:
  // - Classic tokens: ghp_[A-Za-z0-9]{36}
  // - Fine-grained tokens: github_pat_[A-Za-z0-9_]{82}
  const classicPattern = /^ghp_[A-Za-z0-9]{36}$/;
  const fineGrainedPattern = /^github_pat_\w{82}$/;

  return classicPattern.test(token) || fineGrainedPattern.test(token);
}

// Validate token by making a test API call
export async function validateToken(token: string): Promise<{ valid: boolean; error?: string; user?: { login: string; name: string } }> {
  if (!token || !isValidTokenFormat(token)) {
    return { valid: false, error: "Invalid token format" };
  }

  try {
    const response = await fetch("https://api.github.com/user", {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: "application/vnd.github.v3+json",
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        return { valid: false, error: "Invalid or expired token" };
      }
      return { valid: false, error: `API error: ${response.status}` };
    }

    const user = await response.json();
    return {
      valid: true,
      user: {
        login: user.login,
        name: user.name,
      },
    };
  }
  catch {
    return { valid: false, error: "Network error during validation" };
  }
}

// Clear the user token
export function clearUserToken(): void {
  userGitHubToken.set("");
}
