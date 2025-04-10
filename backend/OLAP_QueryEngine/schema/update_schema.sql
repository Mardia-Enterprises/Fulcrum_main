-- Update the team_projects table to add text_ids column for storing multiple text_id references
-- This allows us to store both team chunk and project chunk text IDs in one row

-- Check if the column already exists first to avoid errors
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'team_projects' AND column_name = 'text_ids') THEN
        ALTER TABLE team_projects ADD COLUMN text_ids uuid[];
        
        -- Log the migration
        INSERT INTO schema_migrations (version, name, applied_at)
        VALUES ('20250401001', 'Add text_ids to team_projects', CURRENT_TIMESTAMP);
        
        RAISE NOTICE 'Added text_ids column to team_projects table';
    ELSE
        RAISE NOTICE 'text_ids column already exists in team_projects table';
    END IF;
END $$;

-- Update existing entries to populate text_ids from text_id
-- Only run this if needed and if you have existing data
/*
UPDATE team_projects
SET text_ids = ARRAY[text_id]
WHERE text_ids IS NULL OR array_length(text_ids, 1) = 0;
*/

-- Explain the schema update
COMMENT ON COLUMN team_projects.text_ids IS 'Array of UUID references to text_id values in sharded_documents, storing both team chunk and project chunk IDs'; 