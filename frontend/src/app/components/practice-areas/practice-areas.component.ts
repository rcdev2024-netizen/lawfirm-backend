import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, transition, animate } from '@angular/animations';

@Component({
  selector: 'app-practice-areas',
  standalone: true,
  imports: [CommonModule],
  animations: [
    trigger('cardHover', [
      state('default', style({ transform: 'translateY(0)' })),
      state('hovered', style({ transform: 'translateY(-8px)' })),
      transition('default <=> hovered', animate('0.3s cubic-bezier(0.25,0.46,0.45,0.94)'))
    ])
  ],
  template: `
    <section id="practice-areas" class="practice">
      <div class="practice-bg-pattern"></div>
      <div class="container">
        <div class="practice-header fade-up">
          <p class="section-eyebrow">What We Do</p>
          <h2 class="section-title">Practice Areas</h2>
          <div class="gold-divider">
            <span></span>
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L9.5 9H2l5.9 4.3-2.3 7L12 17l6.4 3.3-2.3-7L22 9h-7.5z"/>
            </svg>
            <span></span>
          </div>
          <p class="practice-sub">
            Comprehensive legal services tailored to your unique needs, delivered with expertise and care.
          </p>
        </div>

        <div class="practice-grid">
          <div class="practice-card fade-up"
               *ngFor="let area of areas; let i = index"
               [style.transition-delay]="i * 80 + 'ms'"
               [@cardHover]="area.hovered ? 'hovered' : 'default'"
               (mouseenter)="area.hovered = true"
               (mouseleave)="area.hovered = false">
            <div class="card-accent"></div>
            <div class="card-icon" [innerHTML]="area.icon"></div>
            <h3>{{ area.title }}</h3>
            <p>{{ area.desc }}</p>
            <div class="card-footer">
              <a class="card-link" (click)="scrollToContact()">
                <span>Consult Now</span>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .practice {
      background: var(--navy);
      padding: 100px 0;
      position: relative;
      overflow: hidden;
    }
    .practice-bg-pattern {
      position: absolute;
      inset: 0;
      background-image:
        radial-gradient(circle at 20% 20%, rgba(201,168,76,0.04) 0%, transparent 50%),
        radial-gradient(circle at 80% 80%, rgba(201,168,76,0.04) 0%, transparent 50%);
    }
    .practice-header {
      text-align: center;
      margin-bottom: 60px;
    }
    .practice-sub {
      max-width: 520px;
      margin: 16px auto 0;
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.05rem;
      color: var(--text-muted);
      line-height: 1.8;
    }
    .practice-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 24px;
    }
    .practice-card {
      background: linear-gradient(135deg, var(--navy-mid) 0%, var(--navy-light) 100%);
      border: 1px solid rgba(201,168,76,0.15);
      padding: 36px 24px 28px;
      position: relative;
      overflow: hidden;
      cursor: pointer;
      transition: border-color 0.3s ease, box-shadow 0.3s ease;
    }
    .practice-card:hover {
      border-color: rgba(201,168,76,0.5);
      box-shadow: 0 20px 60px rgba(0,0,0,0.4), 0 0 0 1px rgba(201,168,76,0.1);
    }
    .card-accent {
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 2px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
      transform: scaleX(0);
      transition: transform 0.4s ease;
    }
    .practice-card:hover .card-accent { transform: scaleX(1); }
    .card-icon {
      width: 52px; height: 52px;
      margin-bottom: 20px;
      color: var(--gold);
    }
    .card-icon svg { width: 100%; height: 100%; }
    h3 {
      font-family: 'Playfair Display', serif;
      font-size: 1.1rem;
      color: var(--white);
      margin-bottom: 12px;
    }
    p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.8rem;
      color: var(--text-muted);
      line-height: 1.7;
    }
    .card-footer { margin-top: 24px; }
    .card-link {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--gold);
      cursor: pointer;
      transition: gap 0.3s ease;
    }
    .card-link:hover { gap: 12px; }
    .card-link svg { width: 14px; height: 14px; }
  `]
})
export class PracticeAreasComponent {
  areas = [
    {
      title: 'Family Law',
      desc: 'Divorce, legal separation, child custody, support, adoption and more.',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>`,
      hovered: false
    },
    {
      title: 'Civil Law',
      desc: 'Contracts, damages, property disputes and other civil matters.',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
        <polyline points="9 22 9 12 15 12 15 22"/>
      </svg>`,
      hovered: false
    },
    {
      title: 'Estate Planning',
      desc: 'Wills, trusts, probate, succession and estate settlement.',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <rect x="2" y="3" width="20" height="14" rx="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>`,
      hovered: false
    },
    {
      title: 'Criminal Defense',
      desc: 'Protecting your rights and providing a strong defense.',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>`,
      hovered: false
    },
    {
      title: 'Other Legal Services',
      desc: 'Notarial services, affidavits, demand letters and other legal assistance.',
      icon: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3">
        <line x1="8" y1="6" x2="21" y2="6"/>
        <line x1="8" y1="12" x2="21" y2="12"/>
        <line x1="8" y1="18" x2="21" y2="18"/>
        <line x1="3" y1="6" x2="3.01" y2="6"/>
        <line x1="3" y1="12" x2="3.01" y2="12"/>
        <line x1="3" y1="18" x2="3.01" y2="18"/>
      </svg>`,
      hovered: false
    }
  ];

  scrollToContact() {
    const el = document.getElementById('contact');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
}
