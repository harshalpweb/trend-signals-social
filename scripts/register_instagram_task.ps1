# Registers TrendRadarWeeklyContent: a weekly local Windows Scheduled Task that runs
# the Claude Code CLI headlessly to generate and queue that week's TrendRadar Instagram
# posts (instagram-weekly-routine skill, in the trend-signals-social repo).
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
# Re-run this script any time the routine's allowed-tools list needs to change.
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

$claude = (Get-Command claude).Source
$contentRepo = "C:\Users\2026\Documents\trend-signals-social"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -WakeToRun

$prompt = @'
Run the instagram-weekly-routine skill (see .claude/skills/instagram-weekly-routine/SKILL.md
in this repo) to generate and queue this week's TrendRadar Instagram posts. Follow that
skill file exactly -- it documents the full sequence: instagram-signals (reads
C:\Users\2026\Documents\income-engine\trend_predictor read-only) -> instagram-caption -> instagram-carousel
(Canva MCP, locked master template DAHSjFtuvnU) -> assemble queue JSON -> git commit and push.
Do not publish anything directly -- that is handled separately by this repo's own hourly
GitHub Actions workflow. If any single post fails after retries, skip only that post (per
the skill's failure-handling section) and continue with the rest of the week rather than
aborting the whole run.
'@

# Scoped to what the routine actually needs -- avoids a blanket bypass-permissions run
# with no one present to approve anything unexpected. The canva:get-design-feedback and
# canva:brand-check plugin skills (called from instagram-carousel) internally use several
# more raw Canva MCP tools than instagram-carousel's own steps do (get-design-pages,
# list-brand-kits, etc) -- rather than enumerate every one and have this silently go stale
# whenever those plugin skills change, allow the whole Canva plugin MCP server. Extend this
# list (and re-run this script) if instagram-weekly-routine starts needing non-Canva tools
# beyond what's listed here.
#
# FIXED 2026-08-25 (trendradar diagnosis): the live 8/23 scheduled run showed every Canva
# MCP call getting denied even with the plugin allowlist -- the runtime call actually goes
# through a different connector, mcp__claude_ai_Canva__*, not mcp__plugin_canva_canva__*.
# Both are now allow-listed. Applying this fix requires re-running this script
# (Register-ScheduledTask -Force is a system-level change) -- that step is
# founder-reserved, not done by this commit. See
# income-engine/docs/registry/instagram_sub_project.md for status.
$allowedTools = @(
    "Bash", "Read", "Write", "Edit", "Glob", "Grep", "Skill",
    "mcp__plugin_canva_canva__*", "mcp__claude_ai_Canva__*"
) -join " "

# instagram-signals reads the trend_predictor checkout, which is outside this task's
# WorkingDirectory (the content repo) -- without --add-dir, Claude Code won't grant tool
# access to it.
$trendPredictorDir = "C:\Users\2026\Documents\income-engine\trend_predictor"

$argList = "-p `"$prompt`" --permission-mode acceptEdits --allowed-tools $allowedTools --add-dir `"$trendPredictorDir`""
$weeklyAction = New-ScheduledTaskAction -Execute $claude -Argument $argList -WorkingDirectory $contentRepo
# Sunday 18:00 local time -- evening IST, ahead of Monday's post slot (see
# instagram-growth/config.yaml posting_time_ist for the actual post-time default).
$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 6:00PM
Register-ScheduledTask -TaskName "TrendRadarWeeklyContent" -Action $weeklyAction -Trigger $weeklyTrigger -Settings $settings -Force
Write-Host "Registered TrendRadarWeeklyContent (weekly Sunday 18:00, catch-up enabled)."
Write-Host "Logs: check trend-signals-social's git log for the weekly queue commit, and Windows Task Scheduler's task history for run status/errors."
