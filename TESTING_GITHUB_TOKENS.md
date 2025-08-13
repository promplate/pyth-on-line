# Testing GitHub Token Support for Private Gists

This document describes how to test the implementation of issue #90 - supporting user-provided GitHub tokens for accessing private/secret gists.

## Overview

The implementation allows users to provide their own GitHub personal access token to access private gists that are not accessible through the OAuth application.

## Features Implemented

1. **Token Storage**: Secure local storage of GitHub personal access tokens
2. **Token Validation**: Client-side format validation and server-side API validation
3. **Token Management UI**: User-friendly interface for token input, validation, and management
4. **API Integration**: Modified gist endpoints to use user tokens when available
5. **Error Handling**: Helpful error messages and guidance for private gist access issues

## How to Test

### Prerequisites

1. A GitHub account with some private gists
2. A GitHub personal access token with `gist` scope

### Creating a GitHub Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Click "Generate new token" → "Generate new token (classic)"
3. Set description: "Pyth-on-line gist access"
4. Select scope: `gist` (Full control of gists)
5. Click "Generate token"
6. Copy the token (it starts with `ghp_`)

### Test Scenarios

#### 1. Test Token Input and Validation

1. Navigate to `/gist` page
2. Click the "Set token" button in the top right
3. Paste your GitHub token
4. Click "Validate & Save"
5. Should show success message with your GitHub username

#### 2. Test Private Gist Access

1. Create a secret gist on GitHub:
   - Go to https://gist.github.com/
   - Create a new gist
   - Select "Create secret gist"
   - Note the gist ID from the URL
2. Try accessing it via OAuth (without user token):
   - Clear your user token if set
   - Navigate to `/gist/{gist_id}`
   - Should get 403/404 error
3. Try accessing with user token:
   - Set your GitHub token via the UI
   - Navigate to `/gist/{gist_id}`
   - Should successfully load the private gist content

#### 3. Test Token Management

1. **Token Status**: Verify the button shows "Token set" when a token is configured
2. **Token Clearing**: Test the "Clear Token" button removes the stored token
3. **Token Visibility**: Test the show/hide token toggle works correctly
4. **Invalid Token**: Test validation with an invalid token format

#### 4. Test Error Handling

1. Try accessing a private gist without a token
2. Should see helpful error page with token setup instructions
3. Error page should guide users to set up a GitHub token

### Expected Behavior

- **Public gists**: Should work with or without user token (OAuth fallback)
- **Private gists**: Should only work with a valid user token that has access
- **Token validation**: Should validate token format and test API access
- **Fallback**: Should gracefully fall back to OAuth token when user token fails
- **Security**: Token should be stored locally only, never sent to the application server

### Token Formats Supported

- Classic tokens: `ghp_` followed by 36 alphanumeric characters
- Fine-grained tokens: `github_pat_` followed by 82 alphanumeric/underscore characters

### UI Elements

1. **Token Button**: Shows current token status and provides access to token management
2. **Token Input**: Secure password field with show/hide toggle
3. **Validation**: Real-time feedback on token validation status
4. **Error Pages**: Helpful guidance for private gist access issues

## Implementation Files

- `src/lib/user-token.ts` - Token storage and validation logic
- `src/lib/components/GitHubTokenManager.svelte` - Token management UI
- `src/routes/(workspace)/gist/+server.ts` - Gist listing API with token support
- `src/routes/(workspace)/gist/[gist_id]/+server.ts` - Individual gist API with token support
- `src/routes/(workspace)/gist/+page.svelte` - Gist listing page with token management
- `src/routes/(workspace)/+error.svelte` - Enhanced error page for private gist access

## Security Considerations

- Tokens are stored in browser's localStorage only
- Tokens are passed via query parameters to maintain server-side compatibility
- Token validation happens both client-side (format) and server-side (API test)
- No sensitive data is logged or exposed in error messages
