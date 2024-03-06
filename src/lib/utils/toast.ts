import { tick } from "svelte";
import { toast } from "svelte-sonner";

export function withToast<T extends () => Promise<any>>(asyncFunction: T, data: { loading: string; success?: string; duration?: number }): T {
  data.success = data.success ?? data.loading;
  return (async () => {
    const promise: Promise<ReturnType<T>> = asyncFunction();
    await tick();
    toast.promise(promise, data);
    return await promise;
  }) as T;
}
