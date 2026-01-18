# Technical Decision Log

**Version:** 1.0  
**Status:** APPROVED  
**Purpose:** Record major architectural and technical decisions  
**Last Updated:** 2026-01-17

---

## Decision Log Format

Each decision includes:
- **Decision ID:** TECH-XXX
- **Date:** When decided
- **Title:** Clear description
- **Context:** Why this decision was needed
- **Options Considered:** Alternatives evaluated
- **Decision:** What was chosen and why
- **Consequences:** Positive and negative impacts
- **Status:** Active, Superseded, Deprecated

---

## Architecture Decisions

### TECH-001: FastAPI for Backend

**Date:** 2025-10-01  
**Status:** Active

**Context:**
Need high-performance Python framework for document processing APIs with async support.

**Options Considered:**
1. **FastAPI** - Modern, async, auto-documentation
2. **Django REST** - Mature, batteries-included
3. **Flask** - Lightweight, flexible
4. **Go** - Faster, typed, learning curve

**Decision:** FastAPI

**Rationale:**
- Native async/await support for concurrent document processing
- Automatic OpenAPI/Swagger documentation
- Type hints for better reliability
- Fast performance (equal to Go)
- Growing ecosystem and community
- Excellent for modern APIs

**Consequences:**
- ✅ Fast development velocity
- ✅ Excellent documentation generation
- ✅ Good async performance for I/O operations
- ✅ Developer experience excellent
- ⚠️ Smaller ecosystem than Django
- ⚠️ Less historical stability than Django

---

### TECH-002: React + TypeScript for Frontend

**Date:** 2025-10-01  
**Status:** Active

**Context:**
Need interactive, maintainable frontend for document management UI.

**Options Considered:**
1. **React + TypeScript** - Type-safe, component-based
2. **Vue 3** - Simpler, smaller bundle
3. **Angular** - Full framework, opinionated
4. **Svelte** - Smaller, compiler-based

**Decision:** React + TypeScript

**Rationale:**
- Largest community and ecosystem
- Type safety catches bugs early
- Component reusability
- Wide developer availability
- Excellent tooling (Vite, React DevTools)
- Strong corporate backing

**Consequences:**
- ✅ Easier to hire React developers
- ✅ Rich ecosystem of libraries
- ✅ Type safety catches bugs
- ✅ Great debugging experience
- ⚠️ Larger bundle size than Vue/Svelte
- ⚠️ Steeper learning curve than Vue

---

### TECH-003: Cosmos DB (MongoDB API) for Database

**Date:** 2025-10-01  
**Status:** Active

**Context:**
Need globally distributed database with flexible schema for multi-tenant SaaS.

**Options Considered:**
1. **Cosmos DB (MongoDB API)** - Managed, global, flexible
2. **PostgreSQL** - Proven, mature, ACID
3. **MongoDB (self-hosted)** - Flexible, learning curve
4. **Firebase** - Fully managed, limited control

**Decision:** Cosmos DB (MongoDB API)

**Rationale:**
- Microsoft-managed (Azure integration)
- Global distribution (multi-region failover)
- Automatic backups and PITR
- MongoDB familiar syntax (flexible schema)
- Document-based (good for content)
- SOC2 compliant
- ACID transactions available

**Consequences:**
- ✅ Fully managed, no ops burden
- ✅ Global replication built-in
- ✅ Automatic backups
- ✅ Scalable (unlimited data)
- ✅ Strong consistency guarantees
- ⚠️ Higher cost than self-hosted
- ⚠️ Vendor lock-in to Azure
- ⚠️ RU consumption model learning curve

---

### TECH-004: Azure Static Web App for Frontend Hosting

**Date:** 2025-10-05  
**Status:** Active

**Context:**
Need simple, reliable hosting for React SPA with GitHub integration.

**Options Considered:**
1. **Azure Static Web App** - Fully managed, CI/CD built-in
2. **Netlify** - Developer-friendly, generous free tier
3. **Vercel** - Next.js optimized, fast
4. **AWS S3 + CloudFront** - Low cost, complex setup

**Decision:** Azure Static Web App

**Rationale:**
- Native GitHub Actions integration
- Automatic CI/CD from main branch
- Built-in authentication (optional)
- Custom domain support
- Cost-effective
- Azure ecosystem consistency

**Consequences:**
- ✅ Automatic deployments
- ✅ Very low cost
- ✅ Built-in CDN
- ✅ Easy to manage
- ⚠️ Less flexible than Netlify
- ⚠️ Limited to Azure ecosystem

---

### TECH-005: Azure Container Apps for Backend

**Date:** 2025-10-05  
**Status:** Active

**Context:**
Need container orchestration for FastAPI backend without Kubernetes complexity.

**Options Considered:**
1. **Azure Container Apps** - Simplified Kubernetes, KEDA scaling
2. **Azure App Service** - Simple but less flexible
3. **AKS (Kubernetes)** - Powerful but complex
4. **AWS ECS** - Good but not Azure
5. **Docker Compose** - Simple but manual scaling

**Decision:** Azure Container Apps

**Rationale:**
- Abstraction over Kubernetes (simpler than AKS)
- KEDA auto-scaling based on metrics
- Cost-effective
- Managed environment (no cluster management)
- GitHub Actions integration
- Azure ecosystem consistency

**Consequences:**
- ✅ Simple deployment
- ✅ Automatic scaling
- ✅ Low management overhead
- ✅ Cost-effective
- ✅ Good for microservices
- ⚠️ Less control than raw Kubernetes
- ⚠️ Limited customization vs AKS

---

## Data Decisions

### TECH-006: Cosmos DB Partitioning Strategy

**Date:** 2025-10-10  
**Status:** Active

**Context:**
Need partitioning strategy to handle multi-tenancy and prevent hot partitions.

**Options Considered:**
1. **user_id + company_id (Hierarchical)** - Good isolation
2. **Single partition key** - Simpler but potential hot partitions
3. **Temporal partitioning** - Good for time-series, complex
4. **No explicit partitioning** - Poor scaling

**Decision:** Hierarchical Partition Key (user_id + company_id)

**Rationale:**
- Ensures tenant data isolation
- Prevents hot partition (even distribution)
- Enables efficient queries
- Hierarchical allows targeted multi-partition queries
- Matches application access patterns

**Consequences:**
- ✅ Better scalability
- ✅ Data isolation
- ✅ Efficient queries
- ⚠️ Requires careful query design
- ⚠️ Some cross-tenant queries challenging

---

### TECH-007: Soft Deletes vs Hard Deletes

**Date:** 2025-10-15  
**Status:** Active

**Context:**
Determine how to handle deleted documents for compliance and recovery.

**Options Considered:**
1. **Soft deletes (logical)** - Keep data, mark as deleted
2. **Hard deletes (physical)** - Remove data immediately
3. **Archival (both)** - Soft delete then hard after period

**Decision:** Soft Deletes + Archival

**Rationale:**
- Regulatory requirement: 30-day recovery window
- Audit trail: must maintain deleted item records
- User experience: accidental deletion recovery
- Compliance: GDPR right-to-be-forgotten (30 day window)

**Consequences:**
- ✅ User protection (recovery possible)
- ✅ Regulatory compliance
- ✅ Audit trail maintained
- ⚠️ Database growth (more storage)
- ⚠️ Query complexity (filter deleted items)

---

## API Decisions

### TECH-008: API Versioning Strategy

**Date:** 2025-10-15  
**Status:** Active

**Context:**
Need strategy for evolving API without breaking clients.

**Options Considered:**
1. **URL-based versioning (/v1/**, /v2/*)** - Explicit, clear
2. **Header-based** - Cleaner URLs, less visible
3. **Query-based** - Flexible, less common
4. **No versioning** - Simple but breaks clients

**Decision:** URL-based (/api/v1/)

**Rationale:**
- Clear, explicit versioning
- Easy to maintain multiple versions
- Standard practice
- API documentation clarity
- Clear deprecation path

**Consequences:**
- ✅ Clear version management
- ✅ Multiple version support
- ✅ Explicit breaking changes
- ⚠️ Longer URLs
- ⚠️ Version maintenance burden

---

### TECH-009: JWT Token Strategy

**Date:** 2025-10-20  
**Status:** Active

**Context:**
Need stateless authentication for distributed backend system.

**Options Considered:**
1. **JWT (stateless)** - Scalable, no session store
2. **Session cookies** - Familiar, stateful
3. **OAuth 2.0** - Complex, federated
4. **API keys** - Simple but limited

**Decision:** JWT with Refresh Tokens

**Rationale:**
- Stateless (horizontal scalability)
- No session store needed
- Works well with mobile/SPA
- Industry standard
- Can include user context (roles, permissions)

**Consequences:**
- ✅ Highly scalable
- ✅ No server state needed
- ✅ Works with SPAs
- ⚠️ Token size (included in every request)
- ⚠️ Token revocation challenging
- ⚠️ Requires HTTPS (tokens in clear)

---

## Security Decisions

### TECH-010: Encryption Strategy

**Date:** 2025-10-25  
**Status:** Active

**Context:**
Secure sensitive data in transit and at rest.

**Options Considered:**
1. **TLS (transit) + AES-256 (rest)** - Standard, secure
2. **TLS only** - Simpler but at-rest unencrypted
3. **Custom encryption** - Complex, risky
4. **No encryption** - Insecure

**Decision:** TLS 1.2+ + Azure-managed Encryption at Rest

**Rationale:**
- TLS 1.2+ required for all connections
- Azure manages encryption keys (at-rest)
- Microsoft-managed vs customer-managed (simpler)
- Meets compliance requirements
- Industry standard practice

**Consequences:**
- ✅ Strong security posture
- ✅ Compliance-ready
- ✅ No key management overhead
- ⚠️ Vendor lock-in (Azure keys)
- ⚠️ Slight performance overhead

---

### TECH-011: File Upload Security

**Date:** 2025-10-25  
**Status:** Active

**Context:**
Prevent malicious file uploads and abuse.

**Options Considered:**
1. **Whitelist + Magic number check + AV scan** - Most secure
2. **Whitelist + Magic number only** - Good balance
3. **Whitelist only** - Simple, less secure
4. **No restrictions** - Unsafe

**Decision:** Whitelist + Magic Number + Virus Scanning

**Rationale:**
- Whitelist: only PDF files allowed
- Magic number: verify file content matches extension
- Virus scanning: detect malware
- File size limit: 5 MB max
- Storage: Azure Blob (isolated, no execution)

**Consequences:**
- ✅ Prevents malicious uploads
- ✅ Protects users
- ✅ Regulatory compliance
- ⚠️ Adds complexity
- ⚠️ Minor performance cost

---

## Testing Decisions

### TECH-012: Testing Strategy (Unit/Integration/E2E)

**Date:** 2025-11-01  
**Status:** Active

**Context:**
Balance between test coverage, maintenance, and velocity.

**Options Considered:**
1. **Pyramid (80% unit, 15% integration, 5% E2E)** - Balanced
2. **Ice cream (5% unit, 15% integration, 80% E2E)** - Slow, thorough
3. **Unit only (100%)** - Fast, limited coverage
4. **No testing** - Risky, fast initially

**Decision:** Test Pyramid (80/15/5)

**Rationale:**
- Unit tests: fast feedback, high coverage
- Integration tests: verify component interaction
- E2E tests: user workflows, final validation
- Balances speed vs confidence
- Industry best practice

**Consequences:**
- ✅ Good test coverage
- ✅ Fast test suite
- ✅ Catches most bugs early
- ⚠️ Some edge cases missed (need E2E)
- ⚠️ Test maintenance burden

---

## Infrastructure Decisions

### TECH-013: Monitoring & Observability

**Date:** 2025-11-05  
**Status:** Active

**Context:**
Monitor system health and debug production issues.

**Options Considered:**
1. **Application Insights + Logs** - Comprehensive, integrated
2. **DataDog** - Powerful, expensive
3. **Prometheus + Grafana** - DIY, flexible
4. **CloudWatch** - AWS-only

**Decision:** Application Insights + Custom Logging

**Rationale:**
- Application Insights: built into Azure
- Automatic instrumentation
- Trace requests end-to-end
- Custom events/metrics
- Cost-effective for MVP

**Consequences:**
- ✅ Integrated with Azure
- ✅ Auto-instrumentation
- ✅ Cost-effective
- ✅ Good alerting
- ⚠️ Less flexible than DataDog
- ⚠️ Learning curve

---

## Process Decisions

### TECH-014: CI/CD Pipeline

**Date:** 2025-11-10  
**Status:** Active

**Context:**
Automate testing and deployment for fast, reliable releases.

**Options Considered:**
1. **GitHub Actions** - Native, free tier
2. **Azure Pipelines** - Powerful, integrated
3. **Jenkins** - Self-hosted, flexible
4. **GitLab CI** - Good, but different platform

**Decision:** GitHub Actions

**Rationale:**
- Free tier for public repos
- Native GitHub integration
- Simple YAML configuration
- Good ecosystem of actions
- No separate infrastructure needed

**Consequences:**
- ✅ No ops overhead
- ✅ Free for public repos
- ✅ Native integration
- ✅ Simple to configure
- ⚠️ Limited UI
- ⚠️ Matrix strategy can be complex

---

## Superseded Decisions

### TECH-S001: Initially Considered Self-Hosted Database

**Date:** 2025-10-01  
**Status:** Superseded (by TECH-003)

**Initial Decision:** Self-hosted MongoDB

**Reason for Change:** 
- Ops burden too high for small team
- Backup/recovery complexity
- No global replication without additional work
- Switched to Cosmos DB for managed solution

---

## Future Considerations

### Potential Decisions Needed

```
1. Message Queue (Kafka/RabbitMQ) - For async processing
   Status: Under consideration
   Timeline: Phase 4 (advanced workflows)
   
2. Search Engine (Elasticsearch) - For full-text search
   Status: Under consideration
   Timeline: Phase 4 (analytics/reporting)
   
3. Caching Layer (Redis) - For performance
   Status: Under consideration
   Timeline: Phase 3 (performance optimization)
   
4. Machine Learning - For intelligent routing
   Status: Exploring
   Timeline: Phase 5+
```

---

**Reference:** `/docs/01-project/TECHNICAL_DECISION_LOG_v1.0.md`
