import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, interval, Subscription } from 'rxjs';
// import { environment } from '../../environments/environment';

export interface Suggestion {
  id: string;
  text: string;
  timestamp: string;
  audio_count: number;
  sent: boolean;
}

export interface SuggestionResponse {
  success: boolean;
  suggestion?: string;
  timestamp?: string;
  suggestion_id?: string;
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class SuggestionService {
  private readonly API_BASE_URL = 'http://localhost:8000';
  
  // Store all suggestions
  private suggestions: Suggestion[] = [];
  private currentSuggestionIndex = 0;
  
  // Observable for current suggestion
  private currentSuggestionSubject = new BehaviorSubject<Suggestion | null>(null);
  public currentSuggestion$: Observable<Suggestion | null> = this.currentSuggestionSubject.asObservable();
  
  // Observable for all suggestions
  private allSuggestionsSubject = new BehaviorSubject<Suggestion[]>([]);
  public allSuggestions$: Observable<Suggestion[]> = this.allSuggestionsSubject.asObservable();
  
  // Auto-fetch interval
  private autoFetchSubscription: Subscription | null = null;
  private isAutoFetching = false;

  constructor(private http: HttpClient) {
    console.log('SuggestionService initialized');
  }

  /**
   * Start auto-fetching suggestions
   */
  startAutoFetch(intervalMs: number = 5000): void {
    if (this.isAutoFetching) return;
    
    this.isAutoFetching = true;
    this.autoFetchSubscription = interval(intervalMs).subscribe(() => {
      this.fetchNextSuggestion();
    });
    
    console.log('Started auto-fetching suggestions every', intervalMs, 'ms');
  }

  /**
   * Stop auto-fetching suggestions
   */
  stopAutoFetch(): void {
    if (this.autoFetchSubscription) {
      this.autoFetchSubscription.unsubscribe();
      this.autoFetchSubscription = null;
    }
    this.isAutoFetching = false;
    console.log('Stopped auto-fetching suggestions');
  }

  /**
   * Fetch the next suggestion from the backend
   */
  async fetchNextSuggestion(): Promise<void> {
    try {
      const response = await this.http.get<SuggestionResponse>(`${this.API_BASE_URL}/api/suggestions/next`).toPromise();
      
      if (response && response.success && response.suggestion) {
        const newSuggestion: Suggestion = {
          id: response.suggestion_id || this.generateId(),
          text: response.suggestion,
          timestamp: response.timestamp || new Date().toISOString(),
          audio_count: 0, // Will be updated when we get all suggestions
          sent: true
        };
        
        // Add to suggestions array
        this.suggestions.push(newSuggestion);
        this.allSuggestionsSubject.next([...this.suggestions]);
        
        // Update current suggestion
        this.currentSuggestionSubject.next(newSuggestion);
        
        console.log('New suggestion received:', newSuggestion.text);
      } else if (response && !response.success) {
        console.log('No new suggestions available:', response.message);
      }
    } catch (error) {
      console.error('Error fetching next suggestion:', error);
    }
  }

  /**
   * Get all suggestions (for debugging)
   */
  async getAllSuggestions(): Promise<void> {
    try {
      const response = await this.http.get(`${this.API_BASE_URL}/api/suggestions/all`).toPromise();
      console.log('All suggestions:', response);
    } catch (error) {
      console.error('Error fetching all suggestions:', error);
    }
  }

  /**
   * Reset suggestions (for testing)
   */
  async resetSuggestions(): Promise<void> {
    try {
      await this.http.post(`${this.API_BASE_URL}/api/suggestions/reset`, {}).toPromise();
      this.suggestions = [];
      this.allSuggestionsSubject.next([]);
      this.currentSuggestionSubject.next(null);
      console.log('Suggestions reset successfully');
    } catch (error) {
      console.error('Error resetting suggestions:', error);
    }
  }

  /**
   * Get current suggestion
   */
  getCurrentSuggestion(): Suggestion | null {
    return this.currentSuggestionSubject.value;
  }

  /**
   * Get all suggestions
   */
  getAllSuggestionsList(): Suggestion[] {
    return [...this.suggestions];
  }

  /**
   * Get previous suggestions (excluding current)
   */
  getPreviousSuggestions(): Suggestion[] {
    return this.suggestions.slice(0, -1);
  }

  /**
   * Check if auto-fetching is active
   */
  isAutoFetchActive(): boolean {
    return this.isAutoFetching;
  }

  /**
   * Generate a unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Clean up resources
   */
  destroy(): void {
    this.stopAutoFetch();
    this.suggestions = [];
    this.allSuggestionsSubject.next([]);
    this.currentSuggestionSubject.next(null);
  }
}
