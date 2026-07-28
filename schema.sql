-- Run this in your Supabase project's SQL Editor (Dashboard -> SQL Editor -> New Query)
-- This creates the tasks table used by task_manager.py
--
-- This version is SAFE TO RUN MULTIPLE TIMES. If the table or policy
-- already exist from a previous run, it will not throw an error.

create table if not exists tasks (
    id uuid primary key default gen_random_uuid(),
    text text not null,
    completed boolean not null default false,
    priority text not null default 'Medium' check (priority in ('Low', 'Medium', 'High')),
    category text not null default 'General',
    due_date date,
    created_at timestamptz not null default now(),
    completed_at timestamptz
);

-- Index to speed up common filters
create index if not exists idx_tasks_completed on tasks (completed);
create index if not exists idx_tasks_priority on tasks (priority);
create index if not exists idx_tasks_category on tasks (category);

-- Enable Row Level Security. For a single-user personal app we allow
-- full access via the anon key. If you add multi-user auth later,
-- replace this policy with per-user rules keyed on auth.uid().
alter table tasks enable row level security;

-- Drop the policy first if it already exists, then recreate it.
-- This makes the script safe to re-run without a "policy already exists" error.
drop policy if exists "Allow all access for anon key" on tasks;

create policy "Allow all access for anon key"
    on tasks
    for all
    using (true)
    with check (true);