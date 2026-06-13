import { api } from "./api";

/** Proxy external images through MARK API (hotlink / CORS). */
export function proxiedImageUrl(url: string | null | undefined, authToken?: string | null): string {
  if (!url?.trim()) return "";
  const raw = url.trim();
  if (raw.startsWith("data:") || raw.includes("/media/proxy")) {
    return raw;
  }
  const token =
    authToken ?? localStorage.getItem("mark_token") ?? localStorage.getItem("token");
  const q = new URLSearchParams({ url: raw });
  if (token) q.set("token", token);
  return `${api.base}/media/proxy?${q.toString()}`;
}
