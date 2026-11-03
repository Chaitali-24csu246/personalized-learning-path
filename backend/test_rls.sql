\set ON_ERROR_STOP on
begin;
insert into auth.users values('00000000-0000-0000-0000-000000000001'),('00000000-0000-0000-0000-000000000002'),('00000000-0000-0000-0000-000000000003');
insert into public.profiles values('00000000-0000-0000-0000-000000000001','student_a','Student A','student'),('00000000-0000-0000-0000-000000000002','student_b','Student B','student'),('00000000-0000-0000-0000-000000000003','admin','Admin','admin');
set local role authenticated;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000001',true);
select public.save_my_progress(0,'{"states":{},"name":"A"}');
insert into public.topic_requests(user_id,subject,topic) values(auth.uid(),'Python','Async');
do $$ begin
 if (select count(*) from public.profiles)<>1 then raise exception 'Profile isolation failed';end if;
 begin update public.profiles set role='admin' where id=auth.uid();raise exception 'Role escalation was permitted';exception when insufficient_privilege then null;end;
 begin perform public.save_catalog(0,'{"courses":[],"topicOverrides":[],"activities":[],"removedTopics":[]}');raise exception 'Student catalog write permitted';exception when raise_exception then if sqlerrm<>'admin_required' then raise;end if;end;
 begin perform public.save_my_progress(0,'{"states":{}}');raise exception 'Stale save accepted';exception when raise_exception then if sqlerrm<>'progress_conflict' then raise;end if;end;
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000002',true);
do $$ begin
 if (select count(*) from public.student_progress)<>0 then raise exception 'Cross-student progress visible';end if;
 if (select count(*) from public.topic_requests)<>0 then raise exception 'Cross-student requests visible';end if;
 begin insert into public.topic_requests(user_id,subject,topic) values('00000000-0000-0000-0000-000000000001','Python','Fake');raise exception 'Cross-student request accepted';exception when insufficient_privilege then null;end;
end $$;
select set_config('request.jwt.claim.sub','00000000-0000-0000-0000-000000000003',true);
select public.save_catalog(0,'{"courses":[],"topicOverrides":[],"activities":[],"removedTopics":[]}');
do $$ begin
 if (select count(*) from public.topic_requests)<>1 then raise exception 'Admin request visibility failed';end if;
 if (select count(*) from public.student_progress)<>0 then raise exception 'Admin can unexpectedly read private progress';end if;
end $$;
reset role;
set local role anon;
do $$ begin
 begin perform * from public.profiles;raise exception 'Anonymous profile access permitted';exception when insufficient_privilege then null;end;
 begin perform public.save_my_progress(0,'{"states":{}}');raise exception 'Anonymous write permitted';exception when insufficient_privilege then null;end;
end $$;
rollback;
