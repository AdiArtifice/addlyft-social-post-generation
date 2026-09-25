import { useEffect, useState } from "react";
import type { PosterResult, SocialPost } from "../api";

type PostPreviewCardProps = {
  post: SocialPost | null;
  poster: PosterResult | null;
  storeBrand: string;
  loading: boolean;
  imageError?: string | null;
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

export function PostPreviewCard({
  post,
  poster,
  storeBrand,
  loading,
  imageError = null,
}: PostPreviewCardProps) {
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const hasPoster = Boolean(poster?.image_base64 && poster?.mime_type);
  const hasCopy = Boolean(post);
  const posterSrc =
    hasPoster && poster
      ? `data:${poster.mime_type};base64,${poster.image_base64}`
      : null;

  useEffect(() => {
    if (!hasPoster) setLightboxOpen(false);
  }, [hasPoster, posterSrc]);

  useEffect(() => {
    if (!lightboxOpen) return;
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setLightboxOpen(false);
    }
    window.addEventListener("keydown", onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      window.removeEventListener("keydown", onKey);
      document.body.style.overflow = prev;
    };
  }, [lightboxOpen]);

  return (
    <article className={`post-card ${loading ? "is-loading" : ""}`}>
      <div className="draft-tag">Draft · not published</div>
      <header className="post-header">
        <div className="avatar" aria-hidden="true">
          {initials(storeBrand)}
        </div>
        <div>
          <strong>{storeBrand}</strong>
          <p>Sponsored · Just now</p>
        </div>
      </header>

      {imageError ? <p className="error tight">{imageError}</p> : null}

      {posterSrc ? (
        <div className="poster-frame">
          <button
            type="button"
            className="poster-open"
            onClick={() => setLightboxOpen(true)}
            aria-label="Enlarge poster"
          >
            <img
              className="post-poster"
              src={posterSrc}
              alt="Generated social post advertisement"
            />
          </button>
          <p className="poster-hint">Click to enlarge</p>
        </div>
      ) : null}

      {hasCopy ? (
        <>
          <p className="caption">{post!.caption}</p>
          <div className="offer">{post!.offer}</div>
          <button type="button" className="cta" tabIndex={-1}>
            {post!.cta}
          </button>
          <ul className="hashtags">
            {post!.hashtags.map((tag) => (
              <li key={tag}>{tag.startsWith("#") ? tag : `#${tag}`}</li>
            ))}
          </ul>
          <div className="checklist">
            <strong>Before you post</strong>
            <ul>
              <li>Offer / price matches the brief</li>
              <li>Store name ({storeBrand}) is correct</li>
              <li>Wording looks accurate (no invented claims)</li>
              {hasPoster ? <li>On-image spelling looks right</li> : null}
            </ul>
          </div>
        </>
      ) : null}

      {!hasPoster && !hasCopy && !loading ? (
        <div className="empty">
          <p>Your social post will appear here.</p>
          <span>
            Generate to create the poster and caption together as one result.
          </span>
        </div>
      ) : null}

      {hasPoster && !hasCopy && !loading ? (
        <div className="empty compact">
          <p>Poster ready — caption could not be generated.</p>
          <span>Fix the brief or try Generate again.</span>
        </div>
      ) : null}

      {lightboxOpen && posterSrc ? (
        <div
          className="poster-lightbox"
          role="dialog"
          aria-modal="true"
          aria-label="Full-size poster"
          onClick={() => setLightboxOpen(false)}
        >
          <button
            type="button"
            className="lightbox-close"
            aria-label="Close"
            onClick={() => setLightboxOpen(false)}
          >
            Close
          </button>
          <img
            src={posterSrc}
            alt="Full-size social post advertisement"
            onClick={(event) => event.stopPropagation()}
          />
        </div>
      ) : null}
    </article>
  );
}
