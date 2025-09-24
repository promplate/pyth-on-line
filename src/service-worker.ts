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

// Helper function to determine if a URL is a Pyodide asset
function isPyodideAsset(url: string): boolean {
  return pyodideAssets.some(asset => url.includes(asset));
}

// Helper function to determine if a URL is a Pyodide wheel/package
function isPyodideWheel(url: string): boolean {
  // Check if URL contains Pyodide base URL and is a wheel or package
  if (baseURL && url.includes(`${baseURL}/`)) {
    return url.includes('.whl') || url.includes('/packages/');
  }

  // Also check for common Pyodide wheel patterns
  return url.includes('.whl') &&
         (url.includes('/pyodide/') || url.includes('cdn.jsdelivr.net/pyodide'));
}

// Helper function to determine if a URL is from Pyodide CDN
function isPyodideCDN(url: string): boolean {
  if (baseURL && url.includes(`${baseURL}/`)) {
    return true;
  }
  return url.startsWith('https://cdn.jsdelivr.net/pyodide/') ||
         (url.includes('/pyodide/') && url.includes('.whl'));
}

// Helper function to determine if a request should use cache-first strategy
function shouldUseCacheFirst(url: string): boolean {
  return isPyodideAsset(url) || isPyodideWheel(url) || isPyodideCDN(url) || allAssets.includes(url);
}

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

// Cache-first strategy for Pyodide assets and wheels
async function handleCacheFirstRequest(request: Request, cache: Cache): Promise<Response> {
  const url = new URL(request.url);

  // First, try to serve from cache
  const cachedResponse = await cache.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // If not in cache, fetch from network
  try {
    const response = await fetchWithProxy(request.clone());

    // Validate response
    if (!(response instanceof Response)) {
      throw new TypeError("invalid response from fetch");
    }

    if (response.status === 200) {
      // Cache the response for future use
      cache.put(request, response.clone());
    }

    return response;
  }
  catch (err) {
    // If network fails and we can't find it in cache, throw error
    throw err;
  }
}

// Network-first strategy for other requests
async function handleNetworkFirstRequest(request: Request, cache: Cache): Promise<Response> {
  try {
    const response = await fetchWithProxy(request.clone());

    // Validate response
    if (!(response instanceof Response)) {
      throw new TypeError("invalid response from fetch");
    }

    if (response.status === 200) {
      // Cache the response for future use
      cache.put(request, response.clone());
    }

    return response;
  }
  catch (err) {
    // Fall back to cache if network fails
    const cachedResponse = await cache.match(request);

    if (cachedResponse) {
      return cachedResponse;
    }

    // If no cache and network fails, throw error
    throw err;
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

    // Use cache-first strategy for Pyodide assets and wheels
    if (shouldUseCacheFirst(url.pathname) || String(url).startsWith(indexURL)) {
      return await handleCacheFirstRequest(event.request, cache);
    }

    // Use network-first strategy for other requests
    return await handleNetworkFirstRequest(event.request, cache);
  }

  event.respondWith(respond());
});
