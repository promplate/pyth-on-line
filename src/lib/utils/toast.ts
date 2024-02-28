import { toast } from "svelte-sonner";

export function withToast<T extends () => Promise<any>>(asyncFunction: T, data: { loading: string; success: string }): T {
  return (async () => {
    const promise: Promise<ReturnType<T>> = asyncFunction();
    toast.promise(promise, data);
    return await promise;
  }) as T;
}
