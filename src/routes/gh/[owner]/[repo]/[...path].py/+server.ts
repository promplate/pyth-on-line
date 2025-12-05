import type { RequestHandler } from "./$types";
import type { DependencySource, Payload } from "./types";

import { findDependencies, parsePep723, prependPep723 } from "./pep723";
import { buildQuery, collectDirectories } from "./query";
import { error, json, text } from "@sveltejs/kit";
import { env } from "$env/dynamic/private";
import { gql } from "$lib/github/client";

interface RepoData {
  repository?: {
    target?: { text?: string };
    stargazerCount?: number;
    forkCount?: number;
    watchers?: { totalCount?: number };
    description?: string | null;
    defaultBranchRef?: { name?: string } | null;
    owner?: { login?: string; avatarUrl?: string };
    [key: `pyproject${number}`]: { text?: string } | undefined;
  };
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
    console.error("GitHub GraphQL failed", err);
    throw error(502, "GitHub GraphQL request failed");
  }

  const repository = data?.repository;
  if (!repository)
    throw error(404, "Repository not found");

  const targetFileText = repository.target?.text;
  if (!targetFileText)
    throw error(404, "File not found");

  const pep = parsePep723(targetFileText);
  const pyprojects = pyprojectPaths.map((p, i) => ({ path: p, text: repository[`pyproject${i}`]?.text }));

  const depsFromPep = pep?.dependencies ?? [];
  const fromPyproject = pep ? null : findDependencies(pyprojects);

  const dependencies = pep ? depsFromPep : fromPyproject?.dependencies ?? [];
  const dependencySource: DependencySource = pep
    ? { type: "pep723", path: filePath }
    : fromPyproject
      ? { type: "pyproject", path: fromPyproject.path }
      : { type: "none", path: null };

  const content = pep ? targetFileText : fromPyproject ? prependPep723(targetFileText, dependencies) : targetFileText;

  // Mark which pyproject was used and filter to only found ones
  const usedPath = fromPyproject?.path;
  const pyprojectPathsWithStatus = pyprojects
    .filter(({ text }) => text) // Only include found files
    .map(({ path: p, text: t }) => ({
      path: p,
      exists: Boolean(t),
      used: p === usedPath && !pep, // used if it's the first one and no PEP 723
    }));

  const payload: Payload = {
    owner,
    repo,
    ref,
    filePath,
    githubUrl: `https://github.com/${owner}/${repo}/blob/${ref}/${filePath}`,
    dependencies,
    dependencySource,
    pep723: { present: Boolean(pep), dependencies: depsFromPep },
    pyprojectPaths: pyprojectPathsWithStatus,
    repository: {
      stargazers: repository.stargazerCount ?? 0,
      forks: repository.forkCount ?? 0,
      watchers: repository.watchers?.totalCount ?? 0,
      description: repository.description ?? "",
      defaultBranch: repository.defaultBranchRef?.name ?? null,
      ownerAvatarUrl: repository.owner?.avatarUrl ?? "",
      ownerLogin: repository.owner?.login ?? owner,
    },
    content,
    original: targetFileText,
  };

  return wantsJson ? json(payload) : text(content);
};
