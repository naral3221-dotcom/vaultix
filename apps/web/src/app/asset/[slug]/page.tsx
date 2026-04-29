import { notFound } from "next/navigation";

import { getAsset } from "../../_lib/api";
import { AssetDetailView } from "./asset-detail-view";

type AssetPageProps = {
  params: {
    slug: string;
  };
};

export const dynamic = "force-dynamic";

export default async function AssetPage({ params }: AssetPageProps) {
  const asset = await getAsset(params.slug);
  if (!asset) {
    notFound();
  }

  return <AssetDetailView asset={asset} />;
}
