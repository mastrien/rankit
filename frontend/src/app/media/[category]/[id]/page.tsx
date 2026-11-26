import { MediaDetailView } from "@/components/media/MediaDetailView";

interface MediaDetailPageProps {
  readonly params: Promise<{ category: string; id: string }>;
}

/** Public detail route for any cataloged Rankit media entry. */
export default async function MediaDetailPage({ params }: MediaDetailPageProps) {
  const { category, id } = await params;
  return <MediaDetailView category={category} externalId={id} />;
}
