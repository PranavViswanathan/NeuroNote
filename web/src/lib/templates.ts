export type TemplateCategory = "daily" | "meeting" | "project" | "reading" | "blank";

export interface Template {
  id: string;
  name: string;
  description: string;
  category: TemplateCategory;
  content: string;
  variables: string[];
}

export const TEMPLATES: Template[] = [
  {
    id: "blank",
    name: "Blank",
    description: "Start with an empty note.",
    category: "blank",
    content: "",
    variables: [],
  },
  {
    id: "daily-note",
    name: "Daily Note",
    description: "A structured template for daily tasks, notes, and reflections.",
    category: "daily",
    content:
      "# {{date}}\n\n## Tasks\n- [ ] \n\n## Notes\n\n\n## Reflections\n",
    variables: ["date"],
  },
  {
    id: "meeting",
    name: "Meeting",
    description: "Capture meeting agenda, discussion points, and action items.",
    category: "meeting",
    content:
      "# {{title}}\n\n**Date:** {{date}}\n**Attendees:** \n\n## Agenda\n\n\n## Discussion\n\n\n## Action Items\n- [ ] \n",
    variables: ["title", "date"],
  },
  {
    id: "project",
    name: "Project",
    description: "Outline a project with goals, milestones, and open questions.",
    category: "project",
    content:
      "# {{title}}\n\n## Goal\n\n\n## Milestones\n- [ ] \n\n## Notes\n\n\n## Open Questions\n",
    variables: ["title"],
  },
  {
    id: "reading",
    name: "Reading Note",
    description: "Summarize a book or article with key ideas and your thoughts.",
    category: "reading",
    content:
      "# {{title}}\n\n**Source:** \n\n## Summary\n\n\n## Key Ideas\n\n\n## Quotes\n\n\n## My Thoughts\n",
    variables: ["title"],
  },
];

export function applyTemplate(
  template: Template,
  vars: Record<string, string>
): string {
  let content = template.content;
  for (const [key, value] of Object.entries(vars)) {
    content = content.replaceAll(`{{${key}}}`, value);
  }
  return content;
}
