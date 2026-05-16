import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, style, animate, transition, query, stagger, keyframes } from '@angular/animations';

@Component({
  selector: 'app-hero',
  standalone: true,
  imports: [CommonModule],
  animations: [
    trigger('heroEnter', [
      transition(':enter', [
        query('.hero-eyebrow', [
          style({ opacity: 0, transform: 'translateY(20px)' }),
          animate('0.6s 0.3s ease', style({ opacity: 1, transform: 'translateY(0)' }))
        ], { optional: true }),
        query('.hero-title-line', [
          style({ opacity: 0, transform: 'translateY(60px)' }),
          stagger(120, animate('0.8s ease', style({ opacity: 1, transform: 'translateY(0)' })))
        ], { optional: true }),
        query('.hero-divider', [
          style({ opacity: 0 }),
          animate('0.5s 1s ease', style({ opacity: 1 }))
        ], { optional: true }),
        query('.hero-sub', [
          style({ opacity: 0, transform: 'translateY(20px)' }),
          animate('0.6s 1.1s ease', style({ opacity: 1, transform: 'translateY(0)' }))
        ], { optional: true }),
        query('.hero-btn', [
          style({ opacity: 0, transform: 'translateY(20px)' }),
          animate('0.6s 1.3s ease', style({ opacity: 1, transform: 'translateY(0)' }))
        ], { optional: true })
      ])
    ]),
    trigger('imageReveal', [
      transition(':enter', [
        style({ opacity: 0, transform: 'scale(1.08)', clipPath: 'inset(0 100% 0 0)' }),
        animate('1.2s 0.5s cubic-bezier(0.25,0.46,0.45,0.94)',
          style({ opacity: 1, transform: 'scale(1)', clipPath: 'inset(0 0% 0 0)' }))
      ])
    ])
  ],
  template: `
    <section id="home" class="hero" [@heroEnter]>
      <div class="hero-particles">
        <div class="particle" *ngFor="let p of particles" [ngStyle]="p"></div>
      </div>

      <div class="hero-content">
        <div class="hero-left">
          <p class="hero-eyebrow section-eyebrow">Legazpi City, Philippines</p>
          <h1 class="hero-title">
            <span class="hero-title-line">Your Rights.</span>
            <span class="hero-title-line gold">My Commitment.</span>
          </h1>
          <div class="hero-divider">
            <div class="divider-line"></div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M12 2L12 5M12 19L12 22M4.22 4.22L6.34 6.34M17.66 17.66L19.78 19.78M2 12H5M19 12H22M4.22 19.78L6.34 17.66M17.66 6.34L19.78 4.22"/>
              <circle cx="12" cy="12" r="4"/>
            </svg>
            <div class="divider-line"></div>
          </div>
          <p class="hero-sub">
            Dedicated legal representation.&nbsp; Practical solutions.<br>Personalized service.
          </p>
          <a class="hero-btn btn-primary" (click)="scrollToContact()">
            <span>Schedule a Consultation</span>
          </a>
          <div class="hero-stats">
            <div class="stat" *ngFor="let s of stats">
              <span class="stat-number">{{ s.number }}</span>
              <span class="stat-label">{{ s.label }}</span>
            </div>
          </div>
        </div>

        <div class="hero-right" [@imageReveal]>
          <div class="hero-image-wrap">
            <img src="assets/atty-rochelle.png" alt="Atty Rochelle Cortez-Naz" class="hero-photo">
            <div class="hero-img-overlay"></div>
            <div class="hero-nameplate">
              <div class="nameplate-inner">
                <p class="nameplate-name">Atty Rochelle Cortez-Naz</p>
                <div class="nameplate-rule"></div>
                <p class="nameplate-title">LAWYER</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="scroll-indicator">
        <div class="scroll-line"></div>
        <span>SCROLL</span>
      </div>
    </section>
  `,
  styles: [`
    .hero {
      min-height: 100vh;
      background: linear-gradient(135deg, var(--navy) 0%, #0e2040 50%, var(--navy) 100%);
      display: flex;
      align-items: center;
      position: relative;
      overflow: hidden;
      padding-top: 80px;
    }
    .hero::before {
      content: '';
      position: absolute;
      inset: 0;
      background:
        radial-gradient(ellipse 60% 60% at 70% 50%, rgba(201,168,76,0.06) 0%, transparent 70%),
        radial-gradient(ellipse 40% 80% at 0% 50%, rgba(201,168,76,0.04) 0%, transparent 60%);
    }
    .hero-particles {
      position: absolute;
      inset: 0;
      pointer-events: none;
    }
    .particle {
      position: absolute;
      border-radius: 50%;
      background: var(--gold);
      animation: float linear infinite;
    }
    @keyframes float {
      0% { transform: translateY(100vh) rotate(0deg); opacity: 0; }
      10% { opacity: 1; }
      90% { opacity: 1; }
      100% { transform: translateY(-100px) rotate(720deg); opacity: 0; }
    }
    .hero-content {
      max-width: 1200px;
      margin: 0 auto;
      padding: 80px 24px 60px;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 60px;
      align-items: center;
      width: 100%;
      position: relative;
      z-index: 1;
    }
    .hero-left { display: flex; flex-direction: column; gap: 20px; }
    .hero-eyebrow {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.7rem;
      font-weight: 600;
      letter-spacing: 0.25em;
      text-transform: uppercase;
      color: var(--gold);
    }
    .hero-title {
      display: flex;
      flex-direction: column;
      font-family: 'Playfair Display', serif;
      font-size: clamp(2.8rem, 5vw, 4.2rem);
      font-weight: 700;
      color: var(--white);
      line-height: 1.1;
    }
    .hero-title-line { display: block; }
    .hero-title .gold {
      color: var(--gold);
      font-style: italic;
    }
    .hero-divider {
      display: flex;
      align-items: center;
      gap: 16px;
      color: var(--gold);
    }
    .hero-divider svg { width: 22px; height: 22px; }
    .divider-line {
      height: 1px;
      width: 48px;
      background: linear-gradient(90deg, var(--gold), transparent);
    }
    .divider-line:last-child {
      background: linear-gradient(90deg, transparent, var(--gold));
    }
    .hero-sub {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.15rem;
      color: var(--text-muted);
      line-height: 1.8;
    }
    .hero-btn {
      align-self: flex-start;
      margin-top: 8px;
    }
    .hero-stats {
      display: flex;
      gap: 32px;
      margin-top: 16px;
      padding-top: 24px;
      border-top: 1px solid rgba(201,168,76,0.15);
    }
    .stat { display: flex; flex-direction: column; }
    .stat-number {
      font-family: 'Playfair Display', serif;
      font-size: 1.8rem;
      font-weight: 700;
      color: var(--gold);
    }
    .stat-label {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--text-muted);
      margin-top: 2px;
    }
    .hero-right { position: relative; }
      .hero-image-wrap {
      position: relative;
      height: 580px;
      border: 1px solid rgba(201,168,76,0.25);
      overflow: hidden;
    }
    .hero-photo {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: cover;
      object-position: center 45%;  
      display: block;
    }
    .hero-img-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(
        to bottom,
        rgba(11,25,41,0.1) 0%,
        rgba(11,25,41,0.05) 50%,
        rgba(11,25,41,0.55) 100%
      );
      z-index: 1;
    }
    .hero-image-wrap::before {
      content: '';
      position: absolute;
      top: -12px; right: -12px;
      width: 100%; height: 100%;
      border: 1px solid rgba(201,168,76,0.15);
      z-index: -1;
    }
    .hero-nameplate {
      position: absolute;
      bottom: 40px;
      right: -24px;
      z-index: 2;
      background: linear-gradient(135deg, var(--navy) 0%, var(--navy-mid) 100%);
      border: 1px solid rgba(201,168,76,0.4);
      padding: 20px 28px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
      z-index: 10;
      animation: floatPlate 4s ease-in-out infinite;
    }
    @keyframes floatPlate {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    .nameplate-inner { text-align: center; }
    .nameplate-name {
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      color: var(--gold);
      font-style: italic;
      white-space: nowrap;
    }
    .nameplate-rule {
      height: 1px;
      background: var(--gold);
      margin: 8px 0;
      opacity: 0.5;
    }
    .nameplate-title {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      letter-spacing: 0.3em;
      color: var(--text-muted);
    }
    .scales-float {
      position: absolute;
      top: 30px;
      left: -30px;
      width: 80px; height: 80px;
      color: var(--gold);
      opacity: 0.6;
      animation: floatScales 6s ease-in-out infinite;
    }
    @keyframes floatScales {
      0%, 100% { transform: translateY(0) rotate(0deg); }
      50% { transform: translateY(-12px) rotate(3deg); }
    }
    .scroll-indicator {
      position: absolute;
      bottom: 32px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      z-index: 2;
    }
    .scroll-line {
      width: 1px;
      height: 48px;
      background: linear-gradient(to bottom, transparent, var(--gold));
      animation: scrollPulse 2s ease-in-out infinite;
    }
    @keyframes scrollPulse {
      0%, 100% { opacity: 0.4; transform: scaleY(0.6); }
      50% { opacity: 1; transform: scaleY(1); }
    }
    .scroll-indicator span {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.55rem;
      letter-spacing: 0.3em;
      color: var(--text-muted);
    }

    @media (max-width: 900px) {
      .hero-content {
        grid-template-columns: 1fr;
        text-align: center;
        padding: 120px 24px 80px;
      }
      .hero-right { display: none; }
      .hero-stats { justify-content: center; }
      .hero-btn { align-self: center; }
      .hero-divider { justify-content: center; }
    }
  `]
})
export class HeroComponent implements OnInit {
  particles: any[] = [];
  stats = [
    { number: '10+', label: 'Years Experience' },
    { number: '500+', label: 'Cases Handled' },
    { number: '5', label: 'Practice Areas' }
  ];

  ngOnInit() {
    this.generateParticles();
  }

  generateParticles() {
    this.particles = Array.from({ length: 20 }, (_, i) => ({
      width: Math.random() * 3 + 1 + 'px',
      height: Math.random() * 3 + 1 + 'px',
      left: Math.random() * 100 + '%',
      animationDuration: Math.random() * 15 + 10 + 's',
      animationDelay: Math.random() * 10 + 's',
      opacity: Math.random() * 0.4 + 0.1
    }));
  }

  scrollToContact() {
    const el = document.getElementById('contact');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
}
