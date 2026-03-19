/**
 * Web Worker for processing and sending audio segments
 * This runs in a separate thread to avoid blocking the main recording thread
 */

interface AudioSegmentMessage {
  type: 'process_audio';
  chunks: Blob[];
  timestamp: string;
  duration: string;
}

interface TranscriptionResult {
  text: string;
  segments: { start: number; end: number; text: string }[];
  language: string;
  language_probability: number;
  duration: number;
}

interface WorkerResponse {
  type: 'audio_processed' | 'audio_error';
  success: boolean;
  message: string;
  timestamp: string;
  transcription?: TranscriptionResult | null;
}

// Listen for messages from the main thread
self.addEventListener('message', async (event: MessageEvent<AudioSegmentMessage>) => {
  const { type, chunks, timestamp, duration } = event.data;

  if (type === 'process_audio') {
    try {
      // Create blob from chunks
      const audioBlob = new Blob(chunks, { type: 'audio/webm' });
      
      // Send to backend
      const formData = new FormData();
      formData.append('audio', audioBlob, `conversation_${Date.now()}.webm`);
      formData.append('timestamp', timestamp);
      formData.append('duration', duration);

      const response = await fetch('http://localhost:8000/api/audio/upload', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        
        // Send success response back to main thread
        const workerResponse: WorkerResponse = {
          type: 'audio_processed',
          success: true,
          message: 'Audio chunk sent successfully',
          timestamp: timestamp,
          transcription: result.transcription || null
        };
        
        self.postMessage(workerResponse);
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
    } catch (error) {
      console.error('Error in audio worker:', error);
      
      // Send error response back to main thread
      const workerResponse: WorkerResponse = {
        type: 'audio_error',
        success: false,
        message: error instanceof Error ? error.message : 'Unknown error',
        timestamp: timestamp
      };
      
      self.postMessage(workerResponse);
    }
  }
});

// Export for TypeScript
export {};
