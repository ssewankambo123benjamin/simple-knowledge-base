# Knowledge Base Frontend

A modern React frontend for the Semantic Knowledge Base system, built with **Cloudscape Design System** for a polished, accessible UI.

## Features

- **Semantic Search Interface** - Natural language query input with real-time search
- **Rich Results Display** - Expandable result cards with relevance scoring
- **Backend Health Monitoring** - Real-time connection status indicator
- **Responsive Design** - Works on desktop and mobile devices
- **Dark Mode Ready** - Cloudscape visual mode support

## Tech Stack

| Technology | Purpose |
|------------|---------|
| [React 19](https://react.dev/) | UI framework |
| [TypeScript](https://www.typescriptlang.org/) | Type safety |
| [Vite](https://vite.dev/) | Build tool & dev server |
| [Cloudscape Design](https://cloudscape.design/) | AWS design system components |
| [pnpm](https://pnpm.io/) | Package manager |

## Quick Start

### Prerequisites

- Node.js 18+
- pnpm (`npm install -g pnpm`)
- Backend server running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The app will be available at `http://localhost:5173`

### Start with Backend

```bash
# Terminal 1: Start backend
../scripts/start-backend.sh

# Terminal 2: Start frontend
pnpm dev
```

## Project Structure

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts      # API client for backend
│   │   ├── types.ts       # TypeScript interfaces
│   │   └── index.ts       # Exports
│   ├── components/
│   │   ├── AddKnowledge.tsx     # Document upload form
│   │   ├── IndexSelector.tsx    # Reusable index dropdown
│   │   ├── ManageIndexes.tsx    # Index creation/deletion
│   │   ├── SearchInterface.tsx  # Search input form
│   │   └── SearchResults.tsx    # Results display
│   ├── App.tsx            # Main application
│   └── main.tsx           # Entry point
├── public/                # Static assets
├── index.html             # HTML template
├── vite.config.ts         # Vite configuration
└── package.json           # Dependencies
```

## Components

### SearchInterface

Search input with:

- Controlled input component
- Enter key submission
- Loading state handling
- Cloudscape FormField with validation

### SearchResults

Results display with:

- Vertical list layout for scanability
- Color-coded relevance badges (green ≥80%, blue ≥60%)
- Progress bar for visual relevance
- Expandable content previews
- Metadata display (chunk offset, content length)

### ManageIndexes

Index management with:

- Tile selector to switch between Create/Delete modes
- Create new index with name validation
- "Add Knowledge" button after creation for quick navigation
- Delete index with confirmation modal
- Real-time record count display

### AddKnowledge

Document ingestion with:

- Index selector dropdown
- Single file upload (drag & drop)
- Batch directory processing
- Progress tracking with polling
- Supported formats: `.md`, `.txt`

### IndexSelector

Reusable index dropdown with:

- Auto-loading of available indexes
- Record count display per index
- Filtering/search capability
- Refresh trigger for external updates

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API URL |

### Vite Proxy

The dev server proxies `/api/*` requests to the backend:

```typescript
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, ''),
    },
  },
}
```

## Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Build for production |
| `pnpm preview` | Preview production build |
| `pnpm lint` | Run ESLint |

## Cloudscape Guidelines

This project follows [Cloudscape Design System](https://cloudscape.design/) patterns:

1. **Design tokens** - No hard-coded colors or spacing
2. **Controlled components** - All form inputs use React state
3. **Event pattern** - `({ detail }) => ...` destructuring
4. **Composition** - Complex UIs built from simple components

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
