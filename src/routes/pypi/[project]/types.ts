export interface RegistryResponse {
  info: {
    name: string;
    version: string;
    summary?: string;
    keywords?: string;
    classifiers: string[];
    requires_python: string;
    requires_dist: string[];
    description: string;
    description_content_type: string;
    author: string | null;
    author_email: string | null;
    license: string;
  };
  releases: {
    [version: string]: unknown[];
  };
}
