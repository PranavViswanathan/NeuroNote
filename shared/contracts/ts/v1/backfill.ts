export type BackfillStatusResponse = {
  total_notes: number;
  processed_notes: number;
  failed_notes: number;
  in_progress: boolean;
};

