import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DashboardService, Document } from '../../services/dashboard.service';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="page">
      <div class="page-header">
        <div>
          <h2>Documents</h2>
          <p>View and manage all your case documents.</p>
        </div>
      </div>

      <div class="card" *ngIf="!loading && documents.length > 0">
        <div class="card-header">
          <h3>All Documents ({{ documents.length }})</h3>
        </div>
        <div class="doc-list">
          <div class="doc-item" *ngFor="let doc of documents">
            <div class="doc-icon" [ngClass]="getFileClass(doc.file_type)">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div class="doc-body">
              <div class="doc-title">{{ doc.title }}</div>
              <div class="doc-meta">
                <span *ngIf="doc.file_type">{{ doc.file_type.toUpperCase() }}</span>
                <span *ngIf="doc.file_size">{{ formatSize(doc.file_size) }}</span>
                <span>{{ formatDate(doc.created_at) }}</span>
              </div>
              <div class="doc-desc" *ngIf="doc.description">{{ doc.description }}</div>
            </div>
            <div class="doc-actions">
              <span class="confidential-badge" *ngIf="doc.is_confidential">Confidential</span>
              <a *ngIf="doc.file_url" [href]="doc.file_url" target="_blank" class="btn-download">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                Download
              </a>
            </div>
          </div>
        </div>
      </div>

      <div class="empty-state" *ngIf="!loading && documents.length === 0">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
        <h3>No documents yet</h3>
        <p>Documents shared by your attorney will appear here.</p>
      </div>

      <div class="loading-state" *ngIf="loading"><div class="spinner"></div></div>
    </div>
  `,
  styles: [`
    .page { font-family: 'Montserrat', sans-serif; }
    .page-header { margin-bottom: 24px; }
    .page-header h2 { font-family: 'Playfair Display', serif; font-size: 1.4rem; color: #1a202c; margin-bottom: 4px; }
    .page-header p { font-size: 0.82rem; color: #718096; }

    .card { background: #fff; border-radius: 12px; box-shadow: 0 1px 6px rgba(0,0,0,0.06); overflow: hidden; }
    .card-header { padding: 16px 20px; border-bottom: 1px solid #f0f2f5; }
    .card-header h3 { font-size: 0.9rem; font-weight: 700; color: #1a202c; }

    .doc-list { padding: 8px 0; }
    .doc-item { display: flex; align-items: center; gap: 14px; padding: 14px 20px; border-bottom: 1px solid #f8f9fb; transition: background 0.15s; }
    .doc-item:hover { background: #fafbfc; }
    .doc-item:last-child { border-bottom: none; }

    .doc-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .doc-icon svg { width: 18px; height: 18px; }
    .doc-icon.pdf { background: rgba(229,62,62,0.1); color: #e53e3e; }
    .doc-icon.doc, .doc-icon.docx { background: rgba(59,130,246,0.1); color: #3b82f6; }
    .doc-icon.default { background: rgba(107,114,128,0.1); color: #6b7280; }

    .doc-body { flex: 1; }
    .doc-title { font-size: 0.88rem; font-weight: 600; color: #1a202c; margin-bottom: 4px; }
    .doc-meta { display: flex; gap: 8px; font-size: 0.68rem; color: #9da8b8; margin-bottom: 4px; }
    .doc-meta span::after { content: '·'; margin-left: 8px; }
    .doc-meta span:last-child::after { content: ''; margin: 0; }
    .doc-desc { font-size: 0.72rem; color: #718096; }

    .doc-actions { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
    .confidential-badge { padding: 3px 8px; background: rgba(229,62,62,0.08); color: #e53e3e; border-radius: 4px; font-size: 0.62rem; font-weight: 600; }
    .btn-download {
      display: flex; align-items: center; gap: 5px;
      padding: 6px 12px;
      background: #f0f2f5;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      color: #4a5568;
      text-decoration: none;
      transition: all 0.2s;
    }
    .btn-download:hover { background: #0b1929; color: #c9a84c; }
    .btn-download svg { width: 14px; height: 14px; }

    .empty-state { text-align: center; padding: 64px 32px; color: #9da8b8; }
    .empty-state svg { width: 48px; height: 48px; color: #e2e8f0; margin: 0 auto 16px; }
    .empty-state h3 { font-size: 1rem; color: #4a5568; margin-bottom: 6px; }
    .empty-state p { font-size: 0.8rem; }

    .loading-state { display: flex; justify-content: center; padding: 64px; }
    .spinner { width: 28px; height: 28px; border: 3px solid #e2e8f0; border-top-color: #c9a84c; border-radius: 50%; animation: spin 0.8s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
  `]
})
export class DocumentsComponent implements OnInit {
  documents: Document[] = [];
  loading = true;

  constructor(private service: DashboardService) {}

  ngOnInit() {
    this.service.getDocuments().subscribe({
      next: d => { this.documents = d; this.loading = false; },
      error: () => { this.loading = false; }
    });
  }

  getFileClass(type?: string): string {
    if (!type) return 'default';
    const t = type.toLowerCase();
    if (t.includes('pdf')) return 'pdf';
    if (t.includes('doc')) return 'doc';
    return 'default';
  }

  formatSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }

  formatDate(d?: string): string {
    if (!d) return '';
    return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }
}
