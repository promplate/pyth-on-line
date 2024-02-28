import ExplainError from "./explain-error.j2?raw";
import Groundings from "./groundings.j2?raw";
import initPromplate from "$lib/pyodide/entries";

export default async () => {
  const { Template } = await initPromplate();

  return {
    ExplainError: new Template(ExplainError),
    Groundings: new Template(Groundings),
  };
};
