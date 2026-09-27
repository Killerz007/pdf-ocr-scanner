# Security policy

## Supported versions

Security fixes are applied to the latest published release only.

| Version | Supported |
|---|---|
| 1.0.0-beta | Yes |
| Earlier versions and development snapshots | No |

## Reporting a vulnerability

Use GitHub's private vulnerability reporting feature:

1. Open the repository's **Security** tab.
2. Select **Advisories**, then **Report a vulnerability**.
3. Describe the affected version, impact, reproduction steps, and any suggested mitigation.

If private reporting is unavailable, open a public issue that asks the maintainer to establish private contact. Do not include vulnerability details in that issue.

Please allow up to three business days for acknowledgement and up to seven business days for an initial assessment. Progress updates will be provided at least every 14 days while a report remains active. Fix and disclosure timing will depend on severity, complexity, and upstream dependencies.

## Keep sensitive details private

Until a coordinated disclosure date is agreed, do not publish:

- exploit code, malicious PDFs, or detailed reproduction steps;
- unpatched vulnerability details or ways to bypass a mitigation;
- credentials, API keys, private model files, or other secrets;
- private documents, unredacted logs, usernames, or local file paths.

Reports about third-party dependencies may need coordination with the upstream project. The broader design and dependency threat review remains available in [SECURITY_REVIEW.md](SECURITY_REVIEW.md).
