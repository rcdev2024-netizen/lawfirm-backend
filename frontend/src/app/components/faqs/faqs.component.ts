import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { trigger, state, style, transition, animate } from '@angular/animations';

@Component({
  selector: 'app-faqs',
  standalone: true,
  imports: [CommonModule],
  animations: [
    trigger('expand', [
      state('closed', style({ height: '0', opacity: 0, overflow: 'hidden', paddingTop: 0, paddingBottom: 0 })),
      state('open', style({ height: '*', opacity: 1, overflow: 'hidden', paddingTop: '16px', paddingBottom: '16px' })),
      transition('closed <=> open', animate('0.35s cubic-bezier(0.25,0.46,0.45,0.94)'))
    ])
  ],
  template: `
    <section id="faqs" class="faqs">
      <div class="container">
        <div class="faqs-inner">
          <div class="faqs-left fade-left">
            <p class="section-eyebrow">Have Questions?</p>
            <h2 class="section-title">Frequently<br><em>Asked Questions</em></h2>
            <div class="gold-divider" style="justify-content: flex-start; margin: 16px 0;">
              <span></span>
              <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2L9.5 9H2l5.9 4.3-2.3 7L12 17l6.4 3.3-2.3-7L22 9h-7.5z"/>
              </svg>
              <span></span>
            </div>
            <p class="faqs-desc">
              Have a legal concern? Browse our most commonly asked questions or reach out directly for a consultation.
            </p>
            <a class="btn-primary" (click)="scrollToContact()" style="margin-top: 24px; cursor:pointer;">
              <span>Ask a Question</span>
            </a>
            <div class="faqs-seal">
              <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="60" cy="60" r="58" stroke="rgba(201,168,76,0.2)" stroke-width="1"/>
                <circle cx="60" cy="60" r="50" stroke="rgba(201,168,76,0.15)" stroke-width="1"/>
                <text x="60" y="48" text-anchor="middle" fill="rgba(201,168,76,0.5)" font-family="Playfair Display" font-size="9" letter-spacing="2">LEGAL</text>
                <text x="60" y="66" text-anchor="middle" fill="rgba(201,168,76,0.8)" font-family="Playfair Display" font-size="13" font-style="italic">Excellence</text>
                <text x="60" y="82" text-anchor="middle" fill="rgba(201,168,76,0.5)" font-family="Playfair Display" font-size="9" letter-spacing="2">SERVICE</text>
                <path d="M60 26 L62 32 L68 32 L63.5 35.5 L65.5 42 L60 38 L54.5 42 L56.5 35.5 L52 32 L58 32 Z" fill="rgba(201,168,76,0.3)"/>
              </svg>
            </div>
          </div>

          <div class="faqs-right">
            <div class="faq-item fade-up"
                 *ngFor="let faq of faqs; let i = index"
                 [style.transition-delay]="i * 60 + 'ms'"
                 [class.active]="faq.open">
              <button class="faq-q" (click)="toggle(faq)">
                <span>{{ faq.q }}</span>
                <div class="faq-icon" [class.rotated]="faq.open">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="6 9 12 15 18 9"></polyline>
                  </svg>
                </div>
              </button>
              <div class="faq-a" [@expand]="faq.open ? 'open' : 'closed'">
                <p>{{ faq.a }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .faqs {
      background: linear-gradient(180deg, var(--navy-mid) 0%, var(--navy) 100%);
      padding: 100px 0;
      position: relative;
      overflow: hidden;
    }
    .faqs::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .faqs::after {
      content: '';
      position: absolute;
      bottom: 0; left: 0; right: 0;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .faqs-inner {
      display: grid;
      grid-template-columns: 1fr 1.4fr;
      gap: 80px;
      align-items: start;
    }
    .faqs-left {
      position: sticky;
      top: 100px;
    }
    .faqs-left .section-title {
      font-size: clamp(1.8rem, 3vw, 2.4rem);
    }
    .faqs-left .section-title em {
      color: var(--gold);
      font-style: italic;
    }
    .faqs-desc {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1rem;
      color: var(--text-muted);
      line-height: 1.8;
    }
    .faqs-seal {
      margin-top: 40px;
      width: 100px; height: 100px;
      opacity: 0.6;
    }
    .faqs-right { display: flex; flex-direction: column; gap: 8px; }
    .faq-item {
      border: 1px solid rgba(201,168,76,0.1);
      transition: border-color 0.3s ease;
    }
    .faq-item.active { border-color: rgba(201,168,76,0.4); }
    .faq-q {
      width: 100%;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 20px 24px;
      background: none;
      border: none;
      cursor: pointer;
      text-align: left;
      transition: background 0.3s ease;
    }
    .faq-q:hover { background: rgba(201,168,76,0.04); }
    .faq-item.active .faq-q { background: rgba(201,168,76,0.06); }
    .faq-q span {
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      color: var(--white);
      line-height: 1.4;
    }
    .faq-icon {
      width: 24px; height: 24px;
      flex-shrink: 0;
      color: var(--gold);
      transition: transform 0.3s ease;
    }
    .faq-icon.rotated { transform: rotate(180deg); }
    .faq-a { padding: 0 24px; }
    .faq-a p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.85rem;
      color: var(--text-muted);
      line-height: 1.8;
    }

    @media (max-width: 900px) {
      .faqs-inner { grid-template-columns: 1fr; gap: 40px; }
      .faqs-left { position: static; }
    }
  `]
})
export class FaqsComponent {
  faqs = [
    {
      q: 'How do I schedule a consultation?',
      a: 'You can contact us via email at attyrochellecortez.naz@gmail.com, call us at 0917 123 4567, or use the contact form on this website. We typically respond within 24 hours to schedule your initial consultation.',
      open: false
    },
    {
      q: 'What should I bring to my first consultation?',
      a: 'Please bring any relevant documents related to your legal matter — contracts, court papers, identification, correspondence, or any other documentation that may help us understand your situation. The more information you provide, the better we can advise you.',
      open: false
    },
    {
      q: 'How much do legal services cost?',
      a: 'Fees vary depending on the nature and complexity of your case. We offer a free initial consultation so we can assess your situation and provide a transparent fee structure before you commit to anything.',
      open: false
    },
    {
      q: 'Do you handle cases outside of Legazpi City?',
      a: 'Yes. While our office is based in Legazpi City, we handle legal matters across the Philippines including Metro Manila and other regions, depending on the nature of the case.',
      open: false
    },
    {
      q: 'How long does a legal case typically take?',
      a: 'The duration varies greatly depending on the type of case, court schedules, and the cooperation of all parties involved. We always aim to resolve matters as efficiently as possible and will give you a realistic timeline during your consultation.',
      open: false
    },
    {
      q: 'Is my information kept confidential?',
      a: 'Absolutely. Attorney-client privilege is a cornerstone of our practice. Everything you share with us is held in strict confidence and protected by professional ethical obligations.',
      open: false
    }
  ];

  toggle(faq: any) {
    this.faqs.forEach(f => { if (f !== faq) f.open = false; });
    faq.open = !faq.open;
  }

  scrollToContact() {
    const el = document.getElementById('contact');
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
}
