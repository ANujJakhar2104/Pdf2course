-- ============================================================
-- PDF to E-Course Learning Platform — Database Schema
-- Target: Supabase Postgres (auth.users already exists via Supabase Auth)
-- ============================================================

-- Documents (uploaded PDFs)
create table if not exists documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    filename text not null,
    storage_path text not null,          -- path in Supabase Storage bucket
    page_count int,
    char_count int,
    status text default 'uploaded',      -- uploaded | extracting | extracted | generating | ready | failed
    created_at timestamptz default now()
);

-- Courses (generated from a document)
create table if not exists courses (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade not null,
    user_id uuid references auth.users(id) on delete cascade not null,
    title text not null,
    description text,
    estimated_time_minutes int,
    difficulty_level text,               -- beginner | intermediate | advanced
    learning_objectives jsonb,           -- array of strings
    prerequisites jsonb,                 -- array of strings
    status text default 'draft',         -- draft | ready
    created_at timestamptz default now()
);

-- Chapters
create table if not exists chapters (
    id uuid primary key default gen_random_uuid(),
    course_id uuid references courses(id) on delete cascade not null,
    title text not null,
    "order" int not null,
    summary text,
    created_at timestamptz default now()
);

-- Lessons (topics/subtopics collapse into lessons w/ ordering)
create table if not exists lessons (
    id uuid primary key default gen_random_uuid(),
    chapter_id uuid references chapters(id) on delete cascade not null,
    title text not null,
    "order" int not null,
    content_markdown text,               -- explanation
    key_takeaways jsonb,                 -- array of strings
    important_notes jsonb,
    real_world_examples jsonb,
    summary text,
    created_at timestamptz default now()
);

-- Progress tracking
create table if not exists lesson_progress (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    lesson_id uuid references lessons(id) on delete cascade not null,
    completed boolean default false,
    completed_at timestamptz,
    time_spent_seconds int default 0,
    unique(user_id, lesson_id)
);

-- Chat history (AI companion, per course)
create table if not exists chat_messages (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    course_id uuid references courses(id) on delete cascade not null,
    role text not null,                  -- user | assistant
    content text not null,
    created_at timestamptz default now()
);

-- Quizzes
create table if not exists quizzes (
    id uuid primary key default gen_random_uuid(),
    chapter_id uuid references chapters(id) on delete cascade not null,
    questions jsonb not null,            -- array of {type, question, options, correct_answer, explanation}
    created_at timestamptz default now()
);

create table if not exists quiz_attempts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) on delete cascade not null,
    quiz_id uuid references quizzes(id) on delete cascade not null,
    answers jsonb not null,
    score numeric,
    attempted_at timestamptz default now()
);

-- Vector store for RAG (pgvector extension needed: create extension if not exists vector;)
create extension if not exists vector;

create table if not exists document_chunks (
    id uuid primary key default gen_random_uuid(),
    document_id uuid references documents(id) on delete cascade not null,
    chunk_index int not null,
    content text not null,
    embedding vector(384)                -- adjust dim to your embedding model
);

-- Helpful indexes
create index if not exists idx_courses_user on courses(user_id);
create index if not exists idx_chapters_course on chapters(course_id);
create index if not exists idx_lessons_chapter on lessons(chapter_id);
create index if not exists idx_progress_user on lesson_progress(user_id);
create index if not exists idx_chunks_document on document_chunks(document_id);

-- Row Level Security (enable + basic policies — tighten later)
alter table documents enable row level security;
alter table courses enable row level security;
alter table lesson_progress enable row level security;
alter table chat_messages enable row level security;
alter table quiz_attempts enable row level security;

create policy "own_documents" on documents for all using (auth.uid() = user_id);
create policy "own_courses" on courses for all using (auth.uid() = user_id);
create policy "own_progress" on lesson_progress for all using (auth.uid() = user_id);
create policy "own_chat" on chat_messages for all using (auth.uid() = user_id);
create policy "own_quiz_attempts" on quiz_attempts for all using (auth.uid() = user_id);
