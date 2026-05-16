import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../environments/environment';

export interface DashboardStats {
  active_cases: number;
  upcoming_appointments: number;
  total_documents: number;
  unpaid_invoices: number;
  unread_messages: number;
  unread_notifications: number;
}

export interface Case {
  id: number;
  case_number: string;
  case_name: string;
  case_type?: string;
  description?: string;
  status: string;
  client_id?: number;
  attorney_id?: number;
  next_hearing_date?: string;
  next_hearing_time?: string;
  court?: string;
  judge?: string;
  filed_date?: string;
  closed_date?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Document {
  id: number;
  title: string;
  file_url?: string;
  file_type?: string;
  file_size?: number;
  case_id?: number;
  uploaded_by?: number;
  description?: string;
  is_confidential: boolean;
  created_at?: string;
}

export interface Message {
  id: number;
  sender_id?: number;
  recipient_id?: number;
  case_id?: number;
  subject?: string;
  body: string;
  is_read: boolean;
  parent_id?: number;
  created_at?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type?: string;
  title: string;
  body?: string;
  is_read: boolean;
  link?: string;
  created_at?: string;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  client_id?: number;
  case_id?: number;
  amount: number;
  tax: number;
  total: number;
  status: string;
  due_date?: string;
  paid_date?: string;
  notes?: string;
  created_at?: string;
}

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private api = environment.apiUrl;

  constructor(private http: HttpClient, private auth: AuthService) {}

  private headers(): HttpHeaders {
    const token = this.auth.token;
    return token ? new HttpHeaders({ Authorization: `Bearer ${token}` }) : new HttpHeaders();
  }

  getStats(): Observable<DashboardStats> {
    return this.http.get<DashboardStats>(`${this.api}/api/dashboard/stats`, { headers: this.headers() });
  }

  getCases(): Observable<Case[]> {
    return this.http.get<Case[]>(`${this.api}/api/cases/my`, { headers: this.headers() });
  }

  getDocuments(): Observable<Document[]> {
    return this.http.get<Document[]>(`${this.api}/api/documents/my`, { headers: this.headers() });
  }

  getInbox(): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.api}/api/messages/inbox`, { headers: this.headers() });
  }

  getSentMessages(): Observable<Message[]> {
    return this.http.get<Message[]>(`${this.api}/api/messages/sent`, { headers: this.headers() });
  }

  markMessageRead(id: number): Observable<Message> {
    return this.http.patch<Message>(`${this.api}/api/messages/${id}/read`, {}, { headers: this.headers() });
  }

  getNotifications(): Observable<Notification[]> {
    return this.http.get<Notification[]>(`${this.api}/api/notifications`, { headers: this.headers() });
  }

  markNotificationRead(id: number): Observable<Notification> {
    return this.http.patch<Notification>(`${this.api}/api/notifications/${id}/read`, {}, { headers: this.headers() });
  }

  markAllNotificationsRead(): Observable<any> {
    return this.http.patch(`${this.api}/api/notifications/read-all`, {}, { headers: this.headers() });
  }

  getInvoices(): Observable<Invoice[]> {
    return this.http.get<Invoice[]>(`${this.api}/api/invoices/my`, { headers: this.headers() });
  }

  getAppointments(): Observable<any[]> {
    return this.http.get<any[]>(`${this.api}/api/appointments/my`, { headers: this.headers() });
  }

  bookAppointment(data: any): Observable<any> {
    return this.http.post(`${this.api}/api/appointments`, data, { headers: this.headers() });
  }
}
