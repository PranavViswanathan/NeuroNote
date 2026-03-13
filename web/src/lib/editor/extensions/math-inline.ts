import { Node, mergeAttributes, nodeInputRule } from "@tiptap/core";
import { renderMathToHtml } from "../math-render";
import { normalizeMathLatex } from "../math";

export const MathInline = Node.create({
  name: "mathInline",
  group: "inline",
  inline: true,
  atom: true,

  addAttributes() {
    return {
      latex: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [{ tag: "span[data-math-inline]" }];
  },

  renderHTML({ HTMLAttributes }) {
    const latex = typeof HTMLAttributes.latex === "string" ? HTMLAttributes.latex : "";
    return [
      "span",
      mergeAttributes(HTMLAttributes, {
        "data-math-inline": "true",
        class: "math-inline-node",
      }),
      `$${latex}$`,
    ];
  },

  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement("span");
      dom.className = "math-inline-node";
      dom.setAttribute("data-math-inline", "true");

      const render = (latex: string) => {
        const rendered = renderMathToHtml(latex, false);
        dom.innerHTML = rendered.html;
        if (rendered.hasError) {
          dom.classList.add("invalid");
        } else {
          dom.classList.remove("invalid");
        }
      };

      const initialLatex = typeof node.attrs.latex === "string" ? node.attrs.latex : "";
      render(initialLatex);

      return {
        dom,
        update: (updatedNode) => {
          if (updatedNode.type.name !== "mathInline") {
            return false;
          }
          const nextLatex = typeof updatedNode.attrs.latex === "string" ? updatedNode.attrs.latex : "";
          render(nextLatex);
          return true;
        },
      };
    };
  },

  addInputRules() {
    return [
      nodeInputRule({
        find: /(?<!\$)\$([^$\n]+)\$$/,
        type: this.type,
        getAttributes: (match) => {
          const rawLatex = typeof match[1] === "string" ? match[1] : "";
          const latex = normalizeMathLatex(rawLatex);
          if (!latex) {
            return null;
          }
          return { latex };
        },
      }),
    ];
  },
});
