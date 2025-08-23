import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable, interval, Subscription } from 'rxjs';
import { HttpClient } from '@angular/common/http';

// Web Worker types (optional)
interface AudioSegmentMessage {
  type: 'process_audio';
  chunks: Blob[];
  timestamp: string;
  duration: string;
}

interface WorkerResponse {
  type: 'audio_processed' | 'audio_error';
  success: boolean;
  message: string;
  timestamp: string;
}

export interface RecordingStatus {
  isRecording: boolean;
  isProcessing: boolean;
  currentDuration: number;
  totalSegments: number;
  lastSegmentSent: Date | null;
}

@Injectable({
  providedIn: 'root'
})
export class AudioRecordingService {
  // Core recording pieces
  private recordingStream: MediaStream | null = null;
  private mediaRecorder: MediaRecorder | null = null;

  // Control flags & timers
  private isRecording = false;
  private isProcessing = false;
  private recordingStartTime = 0;
  private totalSegmentsProcessed = 0;

  private statusTickSub: Subscription | null = null;

  // Segment timing
  private readonly SEGMENT_MS = 10_000; // 10 seconds per file
  private segmentTimer: number | null = null; // window.setTimeout id
  private segmentIndex = 0; // helpful for debugging

  // Optional worker
  private audioWorker: Worker | null = null;

  // Status observable for UI updates
  private statusSubject = new BehaviorSubject<RecordingStatus>({
    isRecording: false,
    isProcessing: false,
    currentDuration: 0,
    totalSegments: 0,
    lastSegmentSent: null
  });
  public status$: Observable<RecordingStatus> = this.statusSubject.asObservable();

  constructor(private http: HttpClient) {
    console.log('AudioRecordingService initialized (Option B segmented).');
    this.initializeWorker();
  }

  /**
   * Initialize the Web Worker (optional).
   */
  private initializeWorker(): void {
    try {
      this.audioWorker = new Worker(new URL('../workers/audio-processor.worker', import.meta.url));
      this.audioWorker.onmessage = (event: MessageEvent<WorkerResponse>) => {
        const { type, success, message } = event.data;
                 if (type === 'audio_processed' && success) {
           console.log('Worker processed segment successfully.');
           this.totalSegmentsProcessed++;
           this.updateStatus();
         } else if (type === 'audio_error') {
          console.error('Worker error:', message);
        }
      };
      this.audioWorker.onerror = (err) => console.error('Worker onerror:', err);
    } catch (e) {
      console.warn('Worker init failed (continuing without worker):', e);
      this.audioWorker = null;
    }
  }

  /**
   * Start high-reliability segmented recording.
   * Each segment is a fresh MediaRecorder instance -> every blob has EBML header.
   */
  async startRecording(): Promise<void> {
    if (this.isRecording) return;

    try {
      // 1) Get (or reuse) mic stream
      if (!this.recordingStream) {
        this.recordingStream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100
          }
        });
      }

      // 2) Flip flags & UI tick
      this.totalSegmentsProcessed = 0;
      this.segmentIndex = 0;
      this.isRecording = true;
      this.recordingStartTime = Date.now();

      // UI ticker
      this.statusTickSub = interval(1000).subscribe(() => {
        if (this.isRecording) this.updateStatus();
      });
      this.updateStatus();

      // 3) Kick off first segment
      await this.startNewSegment();

    } catch (err) {
      console.error('startRecording() error:', err);
      throw new Error('Failed to start recording. Please check microphone permissions.');
    }
  }

  /**
   * Stop recording gracefully. Prevents scheduling new segments and
   * stops current recorder (which will emit its final blob).
   */
  stopRecording(): void {
    if (!this.isRecording) return;

    console.log('Stopping segmented recording...');
    this.isRecording = false;

    // Stop UI tick
    if (this.statusTickSub) {
      this.statusTickSub.unsubscribe();
      this.statusTickSub = null;
    }

    // Cancel next segment timer (if any)
    if (this.segmentTimer !== null) {
      clearTimeout(this.segmentTimer);
      this.segmentTimer = null;
    }

    // Stop current recorder, if active
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try {
        this.mediaRecorder.stop();
      } catch (e) {
        console.warn('Error stopping mediaRecorder:', e);
      }
    }

    // Stop stream tracks
    if (this.recordingStream) {
      this.recordingStream.getTracks().forEach(t => t.stop());
      this.recordingStream = null;
    }

    // Kill worker
    if (this.audioWorker) {
      this.audioWorker.terminate();
      this.audioWorker = null;
      console.log('Web Worker terminated');
    }

    this.updateStatus();
    console.log('Recording stopped.');
  }

  /**
   * Create a fresh MediaRecorder for a new 10s segment.
   * On stop -> next segment (if still recording).
   */
  private async startNewSegment(): Promise<void> {
    if (!this.isRecording) return;
    if (!this.recordingStream) {
      console.error('No recording stream available');
      return;
    }

    // Defensive: ensure prior recorder is fully inactive
    if (this.mediaRecorder && this.mediaRecorder.state !== 'inactive') {
      try { this.mediaRecorder.stop(); } catch {}
      this.mediaRecorder = null;
    }

    // Create a NEW recorder for this segment
    this.mediaRecorder = new MediaRecorder(this.recordingStream, {
      mimeType: 'audio/webm;codecs=opus'
    });

    const segmentNo = ++this.segmentIndex;
    const segmentLabel = `seg#${segmentNo}`;

    this.mediaRecorder.ondataavailable = async (event) => {
      // With "stop after 10s", Chrome/Edge typically fire dataavailable ON STOP with the whole blob
             if (event.data && event.data.size > 0) {
         console.log(`${segmentLabel}: blob size ${event.data.size} bytes`);
         await this.handleSegment(event.data, this.SEGMENT_MS / 1000);
       } else {
        console.warn(`${segmentLabel}: empty blob`);
      }
    };

    this.mediaRecorder.onerror = (e) => {
      console.error(`${segmentLabel} MediaRecorder error:`, e);
      // Attempt to proceed to next segment to keep the chain alive
      if (this.isRecording) {
        this.safeScheduleNextSegment(250);
      }
    };

    this.mediaRecorder.onstop = () => {
      console.log(`${segmentLabel} stopped.`);
      // Schedule next segment if still recording
      if (this.isRecording) {
        this.safeScheduleNextSegment(0);
      }
    };

    // Start this segment now
    this.mediaRecorder.start(); // no timeslice
    console.log(`${segmentLabel} started.`);

    // Stop after exactly SEGMENT_MS
    this.segmentTimer = window.setTimeout(() => {
      if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
        try {
          this.mediaRecorder.stop(); // triggers ondataavailable with a full, headered WebM
        } catch (e) {
          console.warn(`${segmentLabel} stop() threw:`, e);
        }
      }
    }, this.SEGMENT_MS);
  }

  /**
   * Schedules the next segment safely (avoids overlapping timers).
   */
  private safeScheduleNextSegment(delayMs: number) {
    if (!this.isRecording) return;
    if (this.segmentTimer !== null) {
      clearTimeout(this.segmentTimer);
      this.segmentTimer = null;
    }
    this.segmentTimer = window.setTimeout(() => {
      this.startNewSegment();
    }, delayMs);
  }

  /**
   * Handle a completed segment: upload via Web Worker or fallback to main thread.
   */
  private async handleSegment(blob: Blob, durationSeconds: number): Promise<void> {
    try {
      this.isProcessing = true;
      this.updateStatus();

             // Send to Web Worker for processing and upload
       if (this.audioWorker) {
         const message: AudioSegmentMessage = {
           type: 'process_audio',
           chunks: [blob],
           timestamp: new Date().toISOString(),
           duration: String(durationSeconds)
         };
         this.audioWorker.postMessage(message);
         console.log('Audio segment sent to Web Worker for processing');
      } else {
        // Fallback to main thread processing
        console.warn('Web Worker not available, using main thread processing');
        const formData = new FormData();
        formData.append('audio', blob, `conversation_${Date.now()}.webm`);
        formData.append('timestamp', new Date().toISOString());
        formData.append('duration', String(durationSeconds));

        const response = await this.http
          .post('http://localhost:8000/api/audio/upload', formData)
          .toPromise();

                 console.log('Upload response:', response);
         this.totalSegmentsProcessed++;
       }

             // Update "lastSegmentSent" timestamp
       this.statusSubject.next({
         ...this.statusSubject.value,
         lastSegmentSent: new Date()
       });

    } catch (error) {
      console.error('handleChunk upload error:', error);
    } finally {
      this.isProcessing = false;
      this.updateStatus();
    }
  }

  /**
   * Update UI status.
   */
  private updateStatus(): void {
    const currentDuration = this.isRecording
      ? Math.floor((Date.now() - this.recordingStartTime) / 1000)
      : 0;

         this.statusSubject.next({
       isRecording: this.isRecording,
       isProcessing: this.isProcessing,
       currentDuration,
       totalSegments: this.totalSegmentsProcessed,
       lastSegmentSent: this.statusSubject.value.lastSegmentSent
     });
  }

  // Convenience getters
  getCurrentStatus(): RecordingStatus {
    return this.statusSubject.value;
  }

  isCurrentlyRecording(): boolean {
    return this.isRecording;
  }
}
