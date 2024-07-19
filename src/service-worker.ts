/// <reference types="@sveltejs/kit" />
/// <reference no-default-lib="true"/>
/// <reference lib="esnext" />
/// <reference lib="webworker" />

import type lockfile from "pyodide/pyodide-lock.json";

import { indexURL, preloadPackages } from "./lib/pyodide/common";
import { build, files, prerendered, version } from "$service-worker";

const sw = globalThis as unknown as ServiceWorkerGlobalScope;

// Create a unique cache name for this deployment
const CACHE = `v-${version}`;

const websiteAssets = [
  ...prerendered, // prerendered pages and endpoints
  ...build, // the app itself
  ...files, // everything in `static`
];

const pyodideAssets = [
  "pyodide.asm.js",
  "pyodide.asm.wasm",
  "python_stdlib.zip",
  "pyodide-lock.json",
];

const allAssets = [...websiteAssets, ...pyodideAssets];

const baseURL = indexURL ? indexURL?.replace(/\/$/, "") : "";

sw.addEventListener("install", (event) => {
  // Create a new cache and add all files to it
  async function addFilesToCache() {
    const cache = await caches.open(CACHE);
    await cache.addAll(pyodideAssets.map(filename => `${baseURL}/${filename}`));

    const { packages }: typeof lockfile = await cache.match(`${baseURL}/pyodide-lock.json`).then(res => res?.json());
    function getUrls(names: string[]) {
      const urls = new Set<string>();
      for (const name of names) {
        const info = packages[name as keyof typeof packages];
        urls.add(info.file_name);
        if (info.depends) {
          getUrls(info.depends).forEach(url => urls.add(url));
        }
      }
      return urls;
    }
    await cache.addAll([...getUrls(preloadPackages)].map(url => `${baseURL}/${url}`));

    await cache.addAll(websiteAssets);
  }

  event.waitUntil(addFilesToCache());
});

sw.addEventListener("activate", (event) => {
  // Remove previous cached data from disk
  async function deleteOldCaches() {
    for (const key of await caches.keys()) {
      if (key !== CACHE)
        await caches.delete(key);
    }
  }

  event.waitUntil(deleteOldCaches());
});

sw.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET" || !event.request.url.startsWith("http"))
    return;

  async function respond() {
    const url = new URL(event.request.url);
    const cache = await caches.open(CACHE);

    // immutable assets always be served from the cache
    if (allAssets.includes(url.pathname) || String(url).startsWith(indexURL)) {
      const response = await cache.match(event.request);

      if (response) {
        return response;
      }
    }

    // for everything else, try the network first, but
    // fall back to the cache if we're offline
    try {
      const response = await fetch(event.request);

      // if we're offline, fetch can return a value that is not a Response
      // instead of throwing - and we can't pass this non-Response to respondWith
      if (!(response instanceof Response)) {
        throw new TypeError("invalid response from fetch");
      }

      if (response.status === 200) {
        cache.put(event.request, response.clone());
      }

      return response;
    }
    catch (err) {
      const response = await cache.match(event.request);

      if (response) {
        return response;
      }

      // if there's no cache, then just error out
      // as there is nothing we can do to respond to this request
      throw err;
    }
  }

  event.respondWith(respond());
});
