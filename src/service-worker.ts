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

sw.addEventListener("install", (event) => {
  event.waitUntil(addFilesToCache());
});

// Remove previous cached data from disk
async function deleteOldCaches() {
  for (const key of await caches.keys()) {
    if (key !== CACHE)
      await caches.delete(key);
  }
}

sw.addEventListener("activate", (event) => {
  event.waitUntil(deleteOldCaches());
});

async function fetchWithProxy(request: Request) {
  try {
    return await fetch(request);
  }
  catch (e) {
    const url = new URL(request.url);
    if ([location.hostname, "localhost", "127.0.0.1", "::1"].includes(url.hostname))
      throw e;
    return await fetch(`/proxy?url=${encodeURIComponent(request.url)}`, request);
  }
}

sw.addEventListener("fetch", (event) => {
  if (!event.request.url.startsWith("http"))
    return;

  if (event.request.method !== "GET") {
    return event.respondWith(fetchWithProxy(event.request));
  }

  async function respond() {
    const url = new URL(event.request.url);
    const cache = await caches.open(CACHE);

    // Helper: identify pyodide-related requests (runtime assets, CDN content, wheels)
    const isPyodideRequest = (() => {
      // direct pyodide runtime files
      if (allAssets.includes(url.pathname)) return true;
      // anything under the pyodide CDN/base index
      if (String(url).startsWith(indexURL)) return true;
      // wheel requests, including via proxy
      if (url.pathname.endsWith(".whl")) return true;
      const proxied = url.searchParams.get("url");
      if (proxied && /\.whl($|\?)/.test(proxied)) return true;
      return false;
    })();

    // For all pyodide assets and wheels: cache-first, then network, then cache the result
    if (isPyodideRequest) {
      const cached = await cache.match(event.request);
      if (cached) return cached;
      try {
        const networkResponse = await fetchWithProxy(event.request.clone());
        if (networkResponse instanceof Response && networkResponse.status === 200) {
          cache.put(event.request, networkResponse.clone());
        }
        return networkResponse;
      }
      catch (err) {
        const fallback = await cache.match(event.request);
        if (fallback) return fallback;
        throw err;
      }
    }

    // for everything else, try the network first, but
    // fall back to the cache if we're offline
    try {
      const response = await fetchWithProxy(event.request.clone()); // Clone the request before first attempt to avoid "Body is already used" error

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
