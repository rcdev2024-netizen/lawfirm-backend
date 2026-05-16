import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { DashboardService, DashboardStats, Case, Notification, Invoice } from '../../services/dashboard.service';

@Component({
  selector: 'app-dashboard-home',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="dash-home">
      <!-- Welcome Header -->
      <div class="welcome-header">
        <div>
          <h1>Welcome back, {{ firstName }}!</h1>
          <p>Here's what's happening with your cases today.</p>
        </div>
      </div>

      <!-- Stat Cards -->
      <div class="stat-cards">
        <div class="stat-card blue">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats?.active_cases ?? '—' }}</div>
            <div class="stat-label">Active Cases</div>
          </div>
          <a routerLink="/dashboard/cases" class="stat-link">View all cases →</a>
        </div>

        <div class="stat-card green">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats?.upcoming_appointments ?? '—' }}</div>
            <div class="stat-label">Upcoming Appointments</div>
          </div>
          <a routerLink="/dashboard/appointments" class="stat-link">View calendar →</a>
        </div>

        <div class="stat-card orange">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats?.total_documents ?? '—' }}</div>
            <div class="stat-label">Documents</div>
          </div>
          <a routerLink="/dashboard/documents" class="stat-link">View documents →</a>
        </div>

        <div class="stat-card purple">
          <div class="stat-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
          </div>
          <div class="stat-body">
            <div class="stat-num">{{ stats?.unpaid_invoices ?? '—' }}</div>
            <div class="stat-label">Unpaid Invoices</div>
          </div>
          <a routerLink="/dashboard/billing" class="stat-link">View invoices →</a>
        </div>
      </div>

      <!-- Middle Row -->
      <div class="mid-row">
        <!-- Case Overview -->
        <div class="card case-overview">
          <div class="card-header">
            <h3>Case Overview</h3>
            <a routerLink="/dashboard/cases" class="view-all">View all cases →</a>
          </div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>CASE NAME</th>
                  <th>STATUS</th>
                  <th>LAST UPDATE</th>
                  <th>NEXT HEARING</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                <tr *ngFor="let c of cases">
                  <td>
                    <div class="case-name">{{ c.case_name }}</div>
                    <div class="case-type">{{ c.case_type }}</div>
                  </td>
                  <td>
                    <span class="status-badge" [ngClass]="getStatusClass(c.status)">{{ getStatusLabel(c.status) }}</span>
                  </td>
                  <td>
                    <div>{{ formatDate(c.updated_at) }}</div>
                    <div class="sub-text">{{ timeAgo(c.updated_at) }}</div>
                  </td>
                  <td>
                    <div *ngIf="c.next_hearing_date">{{ formatDate(c.next_hearing_date) }}</div>
                    <div *ngIf="c.next_hearing_time" class="sub-text">{{ c.next_hearing_time }}</div>
                    <div *ngIf="!c.next_hearing_date" class="sub-text">—</div>
                  </td>
                  <td>
                    <button class="menu-btn">
                      <svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg>
                    </button>
                  </td>
                </tr>
                <tr *ngIf="cases.length === 0">
                  <td colspan="5" class="empty-row">No cases found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Bottom Row -->
      <div class="bottom-row">
        <!-- Recent Activity -->
        <div class="card activity-card">
          <div class="card-header">
            <h3>Recent Activity</h3>
          </div>
          <div class="activity-list">
            <div class="activity-item" *ngFor="let notif of recentNotifs">
              <div class="activity-icon" [ngClass]="notif.type || 'default'">
                <svg *ngIf="notif.type === 'document'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <svg *ngIf="notif.type === 'message'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
                <svg *ngIf="notif.type === 'appointment'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
                <svg *ngIf="notif.type === 'invoice'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                <svg *ngIf="!notif.type || notif.type === 'case'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
              </div>
              <div class="activity-body">
                <div class="activity-title">{{ notif.title }}</div>
                <div class="activity-sub" *ngIf="notif.body">{{ notif.body }}</div>
              </div>
              <div class="activity-time">{{ timeAgo(notif.created_at) }}</div>
            </div>
            <div *ngIf="recentNotifs.length === 0" class="empty-state">
              <p>No recent activity</p>
            </div>
          </div>
        </div>

        <!-- Case Progress -->
        <div class="card progress-card">
          <div class="card-header">
            <h3>Case Progress</h3>
            <a routerLink="/dashboard/cases" class="view-all">View details →</a>
          </div>
          <div class="donut-wrap">
            <svg viewBox="0 0 140 140" class="donut-svg">
              <circle cx="70" cy="70" r="52" fill="none" stroke="#e8eaf0" stroke-width="20"/>
              <circle cx="70" cy="70" r="52" fill="none" stroke="#3b82f6" stroke-width="20"
                [attr.stroke-dasharray]="getArc(inProgressPct)"
                stroke-dashoffset="0"
                transform="rotate(-90 70 70)"/>
              <circle cx="70" cy="70" r="52" fill="none" stroke="#f59e0b" stroke-width="20"
                [attr.stroke-dasharray]="getArc(reviewPct)"
                [attr.stroke-dashoffset]="-getArcOffset(inProgressPct)"
                transform="rotate(-90 70 70)"/>
              <circle cx="70" cy="70" r="52" fill="none" stroke="#22c55e" stroke-width="20"
                [attr.stroke-dasharray]="getArc(closedPct)"
                [attr.stroke-dashoffset]="-getArcOffset(inProgressPct + reviewPct)"
                transform="rotate(-90 70 70)"/>
              <text x="70" y="65" text-anchor="middle" font-size="22" font-weight="700" fill="#2d3748">{{ cases.length }}</text>
              <text x="70" y="82" text-anchor="middle" font-size="9" fill="#9da8b8">Total Cases</text>
            </svg>
          </div>
          <div class="legend">
            <div class="legend-item"><span class="dot blue"></span> In Progress <strong>{{ inProgressCount }}</strong></div>
            <div class="legend-item"><span class="dot amber"></span> Review <strong>{{ reviewCount }}</strong></div>
            <div class="legend-item"><span class="dot green"></span> Closed <strong>{{ closedCount }}</strong></div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="card quick-actions-card">
          <div class="card-header"><h3>Quick Actions</h3></div>
          <div class="qa-grid">
            <button class="qa-btn" routerLink="/dashboard/documents">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              <span>Upload Document</span>
            </button>
            <button class="qa-btn" routerLink="/dashboard/messages">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
              <span>Send Message</span>
            </button>
            <button class="qa-btn" routerLink="/dashboard/appointments">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="16" y1="2" x2="16" y2="6"/></svg>
              <span>Book Appointment</span>
            </button>
            <button class="qa-btn" routerLink="/dashboard/billing">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
              <span>Make Payment</span>
            </button>
            <button class="qa-btn" routerLink="/dashboard/billing">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
              <span>View Invoices</span>
            </button>
            <button class="qa-btn" routerLink="/dashboard/messages">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
              <span>Contact Support</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dash-home { font-family: 'Montserrat', sans-serif; }

    .welcome-header {
      margin-bottom: 24px;
    }
    .welcome-header h1 {
      font-family: 'Playfair Display', serif;
      font-size: 1.6rem;
      color: #1a202c;
      margin-bottom: 4px;
    }
    .welcome-header p { font-size: 0.82rem; color: #718096; }

    /* STAT CARDS */
    .stat-cards {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .stat-card {
      background: #fff;
      border-radius: 12px;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      box-shadow: 0 1px 6px rgba(0,0,0,0.06);
      position: relative;
      overflow: hidden;
    }
    .stat-card::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 3px;
    }
    .stat-card.blue::before { background: #3b82f6; }
    .stat-card.green::before { background: #22c55e; }
    .stat-card.orange::before { background: #f59e0b; }
    .stat-card.purple::before { background: #8b5cf6; }

    .stat-icon {
      width: 42px; height: 42px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .stat-card.blue .stat-icon { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .stat-card.green .stat-icon { background: rgba(34,197,94,0.1); color: #22c55e; }
    .stat-card.orange .stat-icon { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .stat-card.purple .stat-icon { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .stat-icon svg { width: 22px; height: 22px; }

    .stat-num { font-size: 1.9rem; font-weight: 700; color: #1a202c; line-height: 1; }
    .stat-label { font-size: 0.75rem; color: #718096; font-weight: 500; }
    .stat-link {
      font-size: 0.72rem;
      color: #c9a84c;
      text-decoration: none;
      font-weight: 600;
      margin-top: 4px;
      transition: opacity 0.2s;
    }
    .stat-link:hover { opacity: 0.75; }

    /* MID ROW */
    .mid-row { margin-bottom: 20px; }

    /* BOTTOM ROW */
    .bottom-row {
      display: grid;
      grid-template-columns: 1fr 260px 260px;
      gap: 20px;
    }

    /* CARD */
    .card {
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 1px 6px rgba(0,0,0,0.06);
      overflow: hidden;
    }
    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 20px;
      border-bottom: 1px solid #f0f2f5;
    }
    .card-header h3 { font-size: 0.9rem; font-weight: 700; color: #1a202c; }
    .view-all { font-size: 0.75rem; color: #c9a84c; text-decoration: none; font-weight: 600; }
    .view-all:hover { opacity: 0.75; }

    /* TABLE */
    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    thead tr { background: #f8f9fb; }
    th {
      padding: 10px 16px;
      font-size: 0.65rem;
      font-weight: 600;
      color: #9da8b8;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      text-align: left;
      white-space: nowrap;
    }
    td { padding: 14px 16px; border-bottom: 1px solid #f0f2f5; vertical-align: middle; }
    tr:last-child td { border-bottom: none; }
    .case-name { font-size: 0.82rem; font-weight: 600; color: #2d3748; }
    .case-type { font-size: 0.72rem; color: #9da8b8; margin-top: 2px; }
    .sub-text { font-size: 0.7rem; color: #9da8b8; margin-top: 2px; }
    .empty-row { text-align: center; color: #9da8b8; font-size: 0.8rem; padding: 32px; }

    .status-badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 20px;
      font-size: 0.68rem;
      font-weight: 600;
    }
    .status-badge.in-progress { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .status-badge.review { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .status-badge.open { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .status-badge.closed { background: rgba(22,197,94,0.1); color: #16c47e; }

    .menu-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: #9da8b8;
      padding: 4px;
      border-radius: 4px;
      display: flex;
    }
    .menu-btn:hover { color: #4a5568; background: #f0f2f5; }
    .menu-btn svg { width: 16px; height: 16px; }

    /* ACTIVITY */
    .activity-list { padding: 8px 0; }
    .activity-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 20px;
      border-bottom: 1px solid #f8f9fb;
      transition: background 0.15s;
    }
    .activity-item:hover { background: #fafbfc; }
    .activity-item:last-child { border-bottom: none; }
    .activity-icon {
      width: 32px; height: 32px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .activity-icon svg { width: 15px; height: 15px; }
    .activity-icon.document { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .activity-icon.message { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .activity-icon.appointment { background: rgba(34,197,94,0.1); color: #22c55e; }
    .activity-icon.invoice { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .activity-icon.default, .activity-icon.case { background: rgba(100,116,139,0.1); color: #64748b; }
    .activity-body { flex: 1; }
    .activity-title { font-size: 0.78rem; font-weight: 600; color: #2d3748; }
    .activity-sub { font-size: 0.7rem; color: #9da8b8; margin-top: 2px; }
    .activity-time { font-size: 0.68rem; color: #b0bec5; white-space: nowrap; }
    .empty-state { padding: 32px; text-align: center; color: #9da8b8; font-size: 0.8rem; }

    /* DONUT */
    .donut-wrap { display: flex; justify-content: center; padding: 20px 0 12px; }
    .donut-svg { width: 140px; height: 140px; }
    .legend { padding: 0 20px 20px; display: flex; flex-direction: column; gap: 8px; }
    .legend-item {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.78rem;
      color: #4a5568;
    }
    .legend-item strong { margin-left: auto; font-weight: 700; color: #1a202c; }
    .dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .dot.blue { background: #3b82f6; }
    .dot.amber { background: #f59e0b; }
    .dot.green { background: #22c55e; }

    /* QUICK ACTIONS */
    .qa-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1px;
      background: #f0f2f5;
    }
    .qa-btn {
      background: #fff;
      border: none;
      padding: 16px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      transition: background 0.15s;
      font-family: 'Montserrat', sans-serif;
      text-decoration: none;
    }
    .qa-btn:hover { background: #fafbfc; }
    .qa-btn svg { width: 22px; height: 22px; color: #4a5568; }
    .qa-btn span { font-size: 0.68rem; font-weight: 600; color: #4a5568; text-align: center; line-height: 1.3; }

    @media (max-width: 1200px) {
      .stat-cards { grid-template-columns: repeat(2, 1fr); }
      .bottom-row { grid-template-columns: 1fr; }
    }
    @media (max-width: 768px) {
      .stat-cards { grid-template-columns: 1fr; }
    }
  `]
})
export class DashboardHomeComponent implements OnInit {
  stats: DashboardStats | null = null;
  cases: Case[] = [];
  recentNotifs: Notification[] = [];
  loading = true;

  constructor(
    private authService: AuthService,
    private dashboardService: DashboardService
  ) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.dashboardService.getStats().subscribe({ next: s => this.stats = s, error: () => {} });
    this.dashboardService.getCases().subscribe({ next: c => this.cases = c.slice(0, 5), error: () => {} });
    this.dashboardService.getNotifications().subscribe({ next: n => { this.recentNotifs = n.slice(0, 5); this.loading = false; }, error: () => { this.loading = false; } });
  }

  get firstName(): string {
    const name = this.authService.currentUser?.full_name || 'User';
    return name.split(' ')[0];
  }

  get inProgressCount(): number { return this.cases.filter(c => c.status === 'in_progress' || c.status === 'open').length; }
  get reviewCount(): number { return this.cases.filter(c => c.status === 'review').length; }
  get closedCount(): number { return this.cases.filter(c => c.status === 'closed').length; }
  get inProgressPct(): number { return this.cases.length ? (this.inProgressCount / this.cases.length) * 100 : 0; }
  get reviewPct(): number { return this.cases.length ? (this.reviewCount / this.cases.length) * 100 : 0; }
  get closedPct(): number { return this.cases.length ? (this.closedCount / this.cases.length) * 100 : 0; }

  getArc(pct: number): string {
    const circ = 2 * Math.PI * 52;
    const fill = (pct / 100) * circ;
    return `${fill} ${circ - fill}`;
  }

  getArcOffset(pct: number): number {
    const circ = 2 * Math.PI * 52;
    return (pct / 100) * circ;
  }

  getStatusClass(status: string): string {
    const map: Record<string, string> = { in_progress: 'in-progress', review: 'review', open: 'open', closed: 'closed' };
    return map[status] || 'open';
  }

  getStatusLabel(status: string): string {
    const map: Record<string, string> = { in_progress: 'In Progress', review: 'Review', open: 'Open', closed: 'Closed' };
    return map[status] || status;
  }

  formatDate(d?: string): string {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  timeAgo(d?: string): string {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins || 1} min${mins !== 1 ? 's' : ''} ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs} hour${hrs !== 1 ? 's' : ''} ago`;
    const days = Math.floor(hrs / 24);
    return `${days} day${days !== 1 ? 's' : ''} ago`;
  }
}
