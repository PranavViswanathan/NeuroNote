export interface ImageNodeAttributes {
  src: string;
  alt?: string;
  title?: string;
  assetId?: string;
}

export function createImageNode(attrs: ImageNodeAttributes): Record<string, unknown> {
  return {
    type: "image",
    attrs,
  };
}
