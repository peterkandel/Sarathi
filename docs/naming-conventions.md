# Naming Conventions

## Repositories and Packages
- Use lowercase names with hyphens for Node packages.
- Use lowercase names with underscores for Python service folders.
- Use descriptive names that reflect bounded context and business capability.

## Python Services
- Module names: `snake_case`
- Classes: `PascalCase`
- Functions and variables: `snake_case`
- Database tables: `snake_case`
- API paths: lowercase, versioned, and resource-oriented

## Frontend
- React components: `PascalCase`
- Hooks: `useCamelCase`
- Route folders: lowercase
- Shared design tokens: `kebab-case`

## Events and Contracts
- Domain events: `PastTenseNounEvent` or `NounChanged` style
- Integration events: explicit business meaning, not technical transport terms
- Environment variables: `UPPER_SNAKE_CASE`
- Secrets should never be committed to source control
