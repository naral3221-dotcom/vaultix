export type Category = {
  id: number;
  slug: string;
  name: string;
};

export type AssetCard = {
  id: number;
  slug: string;
  title: string;
  alt_text: string | null;
  thumbnail_url: string | null;
  preview_url: string | null;
  category: Category | null;
  tags: Array<{ slug: string; name: string }>;
  stats: { downloads: number; favorites: number };
};

export type AssetDetail = AssetCard & {
  description: string | null;
  license_summary_url: string;
};

export function getApiBaseUrl() {
  return process.env.VAULTIX_API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8302";
}

export async function getCategories(): Promise<Category[]> {
  const payload = await getJson<{ data: Category[] }>("/api/v1/meta/categories");
  return payload.data;
}

export async function getAssets(params: { category?: string; limit?: number } = {}): Promise<AssetCard[]> {
  const search = new URLSearchParams();
  search.set("limit", String(params.limit ?? 24));
  if (params.category) {
    search.set("category", params.category);
  }
  const payload = await getJson<{ data: AssetCard[] }>(`/api/v1/assets?${search.toString()}`);
  return payload.data;
}

export async function getAsset(slug: string): Promise<AssetDetail | null> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/assets/${encodeURIComponent(slug)}`, {
    cache: "no-store",
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Vaultix API request failed: ${response.status}`);
  }
  const payload = (await response.json()) as { data: AssetDetail };
  return payload.data;
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Vaultix API request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}
