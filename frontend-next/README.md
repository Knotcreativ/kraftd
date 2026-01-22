# KRAFTD Frontend (Next.js)

Production-ready Next.js 15 frontend for KRAFTD intelligent document processing.

## Quick Start

```bash
npm install
npm run dev
```

Open http://localhost:3000

## Environment Variables

Create `.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=https://kraftd-api.calmrock-7db6369d.uaenorth.azurecontainerapps.io/api/v1
```

## Architecture

- **Framework:** Next.js 15 (App Router)
- **Language:** TypeScript
- **Styling:** TailwindCSS
- **State:** React Query + Zustand
- **Auth:** JWT in localStorage (upgrade to secure provider)

## Project Structure

```
app/                 # Next.js App Router pages
  layout.tsx         # Root layout
  page.tsx           # Dashboard
  login/page.tsx     # Authentication
  conversions/       # Conversion workspace
components/          # Reusable UI components
lib/                 # Utilities and API client
  api/               # API endpoints
  types.ts           # Shared types
hooks/               # Custom React hooks
styles/              # Global styles
```

## Core Features

- **Authentication:** JWT-based login
- **Document Conversions:** Upload, process, track
- **Schema Management:** Generate, revise, finalize
- **Summary Generation:** AI-powered document summaries
- **Output Generation:** Multiple export formats
- **Feedback System:** Rate and comment on results
- **Quota Management:** Track usage and limits
- **Responsive Design:** Mobile-first TailwindCSS

## API Integration

All API calls go through `lib/api/client.ts`:

```typescript
import { apiFetch } from '@/lib/api/client'

const data = await apiFetch('/conversions')
```

JWT token automatically included in requests.

## State Management

- **React Query:** Server state (API data)
- **Zustand:** Client state (UI, auth)
- **Component State:** Local component state

## Testing

```bash
npm run type-check  # TypeScript validation
```

## Deployment

### Vercel
```bash
vercel deploy
```

### Azure Static Web Apps
See deployment guide in parent directory.

## API Reference

See `/DEPLOYMENT_GUIDE.md` for backend API documentation.

Endpoints:
- `GET /health` - Health check
- `POST /conversions` - Create conversion
- `GET /conversions/:id` - Get conversion
- `POST /schema/generate` - Generate schema
- `POST /summary/generate` - Generate summary
- `POST /outputs/generate` - Generate output
- `POST /feedback` - Submit feedback
- `GET /quota` - Get quota status

## Support

See parent directory for deployment and operations guides.
