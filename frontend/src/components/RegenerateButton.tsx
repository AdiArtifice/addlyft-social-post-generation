type RegenerateButtonProps = {
  disabled: boolean;
  loading: boolean;
  onRegenerate: () => void;
};

export function RegenerateButton({
  disabled,
  loading,
  onRegenerate,
}: RegenerateButtonProps) {
  return (
    <button
      type="button"
      className="secondary"
      disabled={disabled || loading}
      onClick={onRegenerate}
    >
      {loading ? "Regenerating…" : "Regenerate"}
    </button>
  );
}
