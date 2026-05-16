import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService, Invoice } from '../../services/dashboard.service';

@Component({
  selector: 'app-billing',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Billing & Invoices</h2>
          <p>Track your payments and outstanding invoices.</p>
        </div>
      </div>

      <!-- Summary Cards -->
      <div class="summary-cards">
        <div class="summary-card red">
          <div class="s-label">Unpaid</div>
          <div class="s-num">{{ unpaidCount }}</div>
          <div class="s-amount">{{ formatCurrency(unpaidTotal) }}</div>
        </div>
        <div class="summary-card green">
          <div class="s-label">Paid</div>
          <div class="s-num">{{ paidCount }}</div>
          <div class="s-amount">{{ formatCurrency(paidTotal) }}</div>
        </div>
        <div class="summary-card amber">
          <div class="s-label">Overdue</div>
          <div class="s-num">{{ overdueCount }}</div>
          <div class="s-amount">{{ formatCurrency(overdueTotal) }}</div>
        </div>
      </div>

      <!-- Invoice Table -->
      <div class="card">
        <div class="card-header">
          <h3>Invoice History</h3>
          <div class="filter-tabs">
            <button *ngFor="let f of filters" class="tab" [class.active]="activeFilter === f" (click)="activeFilter = f">{{ f }}</button>
          </div>
        </div>
        <div class="table-wrap" *ngIf="filteredInvoices.length > 0">
          <table>
            <thead>
              <tr>
                <th>INVOICE #</th>
                <th>AMOUNT</th>
                <th>TOTAL</th>
                <th>STATUS</th>
                <th>DUE DATE</th>
                <th>DATE</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let inv of filteredInvoices">
                <td><span class="inv-num">{{ inv.invoice_number }}</span></td>
                <td>{{ formatCurrency(inv.amount) }}</td>
                <td><strong>{{ formatCurrency(inv.total) }}</strong></td>
                <td><span class="status-badge" [ngClass]="inv.status">{{ inv.status }}</span></td>
                <td>
                  <span *ngIf="inv.due_date">{{ formatDate(inv.due_date) }}</span>
                  <span *ngIf="!inv.due_date" class="muted">—</span>
                </td>
                <td class="muted">{{ formatDate(inv.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="empty-state" *ngIf="filteredInvoices.length === 0 && !loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
          <p>No invoices found</p>
        </div>
        <div class="loading" *ngIf="loading"><div class="spinner"></div></div>
      </div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { margin-bottom: 24px; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }

    .summary-cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .summary-card { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); border-top: 3px solid transparent; }
    .summary-card.red { border-top-color: #e53e3e; }
    .summary-card.green { border-top-color: #22c55e; }
    .summary-card.amber { border-top-color: #f59e0b; }
    .s-label { font-size: 0.7rem; font-weight: 600; color: #9da8b8; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
    .s-num { font-size: 2rem; font-weight: 700; color: #1a202c; line-height: 1; margin-bottom: 4px; }
    .s-amount { font-size: 0.8rem; color: #718096; font-weight: 600; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }
    .card-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f0f2f5; flex-wrap: wrap; gap: 10px; }
    .card-header h3 { font-size: 0.9rem; font-weight: 700; color: #1a202c; }
    .filter-tabs { display: flex; gap: 6px; }
    .tab { padding: 5px 12px; border: 1px solid #e2e8f0; background: none; border-radius: 20px; font-size: 0.72rem; font-weight: 600; color: #718096; cursor: pointer; transition: all 0.2s; }
    .tab:hover, .tab.active { background: #0b1929; color: #c9a84c; border-color: #0b1929; }

    .table-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; }
    thead tr { background: #f8f9fb; }
    th { padding: 10px 16px; font-size: 0.65rem; font-weight: 600; color: #9da8b8; letter-spacing: 0.08em; text-transform: uppercase; text-align: left; white-space: nowrap; }
    td { padding: 14px 16px; border-bottom: 1px solid #f8f9fb; font-size: 0.82rem; color: #4a5568; }
    tr:last-child td { border-bottom: none; }
    .inv-num { font-weight: 600; color: #1a202c; font-size: 0.78rem; }
    .muted { color: #9da8b8; }

    .status-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 600; text-transform: capitalize; }
    .status-badge.unpaid { background: rgba(229,62,62,0.1); color: #e53e3e; }
    .status-badge.paid { background: rgba(34,197,94,0.1); color: #22c55e; }
    .status-badge.overdue { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .status-badge.cancelled { background: rgba(107,114,128,0.1); color: #6b7280; }

    .empty-state { padding: 48px; text-align: center; color: #9da8b8; }
    .empty-state svg { width: 40px; height: 40px; color: #e2e8f0; margin: 0 auto 12px; }
    .empty-state p { font-size: 0.82rem; }
    .loading { display: flex; justify-content: center; padding: 48px; }
    .spinner { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    @media (max-width: 600px) { .summary-cards { grid-template-columns: 1fr; } }
  `]
})
export class BillingComponent implements OnInit {
  invoices: Invoice[] = [];
  loading = true;
  activeFilter = 'All';
  filters = ['All', 'Unpaid', 'Paid', 'Overdue', 'Cancelled'];

  constructor(private service: DashboardService) {}

  ngOnInit() {
    this.service.getInvoices().subscribe({
      next: i => { this.invoices = i; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  get filteredInvoices(): Invoice[] {
    if (this.activeFilter === 'All') return this.invoices;
    return this.invoices.filter(i => i.status.toLowerCase() === this.activeFilter.toLowerCase());
  }

  get unpaidCount(): number { return this.invoices.filter(i => i.status === 'unpaid').length; }
  get paidCount(): number { return this.invoices.filter(i => i.status === 'paid').length; }
  get overdueCount(): number { return this.invoices.filter(i => i.status === 'overdue').length; }
  get unpaidTotal(): number { return this.invoices.filter(i => i.status === 'unpaid').reduce((s, i) => s + Number(i.total), 0); }
  get paidTotal(): number { return this.invoices.filter(i => i.status === 'paid').reduce((s, i) => s + Number(i.total), 0); }
  get overdueTotal(): number { return this.invoices.filter(i => i.status === 'overdue').reduce((s, i) => s + Number(i.total), 0); }

  formatCurrency(n: number): string { return new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' }).format(n); }
  formatDate(d?: string): string { if (!d) return '—'; return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }); }
}
