# CI/CD

This folder documents delivery standards for the SARATHI platform monorepo.

## Guidance
- Build and test each app or service independently.
- Validate shared packages before publishing service or portal changes.
- Use separate pipelines for citizen-facing and administrative surfaces when approval rules differ.
- Deploy infrastructure changes through reviewed release workflows.
- Keep environment promotion explicit: dev -> stage -> prod.
