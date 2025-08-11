-- Product Catalog Database Initialization
-- This script creates the initial database structure for the Product Catalog Service

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create indexes for full-text search (if needed)
-- Note: These would normally be handled by migrations in production

-- Performance optimization indexes
-- These will be created automatically by SQLAlchemy, but we can add custom ones here

-- Add any custom database functions or triggers here
-- For example, a trigger to update search_vector when product name/description changes

-- Example trigger function for maintaining search vectors
CREATE OR REPLACE FUNCTION update_product_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector = LOWER(COALESCE(NEW.name, '') || ' ' || COALESCE(NEW.description, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: The actual tables will be created by SQLAlchemy's Base.metadata.create_all()
-- This is just for any custom database setup that can't be handled by the ORM