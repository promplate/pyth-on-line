import { writable } from "svelte/store";

export const pyodideReady = writable(false);

export const currentPushBlock = writable<(source: string) => any>(() => {});
