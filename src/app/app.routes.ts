import { Routes } from '@angular/router';
import { ConversationRecorderComponent } from './components/conversation-recorder/conversation-recorder.component';

export const routes: Routes = [
  { path: '', redirectTo: '/recorder', pathMatch: 'full' },
  { path: 'recorder', component: ConversationRecorderComponent },
];
