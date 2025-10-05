-- Create the notes table
create table if not exists public.notes (
  id uuid default gen_random_uuid() primary key,
  title text not null,
  content text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable Row Level Security (RLS)
alter table public.notes enable row level security;

-- Create a policy that allows public access to all operations
create policy "Allow public access" on public.notes
  for all
  to public
  using (true)
  with check (true);

-- Create an index for faster queries
create index if not exists notes_created_at_idx on public.notes (created_at desc);

-- Add a trigger to automatically update the updated_at timestamp
create or replace function public.handle_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = timezone('utc'::text, now());
  return new;
end;
$$;

create trigger on_notes_updated
  before update on public.notes
  for each row
  execute function handle_updated_at();