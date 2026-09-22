import type { SocialPost } from "../api";

type PostPreviewCardProps = {
  post: SocialPost | null;
  storeBrand: string;
  loading: boolean;
};

function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "ST";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
}

export function PostPreviewCard({
  post,
  storeBrand,
  loading,
}: PostPreviewCardProps) {
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

      {post ? (
        <>
          <p className="caption">{post.caption}</p>
          <div className="offer">{post.offer}</div>
          <button type="button" className="cta" tabIndex={-1}>
            {post.cta}
          </button>
          <ul className="hashtags">
            {post.hashtags.map((tag) => (
              <li key={tag}>{tag.startsWith("#") ? tag : `#${tag}`}</li>
            ))}
          </ul>
          {post.usage ? (
            <dl className="usage-mini">
              <div>
                <dt>Est. cost</dt>
                <dd>${post.usage.estimated_usd.toFixed(4)}</dd>
              </div>
              <div>
                <dt>Tokens</dt>
                <dd>{post.usage.total_tokens.toLocaleString()}</dd>
              </div>
              <div>
                <dt>Model</dt>
                <dd className="mono">{post.usage.model}</dd>
              </div>
            </dl>
          ) : null}
          <div className="checklist">
            <strong>Before you post</strong>
            <ul>
              <li>Offer / price matches the brief</li>
              <li>Store name ({storeBrand}) is correct</li>
              <li>Wording looks accurate (no invented claims)</li>
            </ul>
          </div>
        </>
      ) : (
        <div className="empty">
          <p>Your generated post will appear here.</p>
          <span>Enter a brief, then generate.</span>
        </div>
      )}
    </article>
  );
}
