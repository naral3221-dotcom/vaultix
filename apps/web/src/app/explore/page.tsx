import { getAssets, getCategories } from "../_lib/api";
import { ExploreView } from "./explore-view";

type ExplorePageProps = {
  searchParams?: {
    category?: string;
  };
};

export const dynamic = "force-dynamic";

export default async function ExplorePage({ searchParams }: ExplorePageProps) {
  const selectedCategory = searchParams?.category;
  const [categories, assets] = await Promise.all([
    getCategories(),
    getAssets({ category: selectedCategory, limit: 24 }),
  ]);

  return <ExploreView assets={assets} categories={categories} selectedCategory={selectedCategory} />;
}
