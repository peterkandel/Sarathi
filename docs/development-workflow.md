# Development Workflow

## Local Setup
1. Copy `.env.example` to `.env`.
2. Start infrastructure with `docker compose up --build`.
3. Run the relevant app or service in its own terminal.
4. Validate Python code with `python3 -m compileall apps services packages`.

## Suggested Order
1. Build shared contracts in `packages/*`.
2. Implement backend service logic in `services/*`.
3. Wire the citizen and admin portals to the citizen and admin BFFs.
4. Add integration and end-to-end tests.
5. Promote the same code path through dev, stage, and prod environments.

## Branch Strategy
- `main` is protected and deployable.
- Feature branches must be small and reviewable.
- Infrastructure changes should be isolated when possible.

## Review Rules
- Backend changes require API and security review.
- Client changes require accessibility and contract review.
- Administrative actions require stricter audit and authorization review.
