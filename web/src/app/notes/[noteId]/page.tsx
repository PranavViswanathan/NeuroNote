import { NotesWorkspace } from "../../../components/workspace/NotesWorkspace";

interface NotePageProps {
  params: {
    noteId: string;
  };
}

const DEFAULT_API_BASE_URL = "http://localhost:8000";

export default function NotePage({ params }: NotePageProps) {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? DEFAULT_API_BASE_URL;

  return (
    <NotesWorkspace
      baseUrl={baseUrl}
      initialNoteId={params.noteId}
    />
  );
}
