-- 1. Enable necessary extensions (if not already enabled)
create extension if not exists pgcrypto;  -- for gen_random_uuid()
create extension if not exists vector;    -- for vector embeddings

--------------------------------------------------------------------------------
-- 2. employees (renamed from employees)
--------------------------------------------------------------------------------
create table if not exists public.employee(
    id uuid not null default gen_random_uuid() primary key,
    name text,
    embedding vector,
    role text
);

--------------------------------------------------------------------------------
-- 3. Projects
--------------------------------------------------------------------------------
create table if not exists public.projects(
    id uuid not null default gen_random_uuid() primary key,
    name text,
    location text
);

--------------------------------------------------------------------------------
-- 4. Documents
--------------------------------------------------------------------------------
create table if not exists public.documents (
    id uuid not null default gen_random_uuid() primary key,
    document_link text,
    pdf_name text
);

--------------------------------------------------------------------------------
-- 5. ShardedDocuments
--------------------------------------------------------------------------------
create table if not exists public.sharded_documents (
    text_id uuid not null default gen_random_uuid() primary key,
    document_id uuid references public.documents (id) on delete cascade,
    text text,
    embedding vector
);

--------------------------------------------------------------------------------
-- 6. employeeProjects (renamed from employee_projects)
--------------------------------------------------------------------------------
create table if not exists public.employee_projects (
    employee_id uuid not null references public.employee (id) on delete cascade,
    project_id  uuid not null references public.projects (id) on delete cascade,
    text_id    uuid not null references public.sharded_documents (text_id) on delete cascade, --list of text_id from sharded_documents
    role        text,
    primary key (employee_id, project_id)
);

--------------------------------------------------------------------------------
-- 7. employeeDocuments (renamed from employee_documents)
--------------------------------------------------------------------------------
create table if not exists public.employee_documents (
    employee_id uuid not null references public.employee (id) on delete cascade,
    text_id uuid not null references public.sharded_documents (text_id) on delete cascade, --list of text_id from sharded_documents
    primary key (employee_id, text_id)
);

--------------------------------------------------------------------------------
-- 8. ProjectDocuments
--------------------------------------------------------------------------------
create table if not exists public.project_documents (
    project_id uuid not null references public.projects (id) on delete cascade,
    text_id    uuid not null references public.sharded_documents (text_id) on delete cascade, --list of text_id from sharded_documents
    primary key (project_id, text_id)
);
