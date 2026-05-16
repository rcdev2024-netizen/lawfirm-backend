import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule],
  template: `
    <div class="login-page">
      <div class="login-bg"></div>

      <div class="login-container">
        <div class="login-card">
          <div class="login-logo">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="22" stroke="currentColor" stroke-width="1.5"/>
              <line x1="24" y1="8" x2="24" y2="40" stroke="currentColor" stroke-width="1.5"/>
              <line x1="14" y1="18" x2="34" y2="18" stroke="currentColor" stroke-width="1.5"/>
              <line x1="10" y1="36" x2="18" y2="28" stroke="currentColor" stroke-width="1.5"/>
              <line x1="38" y1="36" x2="30" y2="28" stroke="currentColor" stroke-width="1.5"/>
              <line x1="10" y1="36" x2="38" y2="36" stroke="currentColor" stroke-width="1.5"/>
            </svg>
            <div class="logo-text">
              <span class="logo-name">Atty Rochelle Cortez-Naz</span>
              <span class="logo-sub">LAW OFFICE</span>
            </div>
          </div>

          <div class="tab-header">
            <button class="tab-btn" [class.active]="mode === 'login'" (click)="mode = 'login'">Sign In</button>
            <button class="tab-btn" [class.active]="mode === 'register'" (click)="mode = 'register'">Register</button>
          </div>

          <form (ngSubmit)="onSubmit()" #f="ngForm" *ngIf="mode === 'login'" class="login-form">
            <h2 class="form-title">Welcome Back</h2>
            <p class="form-subtitle">Sign in to manage your consultations</p>

            <div class="form-group">
              <label>Email Address</label>
              <input type="email" name="email" [(ngModel)]="loginData.email" required placeholder="juan@example.com">
            </div>
            <div class="form-group">
              <label>Password</label>
              <div class="password-wrap">
                <input [type]="showPassword ? 'text' : 'password'" name="password" [(ngModel)]="loginData.password" required placeholder="••••••••">
                <button type="button" class="toggle-pw" (click)="showPassword = !showPassword" tabindex="-1">
                  <svg *ngIf="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg *ngIf="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="error-msg" *ngIf="errorMessage">{{ errorMessage }}</div>

            <button type="submit" class="btn-submit" [disabled]="loading">
              <span *ngIf="!loading">Sign In</span>
              <span *ngIf="loading" class="spinner"></span>
            </button>
          </form>

          <form (ngSubmit)="onRegister()" #rf="ngForm" *ngIf="mode === 'register'" class="login-form">
            <h2 class="form-title">Create Account</h2>
            <p class="form-subtitle">Register to book and track your consultations</p>

            <div class="form-group">
              <label>Full Name</label>
              <input type="text" name="fullname" [(ngModel)]="registerData.fullName" required placeholder="Juan dela Cruz">
            </div>
            <div class="form-group">
              <label>Email Address</label>
              <input type="email" name="remail" [(ngModel)]="registerData.email" required placeholder="juan@example.com">
            </div>
            <div class="form-group">
              <label>Password</label>
              <div class="password-wrap">
                <input [type]="showPassword ? 'text' : 'password'" name="rpassword" [(ngModel)]="registerData.password" required placeholder="Min. 6 characters">
                <button type="button" class="toggle-pw" (click)="showPassword = !showPassword" tabindex="-1">
                  <svg *ngIf="!showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                  </svg>
                  <svg *ngIf="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                </button>
              </div>
            </div>

            <div class="error-msg" *ngIf="errorMessage">{{ errorMessage }}</div>

            <button type="submit" class="btn-submit" [disabled]="loading">
              <span *ngIf="!loading">Create Account</span>
              <span *ngIf="loading" class="spinner"></span>
            </button>
          </form>

          <a class="back-home" routerLink="/">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Back to Home
          </a>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .login-page {
      min-height: 100vh;
      background: var(--navy, #0b1929);
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
      padding: 24px;
    }
    .login-bg {
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 60% 60% at 70% 30%, rgba(201,168,76,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 50% 80% at 10% 80%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }
    .login-container {
      position: relative;
      z-index: 1;
      width: 100%;
      max-width: 460px;
    }
    .login-card {
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(201,168,76,0.18);
      padding: 40px 36px;
      position: relative;
    }
    .login-card::before {
      content: '';
      position: absolute;
      top: 0; left: 40px; right: 40px;
      height: 2px;
      background: linear-gradient(90deg, transparent, #c9a84c, transparent);
    }
    .login-logo {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 28px;
      justify-content: center;
    }
    .login-logo svg {
      width: 40px; height: 40px;
      color: #c9a84c;
      flex-shrink: 0;
    }
    .logo-text {
      display: flex;
      flex-direction: column;
    }
    .logo-name {
      font-family: 'Playfair Display', serif;
      font-size: 0.9rem;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.2;
    }
    .logo-sub {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.55rem;
      font-weight: 600;
      letter-spacing: 0.2em;
      color: #c9a84c;
    }
    .tab-header {
      display: flex;
      border-bottom: 1px solid rgba(201,168,76,0.15);
      margin-bottom: 28px;
    }
    .tab-btn {
      flex: 1;
      background: none;
      border: none;
      padding: 10px 0;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(157,168,184,0.6);
      cursor: pointer;
      border-bottom: 2px solid transparent;
      margin-bottom: -1px;
      transition: all 0.3s ease;
    }
    .tab-btn.active {
      color: #c9a84c;
      border-bottom-color: #c9a84c;
    }
    .form-title {
      font-family: 'Playfair Display', serif;
      font-size: 1.5rem;
      color: #ffffff;
      margin-bottom: 4px;
    }
    .form-subtitle {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.72rem;
      color: rgba(157,168,184,0.7);
      margin-bottom: 24px;
    }
    .login-form { display: flex; flex-direction: column; gap: 16px; }
    .form-group { display: flex; flex-direction: column; gap: 6px; }
    .form-group label {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.62rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: rgba(157,168,184,0.8);
    }
    .form-group input {
      background: rgba(255,255,255,0.04);
      border: 1px solid rgba(201,168,76,0.15);
      color: #ffffff;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.85rem;
      padding: 12px 16px;
      outline: none;
      transition: border-color 0.3s ease;
      width: 100%;
      box-sizing: border-box;
    }
    .form-group input::placeholder { color: rgba(157,168,184,0.4); }
    .form-group input:focus { border-color: #c9a84c; }
    .password-wrap { position: relative; }
    .password-wrap input { padding-right: 44px; }
    .toggle-pw {
      position: absolute;
      right: 12px; top: 50%;
      transform: translateY(-50%);
      background: none;
      border: none;
      cursor: pointer;
      color: rgba(157,168,184,0.5);
      padding: 4px;
      display: flex;
      align-items: center;
    }
    .toggle-pw:hover { color: #c9a84c; }
    .toggle-pw svg { width: 16px; height: 16px; }
    .error-msg {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.72rem;
      color: #e07070;
      padding: 10px 14px;
      background: rgba(224,112,112,0.08);
      border: 1px solid rgba(224,112,112,0.2);
    }
    .btn-submit {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      padding: 14px;
      background: #c9a84c;
      color: #0b1929;
      border: none;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.15em;
      text-transform: uppercase;
      cursor: pointer;
      transition: all 0.3s ease;
      margin-top: 4px;
      min-height: 48px;
    }
    .btn-submit:hover:not([disabled]) { background: #d4b55a; }
    .btn-submit[disabled] { opacity: 0.6; cursor: default; }
    .spinner {
      width: 18px; height: 18px;
      border: 2px solid rgba(11,25,41,0.3);
      border-top-color: #0b1929;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
      display: inline-block;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .back-home {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 24px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.68rem;
      letter-spacing: 0.08em;
      color: rgba(157,168,184,0.6);
      text-decoration: none;
      transition: color 0.3s ease;
      justify-content: center;
    }
    .back-home:hover { color: #c9a84c; }
    .back-home svg { width: 14px; height: 14px; }
  `]
})
export class LoginComponent {
  mode: 'login' | 'register' = 'login';
  showPassword = false;
  loading = false;
  errorMessage = '';

  loginData = { email: '', password: '' };
  registerData = { fullName: '', email: '', password: '' };

  constructor(private authService: AuthService, private router: Router) {
    if (this.authService.isLoggedIn) {
      this.router.navigate(['/']);
    }
  }

  onSubmit() {
    this.errorMessage = '';
    if (!this.loginData.email || !this.loginData.password) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }
    this.loading = true;
    this.authService.login(this.loginData.email, this.loginData.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Login failed. Please check your credentials.';
      }
    });
  }

  onRegister() {
    this.errorMessage = '';
    if (!this.registerData.fullName || !this.registerData.email || !this.registerData.password) {
      this.errorMessage = 'Please fill in all fields.';
      return;
    }
    if (this.registerData.password.length < 6) {
      this.errorMessage = 'Password must be at least 6 characters.';
      return;
    }
    this.loading = true;
    this.authService.register(this.registerData.fullName, this.registerData.email, this.registerData.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err?.error?.detail || 'Registration failed. Please try again.';
      }
    });
  }
}
