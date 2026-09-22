import type { PosterResult } from "../api";

type PosterPreviewProps = {
  poster: PosterResult | null;
  loading: boolean;
  error: string | null;
};

function fmtUsd(n: number | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return `$${n.toFixed(4)}`;
}

function fmtSec(n: number | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return `${n.toFixed(1)}s`;
}

function fmtNum(n: number | undefined): string {
  if (n == null || !Number.isFinite(n)) return "—";
  return n.toLocaleString();
}

export function PosterPreview({ poster, loading, error }: PosterPreviewProps) {
  const u = poster?.usage;

  return (
    <article className={`poster-card ${loading ? "is-loading" : ""}`}>
      <div className="draft-tag">Draft · not published</div>
      <h2 className="poster-title">Poster</h2>

      {error ? <p className="error tight">{error}</p> : null}

      {poster ? (
        <>
          <img
            className="poster-image"
            src={`data:${poster.mime_type};base64,${poster.image_base64}`}
            alt="Generated social post advertisement"
          />
          <div className="checklist">
            <strong>Before you use this poster</strong>
            <ul>
              <li>Offer / price matches the brief</li>
              <li>Store / brand name is correct</li>
              <li>On-image spelling looks right</li>
            </ul>
          </div>
          {u ? (
            <dl className="usage-mini">
              <div>
                <dt>Time</dt>
                <dd>{fmtSec(u.wall_seconds)}</dd>
              </div>
              <div>
                <dt>Est. cost</dt>
                <dd>{fmtUsd(u.estimated_usd)}</dd>
              </div>
              <div>
                <dt>Tokens</dt>
                <dd>{fmtNum(u.total_tokens)}</dd>
              </div>
              <div>
                <dt>Model</dt>
                <dd className="mono">{u.model || "—"}</dd>
              </div>
            </dl>
          ) : null}
          {poster.filename ? (
            <p className="usage">{poster.filename}</p>
          ) : null}
        </>
      ) : (
        <div className="empty compact">
          <p>Your poster will appear here.</p>
          <span>Generate to create text + image from the same brief.</span>
        </div>
      )}
    </article>
  );
}
