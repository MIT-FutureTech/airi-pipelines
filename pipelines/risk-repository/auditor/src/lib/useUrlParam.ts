import { useCallback, useState } from "react";

export function useUrlParam(
  key: string,
): [string | null, (value: string | null) => void] {
  const [value, setValueState] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get(key);
  });

  const setValue = useCallback(
    (next: string | null) => {
      setValueState(next);
      const params = new URLSearchParams(window.location.search);
      if (next === null) {
        params.delete(key);
      } else {
        params.set(key, next);
      }
      const search = params.toString();
      const url = search
        ? `${window.location.pathname}?${search}`
        : window.location.pathname;
      window.history.replaceState({}, "", url);
    },
    [key],
  );

  return [value, setValue];
}
