-- Requires approval: grant the existing transformer role to the authenticated user.
-- Default role and warehouse settings are not modified.
SET F1_TRANSFORM_USER = CURRENT_USER();
GRANT ROLE F1_TRANSFORMER TO USER IDENTIFIER($F1_TRANSFORM_USER);
