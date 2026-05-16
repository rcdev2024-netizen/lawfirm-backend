import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { DashboardService, Case } from '../../services/dashboard.service';

@Component({
  selector: 'app-my-cases',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>My Cases</h2>
          <p>Track and manage all your active and past cases.</p>
        </div>
      </div>

      <!-- Filter Tabs -->
      <div class="filter-tabs">
        <button *ngFor="let f of filters" class="tab" [class.active]="activeFilter === f.value" (click)="activeFilter = f.value">
          {{ f.label }} <span class="tab-count">{{ getCount(f.value) }}</span>
        </button>
      </div>

      <!-- Cases Grid -->
      <div class="cases-grid" *ngIf="filteredCases.length > 0">
        <div class="case-card" *ngFor="let c of filteredCases">
          <div class="case-card-header">
            <div class="case-number">#{{ c.case_number }}</div>
            <span class="status-badge" [ngClass]="getStatusClass(c.status)">{{ getStatusLabel(c.status) }}</span>
          </div>
          <h3 class="case-title">{{ c.case_name }}</h3>
          <div class="case-meta">
            <span class="case-type-tag">{{ c.case_type || 'General' }}</span>
          </div>
          <div class="case-details">
            <div class="detail-row" *ngIf="c.court">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/></svg>
              <span>{{ c.court }}</span>
            </div>
            <div class="detail-row" *ngIf="c.next_hearing_date">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
              <span>Next: {{ formatDate(c.next_hearing_date) }} {{ c.next_hearing_time ? 'at ' + c.next_hearing_time : '' }}</span>
            </div>
            <div class="detail-row" *ngIf="c.judge">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
              <span>Judge {{ c.judge }}</span>
            </div>
          </div>
          <div class="case-footer">
            <span class="updated">Updated {{ timeAgo(c.updated_at) }}</span>
          </div>
        </div>
      </div>

      <div class="empty-state" *ngIf="filteredCases.length === 0 && !loading">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>
        <h3>No cases found</h3>
        <p>You don't have any {{ activeFilter !== 'all' ? activeFilter : '' }} cases at the moment.</p>
      </div>

      <div class="loading-state" *ngIf="loading">
        <div class="spinner"></div>
        <p>Loading cases...</p>
      </div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { margin-bottom: 24px; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }

    .filter-tabs { display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }
    .tab {
      padding: 8px 16px;
      border: 1px solid #e2e8f0;
      background: #fff;
      border-radius: 20px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.78rem;
      font-weight: 600;
      color: #718096;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .tab:hover { border-color: #c9a84c; color: #c9a84c; }
    .tab.active { background: #0b1929; color: #c9a84c; border-color: #0b1929; }
    .tab-count {
      background: rgba(201,168,76,0.2);
      color: #c9a84c;
      font-size: 0.62rem;
      padding: 1px 6px;
      border-radius: 10px;
    }

    .cases-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }

    .case-card {
      background: #fff;
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 1px 6px rgba(0,0,0,0.06);
      border: 1px solid #f0f2f5;
      transition: box-shadow 0.2s, transform 0.2s;
    }
    .case-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); transform: translateY(-2px); }

    .case-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
    .case-number { font-size: 0.7rem; color: #9da8b8; font-weight: 600; }

    .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 600; }
    .status-badge.in-progress { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .status-badge.review { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .status-badge.open { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .status-badge.closed { background: rgba(22,197,94,0.1); color: #16c47e; }

    .case-title { font-size: 0.95rem; font-weight: 700; color: #1a202c; margin-bottom: 8px; line-height: 1.3; }
    .case-meta { margin-bottom: 12px; }
    .case-type-tag {
      display: inline-block;
      padding: 2px 10px;
      background: #f0f2f5;
      border-radius: 4px;
      font-size: 0.68rem;
      color: #718096;
      font-weight: 500;
    }
    .case-details { display: flex; flex-direction: column; gap: 6px; margin-bottom: 16px; }
    .detail-row { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #4a5568; }
    .detail-row svg { width: 14px; height: 14px; color: #9da8b8; flex-shrink: 0; }

    .case-footer { border-top: 1px solid #f0f2f5; padding-top: 12px; }
    .updated { font-size: 0.68rem; color: #9da8b8; }

    .empty-state {
      text-align: center;
      padding: 64px 32px;
      color: #9da8b8;
    }
    .empty-state svg { width: 48px; height: 48px; color: #e2e8f0; margin: 0 auto 16px; }
    .empty-state h3 { font-size: 1rem; color: #4a5568; margin-bottom: 6px; }
    .empty-state p { font-size: 0.8rem; }

    .loading-state { display: flex; flex-direction: column; align-items: center; gap: 12px; padding: 64px; color: #9da8b8; }
    .spinner { width: 32px; height: 32px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
  `]
})
export class MyCasesComponent implements OnInit {
  cases: Case[] = [];
  loading = true;
  activeFilter = 'all';

  filters = [
    { label: 'All Cases', value: 'all' },
    { label: 'In Progress', value: 'in_progress' },
    { label: 'Under Review', value: 'review' },
    { label: 'Open', value: 'open' },
    { label: 'Closed', value: 'closed' }
  ];

  constructor(private service: DashboardService) {}

  ngOnInit() {
    this.service.getCases().subscribe({
      next: c => { this.cases = c; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  get filteredCases(): Case[] {
    if (this.activeFilter === 'all') return this.cases;
    return this.cases.filter(c => c.status === this.activeFilter);
  }

  getCount(filter: string): number {
    if (filter === 'all') return this.cases.length;
    return this.cases.filter(c => c.status === filter).length;
  }

  getStatusClass(s: string): string {
    return { in_progress: 'in-progress', review: 'review', open: 'open', closed: 'closed' }[s] || 'open';
  }

  getStatusLabel(s: string): string {
    return { in_progress: 'In Progress', review: 'Review', open: 'Open', closed: 'Closed' }[s] || s;
  }

  formatDate(d?: string): string {
    if (!d) return '—';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  timeAgo(d?: string): string {
    if (!d) return '';
    const diff = Date.now() - new Date(d).getTime();
    const days = Math.floor(diff / 86400000);
    if (days === 0) return 'today';
    if (days === 1) return 'yesterday';
    return `${days} days ago`;
  }
}
