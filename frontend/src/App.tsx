import { useState } from "react";
import {
  DEFAULT_STORE_BRAND,
  generatePost,
  generatePoster,
  type PosterResult,
  type SocialPost,
} from "./api";
import { BriefForm, type RefItem } from "./components/BriefForm";
import { PostPreviewCard } from "./components/PostPreviewCard";
import { PosterPreview } from "./components/PosterPreview";
import { RegenerateButton } from "./components/RegenerateButton";

const STORE_BRAND = DEFAULT_STORE_BRAND;

const SAMPLE_BRIEFS = [
  "Lay's Potato Chips. Headline: CRUNCH MORE. Subhead: SAVE MORE! Offer: GRAB 3 BAGS FOR THE PRICE OF 2. CTA: GRAB YOUR FAVORITES! Keep exact Lay's packaging when product refs are uploaded.",
  "20% off all yoga mats this weekend. Highlight comfort and studio energy.",
  "New oat-milk cold brew. First drink free with any pastry this Friday.",
];

export function App() {
  const [brief, setBrief] = useState(SAMPLE_BRIEFS[0]);
  const [refs, setRefs] = useState<RefItem[]>([]);
  const [allowPeople, setAllowPeople] = useState(false);
  const [history, setHistory] = useState<SocialPost[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [poster, setPoster] = useState<PosterResult | null>(null);
  const [loading, setLoading] = useState<"generate" | "regenerate" | null>(null);
  const [textError, setTextError] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);

  const post = history[selectedIndex] ?? null;
  const busy = loading !== null;

  async function runGenerate(variation: boolean) {
    if (!brief.trim() || busy) return;
    setLoading(variation ? "regenerate" : "generate");
    setTextError(null);
    if (!variation) setImageError(null);

    if (variation) {
      try {
        const next = await generatePost(brief, true, STORE_BRAND);
        setHistory((prev) => [next, ...prev].slice(0, 3));
        setSelectedIndex(0);
      } catch (err) {
        setTextError(err instanceof Error ? err.message : "Something went wrong.");
      } finally {
        setLoading(null);
      }
      return;
    }

    const files = refs.map((r) => r.file);
    const roles = refs.map((r) => r.role);

    const [textResult, imageResult] = await Promise.allSettled([
      generatePost(brief, false, STORE_BRAND),
      generatePoster(brief, files, roles, allowPeople, STORE_BRAND),
    ]);

    if (textResult.status === "fulfilled") {
      setHistory((prev) => [textResult.value, ...prev].slice(0, 3));
      setSelectedIndex(0);
    } else {
      setTextError(
        textResult.reason instanceof Error
          ? textResult.reason.message
          : "Text generation failed.",
      );
    }

    if (imageResult.status === "fulfilled") {
      setPoster(imageResult.value);
    } else {
      setImageError(
        imageResult.reason instanceof Error
          ? imageResult.reason.message
          : "Poster generation failed.",
      );
    }

    setLoading(null);
  }

  return (
    <main className="page">
      <header className="topbar">
        <p className="eyebrow">AddLyft · Client showcase</p>
        <h1>Social post preview</h1>
        <p className="lede">
          Turn a short ad brief into caption, offer, CTA, hashtags, and an
          optional poster from up to 3 reference images — then review as a draft.
        </p>
      </header>

      <aside className="draft-banner" role="note">
        <strong>AI draft — review before posting</strong>
        <p>
          This demo does not publish anywhere. A person must verify claims before
          anything goes live. Avoid pasting customer PII into the brief.
        </p>
        <ul>
          <li>Offer / price matches the brief</li>
          <li>Brand / store name is correct</li>
          <li>No invented discounts or dates</li>
        </ul>
      </aside>

      <section className="layout">
        <div className="panel">
          <BriefForm
            brief={brief}
            storeBrand={STORE_BRAND}
            loading={busy}
            samples={SAMPLE_BRIEFS}
            refs={refs}
            allowPeople={allowPeople}
            onBriefChange={setBrief}
            onRefsChange={setRefs}
            onAllowPeopleChange={setAllowPeople}
            onGenerate={() => void runGenerate(false)}
          />
        </div>

        <div className="preview-col">
          {textError ? <p className="error">{textError}</p> : null}
          <PostPreviewCard
            post={post}
            storeBrand={STORE_BRAND}
            loading={loading === "generate" || loading === "regenerate"}
          />
          <div className="preview-actions">
            <RegenerateButton
              disabled={!brief.trim() || busy}
              loading={loading === "regenerate"}
              onRegenerate={() => void runGenerate(true)}
            />
            {history.length > 1 ? (
              <div className="history">
                {history.map((_, index) => (
                  <button
                    key={index}
                    type="button"
                    className={index === selectedIndex ? "dot active" : "dot"}
                    aria-label={`Show generation ${index + 1}`}
                    onClick={() => setSelectedIndex(index)}
                  />
                ))}
              </div>
            ) : null}
          </div>

          <PosterPreview
            poster={poster}
            loading={loading === "generate"}
            error={imageError}
          />
        </div>
      </section>
    </main>
  );
}
