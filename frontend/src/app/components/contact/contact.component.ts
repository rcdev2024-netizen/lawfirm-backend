import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AppointmentService } from '../../services/appointment.service';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <section id="contact" class="contact">
      <div class="contact-bg"></div>
      <div class="container">
        <div class="contact-inner">
          <div class="contact-left fade-left">
            <p class="section-eyebrow">Get In Touch</p>
            <h2 class="section-title">Schedule a<br><em>Consultation</em></h2>
            <div class="gold-divider" style="justify-content:flex-start; margin:16px 0;">
              <span></span>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L9.5 9H2l5.9 4.3-2.3 7L12 17l6.4 3.3-2.3-7L22 9h-7.5z"/>
              </svg>
              <span></span>
            </div>
            <p class="contact-desc">
              Ready to take the next step? Contact us today for a confidential consultation. We're here to listen, advise, and advocate for you.
            </p>

            <div class="contact-info">
              <div class="info-item" *ngFor="let item of info">
                <div class="info-icon" [innerHTML]="item.icon"></div>
                <div>
                  <p class="info-label">{{ item.label }}</p>
                  <a class="info-value" [href]="item.href">{{ item.value }}</a>
                </div>
              </div>
            </div>

            <div class="social-links">
              <p class="social-label">Follow Us</p>
              <a class="social-link" href="#" aria-label="Facebook">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                </svg>
              </a>
            </div>
          </div>

          <div class="contact-right fade-right">
            <div class="contact-form-wrap">
              <div class="form-header">
                <h3>Book an Appointment</h3>
                <p>We'll respond within 24 hours</p>
              </div>

              <div class="success-message" *ngIf="submitted && !errorMsg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <p>Thank you! Your appointment request has been received. We'll be in touch shortly.</p>
              </div>

              <div class="error-message" *ngIf="errorMsg">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
                <p>{{ errorMsg }}</p>
              </div>

              <form class="contact-form" (ngSubmit)="onSubmit()" #f="ngForm" *ngIf="!submitted">
                <div class="form-row">
                  <div class="form-group">
                    <label>Full Name *</label>
                    <input type="text" name="name" [(ngModel)]="form.name" required placeholder="Juan dela Cruz">
                  </div>
                  <div class="form-group">
                    <label>Phone Number</label>
                    <input type="tel" name="phone" [(ngModel)]="form.phone" placeholder="0917 000 0000">
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Email Address *</label>
                    <input type="email" name="email" [(ngModel)]="form.email" required placeholder="juan@example.com">
                  </div>
                  <div class="form-group">
                    <label>Preferred Date</label>
                    <input type="date" name="date" [(ngModel)]="form.preferred_date" [min]="today">
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label>Practice Area</label>
                    <select name="area" [(ngModel)]="form.area">
                      <option value="">Select a practice area</option>
                      <option *ngFor="let a of areas" [value]="a">{{ a }}</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label>Preferred Time</label>
                    <select name="time" [(ngModel)]="form.preferred_time">
                      <option value="">Select time slot</option>
                      <option *ngFor="let t of timeSlots" [value]="t">{{ t }}</option>
                    </select>
                  </div>
                </div>
                <div class="form-group">
                  <label>Your Message *</label>
                  <textarea name="message" [(ngModel)]="form.message" required rows="5"
                    placeholder="Briefly describe your legal concern..."></textarea>
                </div>
                <button type="submit" class="btn-submit" [disabled]="loading">
                  <span *ngIf="!loading">Book Appointment</span>
                  <span *ngIf="loading" class="spinner"></span>
                  <svg *ngIf="!loading" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
                    <line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/>
                    <line x1="3" y1="10" x2="21" y2="10"/>
                  </svg>
                </button>
                <p class="form-note">* All inquiries are kept strictly confidential.</p>
              </form>
            </div>
          </div>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .contact {
      background: var(--navy);
      padding: 100px 0;
      position: relative;
      overflow: hidden;
    }
    .contact-bg {
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 50% 70% at 0% 50%, rgba(201,168,76,0.05) 0%, transparent 60%),
        radial-gradient(ellipse 50% 70% at 100% 50%, rgba(201,168,76,0.03) 0%, transparent 60%);
    }
    .contact-inner {
      display: grid;
      grid-template-columns: 1fr 1.3fr;
      gap: 80px;
      align-items: start;
      position: relative;
      z-index: 1;
    }
    .contact-left { display: flex; flex-direction: column; gap: 20px; }
    .contact-left .section-title { font-size: clamp(1.8rem, 3vw, 2.4rem); }
    .contact-left .section-title em { color: var(--gold); font-style: italic; }
    .contact-desc {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.05rem;
      color: var(--text-muted);
      line-height: 1.8;
    }
    .contact-info { display: flex; flex-direction: column; gap: 20px; margin-top: 8px; }
    .info-item { display: flex; align-items: flex-start; gap: 16px; }
    .info-icon {
      width: 44px; height: 44px;
      background: rgba(201,168,76,0.08);
      border: 1px solid rgba(201,168,76,0.2);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--gold);
      flex-shrink: 0;
    }
    .info-icon svg { width: 18px; height: 18px; }
    .info-label {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-bottom: 4px;
    }
    .info-value {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1rem;
      color: var(--white);
      transition: color 0.3s ease;
    }
    .info-value:hover { color: var(--gold); }
    .social-links { display: flex; align-items: center; gap: 16px; margin-top: 8px; }
    .social-label {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      color: var(--text-muted);
    }
    .social-link {
      width: 36px; height: 36px;
      background: rgba(201,168,76,0.1);
      border: 1px solid rgba(201,168,76,0.2);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--gold);
      transition: all 0.3s ease;
    }
    .social-link:hover { background: var(--gold); color: var(--navy); }
    .social-link svg { width: 16px; height: 16px; }
    .contact-form-wrap {
      background: var(--navy-mid);
      border: 1px solid rgba(201,168,76,0.15);
      padding: 40px;
      position: relative;
    }
    .contact-form-wrap::before {
      content: '';
      position: absolute;
      top: 0; left: 40px; right: 40px;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .form-header { margin-bottom: 28px; }
    .form-header h3 {
      font-family: 'Playfair Display', serif;
      font-size: 1.4rem;
      color: var(--white);
      margin-bottom: 4px;
    }
    .form-header p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.75rem;
      color: var(--text-muted);
    }
    .contact-form { display: flex; flex-direction: column; gap: 16px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group label {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text-muted);
    }
    .form-group input,
    .form-group select,
    .form-group textarea {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(201,168,76,0.15);
      color: var(--white);
      font-family: 'Montserrat', sans-serif;
      font-size: 0.85rem;
      padding: 12px 16px;
      outline: none;
      transition: border-color 0.3s ease, background 0.3s ease;
      width: 100%;
      box-sizing: border-box;
    }
    .form-group input[type="date"] { color-scheme: dark; }
    .form-group select { cursor: pointer; }
    .form-group select option { background: var(--navy-mid); color: var(--white); }
    .form-group textarea { resize: vertical; min-height: 120px; }
    .form-group input::placeholder,
    .form-group textarea::placeholder { color: rgba(157,168,184,0.5); }
    .form-group input:focus,
    .form-group select:focus,
    .form-group textarea:focus {
      border-color: var(--gold);
      background: rgba(201,168,76,0.04);
    }
    .btn-submit {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
      width: 100%;
      padding: 16px;
      background: var(--gold);
      color: var(--navy);
      border: none;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 4px;
      min-height: 52px;
    }
    .btn-submit:hover:not([disabled]) { background: var(--gold-light); }
    .btn-submit[disabled] { opacity: 0.7; cursor: default; }
    .btn-submit svg { width: 16px; height: 16px; }
    .spinner {
      width: 18px; height: 18px;
      border: 2px solid rgba(11,25,41,0.3);
      border-top-color: #0b1929;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .form-note {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      color: var(--text-muted);
      text-align: center;
    }
    .success-message {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 20px;
      background: rgba(201,168,76,0.08);
      border: 1px solid rgba(201,168,76,0.3);
      margin-bottom: 20px;
      color: var(--gold);
    }
    .success-message svg { width: 22px; height: 22px; flex-shrink: 0; margin-top: 2px; }
    .success-message p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      line-height: 1.5;
    }
    .error-message {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 16px;
      background: rgba(224,112,112,0.08);
      border: 1px solid rgba(224,112,112,0.25);
      margin-bottom: 16px;
      color: #e07070;
    }
    .error-message svg { width: 18px; height: 18px; flex-shrink: 0; }
    .error-message p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.78rem;
    }

    @media (max-width: 900px) {
      .contact-inner { grid-template-columns: 1fr; gap: 40px; }
      .form-row { grid-template-columns: 1fr; }
      .contact-form-wrap { padding: 24px; }
    }
  `]
})
export class ContactComponent {
  submitted = false;
  loading = false;
  errorMsg = '';
  today = new Date().toISOString().split('T')[0];

  form = {
    name: '', phone: '', email: '', area: '',
    message: '', preferred_date: '', preferred_time: ''
  };

  areas = ['Family Law', 'Civil Law', 'Estate Planning', 'Criminal Defense', 'Other Legal Services'];
  timeSlots = ['9:00 AM', '10:00 AM', '11:00 AM', '1:00 PM', '2:00 PM', '3:00 PM', '4:00 PM'];

  info = [
    {
      label: 'Phone', value: '0917 123 4567', href: 'tel:09171234567',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.18 2 2 0 0 1 3.59 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.09a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.73 16.92z"/>
      </svg>`
    },
    {
      label: 'Email', value: 'attyrochellecortez.naz@gmail.com',
      href: 'mailto:attyrochellecortez.naz@gmail.com',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
        <polyline points="22,6 12,13 2,6"/>
      </svg>`
    },
    {
      label: 'Location', value: 'Legazpi City, Philippines',
      href: 'https://maps.google.com/?q=Legazpi+City+Philippines',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
        <circle cx="12" cy="10" r="3"/>
      </svg>`
    }
  ];

  constructor(private appointmentService: AppointmentService) {}

  onSubmit() {
    this.errorMsg = '';
    this.loading = true;

    const payload = {
      full_name: this.form.name,
      email: this.form.email,
      phone: this.form.phone || undefined,
      practice_area: this.form.area || undefined,
      message: this.form.message,
      preferred_date: this.form.preferred_date || undefined,
      preferred_time: this.form.preferred_time || undefined
    };

    this.appointmentService.bookAppointment(payload).subscribe({
      next: () => {
        this.loading = false;
        this.submitted = true;
      },
      error: (err) => {
        this.loading = false;
        this.errorMsg = err?.error?.detail || 'Failed to submit appointment. Please try again or contact us directly.';
      }
    });
  }
}
