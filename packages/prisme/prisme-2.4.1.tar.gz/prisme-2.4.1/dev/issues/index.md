# Issue Tracking

> **Note**: Issues are now tracked on GitHub: https://github.com/Lasse-numerous/prisme/issues
>
> This folder contains detailed analysis documents that are linked from GitHub Issues.

## GitHub Issues (Open)

| Issue | Priority | Labels |
|-------|----------|--------|
| [#4 CLI Simplification & Developer Experience](https://github.com/Lasse-numerous/prisme/issues/4) | High | enhancement, dx |
| [#6 Schema drift detection](https://github.com/Lasse-numerous/prisme/issues/6) | High | enhancement, deferred |
| [#7 GraphQL extension point](https://github.com/Lasse-numerous/prisme/issues/7) | Medium | enhancement, deferred |
| [#9 Managed Subdomain (madewithpris.me)](https://github.com/Lasse-numerous/prisme/issues/9) | High | enhancement |
| [#34 Use workflow_run trigger for terraform after CI tests pass](https://github.com/Lasse-numerous/prisme/issues/34) | — | enhancement |
| [#35 Deploy workflow should accept server_ip as workflow_dispatch input](https://github.com/Lasse-numerous/prisme/issues/35) | — | enhancement |
| [#36 Generate Hetzner Object Storage backend for terraform state](https://github.com/Lasse-numerous/prisme/issues/36) | — | enhancement |
| [#55 Warn when model changes lack corresponding migrations](https://github.com/Lasse-numerous/prisme/issues/55) | — | — |
| [#56 Generated models use DateTime() instead of DateTime(timezone=True)](https://github.com/Lasse-numerous/prisme/issues/56) | — | — |
| [#57 Generate initial schema migration on first prism generate](https://github.com/Lasse-numerous/prisme/issues/57) | — | — |
| [#58 Devcontainer frontend Traefik router priority too low](https://github.com/Lasse-numerous/prisme/issues/58) | — | — |

## Detailed Documents

These documents provide detailed analysis and are linked from GitHub Issues:

| Document | GitHub Issue |
|----------|--------------|
| [cli-simplification-roadmap.md](cli-simplification-roadmap.md) | #4 |
| [schema-drift-not-detected.md](schema-drift-not-detected.md) | #6 |
| [no-custom-graphql-extension.md](no-custom-graphql-extension.md) | #7 |
| [generate-ignores-config-paths.md](generate-ignores-config-paths.md) | #5 (closed) |

## Issue Workflow

1. Create GitHub Issue for new bugs/features
2. Add detailed analysis document here if needed (link from issue)
3. Use GitHub labels for prioritization
4. Close issues via PR references (`Closes #N`)
