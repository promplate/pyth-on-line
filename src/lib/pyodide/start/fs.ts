import type { FS } from "./emscripten_fs";
import type { PyodideInterface } from "pyodide";

export function setupWatcher(py: PyodideInterface) {
  //  onOpenFile: (path: string, trackingFlags: number) => unknown;
  //  onCloseFile: (path: string) => unknown;
  //  onSeekFile: (path: string, position: number, whence: number) => unknown;
  //  onReadFile: (path: string, bytesRead: number) => unknown;
  //  onWriteToFile: (path: string, bytesWritten: number) => unknown;
  //  onMakeDirectory: (path: string, mode: number) => unknown;
  //  onMakeSymlink: (oldpath: string, newpath: string) => unknown;
  //  willMovePath: (old_path: string, new_path: string) => unknown;
  //  onMovePath: (old_path: string, new_path: string) => unknown;
  //  willDeletePath: (path: string) => unknown;
  //  onDeletePath: (path: string) => unknown;
  const { trackingDelegate } = py.FS as unknown as FS;

  // added = 1
  // """A new file or directory was added."""
  // modified = 2
  // """A file or directory was modified, can be either a metadata or data change."""
  // deleted = 3
  // """A file or directory was deleted."""
  const _handle: (change: 1 | 2 | 3, path: string) => void = py.pyimport("watchfiles.handle_fs_event");

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
    console.warn("make-directory", path);
    handle(1, path); // added
  };

  trackingDelegate.onMakeSymlink = (oldpath: string, newpath: string) => {
    console.warn("make-symlink", oldpath, newpath);
    handle(1, newpath); // added
  };

  trackingDelegate.onMovePath = (old_path: string, new_path: string) => {
    console.warn("move-path", old_path, new_path);
    handle(3, old_path); // deleted
    handle(1, new_path); // added
  };

  trackingDelegate.onDeletePath = (path: string) => {
    console.warn("delete-path", path);
    handle(3, path); // deleted
  };
};
