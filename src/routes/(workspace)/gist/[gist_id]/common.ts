export interface GistResponse {
  files: {
    [filename: string]: {
      content: string;
    };
  };
};

export function transformFiles(files: GistResponse["files"]) {
  return Object.fromEntries(Object.entries(files).map(([filename, { content }]) => [filename, content]));
}
