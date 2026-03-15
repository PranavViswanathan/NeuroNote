import { Mark, mergeAttributes } from "@tiptap/core";

export const ReferenceLink = Mark.create({
  name: "referenceLink",

  addAttributes() {
    return {
      href: {
        default: null,
      },
      dataRefType: {
        default: null,
      },
      dataNoteId: {
        default: null,
      },
      dataBlockUid: {
        default: null,
      },
    };
  },

  parseHTML() {
    return [{ tag: "a[data-reference-link]" }];
  },

  renderHTML({ HTMLAttributes }) {
    return [
      "a",
      mergeAttributes(HTMLAttributes, {
        "data-reference-link": "true",
        class: "editor-reference-link",
      }),
      0,
    ];
  },
});
