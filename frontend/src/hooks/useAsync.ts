import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../services/apiClient";
import { getErrorMessage } from "../utils/messages";

export type AsyncState<T> =
  | { status: "loading" }
  | { status: "success"; data: T }
  | { status: "error"; message: string; httpStatus: number | null };

// Runs an async loader when the component mounts (and when deps change),
// tracking loading / success / error. reload() runs it again.
export function useAsync<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [state, setState] = useState<AsyncState<T>>({ status: "loading" });
  const [reloadKey, setReloadKey] = useState(0);

  const load = useCallback(loader, deps);

  useEffect(() => {
    let ignore = false;
    setState((previous) => (previous.status === "success" ? previous : { status: "loading" }));
    load()
      .then((data) => {
        if (!ignore) {
          setState({ status: "success", data });
        }
      })
      .catch((error: unknown) => {
        if (!ignore) {
          setState({
            status: "error",
            message: getErrorMessage(error),
            httpStatus: error instanceof ApiError ? error.status : null,
          });
        }
      });
    return () => {
      ignore = true;
    };
  }, [load, reloadKey]);

  const reload = useCallback(() => setReloadKey((key) => key + 1), []);
  return { state, reload };
}
