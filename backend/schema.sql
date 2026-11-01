-- Run once in a NEW Supabase project's SQL Editor before provisioning accounts.
begin;
create table public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 username text not null unique check (username ~ '^[a-z][a-z0-9_-]{2,39}$'),
 display_name text not null check (length(display_name) between 1 and 80),
 role text not null default 'student' check (role in ('student','admin'))
);
create table public.student_progress (
 user_id uuid primary key references auth.users(id) on delete cascade,
 payload jsonb not null,
 version bigint not null default 1,
 updated_at timestamptz not null default now(),
 constraint progress_size check (octet_length(payload::text)<2000000)
);
create table public.topic_requests (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 subject text not null check(length(subject) between 1 and 100),
 topic text not null check(length(topic) between 1 and 160),
 details text not null default '' check(length(details)<=2000),
 status text not null default 'submitted' check(status in ('submitted','reviewing','planned','closed')),
 created_at timestamptz not null default now()
);
create table public.course_catalog (
 id integer primary key check(id=1), payload jsonb not null,
 revision bigint not null default 1, updated_at timestamptz not null default now(),
 constraint catalog_size check(octet_length(payload::text)<4000000)
);
create function public.is_admin() returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.profiles where id=(select auth.uid()) and role='admin');
$$;
alter table public.profiles enable row level security;
alter table public.student_progress enable row level security;
alter table public.topic_requests enable row level security;
alter table public.course_catalog enable row level security;
revoke all on public.profiles,public.student_progress,public.topic_requests,public.course_catalog from anon, authenticated;
grant select on public.profiles,public.student_progress,public.course_catalog to authenticated;
grant select,insert on public.topic_requests to authenticated;
grant update(status) on public.topic_requests to authenticated;
create policy profiles_read on public.profiles for select to authenticated using(id=(select auth.uid()) or public.is_admin());
create policy progress_read on public.student_progress for select to authenticated using(user_id=(select auth.uid()));
create policy requests_read on public.topic_requests for select to authenticated using(user_id=(select auth.uid()) or public.is_admin());
create policy requests_create on public.topic_requests for insert to authenticated with check(user_id=(select auth.uid()) and status='submitted');
create policy requests_admin_update on public.topic_requests for update to authenticated using(public.is_admin()) with check(public.is_admin());
create policy catalog_read on public.course_catalog for select to authenticated using(true);
-- No authenticated write policy or grants for roles; users cannot promote themselves.
create function public.save_my_progress(expected_version bigint,new_payload jsonb) returns bigint
language plpgsql security definer set search_path='' as $$
declare uid uuid:=auth.uid(); current_version bigint;
begin
 if uid is null or not exists(select 1 from public.profiles where id=uid) then raise exception 'authentication_required'; end if;
 if jsonb_typeof(new_payload)<>'object' or not (new_payload ? 'states') then raise exception 'invalid_progress'; end if;
 perform pg_advisory_xact_lock(hashtextextended(uid::text,0));
 select version into current_version from public.student_progress where user_id=uid for update;
 if coalesce(current_version,0)<>expected_version then raise exception 'progress_conflict'; end if;
 insert into public.student_progress(user_id,payload,version) values(uid,new_payload,expected_version+1)
 on conflict(user_id) do update set payload=excluded.payload,version=excluded.version,updated_at=now();
 return expected_version+1;
end;$$;
create function public.save_catalog(expected_revision bigint,new_payload jsonb) returns bigint
language plpgsql security definer set search_path='' as $$
declare current_revision bigint;
begin
 if not public.is_admin() then raise exception 'admin_required';end if;
 if jsonb_typeof(new_payload)<>'object' or not (new_payload ?& array['courses','topicOverrides','activities','removedTopics']) or jsonb_typeof(new_payload->'courses')<>'array' or jsonb_typeof(new_payload->'topicOverrides')<>'array' or jsonb_typeof(new_payload->'activities')<>'array' or jsonb_typeof(new_payload->'removedTopics')<>'array' then raise exception 'invalid_catalog';end if;
 perform pg_advisory_xact_lock(91726341);
 select revision into current_revision from public.course_catalog where id=1 for update;
 if coalesce(current_revision,0)<>expected_revision then raise exception 'catalog_conflict_reload';end if;
 insert into public.course_catalog(id,payload,revision) values(1,new_payload,expected_revision+1)
 on conflict(id) do update set payload=excluded.payload,revision=excluded.revision,updated_at=now();
 return expected_revision+1;
end;$$;
revoke all on function public.is_admin(),public.save_my_progress(bigint,jsonb),public.save_catalog(bigint,jsonb) from public,anon;
grant execute on function public.is_admin(),public.save_my_progress(bigint,jsonb),public.save_catalog(bigint,jsonb) to authenticated;
commit;
