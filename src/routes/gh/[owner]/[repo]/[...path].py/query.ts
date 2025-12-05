interface QueryArgs {
  owner: string;
  repo: string;
  ref: string;
  filePath: string;
  pyprojectPaths: string[];
}

export function buildQuery(args: QueryArgs) {
  const { owner, repo, ref, filePath, pyprojectPaths } = args;
  const escapedRef = escapeGraphQL(ref);
  const escapedFile = escapeGraphQL(filePath);

  // Helper to get history for a file at a specific ref
  const getHistoryField = (filename: string, fieldName: string) => {
    if (ref === "HEAD") {
      return `${fieldName}: defaultBranchRef { target { ... on Commit { history(first: 1, path: "${escapedFile}") { nodes { committedDate } } } } }`;
    }
    return `${fieldName}: ref(qualifiedName: "${escapedRef}") { target { ... on Commit { history(first: 1, path: "${escapedFile}") { nodes { committedDate } } } } }`;
  };

  const repoFields = [
    "stargazerCount",
    "forkCount",
    "description",
    "watchers { totalCount }",
    "pushedAt",
    "createdAt",
    "defaultBranchRef { name }",
    "owner { login avatarUrl }",
    "isArchived",
    "primaryLanguage { name color }",
    "licenseInfo { name spdxId }",
    "issues(first: 3, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) { totalCount nodes { number title url createdAt } }",
    "releases(first: 1, orderBy: {field: CREATED_AT, direction: DESC}) { nodes { tagName name publishedAt } }",
    `target: object(expression: "${escapedRef}:${escapedFile}") { ... on Blob { text } }`,
    getHistoryField(filePath, "targetHistory"),
    ...pyprojectPaths.map((path, i) => `pyproject${i}: object(expression: "${escapedRef}:${escapeGraphQL(path)}") { ... on Blob { text } }`),
    ...pyprojectPaths.map((path, i) => {
      if (ref === "HEAD") {
        return `pyprojectHistory${i}: defaultBranchRef { target { ... on Commit { history(first: 1, path: "${escapeGraphQL(path)}") { nodes { committedDate } } } } }`;
      }
      return `pyprojectHistory${i}: ref(qualifiedName: "${escapedRef}") { target { ... on Commit { history(first: 1, path: "${escapeGraphQL(path)}") { nodes { committedDate } } } } }`;
    }),
  ].join("\n");

  return `
    query {
      repository(owner: "${escapeGraphQL(owner)}", name: "${escapeGraphQL(repo)}") {
        ${repoFields}
      }
    }
  `;
}

function escapeGraphQL(value: string) {
  return value.replace(/\\/g, "\\\\").replace(/"/g, "\\\"");
}

export function collectDirectories(filePath: string) {
  const parts = filePath.split("/");
  parts.pop();
  const dirs: string[] = [];
  for (let i = parts.length; i >= 0; i -= 1) {
    dirs.push(parts.slice(0, i).join("/").replace(/^\/+|\/+$/g, ""));
  }
  return dirs;
}
