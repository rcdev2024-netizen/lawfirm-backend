import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-profile',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="page">
      <div class="page-header">
        <h2>Profile Settings</h2>
        <p>Manage your personal information and preferences.</p>
      </div>

      <div class="profile-layout">
        <!-- Avatar Card -->
        <div class="card avatar-card">
          <div class="avatar-circle">{{ userInitial }}</div>
          <h3>{{ user?.full_name }}</h3>
          <span class="role-badge">{{ user?.role || 'Client' }}</span>
          <p class="email">{{ user?.email }}</p>
        </div>

        <!-- Info Card -->
        <div class="card info-card">
          <div class="card-header"><h3>Personal Information</h3></div>
          <form class="form" (ngSubmit)="save()">
            <div class="form-row">
              <div class="form-group">
                <label>Full Name</label>
                <input type="text" [(ngModel)]="form.full_name" name="full_name">
              </div>
              <div class="form-group">
                <label>Email Address</label>
                <input type="email" [value]="user?.email" disabled>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone Number</label>
                <input type="tel" [(ngModel)]="form.phone" name="phone" placeholder="+63 XXX XXX XXXX">
              </div>
              <div class="form-group">
                <label>Role</label>
                <input type="text" [value]="user?.role || 'Client'" disabled>
              </div>
            </div>
            <div class="success-msg" *ngIf="saveSuccess">Profile updated successfully!</div>
            <div class="form-actions">
              <button type="submit" class="btn-save" [disabled]="saving">{{ saving ? 'Saving...' : 'Save Changes' }}</button>
            </div>
          </form>
        </div>

        <!-- Security Card -->
        <div class="card security-card">
          <div class="card-header"><h3>Account Security</h3></div>
          <div class="security-list">
            <div class="security-item">
              <div class="security-icon green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <div class="security-body">
                <div class="security-label">Email verified</div>
                <div class="security-sub">Your email address is verified</div>
              </div>
            </div>
            <div class="security-item">
              <div class="security-icon amber">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
              </div>
              <div class="security-body">
                <div class="security-label">Password</div>
                <div class="security-sub">Last changed recently</div>
              </div>
              <button class="btn-change" (click)="showPasswordForm = !showPasswordForm">Change</button>
            </div>
          </div>
          <form *ngIf="showPasswordForm" class="password-form" (ngSubmit)="changePassword()">
            <div class="form-group">
              <label>Current Password</label>
              <input type="password" [(ngModel)]="pwForm.current" name="current" placeholder="••••••••">
            </div>
            <div class="form-group">
              <label>New Password</label>
              <input type="password" [(ngModel)]="pwForm.newPw" name="newPw" placeholder="Min. 6 characters">
            </div>
            <div class="pw-note">Password change is managed through the authentication system.</div>
            <button type="submit" class="btn-save small">Update Password</button>
          </form>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { margin-bottom: 24px; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }

    .profile-layout { display: grid; grid-template-columns: 240px 1fr; grid-template-rows: auto auto; gap: 16px; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }
    .card-header { padding: 16px 20px; border-bottom: 1px solid #f0f2f5; }
    .card-header h3 { font-size: 0.9rem; font-weight: 700; color: #1a202c; }

    .avatar-card { grid-row: 1 / 3; display: flex; flex-direction: column; align-items: center; padding: 32px 20px; text-align: center; }
    .avatar-circle { width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #0b1929, #1a2f4a); border: 3px solid #c9a84c; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 700; color: #c9a84c; margin-bottom: 16px; }
    .avatar-card h3 { font-size: 1rem; font-weight: 700; color: #1a202c; margin-bottom: 8px; }
    .role-badge { display: inline-block; padding: 3px 12px; background: rgba(201,168,76,0.1); color: #c9a84c; border-radius: 20px; font-size: 0.7rem; font-weight: 600; text-transform: capitalize; margin-bottom: 8px; }
    .email { font-size: 0.78rem; color: #9da8b8; }

    .info-card { grid-column: 2; }
    .security-card { grid-column: 2; }

    .form { padding: 20px; }
    .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group label { font-size: 0.7rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.06em; }
    .form-group input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; font-family: 'Montserrat', sans-serif; font-size: 0.82rem; color: #2d3748; outline: none; transition: border-color 0.2s; }
    .form-group input:focus { border-color: #c9a84c; }
    .form-group input:disabled { background: #f8f9fb; color: #9da8b8; cursor: not-allowed; }

    .success-msg { padding: 10px 14px; background: rgba(34,197,94,0.1); color: #16c47e; border-radius: 6px; font-size: 0.8rem; margin-bottom: 12px; }
    .form-actions { display: flex; justify-content: flex-end; }
    .btn-save { padding: 10px 24px; background: #0b1929; color: #c9a84c; border: none; border-radius: 8px; font-family: 'Montserrat', sans-serif; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: background 0.2s; }
    .btn-save:hover { background: #122035; }
    .btn-save.small { font-size: 0.75rem; padding: 8px 18px; margin-top: 12px; }

    .security-list { padding: 8px 0; }
    .security-item { display: flex; align-items: center; gap: 12px; padding: 14px 20px; border-bottom: 1px solid #f8f9fb; }
    .security-item:last-child { border-bottom: none; }
    .security-icon { width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .security-icon svg { width: 16px; height: 16px; }
    .security-icon.green { background: rgba(34,197,94,0.1); color: #22c55e; }
    .security-icon.amber { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .security-body { flex: 1; }
    .security-label { font-size: 0.82rem; font-weight: 600; color: #2d3748; margin-bottom: 2px; }
    .security-sub { font-size: 0.72rem; color: #9da8b8; }
    .btn-change { padding: 6px 14px; background: none; border: 1px solid #e2e8f0; border-radius: 6px; font-family: 'Montserrat', sans-serif; font-size: 0.72rem; font-weight: 600; color: #4a5568; cursor: pointer; transition: all 0.2s; }
    .btn-change:hover { border-color: #c9a84c; color: #c9a84c; }

    .password-form { padding: 0 20px 20px; display: flex; flex-direction: column; gap: 12px; }
    .pw-note { font-size: 0.72rem; color: #9da8b8; padding: 8px 12px; background: #f8f9fb; border-radius: 6px; }

    @media (max-width: 900px) { .profile-layout { grid-template-columns: 1fr; } .avatar-card { grid-row: auto; } .info-card, .security-card { grid-column: 1; } }
    @media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }
  `]
})
export class ProfileComponent implements OnInit {
  saving = false;
  saveSuccess = false;
  showPasswordForm = false;
  form = { full_name: '', phone: '' };
  pwForm = { current: '', newPw: '' };

  constructor(private auth: AuthService) {}

  ngOnInit() {
    const u = this.auth.currentUser;
    if (u) { this.form.full_name = u.full_name; this.form.phone = (u as any).phone || ''; }
  }

  get user() { return this.auth.currentUser; }
  get userInitial(): string { return (this.auth.currentUser?.full_name || 'U')[0].toUpperCase(); }

  save() {
    this.saving = true;
    setTimeout(() => { this.saving = false; this.saveSuccess = true; setTimeout(() => this.saveSuccess = false, 3000); }, 800);
  }

  changePassword() {}
}
