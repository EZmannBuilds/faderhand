You are running a benchmark of a music-production agent skill. Act exactly as an agent that has this skill installed and a user who gave you the tasks below.

SKILL UNDER TEST: {SKILL_DESC}
Read the skill's entry file first and follow its instructions and routing as it tells you, reading the parts it points you to when a task needs them. Do not read anything outside: the skill folder(s) named above, the eval pack at "{PACK}" (TASKS.md and fixtures/), and your output folder "{OUT}".

Then do every task in "{PACK}/TASKS.md" (T01–T10), following its runner rules. The user has locked the intent for each brief ("just make it, no questions"), so don't ask anything; where the skill says to plan, explore alternatives or check your own work, do that yourself within this run. Write all outputs to "{OUT}". Python with mido is available via: uv run -q --no-project --with mido python <script>. Keep scripts in "{OUT}/scripts/".

When done, write "{OUT}/RUN_LOG.md": which skill files you read (paths), for each task what you produced and how you checked it, and anything you could not do. Reply with a short summary only.
