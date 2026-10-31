# Frontend

React + Vite + TypeScript, Tailwind v4 and TanStack Query.

```powershell
npm install
npm run dev      # http://127.0.0.1:5330
npm run build    # typecheck + production build into dist/
```

The dev server proxies `/api` to `http://127.0.0.1:8000`, so start Django
first. No CORS configuration is needed while the proxy is in use.

## Layout

```
src/api/        typed client, one function per endpoint
src/components/ layout, dialogs, small UI pieces
src/pages/      knowledge bases, knowledge base detail, settings
src/lib/        query hooks and formatting helpers
```

Every request goes through `src/api/client.ts`. Add new endpoints there rather
than calling `fetch` from a component.
