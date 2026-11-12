# Trace: django__django-16527, seed 0, fresh against flat

Selection rule (Amendment 3): the lowest-index held-out task for which, in seed 0, the fresh arm retained a stale test record at a compaction and fresh and flat differ in outcome. The task is the 24th in manifests/heldout.txt. Action strings for both runs are in logs/actions/main_s0_fresh.jsonl.gz and logs/actions/main_s0_flat.jsonl.gz.

Both arms make the same sed edit at step 3. Fresh spends steps 4 to 39 seeking a test runner (pytest, manage.py test, runtests.py), finds none that works, edits the module again at step 40, and at step 42 overwrites it with a heredoc holding a placeholder comment, so every later test runs against a broken file. Its third and fourth compactions, after 56 and 67 steps, each count 11 stale test steps. It edits a settings file until the 80-step cap and does not resolve the task. Flat also finds no runner but submits at step 53 a 549-character patch that resolves the task.

What the trace shows: stale test records were present in the fresh arm's memory at compaction. What it does not show: the model reading or acting on the freshness tag. Nothing in the action strings refers to the tags, so we cannot attribute the overwrite at step 42 to the tag.
