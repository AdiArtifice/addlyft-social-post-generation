import { useState } from "react";
import {
  DEFAULT_STORE_BRAND,
  generatePipeline,
  generatePost,
  type PosterResult,
  type SocialPost,
} from "./api";
import { BriefForm, type RefItem } from "./components/BriefForm";
import { PostPreviewCard } from "./components/PostPreviewCard";
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

    if (variation) {
      if (!poster?.image_base64) {
        setTextError("Generate a poster first, then regenerate the caption.");
        setLoading(null);
        return;
      }
      try {
        const next = await generatePost(brief, true, STORE_BRAND, poster);
        setHistory((prev) => [next, ...prev].slice(0, 3));
        setSelectedIndex(0);
      } catch (err) {
        setTextError(err instanceof Error ? err.message : "Something went wrong.");
      } finally {
        setLoading(null);
      }
      return;
    }

    setImageError(null);
    const files = refs.map((r) => r.file);
    const roles = refs.map((r) => r.role);

    try {
      const result = await generatePipeline(
        brief,
        files,
        roles,
        allowPeople,
        STORE_BRAND,
      );

      if (result.image_base64 && result.mime_type) {
        setPoster({
          image_base64: result.image_base64,
          mime_type: result.mime_type,
          filename: result.filename || "poster.png",
          api_calls: result.api_calls,
          person_generation: result.person_generation ?? undefined,
          store_brand: result.store_brand,
        });
      } else {
        setImageError("Poster generation returned no image.");
      }

      if (
        result.caption &&
        result.offer &&
        result.cta &&
        result.hashtags &&
        result.hashtags.length > 0
      ) {
        const next: SocialPost = {
          caption: result.caption,
          offer: result.offer,
          cta: result.cta,
          hashtags: result.hashtags,
          store_brand: result.store_brand,
        };
        setHistory((prev) => [next, ...prev].slice(0, 3));
        setSelectedIndex(0);
      } else if (result.text_error) {
        setTextError(result.text_error);
      } else {
        setTextError("Caption generation returned incomplete fields.");
      }
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Generation failed.";
      setImageError(message);
      setTextError(message);
    } finally {
      setLoading(null);
    }
  }

  return (
    <main className="page">
      <header className="topbar">
        <p className="eyebrow">AddLyft · Client showcase</p>
        <h1>Social post preview</h1>
        <p className="lede">
          Enter an ad brief, optionally add up to 3 reference images, then
          generate a poster and vision-grounded caption, offer, CTA, and
          hashtags as one social post — review as a draft before anything goes
          live.
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
            poster={poster}
            storeBrand={STORE_BRAND}
            loading={loading === "generate" || loading === "regenerate"}
            imageError={imageError}
          />
          <div className="preview-actions">
            <RegenerateButton
              disabled={!brief.trim() || !poster || busy}
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
        </div>
      </section>
    </main>
  );
}
