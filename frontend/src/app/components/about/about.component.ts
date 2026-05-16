import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section id="about" class="about">
      <div class="about-container">
        <div class="about-left fade-left">
          <div class="about-image-frame">
            <div class="about-img-placeholder">
              <svg viewBox="0 0 200 260" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect width="200" height="260" fill="#122035"/>
                <circle cx="100" cy="95" r="45" fill="none" stroke="#c9a84c" stroke-width="1"/>
                <path d="M55 190 Q100 160 145 190 L145 260 L55 260 Z" fill="none" stroke="#c9a84c" stroke-width="1"/>
                <circle cx="100" cy="95" r="35" fill="#1a2f4a"/>
                <text x="100" y="103" text-anchor="middle" fill="#c9a84c" font-family="Playfair Display" font-size="28" font-style="italic">RC</text>
              </svg>
            </div>
            <div class="about-badge">
              <svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="24" cy="24" r="22"/>
                <line x1="24" y1="8" x2="24" y2="40"/>
                <line x1="14" y1="18" x2="34" y2="18"/>
                <line x1="10" y1="36" x2="18" y2="28"/>
                <line x1="38" y1="36" x2="30" y2="28"/>
                <line x1="10" y1="36" x2="38" y2="36"/>
              </svg>
            </div>
          </div>
          <div class="about-quote">
            <span class="quote-mark">"</span>
            <p>Justice is not just a concept — it's a commitment to every client I serve.</p>
            <cite>— Atty Rochelle Cortez-Naz</cite>
          </div>
        </div>

        <div class="about-right">
          <p class="section-eyebrow fade-up">About the Firm</p>
          <h2 class="section-title fade-up">Committed to<br><em>Your Legal Success</em></h2>
          <div class="gold-divider fade-up">
            <span></span>
            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2l2.4 7.4H22l-6.2 4.5 2.4 7.4L12 17l-6.2 4.3 2.4-7.4L2 9.4h7.6z"/></svg>
            <span></span>
          </div>
          <p class="about-body fade-up">
            The Law Office of Atty Rochelle Cortez-Naz is committed to providing competent, efficient, and compassionate legal services. We protect your rights and help you navigate life's legal challenges with confidence.
          </p>
          <p class="about-body fade-up">
            Based in Legazpi City, Philippines, our practice is built on the belief that every client deserves personalized attention, honest counsel, and a dedicated advocate who truly cares about their outcome.
          </p>
          <div class="about-values fade-up">
            <div class="value" *ngFor="let v of values">
              <div class="value-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
              </div>
              <div>
                <strong>{{ v.title }}</strong>
                <p>{{ v.desc }}</p>
              </div>
            </div>
          </div>
          <a class="btn-outline fade-up" (click)="scrollTo('contact')">
            Learn More
          </a>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .about {
      background: var(--cream);
      padding: 100px 0;
      position: relative;
      overflow: hidden;
    }
    .about::before {
      content: '';
      position: absolute;
      top: -80px; right: -80px;
      width: 300px; height: 300px;
      border: 1px solid rgba(201,168,76,0.1);
      border-radius: 50%;
    }
    .about::after {
      content: '';
      position: absolute;
      bottom: -40px; left: -40px;
      width: 200px; height: 200px;
      border: 1px solid rgba(201,168,76,0.08);
      border-radius: 50%;
    }
    .about-container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 0 24px;
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 80px;
      align-items: center;
      position: relative;
      z-index: 1;
    }
    .about-left { display: flex; flex-direction: column; gap: 24px; }
    .about-image-frame {
      position: relative;
      aspect-ratio: 3/4;
      max-height: 380px;
    }
    .about-img-placeholder {
      width: 100%;
      height: 100%;
      border: 1px solid rgba(201,168,76,0.3);
      overflow: hidden;
    }
    .about-img-placeholder svg { width: 100%; height: 100%; }
    .about-image-frame::before {
      content: '';
      position: absolute;
      top: 16px; left: -16px;
      width: 100%; height: 100%;
      border: 1px solid rgba(201,168,76,0.2);
      z-index: -1;
    }
    .about-badge {
      position: absolute;
      top: -20px; right: -20px;
      width: 64px; height: 64px;
      background: var(--navy);
      border: 2px solid var(--gold);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--gold);
      padding: 14px;
      animation: rotateSlow 20s linear infinite;
    }
    @keyframes rotateSlow {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
    .about-quote {
      background: var(--navy);
      padding: 24px;
      border-left: 3px solid var(--gold);
      position: relative;
    }
    .quote-mark {
      font-family: 'Playfair Display', serif;
      font-size: 4rem;
      color: var(--gold);
      opacity: 0.3;
      position: absolute;
      top: -10px;
      left: 16px;
      line-height: 1;
    }
    .about-quote p {
      font-family: 'Cormorant Garamond', serif;
      font-style: italic;
      font-size: 1rem;
      color: var(--text-light);
      line-height: 1.7;
      padding-top: 12px;
    }
    .about-quote cite {
      display: block;
      margin-top: 12px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      letter-spacing: 0.1em;
      color: var(--gold);
    }
    .about-right { display: flex; flex-direction: column; gap: 18px; }
    .about-right .section-title {
      color: var(--navy);
      font-size: clamp(1.8rem, 3vw, 2.5rem);
    }
    .about-right .section-title em {
      color: var(--gold);
      font-style: italic;
    }
    .about-right .section-eyebrow { color: var(--gold); }
    .about-right .gold-divider span {
      background: linear-gradient(90deg, transparent, var(--gold)) !important;
    }
    .about-right .gold-divider span:last-child {
      background: linear-gradient(90deg, var(--gold), transparent) !important;
    }
    .about-body {
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.05rem;
      color: #4a5568;
      line-height: 1.85;
    }
    .about-values { display: flex; flex-direction: column; gap: 14px; margin: 8px 0; }
    .value {
      display: flex;
      align-items: flex-start;
      gap: 14px;
    }
    .value-icon {
      width: 28px; height: 28px;
      background: var(--gold);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
    }
    .value-icon svg { width: 14px; height: 14px; color: var(--navy); stroke: var(--navy); }
    .value strong {
      font-family: 'Playfair Display', serif;
      font-size: 1rem;
      color: var(--navy);
      display: block;
      margin-bottom: 2px;
    }
    .value p {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.8rem;
      color: #718096;
    }
    .about-right .btn-outline {
      align-self: flex-start;
      color: var(--navy);
      border-color: var(--navy);
      cursor: pointer;
    }
    .about-right .btn-outline:hover {
      background: var(--navy);
      color: var(--white);
    }

    @media (max-width: 900px) {
      .about-container { grid-template-columns: 1fr; gap: 40px; }
      .about-left { display: none; }
    }
  `]
})
export class AboutComponent {
  values = [
    { title: 'Competence', desc: 'Deep expertise in Philippine law with years of practical courtroom experience.' },
    { title: 'Integrity', desc: 'Transparent communication and honest guidance throughout every case.' },
    { title: 'Compassion', desc: 'We treat every client as a person, not a case number.' }
  ];

  scrollTo(id: string) {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  }
}
