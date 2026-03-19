import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AudioRecordingService, RecordingStatus, TranscriptionResult } from '../../services/audio-recording.service';
import { SuggestionService, Suggestion } from '../../services/suggestion.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-conversation-recorder',
  templateUrl: './conversation-recorder.component.html',
  styleUrls: ['./conversation-recorder.component.scss'],
  standalone: true,
  imports: [CommonModule]
})
export class ConversationRecorderComponent implements OnInit, OnDestroy {
  recordingStatus: RecordingStatus = {
    isRecording: false,
    isProcessing: false,
    currentDuration: 0,
    totalSegments: 0,
    lastSegmentSent: null
  };

  // Suggestion-related properties
  currentSuggestion: Suggestion | null = null;
  previousSuggestions: Suggestion[] = [];
  showPreviousSuggestions = false;
  isAutoFetchingSuggestions = false;

  // Transcription properties
  transcriptions: TranscriptionResult[] = [];
  fullTranscript = '';

  private statusSubscription: Subscription | null = null;
  private suggestionSubscription: Subscription | null = null;
  private allSuggestionsSubscription: Subscription | null = null;
  private transcriptionSubscription: Subscription | null = null;
  
  errorMessage: string = '';
  successMessage: string = '';

  constructor(
    private audioRecordingService: AudioRecordingService,
    private suggestionService: SuggestionService
  ) {
    console.log('ConversationRecorderComponent initialized');
  }

  ngOnInit(): void {
    // Subscribe to recording status updates
    this.statusSubscription = this.audioRecordingService.status$.subscribe(
      (status) => {
        this.recordingStatus = status;
        console.log('Recording status updated:', status);
        console.log('Is recording:', status.isRecording);
        console.log('Current duration:', status.currentDuration);
      },
      (error) => {
        console.error('Error in status subscription:', error);
        this.errorMessage = 'Error updating recording status';
      }
    );

    // Subscribe to current suggestion updates
    this.suggestionSubscription = this.suggestionService.currentSuggestion$.subscribe(
      (suggestion) => {
        this.currentSuggestion = suggestion;
        console.log('Current suggestion updated:', suggestion);
      },
      (error) => {
        console.error('Error in suggestion subscription:', error);
      }
    );

    // Subscribe to transcription updates
    this.transcriptionSubscription = this.audioRecordingService.transcription$.subscribe(
      (transcription) => {
        this.transcriptions.push(transcription);
        this.fullTranscript = this.transcriptions.map(t => t.text).join(' ');
        console.log('Transcription received:', transcription.text);
      },
      (error) => {
        console.error('Error in transcription subscription:', error);
      }
    );

    // Subscribe to all suggestions updates
    this.allSuggestionsSubscription = this.suggestionService.allSuggestions$.subscribe(
      (suggestions) => {
        this.previousSuggestions = suggestions.slice(0, -1); // All except current
        console.log('Previous suggestions updated:', this.previousSuggestions.length);
      },
      (error) => {
        console.error('Error in all suggestions subscription:', error);
      }
    );
  }

  ngOnDestroy(): void {
    // Clean up subscriptions
    if (this.statusSubscription) {
      this.statusSubscription.unsubscribe();
    }
    if (this.suggestionSubscription) {
      this.suggestionSubscription.unsubscribe();
    }
    if (this.allSuggestionsSubscription) {
      this.allSuggestionsSubscription.unsubscribe();
    }
    if (this.transcriptionSubscription) {
      this.transcriptionSubscription.unsubscribe();
    }

    // Stop recording if active
    if (this.recordingStatus.isRecording) {
      this.stopRecording();
    }

    // Clean up suggestion service
    this.suggestionService.destroy();
  }

  /**
   * Start the conversation recording
   */
  async startRecording(): Promise<void> {
    try {
      this.clearMessages();
      this.transcriptions = [];
      this.fullTranscript = '';
      console.log('Starting conversation recording...');

      await this.audioRecordingService.startRecording();
      console.log('Recording started in component');
      this.successMessage = 'Recording started successfully! Audio will be sent in 10-second segments.';
      
      // Start auto-fetching suggestions
      this.startSuggestionAutoFetch();
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      this.errorMessage = error instanceof Error ? error.message : 'Failed to start recording';
    }
  }

  /**
   * Stop the conversation recording
   */
  stopRecording(): void {
    try {
      console.log('Stopping conversation recording...');
      this.audioRecordingService.stopRecording();
      this.successMessage = 'Recording stopped. Processing remaining audio segments...';
      
      // Stop auto-fetching suggestions
      this.stopSuggestionAutoFetch();
      
    } catch (error) {
      console.error('Failed to stop recording:', error);
      this.errorMessage = 'Failed to stop recording';
    }
  }

  /**
   * Start auto-fetching suggestions
   */
  private startSuggestionAutoFetch(): void {
    this.suggestionService.startAutoFetch(5000); // Fetch every 5 seconds
    this.isAutoFetchingSuggestions = true;
    console.log('Started auto-fetching suggestions');
  }

  /**
   * Stop auto-fetching suggestions
   */
  private stopSuggestionAutoFetch(): void {
    this.suggestionService.stopAutoFetch();
    this.isAutoFetchingSuggestions = false;
    console.log('Stopped auto-fetching suggestions');
  }

  /**
   * Toggle display of previous suggestions
   */
  togglePreviousSuggestions(): void {
    this.showPreviousSuggestions = !this.showPreviousSuggestions;
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    return new Date(timestamp).toLocaleTimeString();
  }

  /**
   * Format duration in MM:SS format
   */
  formatDuration(seconds: number): string {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  }

  /**
   * Clear error and success messages
   */
  private clearMessages(): void {
    this.errorMessage = '';
    this.successMessage = '';
  }

  /**
   * Get the appropriate button text based on recording status
   */
  getButtonText(): string {
    if (this.recordingStatus.isRecording) {
      return 'Stop Recording';
    }
    return 'Start Recording';
  }

  /**
   * Get the appropriate button class based on recording status
   */
  getButtonClass(): string {
    if (this.recordingStatus.isRecording) {
      return 'btn-danger';
    }
    return 'btn-success';
  }

  /**
   * Get the appropriate button icon based on recording status
   */
  getButtonIcon(): string {
    if (this.recordingStatus.isRecording) {
      return 'bi-stop-circle-fill';
    }
    return 'bi-record-circle-fill';
  }

  /**
   * Get the status indicator class
   */
  getStatusClass(): string {
    if (this.recordingStatus.isRecording) {
      return 'text-success';
    }
    return 'text-muted';
  }

  /**
   * Get the processing indicator class
   */
  getProcessingClass(): string {
    if (this.recordingStatus.isProcessing) {
      return 'text-warning';
    }
    return 'text-muted';
  }

  /**
   * Get suggestion status class
   */
  getSuggestionStatusClass(): string {
    if (this.isAutoFetchingSuggestions) {
      return 'text-success';
    }
    return 'text-muted';
  }
}
