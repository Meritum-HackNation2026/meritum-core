-- Undoes migrations/0001_corpus_ready.sql: drops only the corpus_ready tables.
-- Run by hand (psql -f) as the schema owner; corpus.* is untouched.
DROP TABLE IF EXISTS corpus_ready.gold_chunks;
DROP TABLE IF EXISTS corpus_ready.silver_documents;
DROP TABLE IF EXISTS corpus_ready.builds;
DROP TABLE IF EXISTS corpus_ready.schema_migrations;
