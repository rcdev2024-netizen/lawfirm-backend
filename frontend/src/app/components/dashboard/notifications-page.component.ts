import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService, Notification } from '../../services/dashboard.service';

@Component({
  selector: 'app-notifications-page',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Notifications</h2>
          <p>Stay updated on your cases and activities.</p>
        </div>
        <button class="btn-outline" (click)="markAllRead()" *ngIf="unreadCount > 0">
          Mark all as read
        </button>
      </div>

      <div class="card">
        <div class="notif-list" *ngIf="notifications.length > 0">
          <div class="notif-item" *ngFor="let n of notifications" [class.unread]="!n.is_read" (click)="markRead(n)">
            <div class="notif-icon" [ngClass]="n.type || 'default'">
              <svg *ngIf="n.type === 'document'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
              <svg *ngIf="n.type === 'message'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
              <svg *ngIf="n.type === 'appointment'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <svg *ngIf="n.type === 'invoice'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
              <svg *ngIf="!n.type || n.type === 'case' || n.type === 'default'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
            </div>
            <div class="notif-body">
              <div class="notif-title">{{ n.title }}</div>
              <div class="notif-sub" *ngIf="n.body">{{ n.body }}</div>
              <div class="notif-time">{{ timeAgo(n.created_at) }}</div>
            </div>
            <div class="unread-dot" *ngIf="!n.is_read"></div>
          </div>
        </div>
        <div class="empty-state" *ngIf="notifications.length === 0 && !loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
          <h3>All caught up!</h3>
          <p>You have no notifications.</p>
        </div>
        <div class="loading" *ngIf="loading"><div class="spinner"></div></div>
      </div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px; gap: 12px; flex-wrap: wrap; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }
    .btn-outline { padding: 9px 18px; background: none; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-size: 0.78rem; font-weight: 600; color: #4a5568; cursor: pointer; transition: all 0.2s; }
    .btn-outline:hover { border-color: #c9a84c; color: #c9a84c; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }

    .notif-item { display: flex; align-items: flex-start; gap: 14px; padding: 16px 20px; border-bottom: 1px solid #f8f9fb; cursor: pointer; transition: background 0.15s; position: relative; }
    .notif-item:hover { background: #fafbfc; }
    .notif-item:last-child { border-bottom: none; }
    .notif-item.unread { background: rgba(59,130,246,0.02); }
    .notif-item.unread .notif-title { font-weight: 700; color: #1a202c; }

    .notif-icon { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .notif-icon svg { width: 17px; height: 17px; }
    .notif-icon.document { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .notif-icon.message { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .notif-icon.appointment { background: rgba(34,197,94,0.1); color: #22c55e; }
    .notif-icon.invoice { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .notif-icon.case, .notif-icon.default { background: rgba(100,116,139,0.1); color: #64748b; }

    .notif-body { flex: 1; }
    .notif-title { font-size: 0.82rem; font-weight: 600; color: #4a5568; margin-bottom: 3px; }
    .notif-sub { font-size: 0.75rem; color: #9da8b8; margin-bottom: 4px; }
    .notif-time { font-size: 0.68rem; color: #b0bec5; }

    .unread-dot { width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; flex-shrink: 0; margin-top: 6px; }

    .empty-state { text-align: center; padding: 64px 32px; color: #9da8b8; }
    .empty-state svg { width: 48px; height: 48px; color: #e2e8f0; margin: 0 auto 16px; }
    .empty-state h3 { font-size: 1rem; color: #4a5568; margin-bottom: 6px; }
    .empty-state p { font-size: 0.8rem; }

    .loading { display: flex; justify-content: center; padding: 64px; }
    .spinner { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
  `]
})
export class NotificationsPageComponent implements OnInit {
  notifications: Notification[] = [];
  loading = true;

  constructor(private service: DashboardService) {}

  ngOnInit() {
    this.service.getNotifications().subscribe({
      next: n => { this.notifications = n; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  get unreadCount(): number { return this.notifications.filter(n => !n.is_read).length; }

  markRead(n: Notification) {
    if (n.is_read) return;
    this.service.markNotificationRead(n.id).subscribe({ next: () => { n.is_read = true; }, error: () => {} });
  }

  markAllRead() {
    this.service.markAllNotificationsRead().subscribe({ next: () => { this.notifications.forEach(n => n.is_read = true); }, error: () => {} });
  }

  timeAgo(d?: string): string {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins || 1} min${mins !== 1 ? 's' : ''} ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hour${hrs !== 1 ? 's' : ''} ago`;
    return `${Math.floor(hrs / 24)} day${Math.floor(hrs / 24) !== 1 ? 's' : ''} ago`;
  }
}
