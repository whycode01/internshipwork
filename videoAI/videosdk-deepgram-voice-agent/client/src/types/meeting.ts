export interface Message {
  participantId: string;
  text: string;
  timestamp: number;
  isAI: boolean;
}

export interface MeetingControlsProps {
  onClose: () => void;
}

export interface ChatPanelProps {
  messages: Message[];
  isAIConnected: boolean;
  meetingId: string;
}

// Transcript API types
export interface TranscriptEntry {
  speaker: string;
  message: string;
  timestamp: string;
  duration_seconds: number;
  confidence?: number;
  message_type: string;
}

export interface TranscriptInfo {
  filename: string;
  interview_id: string;
  meeting_id: string;
  start_time: string;
  end_time?: string;
  duration_total: number;
  participants: string[];
  message_count: number;
  file_size: number;
}

export interface TranscriptListResponse {
  transcripts: TranscriptInfo[];
  total_count: number;
}

export interface CurrentTranscriptResponse {
  is_recording: boolean;
  interview_id?: string;
  meeting_id?: string;
  start_time?: string;
  participants: string[];
  current_message_count: number;
}

export interface InterviewTranscript {
  interview_id: string;
  meeting_id: string;
  start_time: string;
  end_time?: string;
  duration_total: number;
  participants: string[];
  entries: TranscriptEntry[];
  metadata: Record<string, unknown>;
}
