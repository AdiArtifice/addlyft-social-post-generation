import { useEffect, useMemo, useState } from "react";
import type { RefRole } from "../api";

export type RefItem = {
  id: string;
  file: File;
  previewUrl: string;
  role: RefRole;
};

type BriefFormProps = {
  brief: string;
  storeBrand: string;
  loading: boolean;
  samples: string[];
  refs: RefItem[];
  allowPeople: boolean;
  onBriefChange: (value: string) => void;
  onRefsChange: (refs: RefItem[]) => void;
  onAllowPeopleChange: (value: boolean) => void;
  onGenerate: () => void;
};

const MAX_BRIEF = 2000;
const MAX_REFS = 3;
const ROLE_OPTIONS: RefRole[] = [
  "auto",
  "product",
  "style",
  "brand",
  "background",
];

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function BriefForm({
  brief,
  storeBrand,
  loading,
  samples,
  refs,
  allowPeople,
  onBriefChange,
  onRefsChange,
  onAllowPeopleChange,
  onGenerate,
}: BriefFormProps) {
  const [localError, setLocalError] = useState<string | null>(null);

  // Revoke object URLs when refs change / unmount
  const previewUrls = useMemo(() => refs.map((r) => r.previewUrl), [refs]);
  useEffect(() => {
    return () => {
      for (const url of previewUrls) URL.revokeObjectURL(url);
    };
  }, [previewUrls]);

  function handleFilesSelected(fileList: FileList | null) {
    setLocalError(null);
    if (!fileList) return;
    const incoming = Array.from(fileList);
    const room = MAX_REFS - refs.length;
    if (room <= 0) {
      setLocalError("At most 3 reference images allowed.");
      return;
    }
    if (incoming.length > room) {
      setLocalError(`Only ${room} more reference image(s) allowed; extras dropped.`);
    }
    const next = incoming.slice(0, room).map((file) => ({
      id: makeId(),
      file,
      previewUrl: URL.createObjectURL(file),
      role: "auto" as RefRole,
    }));
    onRefsChange([...refs, ...next]);
  }

  function updateRole(id: string, role: RefRole) {
    onRefsChange(refs.map((r) => (r.id === id ? { ...r, role } : r)));
  }

  function removeRef(id: string) {
    const doomed = refs.find((r) => r.id === id);
    if (doomed) URL.revokeObjectURL(doomed.previewUrl);
    onRefsChange(refs.filter((r) => r.id !== id));
  }

  return (
    <form
      className="brief-form"
      onSubmit={(event) => {
        event.preventDefault();
        onGenerate();
      }}
    >
      <div className="store-context" aria-label="Selected store">
        <span className="store-label">Store</span>
        <strong>{storeBrand}</strong>
        <span className="hint block">
          Fixed for this demo (stands in for a prior store selection). You do not
          need to repeat the store name in the brief.
        </span>
      </div>

      <label htmlFor="brief">Ad brief</label>
      <textarea
        id="brief"
        rows={8}
        maxLength={MAX_BRIEF}
        value={brief}
        placeholder="Product, offer, headline/CTA, and creative notes — store is already selected above…"
        onChange={(event) => onBriefChange(event.target.value)}
        disabled={loading}
      />
      <p className="char-count">
        {brief.length} / {MAX_BRIEF}
      </p>
      <div className="sample-row">
        {samples.map((sample) => (
          <button
            key={sample}
            type="button"
            className="chip"
            disabled={loading}
            onClick={() => onBriefChange(sample)}
          >
            {sample.length > 42 ? `${sample.slice(0, 42)}…` : sample}
          </button>
        ))}
      </div>

      <label htmlFor="refs" className="refs-label">
        Reference images (0–{MAX_REFS})
      </label>
      <input
        id="refs"
        type="file"
        accept="image/*"
        multiple
        disabled={loading || refs.length >= MAX_REFS}
        onChange={(event) => {
          handleFilesSelected(event.target.files);
          event.target.value = "";
        }}
      />
      <p className="hint">
        Optional. Used for the poster. Set each role: product, style, brand,
        background, or auto.
      </p>
      {localError ? <p className="inline-error">{localError}</p> : null}

      {refs.length > 0 ? (
        <div className="ref-grid">
          {refs.map((item) => (
            <div key={item.id} className="ref-card">
              <img src={item.previewUrl} alt={item.file.name} />
              <select
                aria-label={`Role for ${item.file.name}`}
                value={item.role}
                disabled={loading}
                onChange={(event) =>
                  updateRole(item.id, event.target.value as RefRole)
                }
              >
                {ROLE_OPTIONS.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
              <span className="ref-name" title={item.file.name}>
                {item.file.name}
              </span>
              <button
                type="button"
                className="ref-remove"
                disabled={loading}
                onClick={() => removeRef(item.id)}
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      ) : null}

      <label className="toggle-row">
        <input
          type="checkbox"
          checked={allowPeople}
          disabled={loading}
          onChange={(event) => onAllowPeopleChange(event.target.checked)}
        />
        <span>
          Allow people in poster
          <span className="hint block">
            Default is off (no faces). Turn on only if you want people and your
            refs support it.
          </span>
        </span>
      </label>

      <button className="primary" type="submit" disabled={loading || !brief.trim()}>
        {loading ? "Generating…" : "Generate poster + caption"}
      </button>
    </form>
  );
}
