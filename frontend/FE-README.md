# Atty Rochelle Law Office — Angular Frontend

## Requirements
- **Node.js 18+** → https://nodejs.org (LTS version recommended)
- Backend running on http://localhost:8000

## Run Locally

```bash
# Install dependencies
npm install

# Start dev server
npm start
```

App opens at → **http://localhost:4200**

## Pages
- `/` — Main site (Hero, About, Practice Areas, FAQs, Blog, Contact/Booking)
- `/login` — Login & Register page (JWT auth)

## Connecting to your API
The API URL is set in:
```
src/app/environments/environment.ts
```
Default is `http://localhost:8000` — change this if your backend runs elsewhere.

## Build for Production
```bash
npm run build:prod
```
Output goes to `dist/atty-law-office/browser/` — deploy this folder to Vercel.
