# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Security Scanning

This project uses multiple security scanning tools:

- **Bandit**: Static security analysis for Python code
- **Safety**: Dependency vulnerability scanning
- **Semgrep**: Advanced static analysis
- **TruffleHog**: Secret detection
- **Trivy**: Container vulnerability scanning

### Running Security Scans Locally

```bash
# Install security tools
pip install bandit safety semgrep

# Run all scans
bandit -r app/
safety scan --policy-file .safety-policy.yml
semgrep --config=auto app/
```

## Vulnerability Management

### Current Status (October 2024)

All high and critical vulnerabilities have been resolved through dependency updates:

#### ✅ Resolved Vulnerabilities

| Package      | CVE/Issue      | Fixed Version | Status   |
| ------------ | -------------- | ------------- | -------- |
| lightgbm     | CVE-2024-43598 | ≥4.6.0        | ✅ Fixed |
| scikit-learn | CVE-2024-5206  | ≥1.5.0        | ✅ Fixed |
| tqdm         | CVE-2024-34062 | ≥4.66.3       | ✅ Fixed |
| scrapy       | CVE-2024-1968  | ≥2.11.2       | ✅ Fixed |
| scrapy       | CVE-2024-3572  | ≥2.11.2       | ✅ Fixed |
| scrapy       | CVE-2024-3574  | ≥2.11.2       | ✅ Fixed |
| twisted      | CVE-2024-41810 | ≥24.7.0       | ✅ Fixed |
| twisted      | CVE-2024-41671 | ≥24.7.0       | ✅ Fixed |
| twisted      | CVE-2023-46137 | ≥24.7.0       | ✅ Fixed |

#### 📋 Accepted Risks (Documented)

| Package | CVE            | Severity | Justification                                                             | Mitigation                                                             |
| ------- | -------------- | -------- | ------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| scrapy  | CVE-2017-14158 | Medium   | DoS via large file memory consumption. Known limitation since Scrapy 0.7. | Controlled scraping targets with `DOWNLOAD_MAXSIZE` limits configured. |

See `.safety-policy.yml` for detailed policy configuration.

## Reporting a Vulnerability

If you discover a security vulnerability, please follow these steps:

1. **DO NOT** open a public issue
2. Email security concerns to: [Your security email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond within 48 hours and provide a timeline for fix.

## Security Best Practices

### For Developers

1. **Dependencies**:

   - Keep dependencies up to date
   - Review `safety scan` output before merging PRs
   - Pin versions for reproducible builds

2. **Secrets Management**:

   - Never commit secrets to Git
   - Use environment variables for sensitive data
   - Use `.env.example` for documentation

3. **Code Security**:

   - Follow PEP 8 and security best practices
   - Use parameterized queries (SQLAlchemy ORM)
   - Validate all user inputs with Pydantic
   - Implement proper authentication/authorization

4. **API Security**:
   - Use JWT tokens with short expiration
   - Implement rate limiting
   - Enable CORS with specific origins
   - Use security headers (CSP, HSTS, etc.)

### For Deployment

1. **Environment**:

   - Use strong, unique JWT secrets (≥32 characters)
   - Enable HTTPS in production
   - Use secure database connections
   - Enable Redis authentication

2. **Monitoring**:

   - Enable Prometheus metrics
   - Set up alerting for anomalies
   - Monitor error logs
   - Track API response times

3. **Updates**:
   - Apply security patches promptly
   - Review dependency updates weekly
   - Test in staging before production
   - Maintain rollback capability

## Security Checklist for PRs

- [ ] No hardcoded secrets or credentials
- [ ] All user inputs validated
- [ ] Dependencies scanned for vulnerabilities
- [ ] Bandit scan passes
- [ ] No SQL injection risks
- [ ] Proper authentication/authorization
- [ ] Security headers configured
- [ ] Error messages don't leak sensitive data

## Security Contacts

- Security Team: [Your security email]
- Maintainer: [Your email]

---

**Last Updated**: October 2025
**Security Policy Version**: 1.0
