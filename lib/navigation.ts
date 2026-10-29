import type { Recommendation } from "@/types/analysis";

export type GalleryFilter = "ALL" | Recommendation;

export function readGalleryFilter(value: string | null): GalleryFilter {
  return value === "KEEP" || value === "REVIEW" || value === "RECOMMEND_DELETE"
    ? value
    : "ALL";
}

export function galleryHref(filter: GalleryFilter): string {
  return filter === "ALL" ? "/gallery" : `/gallery?filter=${filter}`;
}

// A return destination can only be a gallery/groups route in this app.
export function photoReturnHref(value: string | null): string {
  if (!value || !value.startsWith("/") || value.startsWith("//"))
    return "/gallery";
  try {
    const url = new URL(value, "https://smart-gallery.invalid");
    if (
      url.origin !== "https://smart-gallery.invalid" ||
      (url.pathname !== "/gallery" && url.pathname !== "/groups")
    )
      return "/gallery";
    const route =
      url.pathname === "/gallery"
        ? galleryHref(readGalleryFilter(url.searchParams.get("filter")))
        : "/groups";
    const anchor = /^#photo-[a-zA-Z0-9_-]+$/.test(url.hash) ? url.hash : "";
    return route + anchor;
  } catch {
    return "/gallery";
  }
}
