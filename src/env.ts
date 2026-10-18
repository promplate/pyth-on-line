import { defineEnvVars } from "@sveltejs/kit/env";

export const variables = defineEnvVars({
  GITHUB_CLIENT_SECRET: { static: true, schema: value => value },
  GITHUB_TOKEN: { schema: value => value },
  LIBRARIES_IO_API_KEY: { static: true, schema: value => value },
  PUBLIC_GITHUB_CLIENT_ID: { public: true, static: true, schema: value => value },
  PUBLIC_HEAD_SCRIPTS: { public: true, static: true, schema: value => value },
  PUBLIC_LLM_MODEL: { public: true, static: true, schema: value => value },
  PUBLIC_OPENAI_API_KEY: { public: true, static: true, schema: value => value },
  PUBLIC_OPENAI_BASE_URL: { public: true, static: true, schema: value => value },
  PUBLIC_ORIGIN_TRIAL_TOKEN: { public: true, static: true, schema: value => value },
  PUBLIC_PYODIDE_INDEX_URL: { public: true, static: true, schema: value => value },
  PUBLIC_PYPI_INDEX_URL: { public: true, static: true, schema: value => value },
});
