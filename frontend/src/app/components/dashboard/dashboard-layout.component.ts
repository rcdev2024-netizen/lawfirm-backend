import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterModule, RouterOutlet } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { AuthService } from '../../services/auth.service';
import { DashboardService } from '../../services/dashboard.service';

interface NavItem {
  label: string;
  icon: SafeHtml;
  route: string;
  badge?: number;
}

@Component({
  selector: 'app-dashboard-layout',
  standalone: true,
  imports: [CommonModule, RouterModule, RouterOutlet, FormsModule],
  template: `
    <div class="portal-shell">
      <!-- SIDEBAR -->
      <aside class="sidebar" [class.collapsed]="sidebarCollapsed">
        <!-- Logo -->
        <div class="sidebar-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect x="4" y="2" width="32" height="36" rx="3" fill="#c9a84c" opacity="0.15"/>
              <rect x="8" y="6" width="24" height="3" rx="1.5" fill="#c9a84c"/>
              <rect x="8" y="13" width="16" height="2.5" rx="1.25" fill="#c9a84c" opacity="0.7"/>
              <rect x="8" y="19" width="20" height="2.5" rx="1.25" fill="#c9a84c" opacity="0.7"/>
              <rect x="8" y="25" width="12" height="2.5" rx="1.25" fill="#c9a84c" opacity="0.5"/>
              <circle cx="30" cy="28" r="8" fill="#0b1929"/>
              <path d="M26 28l3 3 5-5" stroke="#c9a84c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <div class="logo-text" *ngIf="!sidebarCollapsed">
            <span class="logo-firm">LEXINGTON</span>
            <span class="logo-sub">LAW FIRM</span>
          </div>
        </div>

        <!-- Nav Items -->
        <nav class="sidebar-nav">
          <a
            *ngFor="let item of navItems"
            [routerLink]="item.route"
            routerLinkActive="active"
            [routerLinkActiveOptions]="{ exact: item.route === '/dashboard' }"
            class="nav-item"
            [title]="item.label"
          >
            <span class="nav-icon" [innerHTML]="item.icon"></span>
            <span class="nav-label" *ngIf="!sidebarCollapsed">{{ item.label }}</span>
            <span class="nav-badge" *ngIf="item.badge && item.badge > 0">{{ item.badge }}</span>
          </a>

          <div class="nav-divider"></div>

          <a routerLink="/dashboard/profile" routerLinkActive="active" class="nav-item" title="Profile Settings">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
            </span>
            <span class="nav-label" *ngIf="!sidebarCollapsed">Profile Settings</span>
          </a>

          <a class="nav-item" title="Refer a Friend" (click)="showReferModal()">
            <span class="nav-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/></svg>
            </span>
            <span class="nav-label" *ngIf="!sidebarCollapsed">Refer a Friend</span>
          </a>
        </nav>

        <!-- Help Card -->
        <div class="help-card" *ngIf="!sidebarCollapsed">
          <div class="help-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/></svg>
          </div>
          <div class="help-text">
            <strong>Need Help?</strong>
            <p>Our support team is here to assist you.</p>
          </div>
          <button class="help-btn" routerLink="/dashboard/messages">Contact Support</button>
        </div>

        <div class="sidebar-footer" *ngIf="!sidebarCollapsed">
          <p>© 2024 Lexington Law Firm</p>
          <p>All rights reserved.</p>
        </div>
      </aside>

      <!-- MAIN CONTENT -->
      <div class="main-wrapper">
        <!-- TOP BAR -->
        <header class="topbar">
          <div class="topbar-left">
            <button class="toggle-btn" (click)="sidebarCollapsed = !sidebarCollapsed">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
            </button>
            <div class="search-wrap">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <input type="text" placeholder="Search anything..." [(ngModel)]="searchQuery" />
            </div>
          </div>
          <div class="topbar-right">
            <button class="live-chat-btn" routerLink="/dashboard/messages">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
              Live Chat
            </button>
            <button class="icon-btn notif-btn" routerLink="/dashboard/notifications">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>
              <span class="badge" *ngIf="unreadNotifs > 0">{{ unreadNotifs }}</span>
            </button>
            <div class="user-menu" (click)="toggleUserMenu()" [class.open]="userMenuOpen">
              <div class="user-avatar">{{ userInitial }}</div>
              <div class="user-info">
                <span class="user-name">{{ userName }}</span>
                <span class="user-role">{{ userRole }}</span>
              </div>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="caret"><polyline points="6 9 12 15 18 9"/></svg>
              <div class="dropdown" *ngIf="userMenuOpen">
                <a routerLink="/dashboard/profile">Profile</a>
                <a routerLink="/dashboard/notifications">Notifications</a>
                <hr/>
                <a (click)="logout()">Sign Out</a>
              </div>
            </div>
          </div>
        </header>

        <!-- PAGE CONTENT -->
        <main class="page-content">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100vh; overflow: hidden; }

    .portal-shell {
      display: flex;
      height: 100vh;
      background: #f0f2f5;
      font-family: 'Montserrat', sans-serif;
      overflow: hidden;
    }

    /* ── SIDEBAR ── */
    .sidebar {
      width: 230px;
      min-width: 230px;
      background: #0b1929;
      display: flex;
      flex-direction: column;
      transition: width 0.25s ease, min-width 0.25s ease;
      overflow: hidden;
      border-right: 1px solid rgba(201,168,76,0.1);
      position: relative;
      z-index: 100;
    }
    .sidebar.collapsed { width: 64px; min-width: 64px; }

    .sidebar-logo {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 20px 16px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.06);
      flex-shrink: 0;
    }
    .logo-icon { width: 36px; height: 36px; flex-shrink: 0; }
    .logo-icon svg { width: 36px; height: 36px; }
    .logo-text { display: flex; flex-direction: column; }
    .logo-firm {
      font-family: 'Playfair Display', serif;
      font-size: 0.85rem;
      font-weight: 700;
      color: #fff;
      line-height: 1.1;
      white-space: nowrap;
    }
    .logo-sub {
      font-size: 0.5rem;
      font-weight: 600;
      letter-spacing: 0.18em;
      color: #c9a84c;
      white-space: nowrap;
    }

    .sidebar-nav {
      flex: 1;
      overflow-y: auto;
      padding: 12px 0;
      scrollbar-width: none;
    }
    .sidebar-nav::-webkit-scrollbar { display: none; }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      color: rgba(157,168,184,0.8);
      text-decoration: none;
      font-size: 0.78rem;
      font-weight: 500;
      transition: all 0.2s ease;
      cursor: pointer;
      position: relative;
      white-space: nowrap;
    }
    .nav-item:hover { color: #fff; background: rgba(255,255,255,0.04); }
    .nav-item.active {
      color: #c9a84c;
      background: rgba(201,168,76,0.08);
      border-right: 3px solid #c9a84c;
    }
    .nav-icon { width: 18px; height: 18px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }
    .nav-icon svg { width: 18px; height: 18px; }
    .nav-label { flex: 1; }
    .nav-badge {
      background: #c9a84c;
      color: #0b1929;
      font-size: 0.6rem;
      font-weight: 700;
      padding: 1px 6px;
      border-radius: 10px;
      min-width: 18px;
      text-align: center;
    }
    .nav-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 8px 0; }

    .help-card {
      margin: 12px;
      background: rgba(201,168,76,0.06);
      border: 1px solid rgba(201,168,76,0.15);
      border-radius: 8px;
      padding: 14px;
      flex-shrink: 0;
    }
    .help-icon svg { width: 22px; height: 22px; color: #c9a84c; margin-bottom: 6px; }
    .help-text strong { color: #fff; font-size: 0.78rem; display: block; margin-bottom: 4px; }
    .help-text p { color: rgba(157,168,184,0.7); font-size: 0.68rem; line-height: 1.4; margin-bottom: 10px; }
    .help-btn {
      width: 100%;
      padding: 8px;
      background: #c9a84c;
      color: #0b1929;
      border: none;
      border-radius: 4px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: background 0.2s;
    }
    .help-btn:hover { background: #d4b55a; }

    .sidebar-footer {
      padding: 10px 16px 14px;
      font-size: 0.6rem;
      color: rgba(157,168,184,0.35);
      border-top: 1px solid rgba(255,255,255,0.04);
      flex-shrink: 0;
      line-height: 1.6;
    }

    /* ── MAIN WRAPPER ── */
    .main-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* ── TOP BAR ── */
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 20px;
      height: 60px;
      background: #fff;
      border-bottom: 1px solid #e8eaf0;
      flex-shrink: 0;
      gap: 16px;
    }
    .topbar-left { display: flex; align-items: center; gap: 12px; flex: 1; }
    .toggle-btn {
      background: none;
      border: none;
      cursor: pointer;
      color: #4a5568;
      padding: 6px;
      border-radius: 6px;
      display: flex;
      align-items: center;
      transition: background 0.2s;
      flex-shrink: 0;
    }
    .toggle-btn:hover { background: #f0f2f5; }
    .toggle-btn svg { width: 20px; height: 20px; }

    .search-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      background: #f0f2f5;
      border-radius: 8px;
      padding: 8px 14px;
      flex: 1;
      max-width: 380px;
    }
    .search-wrap svg { width: 16px; height: 16px; color: #9da8b8; flex-shrink: 0; }
    .search-wrap input {
      background: none;
      border: none;
      outline: none;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      color: #2d3748;
      width: 100%;
    }
    .search-wrap input::placeholder { color: #9da8b8; }

    .topbar-right { display: flex; align-items: center; gap: 10px; }

    .live-chat-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 7px 14px;
      background: none;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.75rem;
      font-weight: 600;
      color: #4a5568;
      cursor: pointer;
      transition: all 0.2s;
      white-space: nowrap;
    }
    .live-chat-btn:hover { border-color: #c9a84c; color: #c9a84c; }
    .live-chat-btn svg { width: 15px; height: 15px; }

    .icon-btn {
      position: relative;
      background: none;
      border: none;
      cursor: pointer;
      color: #4a5568;
      padding: 8px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      transition: background 0.2s;
    }
    .icon-btn:hover { background: #f0f2f5; }
    .icon-btn svg { width: 20px; height: 20px; }
    .badge {
      position: absolute;
      top: 2px; right: 2px;
      background: #e53e3e;
      color: #fff;
      font-size: 0.55rem;
      font-weight: 700;
      width: 16px; height: 16px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .user-menu {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      padding: 6px 10px;
      border-radius: 8px;
      transition: background 0.2s;
      position: relative;
    }
    .user-menu:hover, .user-menu.open { background: #f0f2f5; }
    .user-avatar {
      width: 34px; height: 34px;
      border-radius: 50%;
      background: linear-gradient(135deg, #c9a84c, #e0c46a);
      color: #0b1929;
      font-weight: 700;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .user-info { display: flex; flex-direction: column; }
    .user-name { font-size: 0.78rem; font-weight: 600; color: #2d3748; white-space: nowrap; }
    .user-role { font-size: 0.6rem; color: #9da8b8; text-transform: capitalize; white-space: nowrap; }
    .caret { width: 14px; height: 14px; color: #9da8b8; }

    .dropdown {
      position: absolute;
      top: calc(100% + 6px);
      right: 0;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.1);
      min-width: 160px;
      z-index: 200;
      overflow: hidden;
    }
    .dropdown a {
      display: block;
      padding: 10px 16px;
      font-size: 0.78rem;
      color: #4a5568;
      text-decoration: none;
      cursor: pointer;
      transition: background 0.15s;
    }
    .dropdown a:hover { background: #f7f8fa; color: #c9a84c; }
    .dropdown hr { border: none; border-top: 1px solid #e2e8f0; margin: 4px 0; }

    /* ── PAGE CONTENT ── */
    .page-content {
      flex: 1;
      overflow-y: auto;
      padding: 24px;
      background: #f0f2f5;
    }

  `]
})
export class DashboardLayoutComponent implements OnInit {
  sidebarCollapsed = false;
  searchQuery = '';
  userMenuOpen = false;
  unreadNotifs = 0;

  navItems: NavItem[] = [];

  constructor(
    private authService: AuthService,
    private dashboardService: DashboardService,
    private router: Router,
    private sanitizer: DomSanitizer
  ) {
    const s = (html: string): SafeHtml => this.sanitizer.bypassSecurityTrustHtml(html);
    this.navItems = [
      { label: 'Dashboard', route: '/dashboard', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>') },
      { label: 'My Cases', route: '/dashboard/cases', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/></svg>') },
      { label: 'Appointments', route: '/dashboard/appointments', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>') },
      { label: 'Documents', route: '/dashboard/documents', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>') },
      { label: 'Messages', route: '/dashboard/messages', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>') },
      { label: 'Billing & Invoices', route: '/dashboard/billing', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>') },
      { label: 'Notifications', route: '/dashboard/notifications', icon: s('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 01-3.46 0"/></svg>') }
    ];
  }

  ngOnInit() {
    this.loadStats();
  }

  loadStats() {
    this.dashboardService.getStats().subscribe({
      next: (stats) => {
        this.unreadNotifs = stats.unread_notifications;
        const msgItem = this.navItems.find(n => n.label === 'Messages');
        if (msgItem) msgItem.badge = stats.unread_messages;
        const notifItem = this.navItems.find(n => n.label === 'Notifications');
        if (notifItem) notifItem.badge = stats.unread_notifications;
      },
      error: () => {}
    });
  }

  get userName(): string {
    return this.authService.currentUser?.full_name || 'User';
  }

  get userInitial(): string {
    return (this.authService.currentUser?.full_name || 'U')[0].toUpperCase();
  }

  get userRole(): string {
    return (this.authService.currentUser as any)?.role || 'Client';
  }

  toggleUserMenu() {
    this.userMenuOpen = !this.userMenuOpen;
  }

  showReferModal() {}

  logout() {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
