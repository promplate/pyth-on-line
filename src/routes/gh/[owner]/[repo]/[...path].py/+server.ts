import type { RequestHandler } from "./$types";
import type { DependencySource, Payload } from "./types";

import { findDependencies, parsePep723, prependPep723 } from "./pep723";
import { buildQuery, collectDirectories } from "./query";
import { error, json, text } from "@sveltejs/kit";
import * as env from "$app/env/private";
import { gql } from "$lib/github/client";

type History = { target: { history?: { nodes: Array<{ committedDate: string }> } } | null } | null;

interface RepoData {
  repository: {
    target: { text?: string } | null;
    targetHistory: History;
    stargazerCount: number;
    forkCount: number;
    watchers: { totalCount: number };
    description: string | null;
    defaultBranchRef: { name: string } | null;
    owner: { login: string; avatarUrl: string };
    isArchived: boolean;
    primaryLanguage: { name: string; color: string | null } | null;
    licenseInfo: { name: string; spdxId: string | null } | null;
    createdAt: string;
    pushedAt: string | null;
    issues: {
      totalCount: number;
      nodes: Array<{ number: number; title: string; url: string; createdAt: string }>;
    };
    releases: {
      nodes: Array<{ tagName: string; name: string | null; publishedAt: string | null }>;
    };
    [key: `pyproject${number}`]: { text?: string } | null;
    [key: `pyprojectHistory${number}`]: History;
  } | null;
}

export const GET: RequestHandler = async ({ params, request, cookies }) => {
  const { owner, repo: repoWithRef, path } = params;
  if (!owner || !repoWithRef || !path) {
    throw error(400, "Expected /gh/{owner}/{repo}[@ref]/.../{file}.py");
  }

  const atIdx = repoWithRef.indexOf("@");
  const repo = atIdx >= 0 ? repoWithRef.slice(0, atIdx) : repoWithRef;
  const ref = atIdx >= 0 ? repoWithRef.slice(atIdx + 1) : "HEAD";
  const filePath = `${path}.py`;

  const wantsJson = (request.headers.get("accept") ?? "").includes("application/json");

  const pyprojectPaths = collectDirectories(filePath).map(dir => (dir ? `${dir}/pyproject.toml` : "pyproject.toml"));
  const query = buildQuery({ owner, repo, ref, filePath, pyprojectPaths });

  let data: RepoData;
  try {
    const token = cookies.get("access_token") || env.GITHUB_TOKEN;
    data = await gql(query, token);
  }
  catch (err) {
    if (Array.isArray(err) && err.some(e => e.type === "NOT_FOUND"))
      throw error(404, "Repository not found");
    console.error("GitHub GraphQL failed", err);
    throw error(502, "GitHub GraphQL request failed");
  }

  const { repository } = data;
  // Tokens without access to the repository may get `null` here without a `NOT_FOUND` error
  if (!repository)
    throw error(404, "Repository not found");

  const targetFileText = repository.target?.text;
  if (!targetFileText)
    throw error(404, "File not found");

  const pep = parsePep723(targetFileText);
  const pyprojects = pyprojectPaths.map((p, i) => ({ path: p, text: repository[`pyproject${i}`]?.text }));

  const fromPyproject = pep ? null : findDependencies(pyprojects);

  const dependencies = pep?.dependencies ?? fromPyproject?.dependencies ?? [];
  const dependencySource: DependencySource = pep
    ? { type: "pep723", path: filePath }
    : fromPyproject
      ? { type: "pyproject", path: fromPyproject.path }
      : { type: "none", path: null };

  const content = fromPyproject ? prependPep723(targetFileText, dependencies) : targetFileText;

  const pyprojectPathsWithStatus = pyprojects.filter(({ text }) => text).map(({ path: p }) => ({ path: p, used: p === fromPyproject?.path }));

  // Latest commit touching the script or any pyproject.toml above it.
  // GitHub returns UTC ISO 8601 timestamps, so they sort chronologically as strings.
  const timestamps = [repository.targetHistory, ...pyprojectPaths.map((_, i) => repository[`pyprojectHistory${i}`])]
    .map(history => history?.target?.history?.nodes[0]?.committedDate)
    .filter(Boolean)
    .sort();
  const fileLastUpdatedAt = timestamps.at(-1) ?? repository.pushedAt ?? "";

  const latestRelease = repository.releases.nodes[0];

  const payload: Payload = {
    owner,
    repo,
    ref,
    filePath,
    githubUrl: `https://github.com/${owner}/${repo}/blob/${ref}/${filePath}`,
    dependencies,
    dependencySource,
    pep723: { present: Boolean(pep), dependencies: pep?.dependencies ?? [] },
    pyprojectPaths: pyprojectPathsWithStatus,
    repository: {
      stargazers: repository.stargazerCount,
      forks: repository.forkCount,
      watchers: repository.watchers.totalCount,
      description: repository.description ?? "",
      defaultBranch: repository.defaultBranchRef?.name ?? null,
      ownerAvatarUrl: repository.owner.avatarUrl,
      ownerLogin: repository.owner.login,
      isArchived: repository.isArchived,
      primaryLanguage: repository.primaryLanguage && { name: repository.primaryLanguage.name, color: repository.primaryLanguage.color ?? "" },
      licenseInfo: repository.licenseInfo && { name: repository.licenseInfo.name, spdxId: repository.licenseInfo.spdxId ?? "" },
      openIssuesCount: repository.issues.totalCount,
      recentIssues: repository.issues.nodes,
      latestRelease: latestRelease ? { ...latestRelease, publishedAt: latestRelease.publishedAt ?? "" } : null,
      createdAt: repository.createdAt,
      pushedAt: repository.pushedAt ?? "",
      fileLastUpdatedAt,
    },
    content,
    original: targetFileText,
  };

  return wantsJson ? json(payload) : text(content);
};
