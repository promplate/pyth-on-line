import * as env from "$env/static/public";

export const indexURL = env.PUBLIC_PYODIDE_INDEX_URL ?? (import.meta.env.PROD ? "/pyodide/" : "https://cdn.jsdelivr.net/pyodide/v0.26.1/full/");
