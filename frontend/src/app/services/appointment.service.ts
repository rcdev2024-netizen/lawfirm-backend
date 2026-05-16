import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../environments/environment';

export interface AppointmentPayload {
  full_name: string;
  email: string;
  phone?: string;
  practice_area?: string;
  message: string;
  preferred_date?: string;
  preferred_time?: string;
}

export interface Appointment {
  id: number;
  full_name: string;
  email: string;
  phone?: string;
  practice_area?: string;
  message: string;
  preferred_date?: string;
  preferred_time?: string;
  status: string;
  user_id?: number;
  created_at: string;
}

@Injectable({ providedIn: 'root' })
export class AppointmentService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient, private authService: AuthService) {}

  private getHeaders(): HttpHeaders {
    const token = this.authService.token;
    return token
      ? new HttpHeaders({ Authorization: `Bearer ${token}` })
      : new HttpHeaders();
  }

  bookAppointment(data: AppointmentPayload): Observable<Appointment> {
    return this.http.post<Appointment>(
      `${this.apiUrl}/api/appointments`,
      data,
      { headers: this.getHeaders() }
    );
  }

  getMyAppointments(): Observable<Appointment[]> {
    return this.http.get<Appointment[]>(
      `${this.apiUrl}/api/appointments/my`,
      { headers: this.getHeaders() }
    );
  }

  getAllAppointments(): Observable<Appointment[]> {
    return this.http.get<Appointment[]>(
      `${this.apiUrl}/api/appointments`,
      { headers: this.getHeaders() }
    );
  }
}
