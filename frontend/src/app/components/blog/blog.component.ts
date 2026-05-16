import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-blog',
  standalone: true,
  imports: [CommonModule],
  template: `
    <section id="blog" class="blog">
      <div class="blog-bg"></div>
      <div class="container">
        <div class="blog-header fade-up">
          <p class="section-eyebrow">Insights & Updates</p>
          <h2 class="section-title">Legal Blog</h2>
          <div class="gold-divider">
            <span></span>
            <svg viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2L9.5 9H2l5.9 4.3-2.3 7L12 17l6.4 3.3-2.3-7L22 9h-7.5z"/>
            </svg>
            <span></span>
          </div>
          <p class="blog-sub">Legal insights, updates, and guidance written for everyday Filipinos.</p>
        </div>

        <div class="blog-grid">
          <article class="blog-card featured fade-up" *ngIf="posts[0]">
            <div class="blog-card-img featured-img">
              <div class="img-overlay"></div>
              <div class="blog-category">{{ posts[0].category }}</div>
              <div class="featured-label">Featured</div>
            </div>
            <div class="blog-card-body">
              <p class="blog-date">{{ posts[0].date }}</p>
              <h3>{{ posts[0].title }}</h3>
              <p class="blog-excerpt">{{ posts[0].excerpt }}</p>
              <a class="blog-read-more">
                Read More
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M5 12h14M12 5l7 7-7 7"/>
                </svg>
              </a>
            </div>
          </article>

          <div class="blog-list">
            <article class="blog-card-small fade-up"
                     *ngFor="let post of posts.slice(1); let i = index"
                     [style.transition-delay]="i * 100 + 'ms'">
              <div class="blog-small-img">
                <div class="small-overlay"></div>
                <div class="blog-category small">{{ post.category }}</div>
              </div>
              <div class="blog-small-body">
                <p class="blog-date">{{ post.date }}</p>
                <h4>{{ post.title }}</h4>
                <p class="blog-excerpt small">{{ post.excerpt }}</p>
                <a class="blog-read-more small">
                  Read
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </a>
              </div>
            </article>
          </div>
        </div>
      </div>
    </section>
  `,
  styles: [`
    .blog {
      background: var(--cream);
      padding: 100px 0;
      position: relative;
      overflow: hidden;
    }
    .blog-bg {
      position: absolute;
      inset: 0;
      background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23c9a84c' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }
    .blog-header {
      text-align: center;
      margin-bottom: 60px;
    }
    .blog-header .section-title { color: var(--navy); }
    .blog-header .section-eyebrow { color: var(--gold); }
    .blog-sub {
      max-width: 480px;
      margin: 16px auto 0;
      font-family: 'Cormorant Garamond', serif;
      font-size: 1.05rem;
      color: #718096;
    }
    .blog-grid {
      display: grid;
      grid-template-columns: 1.2fr 1fr;
      gap: 28px;
    }
    .blog-card {
      background: var(--white);
      border: 1px solid rgba(201,168,76,0.2);
      overflow: hidden;
      transition: box-shadow 0.3s ease, transform 0.3s ease;
    }
    .blog-card:hover {
      box-shadow: 0 20px 60px rgba(0,0,0,0.12);
      transform: translateY(-4px);
    }
    .blog-card-img {
      position: relative;
      overflow: hidden;
    }
    .featured-img {
      height: 240px;
      background: linear-gradient(135deg, var(--navy) 0%, var(--navy-light) 60%, rgba(201,168,76,0.3) 100%);
    }
    .img-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(to top, rgba(11,25,41,0.8) 0%, transparent 60%);
    }
    .blog-category {
      position: absolute;
      top: 16px; left: 16px;
      background: var(--gold);
      color: var(--navy);
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 4px 12px;
    }
    .featured-label {
      position: absolute;
      bottom: 16px; left: 16px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.6rem;
      letter-spacing: 0.2em;
      text-transform: uppercase;
      color: rgba(255,255,255,0.6);
      border: 1px solid rgba(255,255,255,0.2);
      padding: 4px 10px;
    }
    .blog-card-body { padding: 28px; }
    .blog-date {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.65rem;
      letter-spacing: 0.08em;
      color: var(--gold);
      margin-bottom: 10px;
      text-transform: uppercase;
    }
    .blog-card-body h3 {
      font-family: 'Playfair Display', serif;
      font-size: 1.25rem;
      color: var(--navy);
      margin-bottom: 12px;
      line-height: 1.4;
    }
    .blog-excerpt {
      font-family: 'Montserrat', sans-serif;
      font-size: 0.82rem;
      color: #718096;
      line-height: 1.7;
      margin-bottom: 20px;
    }
    .blog-read-more {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      font-family: 'Montserrat', sans-serif;
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--gold);
      cursor: pointer;
      transition: gap 0.3s ease;
    }
    .blog-read-more:hover { gap: 12px; }
    .blog-read-more svg { width: 14px; height: 14px; }
    .blog-list { display: flex; flex-direction: column; gap: 16px; }
    .blog-card-small {
      display: grid;
      grid-template-columns: 100px 1fr;
      background: var(--white);
      border: 1px solid rgba(201,168,76,0.15);
      overflow: hidden;
      transition: box-shadow 0.3s ease, border-color 0.3s ease;
    }
    .blog-card-small:hover {
      box-shadow: 0 8px 30px rgba(0,0,0,0.08);
      border-color: rgba(201,168,76,0.4);
    }
    .blog-small-img {
      position: relative;
      background: linear-gradient(135deg, var(--navy-mid) 0%, var(--navy-light) 100%);
    }
    .small-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(135deg, rgba(201,168,76,0.1) 0%, transparent 100%);
    }
    .blog-category.small {
      position: absolute;
      top: 8px; left: 8px;
      font-size: 0.5rem;
      padding: 3px 8px;
      white-space: nowrap;
    }
    .blog-small-body { padding: 16px; }
    .blog-small-body h4 {
      font-family: 'Playfair Display', serif;
      font-size: 0.95rem;
      color: var(--navy);
      line-height: 1.4;
      margin-bottom: 6px;
    }
    .blog-excerpt.small {
      font-size: 0.75rem;
      margin-bottom: 12px;
    }
    .blog-read-more.small {
      font-size: 0.6rem;
    }

    @media (max-width: 900px) {
      .blog-grid { grid-template-columns: 1fr; }
      .blog-card-small { grid-template-columns: 80px 1fr; }
    }
  `]
})
export class BlogComponent {
  posts = [
    {
      title: 'Understanding Legal Separation vs. Annulment in the Philippines',
      excerpt: 'Many Filipinos confuse legal separation with annulment. This article breaks down the key differences, the legal process involved, and which option may be right for your situation.',
      category: 'Family Law',
      date: 'April 28, 2028'
    },
    {
      title: 'Your Rights When Dealing with Debt Collectors',
      excerpt: 'Know your rights under Philippine law when creditors come calling.',
      category: 'Civil Law',
      date: 'April 14, 2028'
    },
    {
      title: 'Why Every Filipino Should Have a Last Will and Testament',
      excerpt: 'Estate planning is not just for the wealthy. Learn why a will is essential.',
      category: 'Estate Planning',
      date: 'March 30, 2028'
    },
    {
      title: 'What to Do If You Are Arrested: A Step-by-Step Guide',
      excerpt: 'Understanding your rights during an arrest can make all the difference.',
      category: 'Criminal Defense',
      date: 'March 15, 2028'
    }
  ];
}
