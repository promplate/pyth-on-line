import * as env from "$env/static/public";
import { version } from "pyodide/package.json";

export const indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? (import.meta.env.PROD ? `/pyodide/v${version}/` : `https://cdn.jsdelivr.net/pyodide/v${version}/full/`);

export const preloadPackages = ["micropip", "pure-eval"];
