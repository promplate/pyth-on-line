export interface DependencySource {
  type: "pep723" | "pyproject" | "none";
  path: string | null;
}

export interface RepoInfo {
  stargazers: number;
  forks: number;
  watchers: number;
  description: string;
  defaultBranch: string | null;
  ownerAvatarUrl: string;
  ownerLogin: string;
}

export interface Payload {
  owner: string;
  repo: string;
  ref: string;
  filePath: string;
  githubUrl: string;
  dependencies: string[];
  dependencySource: DependencySource;
  pep723: { present: boolean; dependencies: string[] };
  pyprojectPaths: Array<{ path: string; exists: boolean; used: boolean }>;
  repository: RepoInfo;
  content: string;
  original: string;
}
