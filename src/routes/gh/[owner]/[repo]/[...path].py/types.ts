export interface DependencySource {
  type: "pep723" | "pyproject" | "none";
  path: string | null;
}

export interface GitHubIssue {
  number: number;
  title: string;
  url: string;
  createdAt: string;
}

export interface GitHubRelease {
  tagName: string;
  name: string | null;
  publishedAt: string;
}

export interface RepoInfo {
  stargazers: number;
  forks: number;
  watchers: number;
  description: string;
  defaultBranch: string | null;
  ownerAvatarUrl: string;
  ownerLogin: string;
  isArchived: boolean;
  primaryLanguage: { name: string; color: string } | null;
  licenseInfo: { name: string; spdxId: string } | null;
  openIssuesCount: number;
  recentIssues: GitHubIssue[];
  latestRelease: GitHubRelease | null;
  createdAt: string;
  pushedAt: string;
  fileLastUpdatedAt: string;
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
