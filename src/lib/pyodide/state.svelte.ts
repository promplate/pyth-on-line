// Console instances share the single cached browser runtime's readiness.
export const pyodideState = $state({ ready: false });
