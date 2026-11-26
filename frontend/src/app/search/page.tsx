import { MediaSearchView } from "@/components/media/MediaSearchView";

interface SearchPageProps {
  readonly searchParams: Promise<{ category?: string; q?: string }>;
}

/** Public catalog search page pre-populated from URL query params. */
export default async function SearchPage({ searchParams }: SearchPageProps) {
  const resolved = await searchParams;
  return (
    <MediaSearchView
      initialCategory={resolved.category ?? "movie"}
      initialQuery={resolved.q ?? ""}
    />
  );
}
