import { createContext } from "svelte";

export const [getSearchState, setSearchState] = createContext<{ query: string; setQuery: (value: string) => void }>();
