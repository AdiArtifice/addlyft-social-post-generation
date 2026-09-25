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

export type PipelineResult = {
  optimized_prompt?: string;
  image_base64: string | null;
  mime_type: string | null;
  filename: string | null;
  person_generation?: string | null;
  caption: string | null;
  offer: string | null;
  cta: string | null;
  hashtags: string[] | null;
  text_error: string | null;
  store_brand?: string;
  usage?: {
    optimize?: UsageInfo | null;
    image?: PosterUsage | null;
    caption?: UsageInfo | null;
  } | null;
  api_calls?: number;
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
  poster?: Pick<PosterResult, "image_base64" | "mime_type"> | null,
): Promise<SocialPost> {
  const payload: Record<string, unknown> = {
    brief,
    variation,
    store_brand: storeBrand,
  };
  if (poster?.image_base64) {
    payload.image_base64 = poster.image_base64;
    payload.mime_type = poster.mime_type || "image/png";
  }

  const response = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
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

export async function generatePipeline(
  brief: string,
  files: File[],
  roles: RefRole[],
  allowPeople: boolean,
  storeBrand: string = DEFAULT_STORE_BRAND,
): Promise<PipelineResult> {
  const fd = new FormData();
  fd.append("brief", brief.trim());
  fd.append("roles", JSON.stringify(roles.slice(0, files.length)));
  fd.append("allow_people", allowPeople ? "true" : "false");
  fd.append("store_brand", storeBrand);
  for (const file of files.slice(0, 3)) {
    fd.append("refs", file, file.name);
  }

  const response = await fetch("/api/generate-pipeline", {
    method: "POST",
    body: fd,
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(
      detailMessage(body, "Generation failed. Please try again."),
    );
  }
  return body as PipelineResult;
}
