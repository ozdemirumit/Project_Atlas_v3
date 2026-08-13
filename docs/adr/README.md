# Project Atlas Architecture Decision Records

Architecture Decision Records capture significant implementation choices made under the approved Project Atlas documentation baseline.

## Lifecycle

- `Proposed`: under evaluation and not implementation authority.
- `Accepted`: approved for implementation.
- `Superseded`: replaced by a later ADR that links back to the prior decision.
- `Deprecated`: retained for history but no longer applicable.

ADR numbers are permanent and never reused. Material changes require a new ADR rather than silent editing of an accepted decision.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [ADR-001](ADR-001_Initial_Application_Stack.md) | Initial application stack | Accepted |
| [ADR-002](ADR-002_Development_and_Delivery_Toolchain.md) | Development and delivery toolchain | Accepted |
| [ADR-003](ADR-003_Development_Identity.md) | Development identity boundary | Accepted |
| [ADR-004](ADR-004_MCP_Builder_Python_Generation_Profile.md) | MCP Builder Python generation profile | Accepted |
| [ADR-005](ADR-005_MCP_Builder_Static_Validation_Profile.md) | MCP Builder static validation profile | Accepted |
| [ADR-006](ADR-006_MCP_Builder_Domain_Review_Contract.md) | MCP Builder domain review contract | Accepted |
| [ADR-007](ADR-007_MCP_Builder_Security_Review_Contract.md) | MCP Builder security review contract | Accepted |
| [ADR-008](ADR-008_MCP_Builder_Isolated_Lab_Validation_Contract.md) | MCP Builder isolated lab validation contract | Accepted |
| [ADR-009](ADR-009_MCP_Builder_Candidate_Package_Handoff_Contract.md) | MCP Builder candidate package handoff contract | Accepted |
| [ADR-010](ADR-010_MCP_Builder_Package_Acquisition_Contract.md) | MCP Builder package acquisition contract | Accepted |
| [ADR-011](ADR-011_Connector_Package_Validation_Intake_Contract.md) | Connector package validation intake contract | Accepted |
| [ADR-012](ADR-012_Connector_Package_Content_Dependency_Inventory_Contract.md) | Connector package content and dependency inventory contract | Accepted |
| [ADR-013](ADR-013_Connector_Package_Secret_Prohibited_Content_Scan_Contract.md) | Connector package secret and prohibited-content scan contract | Accepted |
| [ADR-014](ADR-014_Connector_Configuration_Capability_Schema_Semantics_Contract.md) | Connector configuration and capability schema semantics contract | Accepted |
| [ADR-015](ADR-015_Connector_Declared_Authority_Implementation_Behavior_Contract.md) | Connector declared authority and implementation behavior contract | Accepted |
| [ADR-016](ADR-016_Connector_Static_Code_Dependency_Hygiene_Contract.md) | Connector static code and dependency hygiene contract | Accepted |
| [ADR-017](ADR-017_Connector_Dependency_Vulnerability_Analysis_Contract.md) | Connector dependency vulnerability analysis contract | Accepted |
| [ADR-018](ADR-018_Connector_Package_Malware_Analysis_Contract.md) | Connector package malware analysis contract | Accepted |
| [ADR-019](ADR-019_Connector_Package_License_Analysis_Contract.md) | Connector package license analysis contract | Accepted |
| [ADR-020](ADR-020_Connector_Contract_Validation_Contract.md) | Connector contract validation contract | Accepted |
| [ADR-021](ADR-021_Connector_Isolated_Runner_Validation_Contract.md) | Connector isolated runner validation contract | Accepted |
| [ADR-022](ADR-022_Connector_Isolated_Lab_Self_Test_Contract.md) | Connector isolated lab self-test contract | Accepted |
| [ADR-023](ADR-023_Connector_Final_Validation_Contract.md) | Connector final validation contract | Accepted |
| [ADR-024](ADR-024_Connector_Package_Human_Approval_Contract.md) | Connector package human approval contract | Accepted |
| [ADR-025](ADR-025_Connector_Publisher_Attestation_Contract.md) | Connector publisher attestation contract | Accepted |
| [ADR-026](ADR-026_Connector_Package_Signing_Contract.md) | Connector package signing contract | Accepted |
| [ADR-027](ADR-027_Connector_Internal_Registry_Publication_Contract.md) | Connector internal registry publication contract | Accepted |
| [ADR-028](ADR-028_Connector_Package_Registration_Contract.md) | Connector package registration contract | Accepted |
| [ADR-029](ADR-029_Connector_Package_Installation_Contract.md) | Connector package installation contract | Accepted |
| [ADR-030](ADR-030_Connector_Instance_Creation_Contract.md) | Connector instance creation contract | Accepted |
| [ADR-031](ADR-031_Connector_Target_Configuration_Binding_Contract.md) | Connector target and configuration binding contract | Accepted |
| [ADR-032](ADR-032_Connector_Credential_Reference_Assignment_Contract.md) | Connector credential-reference assignment contract | Accepted |
| [ADR-033](ADR-033_Connector_Configuration_Connectivity_Validation_Contract.md) | Connector configuration and connectivity validation contract | Accepted |
| [ADR-034](ADR-034_Connector_Capability_Governance_Enablement_Contract.md) | Connector capability governance and enablement contract | Accepted |
| [ADR-035](ADR-035_Connector_Runtime_Trust_Grant_Contract.md) | Connector runtime trust grant contract | Accepted |
| [ADR-036](ADR-036_Connector_Secret_Brokerage_Authorization_Contract.md) | Connector secret brokerage authorization contract | Accepted |
| [ADR-037](ADR-037_Connector_Runtime_Activation_and_Health_Evidence_Contract.md) | Connector runtime activation and health evidence contract | Accepted |
| [ADR-038](ADR-038_Connector_Target_Session_and_Connectivity_Evidence_Contract.md) | Connector target session and connectivity evidence contract | Accepted |
| [ADR-039](ADR-039_Connector_Capability_Invocation_Authorization_Contract.md) | Connector capability invocation authorization contract | Accepted |
| [ADR-040](ADR-040_Bounded_Connector_Capability_Invocation_Contract.md) | Bounded connector capability invocation contract | Accepted |
| [ADR-041](ADR-041_Governed_Connector_Invocation_Evidence_Ingestion_Contract.md) | Governed connector invocation evidence ingestion contract | Accepted |
| [ADR-042](ADR-042_Governed_Operational_Evidence_Knowledge_Draft_Curation_Contract.md) | Governed operational evidence knowledge-draft curation contract | Accepted |
| [ADR-043](ADR-043_Governed_Operational_Knowledge_Draft_Review_Request_Contract.md) | Governed operational knowledge draft review request contract | Accepted |
| [ADR-044](ADR-044_Governed_Operational_Knowledge_Reviewer_Assignment_Contract.md) | Governed operational knowledge reviewer assignment contract | Accepted |
| [ADR-045](ADR-045_Governed_Operational_Knowledge_Protected_Inspection_Lease_Contract.md) | Governed operational knowledge protected inspection lease contract | Accepted |
| [ADR-046](ADR-046_Governed_Operational_Knowledge_Protected_Content_Presentation_Contract.md) | Governed operational knowledge protected content presentation contract | Accepted |
| [ADR-047](ADR-047_Governed_Operational_Knowledge_Review_Finding_Contract.md) | Governed operational knowledge review finding contract | Accepted |
| [ADR-048](ADR-048_Governed_Operational_Knowledge_Protected_Finding_Presentation_Contract.md) | Governed operational knowledge protected finding presentation contract | Accepted |
| [ADR-049](ADR-049_Governed_Operational_Knowledge_Track_Review_Decision_Contract.md) | Governed operational knowledge track review decision contract | Accepted |
| [ADR-050](ADR-050_Governed_Operational_Knowledge_Correction_and_Resubmission_Contract.md) | Governed operational knowledge correction and resubmission contract | Accepted |
| [ADR-051](ADR-051_Governed_Operational_Knowledge_Final_Resolution_Contract.md) | Governed operational knowledge final resolution contract | Accepted |
| [ADR-052](ADR-052_Governed_Operational_Knowledge_Publication_Preparation_Contract.md) | Governed operational knowledge publication preparation contract | Accepted |
| [ADR-053](ADR-053_Governed_Protected_Knowledge_Source_Materialization_Contract.md) | Governed protected knowledge source materialization contract | Accepted |
| [ADR-054](ADR-054_Governed_Deterministic_Protected_Knowledge_Chunking_Contract.md) | Governed deterministic protected knowledge chunking contract | Accepted |
| [ADR-055](ADR-055_Governed_Protected_Knowledge_Embedding_Generation_Contract.md) | Governed protected knowledge embedding generation contract | Accepted |
| [ADR-056](ADR-056_Governed_Protected_Knowledge_Retrieval_Index_Staging_and_Validation_Contract.md) | Governed protected knowledge retrieval index staging and validation contract | Accepted |
| [ADR-057](ADR-057_Governed_Protected_Knowledge_Retrieval_Index_Publication_Contract.md) | Governed protected knowledge retrieval index publication contract | Accepted |
| [ADR-058](ADR-058_Governed_Protected_Knowledge_Retrieval_Contract.md) | Governed protected knowledge retrieval contract | Accepted |
| [ADR-059](ADR-059_Governed_Protected_Model_Context_Assembly_Contract.md) | Governed protected model-context assembly contract | Accepted |
| [ADR-060](ADR-060_Governed_Protected_Model_Invocation_Contract.md) | Governed protected model invocation contract | Accepted |
| [ADR-061](ADR-061_Governed_Protected_Model_Draft_Adjudication_Contract.md) | Governed protected model draft adjudication contract | Accepted |
| [ADR-062](ADR-062_Governed_Protected_Answer_Presentation_Contract.md) | Governed protected answer presentation contract | Accepted |
| [ADR-063](ADR-063_Governed_Grounded_Recommendation_Candidate_Generation_Contract.md) | Governed grounded recommendation candidate generation contract | Accepted |
| [ADR-064](ADR-064_Governed_Protected_Candidate_Service_Impact_Enrichment_Contract.md) | Governed protected candidate service-impact enrichment contract | Accepted |
| [ADR-065](ADR-065_Governed_Protected_Candidate_Risk_Interruption_Duration_Recovery_Completion_Contract.md) | Governed protected candidate risk, interruption, duration, and recovery completion contract | Accepted |
| [ADR-066](ADR-066_Governed_Deterministic_Protected_Recommendation_Adjudication_Contract.md) | Governed deterministic protected recommendation adjudication contract | Accepted |
| [ADR-067](ADR-067_Governed_Protected_Recommendation_Presentation_Contract.md) | Governed protected recommendation presentation contract | Accepted |
| [ADR-068](ADR-068_Governed_Recommendation_Domain_Promotion_Contract.md) | Governed recommendation domain promotion contract | Accepted |
| [ADR-069](ADR-069_Governed_Recommendation_Review_Readiness_Contract.md) | Governed recommendation review readiness contract | Accepted |
| [ADR-070](ADR-070_Governed_Recommendation_Human_Review_Request_Contract.md) | Governed recommendation human review request contract | Accepted |
| [ADR-071](ADR-071_Governed_Recommendation_Reviewer_Assignment_Contract.md) | Governed recommendation reviewer assignment contract | Accepted |
| [ADR-072](ADR-072_Governed_Recommendation_Protected_Inspection_Lease_Contract.md) | Governed recommendation protected inspection lease contract | Accepted |
| [ADR-073](ADR-073_Governed_Recommendation_Protected_Content_Presentation_Contract.md) | Governed recommendation protected content presentation contract | Accepted |
| [ADR-074](ADR-074_Governed_Recommendation_Human_Review_Finding_Contract.md) | Governed recommendation human review finding contract | Accepted |
| [ADR-075](ADR-075_Governed_Recommendation_Protected_Finding_Presentation_Contract.md) | Governed recommendation protected finding presentation contract | Accepted |
| [ADR-076](ADR-076_Governed_Recommendation_Track_Review_Decision_Contract.md) | Governed recommendation track review decision contract | Accepted |
| [ADR-077](ADR-077_Governed_Recommendation_Correction_and_Resubmission_Contract.md) | Governed recommendation correction and resubmission contract | Accepted |
| [ADR-078](ADR-078_Governed_Final_Recommendation_Disposition_Contract.md) | Governed final recommendation disposition contract | Accepted |
| [ADR-079](ADR-079_Local_and_LDAP_Authentication_Without_Mandatory_MFA.md) | Local and LDAP/Active Directory authentication without mandatory MFA | Accepted |
