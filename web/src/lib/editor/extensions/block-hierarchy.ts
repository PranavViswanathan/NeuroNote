import { Extension } from "@tiptap/core";

const HIERARCHY_NODE_TYPES = [
  "paragraph",
  "heading",
  "blockquote",
  "codeBlock",
  "horizontalRule",
  "bulletList",
  "orderedList",
  "taskList",
  "taskItem",
  "listItem",
  "mathBlock",
  "image",
];

export const BlockHierarchy = Extension.create({
  name: "blockHierarchy",

  addGlobalAttributes() {
    return [
      {
        types: HIERARCHY_NODE_TYPES,
        attributes: {
          blockUid: {
            default: null,
            parseHTML: (element) => element.getAttribute("data-block-uid"),
            renderHTML: (attributes) => {
              if (!attributes.blockUid) {
                return {};
              }
              return { "data-block-uid": attributes.blockUid };
            },
          },
          parentBlockUid: {
            default: null,
            parseHTML: (element) => element.getAttribute("data-parent-block-uid"),
            renderHTML: (attributes) => {
              if (!attributes.parentBlockUid) {
                return {};
              }
              return { "data-parent-block-uid": attributes.parentBlockUid };
            },
          },
          indentLevel: {
            default: 0,
            parseHTML: (element) => Number(element.getAttribute("data-indent-level") ?? "0") || 0,
            renderHTML: (attributes) => {
              const level = Number(attributes.indentLevel ?? 0);
              return { "data-indent-level": String(Math.max(0, level)) };
            },
          },
        },
      },
    ];
  },
});
