const TAG_COLORS = [
  { bg: "#dbeafe", text: "#1e40af" }, // blue
  { bg: "#dcfce7", text: "#15803d" }, // green
  { bg: "#fef3c7", text: "#b45309" }, // amber
  { bg: "#fce7f3", text: "#be185d" }, // pink
  { bg: "#ede9fe", text: "#6d28d9" }, // purple
  { bg: "#fee2e2", text: "#b91c1c" }, // red
  { bg: "#e0f2fe", text: "#0369a1" }, // sky
  { bg: "#f3e8ff", text: "#7e22ce" }, // violet
] as const;

export function getTagColor(tag: string): { bg: string; text: string } {
  let hash = 0;
  for (const c of tag) hash = (hash * 31 + c.charCodeAt(0)) | 0;
  return TAG_COLORS[Math.abs(hash) % TAG_COLORS.length];
}
