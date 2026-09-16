import type { PipelineStage, StageState } from '../types/api.ts'

export const STAGE_GUIDE: Record<
  string,
  { doing: string; done: string; wait: string; failed: string }
> = {
  ingest: {
    doing: 'Storing the file in Supabase. The laptop only keeps a temp copy while YOLO runs.',
    done: 'File is stored. Next stages read that object, not your local disk.',
    wait: 'Upload lands here first.',
    failed: 'The file did not reach storage. Retry uses the same video if it did.',
  },
  sample: {
    doing: 'Extracting stills every 0.8s. The raw video is not sent to Gemini.',
    done: 'Stills are ready. Detection runs on these frames only.',
    wait: 'Opens the video and pulls stills at a fixed interval.',
    failed: 'The file could not be read as video.',
  },
  detect: {
    doing: 'YOLO11 is labeling people, vehicles, and bags on each still.',
    done: 'Detector boxes are ready. They become events, then captions.',
    wait: 'Local YOLO11 pass — cheap, runs before any language model.',
    failed: 'Detection did not finish. Nothing was captioned or indexed.',
  },
  events: {
    doing: 'Grouping nearby boxes of the same object into time windows.',
    done: 'Each event is one tracked object with a start/end time.',
    wait: 'Turns raw boxes into searchable time windows.',
    failed: 'Events could not be built from the detections.',
  },
  caption: {
    doing: 'Gemini is describing a crop of each event frame. That text becomes the index.',
    done: 'Each event now has a caption. Those sentences are what search reads.',
    wait: 'Writes the natural-language text stored on each event.',
    failed: 'Captioning stopped. Retry will try Gemini again, then a rule-based line.',
  },
  index: {
    doing: 'Embedding captions into pgvector. After this, questions can run.',
    done: 'The index is searchable. Answers will come from these captions, not the raw video.',
    wait: 'Last step — vectors are written so retrieval can run.',
    failed: 'Embeddings did not write. Query stays locked until this succeeds.',
  },
}

export function stageExplanation(stage: PipelineStage): string {
  const copy = STAGE_GUIDE[stage.key]
  if (!copy) return ''
  if (stage.state === 'running') return copy.doing
  if (stage.state === 'complete') return copy.done
  if (stage.state === 'failed') return copy.failed
  return copy.wait
}

export function captionSourceLabel(source?: string | null): string {
  if (source === 'vlm') return 'Gemini vision on the cited frame'
  if (source === 'rule_based') return 'Rule-based line from YOLO labels (Gemini skipped or failed)'
  return 'Indexed caption'
}

export function captionSourceShort(source?: string | null): string {
  if (source === 'vlm') return 'Gemini caption'
  if (source === 'rule_based') return 'Rule-based caption'
  return 'Indexed caption'
}

export function answerSourceLabel(source?: string | null): string {
  if (source === 'llm') return 'Composed by Gemini from retrieved events'
  if (source === 'extractive') return 'Quoted from the top indexed caption'
  if (source === 'none') return 'Status only — no event was retrieved'
  return 'Answer'
}

export function currentStageHeadline(
  stages: PipelineStage[] | undefined,
  current?: string | null,
  status?: string | null,
): string {
  if (status === 'ready') {
    return 'Index ready. Questions search these captions — they do not re-watch the video.'
  }
  if (status === 'failed') {
    return 'A pipeline stage failed. The uploaded file is still stored; retry from that file.'
  }
  const key = current ?? stages?.find((stage) => stage.state === 'running')?.key
  const running = stages?.find((stage) => stage.key === key)
  if (running) return stageExplanation(running)
  return 'Waiting for the next ingest stage.'
}

export function stageToneClass(state: StageState): string {
  if (state === 'running') return 'text-[#DDDDDD]'
  if (state === 'complete') return 'text-[#999999]'
  if (state === 'failed') return 'text-[#B5533C]'
  return 'text-[#777777]'
}
