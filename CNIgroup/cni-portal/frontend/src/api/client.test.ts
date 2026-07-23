import { beforeEach, expect, test, vi } from "vitest";
import { apiGet, apiPost } from "./client";

beforeEach(() => {
  vi.restoreAllMocks();
});

test("apiGet requests the /api path with credentials", async () => {
  const fetchMock = vi.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ x: 1 }) }),
  );
  vi.stubGlobal("fetch", fetchMock);

  const r = await apiGet("/me/");
  expect(r).toEqual({ x: 1 });
  const [url, opts] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
  expect(url).toBe("/api/me/");
  expect(opts.method).toBe("GET");
  expect(opts.credentials).toBe("include");
});

test("apiPost sends JSON body and a CSRF header", async () => {
  document.cookie = "csrftoken=abc123";
  const fetchMock = vi.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ ok: true }) }),
  );
  vi.stubGlobal("fetch", fetchMock);

  await apiPost("/auth/login/", { email: "a@cni.test" });
  const [, opts] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
  expect(opts.method).toBe("POST");
  expect(JSON.parse(opts.body as string)).toEqual({ email: "a@cni.test" });
  expect((opts.headers as Record<string, string>)["X-CSRFToken"]).toBe("abc123");
});

test("non-ok responses throw ApiError", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ ok: false, status: 401, json: () => Promise.resolve({ detail: "no" }) })),
  );
  await expect(apiGet("/me/")).rejects.toMatchObject({ status: 401 });
});
