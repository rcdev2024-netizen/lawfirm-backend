import { Routes } from '@angular/router';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./app.component').then(m => m.AppComponent)
  },
  {
    path: 'login',
    loadComponent: () => import('./components/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./components/dashboard/dashboard-layout.component').then(m => m.DashboardLayoutComponent),
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () => import('./components/dashboard/dashboard-home.component').then(m => m.DashboardHomeComponent)
      },
      {
        path: 'cases',
        loadComponent: () => import('./components/dashboard/my-cases.component').then(m => m.MyCasesComponent)
      },
      {
        path: 'appointments',
        loadComponent: () => import('./components/dashboard/dashboard-appointments.component').then(m => m.DashboardAppointmentsComponent)
      },
      {
        path: 'documents',
        loadComponent: () => import('./components/dashboard/documents.component').then(m => m.DocumentsComponent)
      },
      {
        path: 'messages',
        loadComponent: () => import('./components/dashboard/messages.component').then(m => m.MessagesComponent)
      },
      {
        path: 'billing',
        loadComponent: () => import('./components/dashboard/billing.component').then(m => m.BillingComponent)
      },
      {
        path: 'notifications',
        loadComponent: () => import('./components/dashboard/notifications-page.component').then(m => m.NotificationsPageComponent)
      },
      {
        path: 'profile',
        loadComponent: () => import('./components/dashboard/profile.component').then(m => m.ProfileComponent)
      }
    ]
  },
  {
    path: '**',
    redirectTo: ''
  }
];
