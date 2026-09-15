-- Requires user approval. Run as a role allowed to grant F1_INGESTOR.
-- Assign only the ingestion role to the authenticated user; preserve default role.
SET F1_PIPELINE_USER = CURRENT_USER();
GRANT ROLE F1_INGESTOR TO USER IDENTIFIER($F1_PIPELINE_USER);
