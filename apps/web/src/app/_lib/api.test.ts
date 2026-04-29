import { afterEach, describe, expect, it, vi } from "vitest";

import { getApiBaseUrl, getAsset, getAssets, getCategories } from "./api";

describe("web API client", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.restoreAllMocks();
  });

  it("uses NEXT_PUBLIC_API_BASE_URL when configured", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://vaultix.example.com");

    expect(getApiBaseUrl()).toBe("https://vaultix.example.com");
  });

  it("prefers VAULTIX_API_INTERNAL_URL for server-side container requests", () => {
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://vaultix.example.com");
    vi.stubEnv("VAULTIX_API_INTERNAL_URL", "http://api:8000");

    expect(getApiBaseUrl()).toBe("http://api:8000");
  });

  it("fetches categories, assets, and asset detail", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/api/v1/meta/categories")) {
        return response({ data: [{ id: 1, slug: "business", name: "비즈니스" }] });
      }
      if (url.endsWith("/api/v1/assets?limit=24")) {
        return response({ data: [{ id: 101, slug: "asset", title: "자산" }], meta: {} });
      }
      if (url.endsWith("/api/v1/assets/asset")) {
        return response({ data: { id: 101, slug: "asset", title: "자산 상세" } });
      }
      return response({}, 404);
    });
    vi.stubGlobal("fetch", fetchMock);
    vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", "https://vaultix.example.com");

    await expect(getCategories()).resolves.toEqual([{ id: 1, slug: "business", name: "비즈니스" }]);
    await expect(getAssets()).resolves.toEqual([{ id: 101, slug: "asset", title: "자산" }]);
    await expect(getAsset("asset")).resolves.toEqual({ id: 101, slug: "asset", title: "자산 상세" });
  });
});

function response(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
  } as Response;
}
