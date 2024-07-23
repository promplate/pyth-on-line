const globalCache = new Map<string, any>();

export function cacheGlobally<T extends () => R, R>(key: string, target: T): T {
  return (() => {
    const cache = globalCache as Map<string, R>;

    if (cache.has(key))
      return cache.get(key);

    const result = target();
    cache.set(key, result);
    return result;
  }) as T;
}

export function cacheSingleton<T extends () => any>(target: T): T {
  const UNSET = {};
  let result: any = UNSET;

  return (() => {
    if (result !== UNSET)
      return result;

    result = target();
    return result;
  }) as T;
}
