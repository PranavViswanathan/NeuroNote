import { Node, mergeAttributes } from "@tiptap/core";

export const ImageNode = Node.create({
  name: "image",
  group: "block",
  atom: true,
  draggable: true,

  addAttributes() {
    return {
      src: {
        default: "",
      },
      alt: {
        default: "",
      },
      title: {
        default: "",
      },
      assetId: {
        default: "",
      },
      filename: {
        default: "",
      },
      ext: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [{ tag: "img[src]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "img",
      mergeAttributes(HTMLAttributes, {
        class: "editor-image-node",
      }),
    ];
  },
});
