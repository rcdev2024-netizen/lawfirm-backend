import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { DashboardService, Message } from '../../services/dashboard.service';
import { AuthService } from '../../services/auth.service';
import { environment } from '../../environments/environment';

@Component({
  selector: 'app-messages',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Messages</h2>
          <p>Communicate securely with your attorney.</p>
        </div>
        <button class="btn-primary" (click)="showCompose = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Compose
        </button>
      </div>

      <div class="messages-layout">
        <!-- Left: Inbox List -->
        <div class="card inbox-panel">
          <div class="inbox-tabs">
            <button class="tab" [class.active]="activeTab === 'inbox'" (click)="activeTab = 'inbox'">
              Inbox <span class="badge" *ngIf="unreadCount > 0">{{ unreadCount }}</span>
            </button>
            <button class="tab" [class.active]="activeTab === 'sent'" (click)="activeTab = 'sent'">Sent</button>
          </div>
          <div class="msg-list">
            <div
              class="msg-item"
              *ngFor="let m of displayMessages"
              [class.unread]="!m.is_read && activeTab === 'inbox'"
              [class.selected]="selectedMsg?.id === m.id"
              (click)="selectMsg(m)"
            >
              <div class="msg-avatar">{{ (m.subject || 'M')[0].toUpperCase() }}</div>
              <div class="msg-preview">
                <div class="msg-from">{{ m.subject || 'No Subject' }}</div>
                <div class="msg-snippet">{{ m.body.length > 60 ? (m.body | slice:0:60) + '...' : m.body }}</div>
              </div>
              <div class="msg-meta">
                <div class="msg-time">{{ timeAgo(m.created_at) }}</div>
                <div class="unread-dot" *ngIf="!m.is_read && activeTab === 'inbox'"></div>
              </div>
            </div>
            <div class="empty-state" *ngIf="displayMessages.length === 0 && !loading">
              <p>No messages</p>
            </div>
            <div class="loading" *ngIf="loading"><div class="spinner"></div></div>
          </div>
        </div>

        <!-- Right: Message Detail -->
        <div class="card detail-panel" *ngIf="selectedMsg">
          <div class="detail-header">
            <h3>{{ selectedMsg.subject || 'No Subject' }}</h3>
            <span class="detail-time">{{ formatDate(selectedMsg.created_at) }}</span>
          </div>
          <div class="detail-body">
            <p>{{ selectedMsg.body }}</p>
          </div>
        </div>
        <div class="card detail-panel empty-detail" *ngIf="!selectedMsg">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          <p>Select a message to read</p>
        </div>
      </div>

      <!-- Compose Modal -->
      <div class="modal-overlay" *ngIf="showCompose" (click)="showCompose = false">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>New Message</h3>
            <button class="close-btn" (click)="showCompose = false">✕</button>
          </div>
          <form class="modal-form" (ngSubmit)="sendMessage()">
            <div class="form-group">
              <label>Recipient ID</label>
              <input type="number" [(ngModel)]="composeForm.recipient_id" name="recipient_id" required placeholder="Attorney user ID">
            </div>
            <div class="form-group">
              <label>Subject</label>
              <input type="text" [(ngModel)]="composeForm.subject" name="subject" placeholder="Message subject">
            </div>
            <div class="form-group">
              <label>Message</label>
              <textarea [(ngModel)]="composeForm.body" name="body" rows="5" required placeholder="Write your message..."></textarea>
            </div>
            <div class="success-msg" *ngIf="sendSuccess">Message sent!</div>
            <div class="error-msg" *ngIf="sendError">{{ sendError }}</div>
            <div class="modal-actions">
              <button type="button" class="btn-cancel" (click)="showCompose = false">Cancel</button>
              <button type="submit" class="btn-primary" [disabled]="sending">{{ sending ? 'Sending...' : 'Send Message' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; flex-wrap: wrap; gap: 12px; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }
    .btn-primary { display: flex; align-items: center; gap: 6px; padding: 10px 18px; background: #0b1929; color: #c9a84c; border: none; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-size: 0.8rem; font-weight: 600; cursor: pointer; }
    .btn-primary:hover { background: #122035; }
    .btn-primary svg { width: 16px; height: 16px; }

    .messages-layout { display: grid; grid-template-columns: 340px 1fr; gap: 16px; height: calc(100vh - 240px); min-height: 400px; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; display: flex; flex-direction: column; }

    .inbox-tabs { display: flex; border-bottom: 1px solid #f0f2f5; flex-shrink: 0; }
    .tab { flex: 1; padding: 12px; background: none; border: none; font-family: 'Montserrat', sans-serif; font-size: 0.78rem; font-weight: 600; color: #9da8b8; cursor: pointer; border-bottom: 2px solid transparent; margin-bottom: -1px; transition: all 0.2s; display: flex; align-items: center; justify-content: center; gap: 6px; }
    .tab.active { color: #0b1929; border-bottom-color: #c9a84c; }
    .badge { background: #e53e3e; color: #fff; font-size: 0.6rem; font-weight: 700; padding: 1px 5px; border-radius: 8px; }

    .msg-list { flex: 1; overflow-y: auto; }
    .msg-item { display: flex; align-items: flex-start; gap: 10px; padding: 14px 16px; border-bottom: 1px solid #f8f9fb; cursor: pointer; transition: background 0.15s; }
    .msg-item:hover, .msg-item.selected { background: #f8f9fb; }
    .msg-item.unread .msg-from { color: #1a202c; font-weight: 700; }
    .msg-avatar { width: 34px; height: 34px; border-radius: 50%; background: linear-gradient(135deg, #c9a84c, #e0c46a); display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; color: #0b1929; flex-shrink: 0; }
    .msg-preview { flex: 1; overflow: hidden; }
    .msg-from { font-size: 0.8rem; font-weight: 600; color: #4a5568; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .msg-snippet { font-size: 0.72rem; color: #9da8b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-top: 2px; }
    .msg-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; flex-shrink: 0; }
    .msg-time { font-size: 0.65rem; color: #9da8b8; }
    .unread-dot { width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; }

    .detail-panel { flex: 1; }
    .detail-header { padding: 20px 24px; border-bottom: 1px solid #f0f2f5; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
    .detail-header h3 { font-size: 1rem; font-weight: 700; color: #1a202c; }
    .detail-time { font-size: 0.72rem; color: #9da8b8; }
    .detail-body { padding: 24px; font-size: 0.85rem; color: #4a5568; line-height: 1.7; flex: 1; overflow-y: auto; }

    .empty-detail { display: flex; flex-direction: column; align-items: center; justify-content: center; color: #9da8b8; gap: 12px; }
    .empty-detail svg { width: 48px; height: 48px; color: #e2e8f0; }
    .empty-detail p { font-size: 0.82rem; }

    .empty-state { padding: 32px; text-align: center; color: #9da8b8; font-size: 0.8rem; }
    .loading { display: flex; justify-content: center; padding: 32px; }
    .spinner { width: 24px; height: 24px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; }
    .modal { background: #fff; border-radius: 16px; width: 100%; max-width: 480px; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
    .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid #f0f2f5; }
    .modal-header h3 { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a202c; }
    .close-btn { background: none; border: none; font-size: 1rem; color: #9da8b8; cursor: pointer; }
    .modal-form { padding: 24px; display: flex; flex-direction: column; gap: 14px; }
    .form-group { display: flex; flex-direction: column; gap: 5px; }
    .form-group label { font-size: 0.7rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.06em; }
    .form-group input, .form-group textarea { border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-family: 'Montserrat', sans-serif; font-size: 0.82rem; color: #2d3748; outline: none; transition: border-color 0.2s; }
    .form-group input:focus, .form-group textarea:focus { border-color: #c9a84c; }
    .form-group textarea { resize: vertical; }
    .success-msg { padding: 10px 14px; background: rgba(34,197,94,0.1); color: #16c47e; border-radius: 6px; font-size: 0.8rem; }
    .error-msg { padding: 10px 14px; background: rgba(229,62,62,0.1); color: #e53e3e; border-radius: 6px; font-size: 0.8rem; }
    .modal-actions { display: flex; gap: 12px; justify-content: flex-end; }
    .btn-cancel { padding: 10px 18px; background: none; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-size: 0.8rem; font-weight: 600; color: #718096; cursor: pointer; }

    @media (max-width: 900px) { .messages-layout { grid-template-columns: 1fr; height: auto; } }
  `]
})
export class MessagesComponent implements OnInit {
  inbox: Message[] = [];
  sent: Message[] = [];
  loading = true;
  activeTab = 'inbox';
  selectedMsg: Message | null = null;

  showCompose = false;
  sending = false;
  sendSuccess = false;
  sendError = '';
  composeForm: { recipient_id: number | null; subject: string; body: string } = { recipient_id: null, subject: '', body: '' };

  constructor(
    private service: DashboardService,
    private auth: AuthService,
    private http: HttpClient
  ) {}

  ngOnInit() {
    this.service.getInbox().subscribe({
      next: m => { this.inbox = m; this.loading = false; },
      error: () => { this.loading = false; }
    });
    this.service.getSentMessages().subscribe({ next: m => this.sent = m, error: () => {} });
  }

  get displayMessages(): Message[] { return this.activeTab === 'inbox' ? this.inbox : this.sent; }
  get unreadCount(): number { return this.inbox.filter(m => !m.is_read).length; }

  selectMsg(m: Message) {
    this.selectedMsg = m;
    if (!m.is_read && this.activeTab === 'inbox') {
      this.service.markMessageRead(m.id).subscribe({ next: () => { m.is_read = true; }, error: () => {} });
    }
  }

  sendMessage() {
    this.sending = true;
    this.sendError = '';
    const token = this.auth.token;
    const headers = token ? new HttpHeaders({ Authorization: `Bearer ${token}` }) : new HttpHeaders();
    this.http.post<Message>(`${environment.apiUrl}/api/messages`, this.composeForm, { headers }).subscribe({
      next: (m) => {
        this.sent.unshift(m);
        this.sending = false;
        this.sendSuccess = true;
        setTimeout(() => {
          this.showCompose = false;
          this.sendSuccess = false;
          this.composeForm = { recipient_id: null, subject: '', body: '' };
        }, 1500);
      },
      error: (err) => {
        this.sending = false;
        this.sendError = err?.error?.detail || 'Failed to send message.';
      }
    });
  }

  timeAgo(d?: string): string {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins || 1}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return `${Math.floor(hrs / 24)}d`;
  }

  formatDate(d?: string): string {
    if (!d) return '';
    return new Date(d).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  }
}
