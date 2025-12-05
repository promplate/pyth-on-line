const fileFragment = `
  fragment fileBlob on GitObject {
    ... on Blob { text }
  }
`;

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

  const repoFields = [
    "stargazerCount",
    "forkCount",
    "description",
    "watchers { totalCount }",
    "defaultBranchRef { name }",
    "owner { login avatarUrl }",
    `target: object(expression: "${escapedRef}:${escapedFile}") { ...fileBlob }`,
    ...pyprojectPaths.map((path, i) => `pyproject${i}: object(expression: "${escapedRef}:${escapeGraphQL(path)}") { ...fileBlob }`),
  ].join("\n");

  return `
    query {
      repository(owner: "${escapeGraphQL(owner)}", name: "${escapeGraphQL(repo)}") {
        ${repoFields}
      }
    }
    ${fileFragment}
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
