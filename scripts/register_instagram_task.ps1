# Registers TrendRadarWeeklyContent: a local Windows Scheduled Task, firing EVERY
# 2 DAYS (cadence changed from weekly 2026-08-28, founder decision -- task name kept
# for continuity), that runs scripts/run_weekly_routine.py, which wraps the headless
# Claude Code CLI invocation of the instagram-weekly-routine skill with an
# output-count guard (a "successful" run that queues nothing is a failure, exit 2).
#
# ACTION CHANGE 2026-08-28: the Action now invokes run_weekly_routine.py instead of
# claude.exe directly -- the headless prompt and allowed-tools list live ONLY in that
# script now (single source of truth; this file no longer embeds its own copy).
#
# Why a local Task, not a cloud routine (see 2026-08-17 build session):
# - The account's Canva connection is a locally-installed Claude Code *plugin* MCP
#   connector, not one of the claude.ai connectors (Gmail/Todoist/Calendar/Drive)
#   available to cloud routines (RemoteTrigger) as of this writing.
# - The weekly routine reads trend_predictor's live SQLite DB (data/trend.db)
#   read-only and locally — a cloud checkout would only see whatever's committed to
#   git, not the live DB.
# Both are satisfied by a local scheduled task, matching the existing
# TrendPredictorDaily / TrendPredictorBackup pattern in this same script family.
#
# Re-run this script only when the SCHEDULE or the Action target changes.
# Allowed-tools / prompt changes no longer need a re-registration -- they live in
# scripts/run_weekly_routine.py, which the task invokes fresh each run.
#
# Caveat (same as the existing TrendPredictorDaily/Backup tasks): this fires under the
# logged-on user session (LogonType Interactive), so the machine needs to be powered on
# and logged in around the scheduled time -- it won't fire from a fully signed-out state.
# WakeToRun handles sleep, not signed-out/powered-off.
#
# Path note (2026-08-25, instagram_sub_project extraction): trend_predictor was
# migrated from C:\Users\2026\Documents\trend_predictor into
# C:\Users\2026\Documents\income-engine\trend_predictor as part of the portfolio
# migration -- the old path is stale and its data is no longer live (see
# income-engine/docs/registry/trend_predictor.md's environment-reconciliation entry,
# 2026-08-25). $trendPredictorDir below is updated to the current path; re-verify this
# if trend_predictor ever moves again.

$py = (Get-Command py).Source
$contentRepo = "C:\Users\2026\Documents\trend-signals-social"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -WakeToRun

# The headless prompt, allowed-tools list (including both Canva connector
# namespaces -- the 2026-08-25 allowlist fix) and --add-dir for the
# trend_predictor checkout all live in scripts/run_weekly_routine.py's
# CLAUDE_ARGS now. Edit them THERE; this script only wires the scheduler.
$action = New-ScheduledTaskAction -Execute $py -Argument "-3.12 scripts\run_weekly_routine.py" -WorkingDirectory $contentRepo

# Every 2 days at 18:00 local (evening IST), anchored on the next Sunday so the
# cycle runs Sun/Tue/Thu/Sat/... -- each run generates the NEXT 2 days' posts
# (see instagram-weekly-routine SKILL.md's horizon note). Anchor is computed as
# a FUTURE start boundary so registration never causes an immediate catch-up
# fire (-StartWhenAvailable would otherwise run a past-dated boundary at once).
$daysUntilSunday = (7 - [int](Get-Date).DayOfWeek) % 7
$anchor = (Get-Date -Hour 18 -Minute 0 -Second 0).AddDays($daysUntilSunday)
if ($anchor -le (Get-Date)) { $anchor = $anchor.AddDays(7) }
$trigger = New-ScheduledTaskTrigger -Daily -DaysInterval 2 -At $anchor
Register-ScheduledTask -TaskName "TrendRadarWeeklyContent" -Action $action -Trigger $trigger -Settings $settings -Force
Write-Host "Registered TrendRadarWeeklyContent (every 2 days at 18:00, first fire $anchor, catch-up enabled)."
Write-Host "Task name kept for continuity; cadence is every-2-days since 2026-08-28."
Write-Host "Logs: check trend-signals-social's git log for queue commits, and Windows Task Scheduler's task history for run status/errors (LastTaskResult maps to run_weekly_routine.py's exit codes)."
