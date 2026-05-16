import { Component, HostListener, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { Subscription } from 'rxjs';
import { AuthService, User } from '../../services/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterModule],
  animations: [
    trigger('slideDown', [
      transition(':enter', [
        style({ transform: 'translateY(-100%)', opacity: 0 }),
        animate('0.6s cubic-bezier(0.25,0.46,0.45,0.94)', style({ transform: 'translateY(0)', opacity: 1 }))
      ])
    ]),
    trigger('mobileMenu', [
      state('closed', style({ height: '0', opacity: 0, overflow: 'hidden' })),
      state('open', style({ height: '*', opacity: 1, overflow: 'hidden' })),
      transition('closed <=> open', animate('0.35s cubic-bezier(0.25,0.46,0.45,0.94)'))
    ])
  ],
  template: `
    <nav [@slideDown] [class.scrolled]="isScrolled" [class.navbar]="true">
      <div class="nav-container">
        <a class="logo" (click)="scrollTo('home')">
          <div class="logo-icon">
            <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="24" cy="24" r="22" stroke="currentColor" stroke-width="1.5"/>
              <line x1="24" y1="8" x2="24" y2="40" stroke="currentColor" stroke-width="1.5"/>
              <line x1="14" y1="18" x2="34" y2="18" stroke="currentColor" stroke-width="1.5"/>
              <line x1="10" y1="36" x2="18" y2="28" stroke="currentColor" stroke-width="1.5"/>
              <line x1="38" y1="36" x2="30" y2="28" stroke="currentColor" stroke-width="1.5"/>
              <line x1="10" y1="36" x2="38" y2="36" stroke="currentColor" stroke-width="1.5"/>
            </svg>
          </div>
          <div class="logo-text">
            <span class="logo-name">Atty Rochelle<br>Cortez-Naz</span>
            <span class="logo-sub">LAW OFFICE</span>
          </div>
        </a>

        <button class="hamburger" (click)="toggleMenu()" [class.active]="menuOpen" aria-label="Toggle menu">
          <span></span><span></span><span></span>
        </button>

        <ul class="nav-links" [class.open]="menuOpen">
          <li *ngFor="let link of links">
            <a (click)="scrollTo(link.id); closeMenu()"
               [class.active]="activeSection === link.id">
              {{ link.label }}
            </a>
          </li>

          <li class="nav-auth">
            <ng-container *ngIf="!currentUser; else loggedIn">
              <a class="btn-login" routerLink="/login" (click)="closeMenu()">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
                  <circle cx="12" cy="7" r="4"/>
                </svg>
                Login
              </a>
            </ng-container>
            <ng-template #loggedIn>
              <div class="user-menu" (click)="toggleUserMenu()" [class.open]="userMenuOpen">
                <span class="user-name">{{ currentUser?.full_name?.split(' ')?.[0] }}</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="chevron">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
                <div class="user-dropdown" *ngIf="userMenuOpen">
                  <a class="dropdown-item" (click)="logout()">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
                      <polyline points="16 17 21 12 16 7"/>
                      <line x1="21" y1="12" x2="9" y2="12"/>
                    </svg>
                    Logout
                  </a>
                </div>
              </div>
            </ng-template>
          </li>
        </ul>
      </div>
    </nav>
  `,
  styles: [`
    .navbar {
      position: fixed;
      top: 0; left: 0; right: 0;
      z-index: 1000;
      padding: 20px 0;
      transition: all 0.4s cubic-bezier(0.25,0.46,0.45,0.94);
      background: transparent;
    }
    .navbar.scrolled {
      background: rgba(11, 25, 41, 0.97);
      backdrop-filter: blur(12px);
      padding: 12px 0;
      box-shadow: 0 2px 40px rgba(0,0,0,0.4);
      border-bottom: 1px solid rgba(201,168,76,0.15);
    }
    .nav-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .logo {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
    }
    .logo-icon {
      width: 44px; height: 44px;
      color: #c9a84c;
      flex-shrink: 0;
    }
    .logo-text { display: flex; flex-direction: column; }
    .logo-name {
      font-family: 'Playfair Display', serif;
      font-size: 0.95rem;
      font-weight: 700;
      color: #ffffff;
      line-height: 1.2;
    }
    .logo-sub {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      font-weight: 600;
      letter-spacing: 0.2em;
      color: #c9a84c;
      margin-top: 2px;
    }
    .nav-links {
      display: flex;
      list-style: none;
      gap: 8px;
      align-items: center;
      margin: 0;
      padding: 0;
    }
    .nav-links a {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: rgba(232,226,213,0.8);
      padding: 8px 14px;
      cursor: pointer;
      position: relative;
      transition: color 0.3s ease;
      text-decoration: none;
    }
    .nav-links a::after {
      content: '';
      position: absolute;
      bottom: 4px; left: 14px; right: 14px;
      height: 1px;
      background: #c9a84c;
      transform: scaleX(0);
      transition: transform 0.3s ease;
    }
    .nav-links a:hover, .nav-links a.active { color: #c9a84c; }
    .nav-links a:hover::after, .nav-links a.active::after { transform: scaleX(1); }

    .nav-auth { margin-left: 8px; }
    .btn-login {
      display: flex !important;
      align-items: center;
      gap: 6px;
      padding: 8px 18px !important;
      border: 1px solid rgba(201,168,76,0.5) !important;
      color: #c9a84c !important;
      border-radius: 2px;
      transition: all 0.3s ease !important;
      white-space: nowrap;
    }
    .btn-login::after { display: none !important; }
    .btn-login:hover {
      background: rgba(201,168,76,0.1) !important;
      border-color: #c9a84c !important;
    }
    .btn-login svg { width: 14px; height: 14px; }

    .user-menu {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 8px 14px;
      cursor: pointer;
      color: #c9a84c;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      position: relative;
      border: 1px solid rgba(201,168,76,0.3);
      border-radius: 2px;
      transition: background 0.3s;
    }
    .user-menu:hover { background: rgba(201,168,76,0.08); }
    .chevron { width: 12px; height: 12px; transition: transform 0.3s ease; }
    .user-menu.open .chevron { transform: rotate(180deg); }
    .user-dropdown {
      position: absolute;
      top: calc(100% + 8px);
      right: 0;
      background: rgba(11,25,41,0.98);
      border: 1px solid rgba(201,168,76,0.2);
      min-width: 160px;
      box-shadow: 0 8px 32px rgba(0,0,0,0.4);
      z-index: 100;
    }
    .dropdown-item {
      display: flex !important;
      align-items: center;
      gap: 10px;
      padding: 12px 16px !important;
      color: rgba(232,226,213,0.8) !important;
      font-size: 0.68rem !important;
      transition: all 0.2s ease !important;
      border-bottom: 1px solid rgba(201,168,76,0.08);
      cursor: pointer;
      text-transform: none !important;
      letter-spacing: 0.05em !important;
    }
    .dropdown-item::after { display: none !important; }
    .dropdown-item:hover { color: #c9a84c !important; background: rgba(201,168,76,0.06); }
    .dropdown-item svg { width: 14px; height: 14px; flex-shrink: 0; }

    .hamburger {
      display: none;
      flex-direction: column;
      gap: 5px;
      background: none;
      border: none;
      cursor: pointer;
      padding: 4px;
    }
    .hamburger span {
      display: block;
      width: 24px; height: 2px;
      background: #c9a84c;
      transition: all 0.3s ease;
      transform-origin: center;
    }
    .hamburger.active span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .hamburger.active span:nth-child(2) { opacity: 0; transform: scaleX(0); }
    .hamburger.active span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

    @media (max-width: 768px) {
      .hamburger { display: flex; }
      .nav-links {
        display: none;
        position: absolute;
        top: 100%; left: 0; right: 0;
        background: rgba(11,25,41,0.98);
        flex-direction: column;
        padding: 16px 0;
        border-top: 1px solid rgba(201,168,76,0.2);
        align-items: flex-start;
      }
      .nav-links.open { display: flex; }
      .nav-links a { padding: 12px 24px; font-size: 0.75rem; }
      .nav-auth { margin-left: 24px; margin-top: 8px; padding-bottom: 8px; }
      .user-dropdown { right: auto; left: 0; }
    }
  `]
})
export class NavbarComponent implements OnInit, OnDestroy {
  isScrolled = false;
  menuOpen = false;
  userMenuOpen = false;
  activeSection = 'home';
  currentUser: User | null = null;
  private sub!: Subscription;

  links = [
    { label: 'Home', id: 'home' },
    { label: 'About', id: 'about' },
    { label: 'Practice Areas', id: 'practice-areas' },
    { label: 'FAQs', id: 'faqs' },
    { label: 'Blog', id: 'blog' },
    { label: 'Contact', id: 'contact' }
  ];

  constructor(private authService: AuthService, private router: Router) {}

  @HostListener('window:scroll')
  onScroll() {
    this.isScrolled = window.scrollY > 60;
    this.updateActiveSection();
  }

  @HostListener('document:click', ['$event'])
  onDocClick(e: Event) {
    const target = e.target as HTMLElement;
    if (!target.closest('.user-menu')) {
      this.userMenuOpen = false;
    }
  }

  ngOnInit() {
    this.onScroll();
    this.sub = this.authService.currentUser$.subscribe(u => (this.currentUser = u));
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  updateActiveSection() {
    const sections = this.links.map(l => l.id);
    for (const id of [...sections].reverse()) {
      const el = document.getElementById(id);
      if (el && window.scrollY >= el.offsetTop - 100) {
        this.activeSection = id;
        break;
      }
    }
  }

  scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }

  toggleMenu() { this.menuOpen = !this.menuOpen; }
  closeMenu() { this.menuOpen = false; }
  toggleUserMenu() { this.userMenuOpen = !this.userMenuOpen; }

  logout() {
    this.authService.logout();
    this.userMenuOpen = false;
    this.router.navigate(['/']);
  }
}
