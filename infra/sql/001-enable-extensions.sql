DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_available_extensions
    WHERE name = 'age'
  ) THEN
    CREATE EXTENSION IF NOT EXISTS age;
  ELSE
    RAISE NOTICE 'age extension is not available in this Postgres image';
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM pg_available_extensions
    WHERE name = 'vector'
  ) THEN
    CREATE EXTENSION IF NOT EXISTS vector;
  ELSE
    RAISE NOTICE 'vector extension is not available in this Postgres image';
  END IF;
END$$;
