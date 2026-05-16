import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  template: `
    <footer class="footer">
      <div class="footer-top">
        <div class="footer-container">
          <div class="footer-brand">
            <div class="footer-logo">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="24" cy="24" r="22"/>
                <line x1="24" y1="8" x2="24" y2="40"/>
                <line x1="14" y1="18" x2="34" y2="18"/>
                <line x1="10" y1="36" x2="18" y2="28"/>
                <line x1="38" y1="36" x2="30" y2="28"/>
                <line x1="10" y1="36" x2="38" y2="36"/>
              </svg>
            </div>
            <div>
              <p class="brand-name">Atty Rochelle Cortez-Naz</p>
              <p class="brand-sub">LAW OFFICE</p>
              <p class="brand-tagline">Your Rights. My Commitment.</p>
            </div>
          </div>

          <div class="footer-links">
            <h4>Quick Links</h4>
            <ul>
              <li *ngFor="let link of links">
                <a (click)="scrollTo(link.id)">{{ link.label }}</a>
              </li>
            </ul>
          </div>

          <div class="footer-practice">
            <h4>Practice Areas</h4>
            <ul>
              <li *ngFor="let a of areas"><a>{{ a }}</a></li>
            </ul>
          </div>

          <div class="footer-contact">
            <h4>Contact</h4>
            <div class="footer-contact-items">
              <div class="footer-contact-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.61 3.18 2 2 0 0 1 3.59 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.09a16 16 0 0 0 6 6l.91-.91a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 21.73 16.92z"/>
                </svg>
                <a href="tel:09171234567">0917 123 4567</a>
              </div>
              <div class="footer-contact-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                  <polyline points="22,6 12,13 2,6"/>
                </svg>
                <a href="mailto:attyrochellecortez.naz@gmail.com">
                  attyrochellecortez.naz&#64;gmail.com
                </a>
              </div>
              <div class="footer-contact-item">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                  <circle cx="12" cy="10" r="3"/>
                </svg>
                <span>Legazpi City, Philippines</span>
              </div>
              <div class="footer-contact-item">
                <svg viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>
                </svg>
                <a href="#">Atty Rochelle Cortez-Naz Law Office</a>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="footer-bottom">
        <div class="footer-container footer-bottom-inner">
          <p class="footer-copy">
            &copy; 2028 Atty Rochelle Cortez-Naz Law Office. All Rights Reserved.
          </p>
          <div class="footer-gold-bar">
            <span class="footer-bar-line"></span>
            <svg viewBox="0 0 20 20" fill="currentColor" style="width:14px;height:14px;color:var(--gold)">
              <path d="M10 2L7.5 9H1l5.9 3.3-2.3 5.7L10 15l5.4 3 -2.3-5.7L19 9h-6.5z"/>
            </svg>
            <span class="footer-bar-line"></span>
          </div>
          <p class="footer-disclaimer">
            Created by ZetaCodeSolutions | Your Automation Partner.
          </p>
        </div>
      </div>
    </footer>
  `,
  styles: [`
    .footer {
      background: #060f1a;
    }
    .footer-top {
      padding: 70px 0 50px;
      border-top: 1px solid rgba(201,168,76,0.2);
    }
    .footer-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
    }
    .footer-top .footer-container {
      display: grid;
      grid-template-columns: 2fr 1fr 1fr 1.5fr;
      gap: 40px;
    }
    .footer-brand { display: flex; align-items: flex-start; gap: 14px; }
    .footer-logo {
      width: 44px; height: 44px;
      color: var(--gold);
      flex-shrink: 0;
      margin-top: 4px;
    }
    .brand-name {
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      color: var(--white);
      font-weight: 700;
      margin-bottom: 2px;
    }
    .brand-sub {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      letter-spacing: 0.2em;
      color: var(--gold);
    }
    .brand-tagline {
      font-family: 'Cormorant Garamond', serif;
      font-style: italic;
      font-size: 0.9rem;
      color: var(--text-muted);
      margin-top: 8px;
    }
    h4 {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: var(--gold);
      margin-bottom: 20px;
    }
    ul { list-style: none; display: flex; flex-direction: column; gap: 10px; }
    li a {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.8rem;
      color: var(--text-muted);
      cursor: pointer;
      transition: color 0.3s ease;
    }
    li a:hover { color: var(--gold); }
    .footer-contact-items { display: flex; flex-direction: column; gap: 14px; }
    .footer-contact-item {
      display: flex;
      align-items: flex-start;
      gap: 10px;
    }
    .footer-contact-item svg { width: 16px; height: 16px; color: var(--gold); flex-shrink: 0; margin-top: 2px; }
    .footer-contact-item a,
    .footer-contact-item span {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.78rem;
      color: var(--text-muted);
      transition: color 0.3s ease;
      word-break: break-all;
    }
    .footer-contact-item a:hover { color: var(--gold); }
    .footer-bottom {
      padding: 20px 0;
      border-top: 1px solid rgba(255,255,255,0.04);
    }
    .footer-bottom-inner {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .footer-copy {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.72rem;
      color: var(--gold);
    }
    .footer-gold-bar {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .footer-bar-line {
      display: inline-block;
      width: 40px; height: 1px;
      background: rgba(201,168,76,0.3);
    }
    .footer-disclaimer {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      color: rgba(157,168,184,0.5);
      max-width: 300px;
      text-align: right;
    }

    @media (max-width: 900px) {
      .footer-top .footer-container {
        grid-template-columns: 1fr 1fr;
        gap: 32px;
      }
      .footer-brand { grid-column: 1 / -1; }
      .footer-bottom-inner { flex-direction: column; text-align: center; }
      .footer-disclaimer { text-align: center; max-width: none; }
    }
    @media (max-width: 500px) {
      .footer-top .footer-container { grid-template-columns: 1fr; }
    }
  `]
})
export class FooterComponent {
  links = [
    { label: 'Home', id: 'home' },
    { label: 'About', id: 'about' },
    { label: 'Practice Areas', id: 'practice-areas' },
    { label: 'FAQs', id: 'faqs' },
    { label: 'Blog', id: 'blog' },
    { label: 'Contact', id: 'contact' }
  ];
  areas = ['Family Law', 'Civil Law', 'Estate Planning', 'Criminal Defense', 'Other Legal Services'];

  scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
}
