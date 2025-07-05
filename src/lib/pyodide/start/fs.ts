import type { FS } from "./emscripten_fs";
import type { PyodideInterface } from "pyodide";

import { dev } from "$app/environment";

export function setupWatcher(py: PyodideInterface) {
  const { trackingDelegate } = py.FS as unknown as FS;

  const _handle: (change: 1 | 2 | 3, path: string) => void = py.pyimport("watchfiles.handle_fs_event");
  // 1. added: A new file or directory was added.
  // 2. modified: A file or directory was modified, can be either a metadata or data change.
  // 3. deleted: A file or directory was deleted.
  const handle = (change: 1 | 2 | 3, path: string) => {
    if (!path.startsWith("/dev")) {
      setTimeout(() => {
        _handle(change, path);
      }, 0);
    }
  };

  trackingDelegate.onWriteToFile = (path: string) => {
    handle(2, path); // modified
  };

  trackingDelegate.onMakeDirectory = (path: string) => {
    dev && console.warn("make-directory", path);
    handle(1, path); // added
  };

  trackingDelegate.onMakeSymlink = (oldpath: string, newpath: string) => {
    dev && console.warn("make-symlink", oldpath, newpath);
    handle(1, newpath); // added
  };

  trackingDelegate.onMovePath = (old_path: string, new_path: string) => {
    dev && console.warn("move-path", old_path, new_path);
    handle(3, old_path); // deleted
    handle(1, new_path); // added
  };

  trackingDelegate.onDeletePath = (path: string) => {
    dev && console.warn("delete-path", path);
    handle(3, path); // deleted
  };
};
