import { useEffect, useState } from "react";
import { apiGet } from "./client";

export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    apiGet<T>(path)
      .then((d) => alive && (setData(d), setError(null)))
      .catch(() => alive && setError("Failed to load."))
      .finally(() => alive && setLoading(false));
    return () => {
      alive = false;
    };
  }, [path, nonce]);

  return { data, error, loading, reload: () => setNonce((n) => n + 1) };
}
