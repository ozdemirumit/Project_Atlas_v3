# ADR-079: Local and LDAP/Active Directory Authentication Without Mandatory Multi-Factor Authentication

- Status: Accepted
- Date: 2026-08-13
- Owners: Product Owner, Security Architecture
- Governing documents: ATLAS-003, ATLAS-030, ATLAS-031, ATLAS-032, ATLAS-037, ADR-005 through
  ADR-078

## Context

ATLAS-030 (Authentication) originally stated that multi-factor authentication (MFA) is enforced by
the enterprise identity provider where available, and many governed connector, knowledge-review,
and recommendation-review ADRs (ADR-005 through ADR-078) embedded an actor-eligibility requirement
of "MFA," "hardware-backed MFA," or "hardware MFA" for the human who may submit, approve, or review
a governed action.

The Product Owner has decided that Project Atlas will authenticate human users through local
bootstrap/recovery accounts and LDAP/Active Directory only (ATLAS-030 Section 6), and will not
require multi-factor authentication for any actor class.

## Decision

Atlas does not require multi-factor authentication for any human, service, connector, or
integration actor.

Wherever a prior ADR (ADR-005 through ADR-078) specified "MFA," "hardware-backed MFA," or "hardware
MFA" as part of actor eligibility, a request contract, an audit or testing checklist, or an API
security control, that requirement is replaced as follows:

- Where MFA gated who may act (for example, "MFA human," "hardware-backed MFA human," "MFA-protected
  human"), the clause becomes "authenticated enterprise human" (a local or LDAP/Active Directory
  session), with every other named control (tenant scope, separation of duties, dedicated
  permission, browser-session binding, CSRF protection, and so on) unchanged.
- Where MFA expressed an authentication-freshness requirement (for example, "recent hardware-backed
  MFA"), the clause becomes "recent authentication" — a fresh, non-remembered local or LDAP/Active
  Directory session verification — preserving the freshness control without a multi-factor
  requirement.
- Where "MFA" appeared as a standalone item in a comma-separated list of tested or audited
  properties, the item is removed from the list.

This ADR amends only the actor-eligibility and authentication-assurance language of ADR-005 through
ADR-078. It does not alter any other decision in those ADRs: connector governance, knowledge-review,
recommendation-review, capability, evidence, and lifecycle contracts remain as approved.

ATLAS-030 Section 7 (Authentication Assurance) is updated to remove the multi-factor authentication
requirement and to state that step-up assurance for sensitive actions relies on re-authentication
(fresh credential verification), not an additional factor.

## Consequences

### Positive

- Documentation now matches the selected identity-provider model: local bootstrap/recovery accounts
  and LDAP/Active Directory only, with no dependency on an MFA-capable identity provider.
- Removes an assurance mechanism the organization does not plan to operate, avoiding a documented
  requirement that implementation could not satisfy.
- Preserves freshness-based step-up (re-authentication) as the control for sensitive administration,
  secret changes, emergency access, and approval of high-risk operations.

### Costs and Risks

- Reduces authentication-factor assurance for high-risk human approval actions (connector approval,
  secret brokerage authorization, package signing, knowledge and recommendation disposition, and
  similar governed actions) to whatever a single-factor local or LDAP/Active Directory session
  provides.
- This decision was made under the single-maintainer governance exception recorded in
  `docs/reviews/2026-08-03_Foundation_Review.md` Section 8: the same individual holds Product Owner,
  acting Architecture Owner, and acting Security Architecture Owner authority. No independent
  security reviewer has challenged this specific relaxation.
- Per the same recorded exception, independent security review must be obtained before a production
  release; that review should explicitly re-examine whether single-factor authentication is
  sufficient for the governed high-risk actions listed above.

## Rejected Alternatives

### Keep MFA for the highest-risk actions only

Keeping MFA for a narrow subset of actions (for example, secret brokerage authorization or package
signing) while removing it elsewhere was considered. Rejected for consistency and implementation
simplicity per explicit product direction to remove the MFA requirement uniformly. A future ADR may
reintroduce a narrower MFA requirement if a subsequent security review recommends it.

## Follow-Up

- ATLAS-030 Section 7 and Section 24 updated to record this decision (version 2.0.0).
- ADR-005 through ADR-078 updated to replace MFA-specific actor-eligibility and freshness language
  per the Decision section above.
- `docs/adr/README.md` index updated to include this ADR.
