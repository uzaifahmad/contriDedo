# contriDedo

A modern, friendly app for tracking and splitting expenses on trips. The monorepo keeps the service, browser client, and Android app together while allowing each to use tooling suited to its platform.

## Repository layout

```text
contriDedo/
├── backend/   # API, persistence, authentication, and expense-splitting rules
├── web/       # Browser client for organizing trips and managing expenses
└── android/   # Android client for the same trip and expense workflows
```

## Architecture

The backend is the source of truth for users, trips, participants, expenses, shares, and settlement state. It validates changes, enforces access, persists data, and exposes the contract consumed by both clients. Balance and settlement calculations should follow one canonical set of backend rules so web and Android results stay consistent.

The web and Android apps are separate presentation clients. They handle platform-specific navigation and interaction, and use the backend API for shared trip data and mutations. Keep the API contract documented and versioned with the backend; update both clients when a contract change affects them.

Each directory owns its platform-specific source and build configuration. This root currently provides shared repository hygiene through `.gitignore`; add common tooling here only when the project adopts it.

## Getting started

Run the checks for each component from the repository root:

```bash
# backend (Python 3.10+, standard library only)
cd backend && python3 -m unittest tests.test_debt_simplifier

# web
cd web && npm ci && npm run build

# android (requires the Android SDK)
cd android && ./gradlew testDebugUnitTest
```

Choose and document the backend, web, and Android toolchains in their respective directories. Run and test each component using its local instructions. The clients require a reachable backend API; configure its base URL through local environment settings and do not commit secrets.
