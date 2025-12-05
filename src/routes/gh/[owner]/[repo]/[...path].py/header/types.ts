export interface DepLineData {
  prefix: string;
  quote: string;
  name: string;
  extras: string;
  versionParts: string[];
  marker: string;
  suffix: string;
}

export type HeaderLineData = { kind: "text"; text: string } | { kind: "dep"; line: DepLineData };
