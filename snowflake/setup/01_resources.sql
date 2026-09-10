-- Run using an existing role authorized to create project resources.
-- Non-destructive: existing objects are preserved. Validate their configuration separately.
-- Reuse existing COMPUTE_WH. Do not create or alter this shared warehouse.
CREATE DATABASE IF NOT EXISTS F1_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS F1_ANALYTICS.RAW;
CREATE SCHEMA IF NOT EXISTS F1_ANALYTICS.STAGING;
CREATE SCHEMA IF NOT EXISTS F1_ANALYTICS.INTERMEDIATE;
CREATE SCHEMA IF NOT EXISTS F1_ANALYTICS.MARTS;
CREATE SCHEMA IF NOT EXISTS F1_ANALYTICS.AUDIT;
