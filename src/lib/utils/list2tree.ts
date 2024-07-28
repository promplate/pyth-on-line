export interface File {
  type: "file";
  name: string;
}

export interface Folder {
  type: "folder";
  name: string;
  children: Tree;
}

export type Tree = (File | Folder)[];

export function unflatten(paths: string[]) {
  const root: Folder = { type: "folder", name: "", children: [] };

  paths.forEach((path) => {
    const parts = path.split("/");
    let currentFolder = root;

    parts.forEach((part, index) => {
      // Check if the part is the last part in the path
      const isFile = index === parts.length - 1;

      // Try to find the child in the current folder
      let child = currentFolder.children.find(child => child.name === part);

      if (!child) {
        if (isFile) {
          // If it's a file, create a File object
          child = { type: "file", name: part };
        }
        else {
          // If it's a folder, create a Folder object
          child = { type: "folder", name: part, children: [] };
        }

        // Add the child to the current folder's children
        currentFolder.children.push(child);
      }

      // Move to the child folder if it's a folder
      if (!isFile) {
        currentFolder = child as Folder;
      }
    });
  });

  return root.children;
}
