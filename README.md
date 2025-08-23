# Conversation Recorder Application

A modern Angular application for recording conversations and receiving real-time suggestions. The application consists of a frontend built with Angular and a backend built with FastAPI.

## Features

### Frontend (Angular)
- **Real-time Audio Recording**: Continuous audio recording in 10-second segments
- **Live Suggestion Display**: Real-time conversation suggestions from the backend
- **Suggestion History**: Accordion-style display of previous suggestions
- **Responsive Design**: Bootstrap-based UI with modern styling
- **Auto-fetching**: Automatic suggestion retrieval during recording

### Backend (FastAPI)
- **Audio File Storage**: Secure storage of uploaded audio segments
- **Suggestion Generation**: Dummy conversation suggestions based on audio files
- **Suggestion Queue**: One-by-one suggestion delivery with tracking
- **RESTful API**: Clean API endpoints for frontend integration

## Architecture

```
Frontend (Angular) ←→ Backend (FastAPI)
     ↓                    ↓
Audio Recording    Audio Storage
Suggestion Display  Suggestion Generation
Real-time Updates   Queue Management
```

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- Python 3.9 or higher
- Poetry (for backend dependency management)

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run the backend server:
   ```bash
   poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

The backend will be available at `http://localhost:8000`

### Frontend Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the development server:
   ```bash
   ng serve
   ```

The frontend will be available at `http://localhost:4200`

## How It Works

### Recording Flow
1. **Start Recording**: User clicks "Start Recording" button
2. **Audio Capture**: Frontend captures audio in 10-second segments
3. **Backend Upload**: Each segment is automatically uploaded to the backend
4. **Suggestion Generation**: Backend generates dummy suggestions based on audio count
5. **Suggestion Display**: Frontend fetches and displays suggestions in real-time
6. **Stop Recording**: User clicks "Stop Recording" to end the session

### Suggestion System
- **Auto-fetching**: Frontend automatically fetches new suggestions every 5 seconds during recording
- **Current Suggestion**: Latest suggestion is prominently displayed
- **Previous Suggestions**: Older suggestions are stored in a collapsible accordion
- **One-by-One Delivery**: Backend ensures each suggestion is delivered only once

## API Endpoints

### Backend API
- `POST /api/audio/upload` - Upload audio segments
- `GET /api/suggestions/next` - Get next suggestion
- `GET /api/suggestions/all` - Get all suggestions (debug)
- `POST /api/suggestions/reset` - Reset suggestions (debug)
- `GET /api/audio/files` - List uploaded files
- `GET /health` - Health check

### Frontend Services
- `AudioRecordingService` - Handles audio recording and upload
- `SuggestionService` - Manages suggestion fetching and display

## UI Components

### Conversation Recorder Component
- **Recording Controls**: Start/Stop recording buttons
- **Status Display**: Real-time recording status and duration
- **Segment Tracking**: Audio segment processing information
- **Suggestion Display**: Current and previous suggestions
- **Live Indicators**: Visual feedback for active recording and suggestion fetching

## Styling

The application uses:
- **Bootstrap 5.3.0** for responsive layout and components
- **Bootstrap Icons 1.11.0** for consistent iconography
- **Custom SCSS** for animations and enhancements
- **Atomic CSS** approach with minimal custom styles

## Development

### Code Organization
```
src/app/
├── components/
│   └── conversation-recorder/
│       ├── conversation-recorder.component.ts
│       ├── conversation-recorder.component.html
│       └── conversation-recorder.component.scss
├── services/
│   ├── audio-recording.service.ts
│   └── suggestion.service.ts
└── workers/
    └── audio-processor.worker.ts
```

### Key Features
- **Standalone Components**: Modern Angular standalone component architecture
- **Reactive Programming**: RxJS observables for real-time updates
- **Type Safety**: Full TypeScript implementation
- **Error Handling**: Comprehensive error handling and user feedback
- **Performance**: Web Workers for audio processing

## Future Enhancements

The current implementation includes dummy suggestions. Future versions could include:
- **Real Transcription**: Integration with OpenAI Whisper or similar services
- **AI-Powered Suggestions**: Context-aware conversation suggestions
- **User Preferences**: Customizable suggestion types and frequency
- **Export Features**: Audio and suggestion export capabilities
- **Analytics**: Recording statistics and insights

## Troubleshooting

### Common Issues
1. **Microphone Permissions**: Ensure browser has microphone access
2. **Backend Connection**: Verify backend is running on port 8000
3. **CORS Issues**: Backend is configured for localhost:4200
4. **Audio Format**: Application uses WebM format for audio recording

### Debug Tools
- Browser Developer Tools for frontend debugging
- Backend API documentation at `http://localhost:8000/docs`
- Console logging for detailed operation tracking

## License

This project is licensed under the MIT License.
