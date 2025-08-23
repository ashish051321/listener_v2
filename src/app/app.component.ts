import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { ConversationRecorderComponent } from './components/conversation-recorder/conversation-recorder.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, ConversationRecorderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Conversation Recorder';
}
