export const DEFAULT_STORE_BRAND = "AMPM Woodstock";

export type UsageInfo = {
  prompt_tokens: number;
  output_tokens: number;
  thoughts_tokens: number;
  total_tokens: number;
  estimated_usd: number;
  model: string;
};

export type SocialPost = {
  caption: string;
  offer: string;
  cta: string;
  hashtags: string[];
  usage?: UsageInfo | null;
  store_brand?: string;
};

export type PosterUsage = {
  prompt_tokens?: number;
  text_output_tokens?: number;
  thoughts_tokens?: number;
  image_output_tokens?: number;
  total_tokens?: number;
  estimated_usd?: number;
  wall_seconds?: number;
  model?: string;
  aspect_ratio?: string;
  image_size?: string;
};

export type PosterResult = {
  image_base64: string;
  mime_type: string;
  filename: string;
  usage?: PosterUsage | null;
  api_calls?: number;
  model_text?: string;
  person_generation?: string;
  store_brand?: string;
};

export type RefRole = "auto" | "product" | "style" | "brand" | "background";

function detailMessage(body: unknown, fallback: string): string {
  if (body && typeof body === "object" && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((d) =>
          d && typeof d === "object" && "msg" in d
            ? String((d as { msg: unknown }).msg)
            : JSON.stringify(d),
        )
        .join("; ");
    }
  }
  return fallback;
}

export async function generatePost(
  brief: string,
  variation = false,
  storeBrand: string = DEFAULT_STORE_BRAND,
): Promise<SocialPost> {
  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brief,
      variation,
      store_brand: storeBrand,
    }),
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(detailMessage(body, "Generation failed. Please try again."));
  }
  return body as SocialPost;
}

export async function generatePoster(
  brief: string,
  files: File[],
  roles: RefRole[],
  allowPeople: boolean,
  storeBrand: string = DEFAULT_STORE_BRAND,
): Promise<PosterResult> {
  const fd = new FormData();
  fd.append("prompt", brief.trim());
  fd.append("roles", JSON.stringify(roles.slice(0, files.length)));
  fd.append("allow_people", allowPeople ? "true" : "false");
  fd.append("store_brand", storeBrand);
  for (const file of files.slice(0, 3)) {
    fd.append("refs", file, file.name);
  }

  const response = await fetch("/api/generate-image", {
    method: "POST",
    body: fd,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      detailMessage(body, "Poster generation failed. Please try again."),
    );
  }
  return body as PosterResult;
}
