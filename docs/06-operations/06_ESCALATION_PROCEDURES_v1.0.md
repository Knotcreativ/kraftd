# Escalation Procedures v1.0

**Document**: Support Escalation Chains  
**Version**: 1.0  
**Last Updated**: January 2026  
**Audience**: On-call engineers, Team leads, Management

---

## Overview

This document defines who to contact for different types of issues and how quickly to escalate. Use this when you need help beyond your current level.

---

## Support Levels

### Level 1: On-Call Engineer (You)

**Responsibilities**:
- Monitor system health
- Respond to alerts
- Perform basic troubleshooting
- Follow runbooks
- Escalate if needed

**Authority**:
- Restart services
- Clear caches
- Check logs
- Restart processes

**Authority NOT Granted**:
- Modify code
- Delete data
- Change infrastructure
- Spend > $100

**Escalation Criteria** (call Level 2 if):
- Issue not resolved in 15 minutes
- Multiple systems affected
- Data loss risk
- > 10 users impacted

---

### Level 2: DevOps Engineer

**Responsibilities**:
- Review infrastructure
- Analyze system architecture
- Perform advanced troubleshooting
- Modify cloud resources
- Database optimization

**Authority**:
- Scale infrastructure up/down
- Increase database RU/s
- Modify firewall rules
- Access production systems
- Approve code hot-fixes

**Escalation Criteria** (call Level 3 if):
- Infrastructure failure
- Region outage
- Data loss occurred
- > 100 users impacted
- Suspected security breach

---

### Level 3: Engineering Lead

**Responsibilities**:
- Lead incident response
- Make architectural decisions
- Authorize emergency changes
- Post-mortem analysis
- System redesign decisions

**Authority**:
- Approve production changes
- Override standard processes
- Declare incidents
- Authorize vendor escalations
- Approve incident communications

**Escalation Criteria** (call Level 4 if):
- Requires vendor involvement
- Major data loss
- Security breach confirmed
- > 1000 users impacted
- Service down > 1 hour

---

### Level 4: Management

**Responsibilities**:
- Strategic decisions
- Customer communication
- Media handling
- Post-incident reviews
- External escalations

**Authority**:
- Approve emergency spending
- Contact vendors
- Notify customers
- Media statements
- Service shutdown decision

---

## On-Call Rotation Schedule

### Current On-Call Engineer

**Period**: Jan 18 - Jan 24, 2026

| Day | Engineer | Phone | Email |
|-----|----------|-------|-------|
| Mon-Fri | John Smith | (555) 123-4567 | john@company.com |
| Sat-Sun | Jane Doe | (555) 234-5678 | jane@company.com |
| After Hours | On-Call Pager | Dial extension 99 | N/A |

### Next On-Call Engineer

**Period**: Jan 25 - Jan 31, 2026
- Primary: Mike Johnson
- Secondary: Sarah Williams

---

## Escalation Triggers

### By Severity Level

**CRITICAL** (Escalate Immediately)
- Service completely down
- Data loss occurring
- Security breach detected
- Multiple systems failing
- > 500 users affected

**HIGH** (Escalate in 15 minutes if unresolved)
- Service partially down
- Significant degradation
- Risk of data loss
- Single system failure
- 50-500 users affected

**MEDIUM** (Escalate in 1 hour if unresolved)
- Service slow but working
- Non-critical features down
- Limited user impact
- < 50 users affected

**LOW** (Escalate if not fixed in 24 hours)
- Minor issues
- Workarounds available
- No user impact
- Documentation/cosmetic issues

---

## Escalation Process

### Step 1: Assess Severity

**Ask Yourself**:
1. How many users affected?
   - < 10 users = LOW/MEDIUM
   - 10-100 users = MEDIUM/HIGH
   - > 100 users = CRITICAL

2. What's impacted?
   - Non-critical feature = LOW
   - Main feature = MEDIUM
   - Core functionality = HIGH
   - User data = CRITICAL

3. Can users work around it?
   - Yes, easily = LOW
   - Yes, with difficulty = MEDIUM
   - No = HIGH/CRITICAL

4. Is data loss risk?
   - No = Lower severity
   - Yes = Higher severity

---

### Step 2: Attempt Resolution (Level 1)

**Time Limit**: 15 minutes

**Standard Steps**:
1. Check Application Insights for errors
2. Verify backend is running
3. Verify database is connected
4. Check for network issues
5. Review recent log entries
6. Try restarting service if safe
7. Check documentation for known issues

**If Resolved** → Document and close
**If Not Resolved** → Go to Step 3

---

### Step 3: Escalate to Level 2

**Call DevOps Engineer**:
```
"Hi, I've detected a [SEVERITY] issue.
[Brief description]
I've already tried [what you tried]
The current status is [status]
I need your help to [what you need]"
```

**Example Escalation Call**:
```
"Hi Mike, I've detected a CRITICAL issue.
The backend is not starting - getting connection timeout.
I've already restarted the service, checked the logs,
and verified the firewall rules.
Currently, users cannot login.
I need you to check the Cosmos DB configuration
and verify the connection string is correct."
```

**What DevOps Will Do**:
- Connect to systems
- Review infrastructure
- Check cloud resources
- Perform advanced diagnostics
- Make configuration changes if needed
- Escalate further if needed

---

### Step 4: Escalate to Level 3 (If Level 2 Needs Help)

**When**:
- Level 2 determines architectural issue
- Requires code changes
- Multiple systems affected
- Major incident declared

**Level 3 Will**:
- Take command of incident
- Authorize emergency changes
- Coordinate all teams
- Make critical decisions
- Prepare customer communication

---

### Step 5: Escalate to Level 4 (If Critical)

**When**:
- Service down > 1 hour
- Data loss confirmed
- Security breach confirmed
- Customer notification needed
- Requires vendor support

**Level 4 Will**:
- Authorize emergency spending
- Contact vendors
- Notify customers
- Prepare media response
- Declare incident status

---

## Contact Information

### On-Call Rotation

```
NEVER CALL DIRECTLY - Use escalation chain first!

Level 1: You (the current on-call engineer)
Level 2: DevOps Lead - Mike Johnson
         Office: (555) 123-9999
         Mobile: (555) 123-4567
         Email: mike@company.com
         Slack: @mjohnson

Level 3: Engineering Manager - Sarah Chen
         Office: (555) 123-8888
         Mobile: (555) 123-5678
         Email: sarah@company.com
         Slack: @schen

Level 4: VP Engineering - Robert Davis
         Office: (555) 123-7777
         Mobile: (555) 123-6789
         Email: robert@company.com
```

### Vendor Escalations

**Azure Support** (for infrastructure issues):
- Support Ticket: (555) 100-0001
- Severity P1 (critical): Direct escalation
- Severity P2 (high): 4-hour response
- Severity P3 (medium): 24-hour response

**SendGrid Support** (for email issues):
- Support Portal: support.sendgrid.com
- Account Manager: contacts@sendgrid.com
- Emergency: (555) 100-0002

---

## Escalation Communication Template

### When Escalating, Say:

**"I'm experiencing a [SEVERITY] [COMPONENT] issue:**

**Symptoms**: [What users are experiencing]

**Impact**: [How many users, what can't they do]

**What I've already tried**: [List steps taken]

**Current status**: [Where things stand]

**What I need**: [Specific help needed]

**Timeline**: [How long it's been happening]"

### Example

**"I'm experiencing a CRITICAL database connectivity issue:**

**Symptoms**: Backend service crashes on startup with connection timeout

**Impact**: 100% of users cannot login, core service down

**What I've already tried**: 
- Restarted backend service
- Verified environment variables are set
- Checked firewall rules allow outbound 443
- Pinged Cosmos DB endpoint (succeeds)

**Current status**: Backend stuck in restart loop, database unreachable despite network working

**What I need**: Help diagnosing Cosmos DB configuration issue

**Timeline**: Issue started 5 minutes ago"

---

## Incident Severity Guide

### CRITICAL (Escalate Level 1 → Level 2 → Level 3 Immediately)

**Examples**:
- [ ] Service completely down (no users can access)
- [ ] Data loss occurring (customers losing information)
- [ ] Security breach (unauthorized access confirmed)
- [ ] Multiple core systems failing
- [ ] > 500 users unable to work

**Response Time**: Escalate within 5 minutes
**SLA**: Incident commander on call within 15 minutes

---

### HIGH (Escalate Level 1 → Level 2 within 15 minutes)

**Examples**:
- [ ] Service partially down (some features broken)
- [ ] Major performance degradation (> 5 second response times)
- [ ] Critical feature down (document processing, exports)
- [ ] Database slow or intermittent
- [ ] 50-500 users affected

**Response Time**: Escalate if not fixed in 15 minutes
**SLA**: Level 2 available within 30 minutes

---

### MEDIUM (Consider escalation after 1 hour)

**Examples**:
- [ ] Non-critical feature broken
- [ ] API endpoint slow but responding
- [ ] Dashboard slow but working
- [ ] < 50 users affected
- [ ] Workarounds available

**Response Time**: Escalate if not fixed in 1 hour
**SLA**: Level 2 available within 2 hours

---

### LOW (Document and escalate next business day)

**Examples**:
- [ ] Documentation errors
- [ ] Minor UI issues
- [ ] Cosmetic problems
- [ ] No user impact
- [ ] Known workarounds exist

**Response Time**: Not urgent, document and plan
**SLA**: Fix within one week

---

## War Room Setup (Critical Incidents)

### When to Declare War Room

**If incident is**:
- CRITICAL severity
- Likely to take > 30 minutes to fix
- Requires multiple teams

### Setup Steps

1. **Create incident war room** (Teams/Slack):
   - Channel: #incident-response
   - Invite: All Level 2-4 engineers
   - Pin: Links to runbooks and dashboards

2. **Schedule war room call**:
   - Zoom: [link]
   - Dial-in: [number]
   - Duration: Until resolved + 15 minutes

3. **Assign roles**:
   - **Incident Commander**: Leads response
   - **Technical Lead**: Investigation & decisions
   - **DevOps**: Infrastructure changes
   - **Communication Lead**: Status updates
   - **Scribe**: Documents timeline & actions

4. **Update every 15 minutes**:
   - Current status
   - What's changed
   - Next steps
   - ETA to resolution

5. **Close war room**:
   - Once resolved and verified
   - Schedule post-mortem
   - Send summary email

---

## Post-Incident Review

### After Any CRITICAL or HIGH Incident

**Timeline**: Within 24 hours

**Attendees**:
- Incident commander
- All engineers involved
- Relevant managers

**Agenda**:
1. What happened? (timeline)
2. Why did it happen? (root cause)
3. How did we respond? (what went well)
4. What could we improve? (action items)
5. How do we prevent recurrence?

**Output**:
- Incident report filed
- Action items tracked
- Preventive measures planned
- Team trained on lessons learned

---

## Quick Reference Card

```
╔════════════════════════════════════════════════════════════╗
║         ESCALATION QUICK REFERENCE CARD                   ║
║                                                            ║
║ CRITICAL (Escalate NOW)                                   ║
║  · Service down                                            ║
║  · Data loss                                               ║
║  · Security breach                                         ║
║  · > 500 users affected                                    ║
║  Call: Mike (555) 123-4567                                ║
║  Then: Sarah (555) 123-5678                               ║
║                                                            ║
║ HIGH (Escalate in 15 min if unfixed)                       ║
║  · Service partially down                                  ║
║  · Major performance issue                                 ║
║  · 50-500 users affected                                   ║
║  Call: Mike (555) 123-4567                                ║
║                                                            ║
║ MEDIUM (Escalate in 1 hour if unfixed)                     ║
║  · Feature broken                                          ║
║  · < 50 users affected                                     ║
║  · Workarounds exist                                       ║
║  Call: Mike (555) 123-4567 (next day if OK)               ║
║                                                            ║
║ LOW (Next business day)                                    ║
║  · Minor issue                                             ║
║  · No user impact                                          ║
║  · Document and schedule                                   ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
```

---

**Document Complete** - Last updated January 2026

**Print this document and keep near your desk during on-call shifts**
