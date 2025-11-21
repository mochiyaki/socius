## Socius workspace

Socius is split into two apps that work together:

| Directory | Purpose |
| --- | --- |
| `nextjs-socios-/` | Next.js frontend that renders published Sanity content |
| `studio-socios-/` | Sanity Studio used to author/manage the same content |

Run both locally to edit content in the Studio and immediately see it on the frontend.

---

## Requirements

- Node.js 18+ (npm 9+)
- Sanity CLI (`npm install -g sanity`) for Studio actions
- Sanity project access: `projectId = c0j8rp13`, `dataset = production`

Optional (but recommended):

- `SANITY_READ_TOKEN` for the Next.js app if you need private/draft access
- `SANITY_AUTH_TOKEN` for Studio deployment automation

---

## Setup

Clone this repo, then install dependencies per app:

```bash
cd nextjs-socios-
npm install

cd ../studio-socios-
npm install
```

> Keep each command scoped to its folder so the correct `package.json` is used.

---

## Running locally

### Next.js frontend (`nextjs-socios-/`)

```bash
cd nextjs-socios-
npm run dev
```

- Serves at <http://localhost:3000>.
- Uses `src/sanity/client.ts` which is configured for project `c0j8rp13`, dataset `production`.
- To read protected content, expose a token via env (e.g. `SANITY_READ_TOKEN`) and update the client config accordingly.
- Additional scripts: `npm run build`, `npm run start`, `npm run lint`.

### Sanity Studio (`studio-socios-/`)

```bash
cd studio-socios-
npm run dev
```

- Runs `sanity dev` at <http://localhost:3333> using Vite.
- Requires you to be logged in via `sanity login` with access to the project/dataset above.
- Scripts: `npm run start` (alias), `npm run build`, `npm run deploy`.

---

## Deploying

### Sanity Studio

The Studio is hosted by Sanity at <https://socius-studio.sanity.studio/>.

1. Ensure `studio-socios-/sanity.cli.ts` contains:
   ```ts
   deployment: {
     host: 'socius-studio',
     autoUpdates: true,
     appId: 'av4afacc31hqngek1m6bn1xz', // add once assigned in Manage UI
   }
   ```
2. Deploy:
   ```bash
   cd studio-socios-
   npm run deploy
   ```
   You’ll be prompted for login if not already authenticated.

### Next.js app

Deploy however you prefer (e.g. Vercel). Ensure the environment contains:

- `SANITY_PROJECT_ID=c0j8rp13`
- `SANITY_DATASET=production`
- `SANITY_READ_TOKEN=<optional token>`

Build/start commands:

```bash
cd nextjs-socios-
npm run build
npm run start
```

---

## Useful references

- Sanity docs: https://www.sanity.io/docs
- Sanity project: https://www.sanity.io/manage/project/c0j8rp13
- Studio deployment dashboard: https://www.sanity.io/manage/project/c0j8rp13/studios
- Next.js docs: https://nextjs.org/docs
