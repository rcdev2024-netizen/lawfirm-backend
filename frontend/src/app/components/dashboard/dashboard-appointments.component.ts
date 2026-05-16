import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DashboardService } from '../../services/dashboard.service';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-dashboard-appointments',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Appointments</h2>
          <p>Manage your scheduled consultations and hearings.</p>
        </div>
        <button class="btn-primary" (click)="showBookModal = true">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Book Appointment
        </button>
      </div>

      <!-- Appointments List -->
      <div class="card">
        <div class="card-header">
          <h3>My Appointments</h3>
          <div class="filter-tabs">
            <button *ngFor="let f of filters" class="tab" [class.active]="activeFilter === f" (click)="activeFilter = f">{{ f }}</button>
          </div>
        </div>
        <div class="appt-list" *ngIf="filteredAppts.length > 0">
          <div class="appt-item" *ngFor="let a of filteredAppts">
            <div class="appt-date-box">
              <span class="month">{{ getMonth(a.preferred_date) }}</span>
              <span class="day">{{ getDay(a.preferred_date) }}</span>
            </div>
            <div class="appt-body">
              <div class="appt-title">{{ a.practice_area || 'Legal Consultation' }}</div>
              <div class="appt-sub">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                {{ a.preferred_time || 'Time TBD' }}
              </div>
              <div class="appt-note" *ngIf="a.message">{{ a.message | slice:0:80 }}{{ a.message.length > 80 ? '...' : '' }}</div>
            </div>
            <span class="status-badge" [ngClass]="a.status">{{ a.status }}</span>
          </div>
        </div>
        <div class="empty-state" *ngIf="filteredAppts.length === 0 && !loading">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
          <p>No appointments found</p>
        </div>
        <div class="loading" *ngIf="loading"><div class="spinner"></div></div>
      </div>

      <!-- Book Modal -->
      <div class="modal-overlay" *ngIf="showBookModal" (click)="showBookModal = false">
        <div class="modal" (click)="$event.stopPropagation()">
          <div class="modal-header">
            <h3>Book Appointment</h3>
            <button class="close-btn" (click)="showBookModal = false">✕</button>
          </div>
          <form class="modal-form" (ngSubmit)="bookAppointment()">
            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input type="text" [(ngModel)]="form.full_name" name="full_name" required>
              </div>
              <div class="form-group">
                <label>Email</label>
                <input type="email" [(ngModel)]="form.email" name="email" required>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone</label>
                <input type="tel" [(ngModel)]="form.phone" name="phone">
              </div>
              <div class="form-group">
                <label>Practice Area</label>
                <select [(ngModel)]="form.practice_area" name="practice_area">
                  <option value="">Select area</option>
                  <option>Civil Litigation</option>
                  <option>Criminal Defense</option>
                  <option>Family Law</option>
                  <option>Corporate Law</option>
                  <option>Real Estate</option>
                  <option>Immigration</option>
                  <option>Labor Law</option>
                  <option>General Consultation</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Preferred Date</label>
                <input type="date" [(ngModel)]="form.preferred_date" name="preferred_date">
              </div>
              <div class="form-group">
                <label>Preferred Time</label>
                <input type="time" [(ngModel)]="form.preferred_time" name="preferred_time">
              </div>
            </div>
            <div class="form-group">
              <label>Message / Reason</label>
              <textarea [(ngModel)]="form.message" name="message" rows="3" required placeholder="Briefly describe your legal concern..."></textarea>
            </div>
            <div class="success-msg" *ngIf="bookSuccess">Appointment booked successfully!</div>
            <div class="error-msg" *ngIf="bookError">{{ bookError }}</div>
            <div class="modal-actions">
              <button type="button" class="btn-cancel" (click)="showBookModal = false">Cancel</button>
              <button type="submit" class="btn-primary" [disabled]="booking">{{ booking ? 'Booking...' : 'Book Appointment' }}</button>
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
    .btn-primary {
      display: flex; align-items: center; gap: 6px;
      padding: 10px 18px;
      background: #0b1929;
      color: #c9a84c;
      border: none;
      border-radius: 8px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
      white-space: nowrap;
    }
    .btn-primary:hover { background: #122035; }
    .btn-primary svg { width: 16px; height: 16px; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }
    .card-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid #f0f2f5; flex-wrap: wrap; gap: 12px; }
    .card-header h3 { font-size: 0.9rem; font-weight: 700; color: #1a202c; }

    .filter-tabs { display: flex; gap: 6px; }
    .tab { padding: 5px 12px; border: 1px solid #e2e8f0; background: none; border-radius: 20px; font-size: 0.72rem; font-weight: 600; color: #718096; cursor: pointer; transition: all 0.2s; }
    .tab:hover, .tab.active { background: #0b1929; color: #c9a84c; border-color: #0b1929; }

    .appt-list { padding: 8px 0; }
    .appt-item { display: flex; align-items: flex-start; gap: 16px; padding: 16px 20px; border-bottom: 1px solid #f8f9fb; transition: background 0.15s; }
    .appt-item:hover { background: #fafbfc; }
    .appt-item:last-child { border-bottom: none; }

    .appt-date-box {
      display: flex; flex-direction: column; align-items: center;
      background: #0b1929; color: #c9a84c;
      border-radius: 10px;
      padding: 8px 14px;
      min-width: 50px;
      flex-shrink: 0;
    }
    .month { font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
    .day { font-size: 1.4rem; font-weight: 700; line-height: 1; }

    .appt-body { flex: 1; }
    .appt-title { font-size: 0.88rem; font-weight: 700; color: #1a202c; margin-bottom: 4px; }
    .appt-sub { display: flex; align-items: center; gap: 5px; font-size: 0.75rem; color: #718096; margin-bottom: 4px; }
    .appt-sub svg { width: 14px; height: 14px; }
    .appt-note { font-size: 0.72rem; color: #9da8b8; }

    .status-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.68rem; font-weight: 600; align-self: flex-start; text-transform: capitalize; }
    .status-badge.pending { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .status-badge.confirmed { background: rgba(34,197,94,0.1); color: #22c55e; }
    .status-badge.cancelled { background: rgba(229,62,62,0.1); color: #e53e3e; }
    .status-badge.completed { background: rgba(107,114,128,0.1); color: #6b7280; }

    .empty-state { padding: 48px; text-align: center; color: #9da8b8; }
    .empty-state svg { width: 40px; height: 40px; color: #e2e8f0; margin: 0 auto 12px; }
    .empty-state p { font-size: 0.82rem; }
    .loading { display: flex; justify-content: center; padding: 48px; }
    .spinner { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 24px; }
    .modal { background: #fff; border-radius: 16px; width: 100%; max-width: 560px; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
    .modal-header { display: flex; align-items: center; justify-content: space-between; padding: 20px 24px; border-bottom: 1px solid #f0f2f5; }
    .modal-header h3 { font-family: 'Playfair Display', serif; font-size: 1.1rem; color: #1a202c; }
    .close-btn { background: none; border: none; font-size: 1rem; color: #9da8b8; cursor: pointer; padding: 4px; }
    .close-btn:hover { color: #4a5568; }

    .modal-form { padding: 24px; display: flex; flex-direction: column; gap: 16px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group label { font-size: 0.72rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.06em; }
    .form-group input, .form-group select, .form-group textarea {
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px 12px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      color: #2d3748;
      outline: none;
      transition: border-color 0.2s;
    }
    .form-group input:focus, .form-group select:focus, .form-group textarea:focus { border-color: #c9a84c; }
    .form-group textarea { resize: vertical; }

    .success-msg { padding: 10px 14px; background: rgba(34,197,94,0.1); color: #16c47e; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }
    .error-msg { padding: 10px 14px; background: rgba(229,62,62,0.1); color: #e53e3e; border-radius: 6px; font-size: 0.8rem; }
    .modal-actions { display: flex; gap: 12px; justify-content: flex-end; }
    .btn-cancel { padding: 10px 18px; background: none; border: 1px solid #e2e8f0; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-size: 0.8rem; font-weight: 600; color: #718096; cursor: pointer; }
    .btn-cancel:hover { background: #f0f2f5; }

    @media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }
  `]
})
export class DashboardAppointmentsComponent implements OnInit {
  appointments: any[] = [];
  loading = true;
  activeFilter = 'All';
  filters = ['All', 'Pending', 'Confirmed', 'Completed', 'Cancelled'];

  showBookModal = false;
  booking = false;
  bookSuccess = false;
  bookError = '';

  form = { full_name: '', email: '', phone: '', practice_area: '', message: '', preferred_date: '', preferred_time: '' };

  constructor(private service: DashboardService, private auth: AuthService) {}

  ngOnInit() {
    const user = this.auth.currentUser;
    if (user) { this.form.full_name = user.full_name; this.form.email = user.email; }
    this.service.getAppointments().subscribe({
      next: a => { this.appointments = a; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  get filteredAppts(): any[] {
    if (this.activeFilter === 'All') return this.appointments;
    return this.appointments.filter(a => a.status.toLowerCase() === this.activeFilter.toLowerCase());
  }

  bookAppointment() {
    this.booking = true; this.bookError = '';
    this.service.bookAppointment(this.form).subscribe({
      next: a => {
        this.appointments.unshift(a);
        this.booking = false; this.bookSuccess = true;
        setTimeout(() => { this.showBookModal = false; this.bookSuccess = false; }, 2000);
      },
      error: err => { this.booking = false; this.bookError = err?.error?.detail || 'Failed to book appointment.'; }
    });
  }

  getMonth(d?: string): string { return d ? new Date(d).toLocaleDateString('en-US', { month: 'short' }).toUpperCase() : '—'; }
  getDay(d?: string): string { return d ? new Date(d).getDate().toString() : '—'; }
}
