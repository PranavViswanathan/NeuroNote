import { Node, mergeAttributes } from "@tiptap/core";
import { renderMathToHtml } from "../math-render";

export const MathBlock = Node.create({
  name: "mathBlock",
  group: "block",
  atom: true,

  addAttributes() {
    return {
      latex: {
        default: "",
      },
    };
  },

  parseHTML() {
    return [{ tag: "div[data-math-block]" }];
  },

  renderHTML({ HTMLAttributes }) {
    const latex = typeof HTMLAttributes.latex === "string" ? HTMLAttributes.latex : "";
    return [
      "div",
      mergeAttributes(HTMLAttributes, {
        "data-math-block": "true",
        class: "math-block-node",
      }),
      `$$${latex}$$`,
    ];
  },

  addNodeView() {
    return ({ node }) => {
      const dom = document.createElement("div");
      dom.className = "math-block-node";
      dom.setAttribute("data-math-block", "true");

      const render = (latex: string) => {
        const rendered = renderMathToHtml(latex, true);
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
          if (updatedNode.type.name !== "mathBlock") {
            return false;
          }
          const nextLatex = typeof updatedNode.attrs.latex === "string" ? updatedNode.attrs.latex : "";
          render(nextLatex);
          return true;
        },
      };
    };
  },
});
