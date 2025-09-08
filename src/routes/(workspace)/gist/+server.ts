import type { RequestHandler } from "./$types";

import { error, json } from "@sveltejs/kit";
import { gql } from "$lib/github/client";

export interface GistMetadata {
  name: string;
  description: string | null;
  updatedAt: string;
  stargazerCount: number;
  viewerHasStarred: boolean;
  isPublic: boolean;
}

export const GET: RequestHandler = async ({ cookies, url }) => {
  // Prefer user-provided token from query param, then OAuth token
  const userToken = url.searchParams.get("token");
  const oauthToken = cookies.get("access_token");
  const token = userToken || oauthToken;

  if (!token) {
    error(401, "Unauthorized");
  }

  const data: {
    viewer: {
      name: string | null;
      login: string;
      avatarUrl: string;
      gists: {
        totalCount: number;
        nodes: GistMetadata[];
      };
    };
  } = await gql(`
    {
      viewer {
        name
        login
        avatarUrl
        gists(first: 100) {
          totalCount
          nodes {
            name
            description
            updatedAt
            stargazerCount
            viewerHasStarred
            isPublic
          }
        }
      }
    }
  `, token);

  // todo: implement pagination

  const { viewer: { name, login, avatarUrl, gists: { nodes: gists, totalCount: total } } } = data;
  return json({ name, login, avatarUrl, total, gists });
};
