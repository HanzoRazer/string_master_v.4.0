-- scripts/reaper/reaper_sg_setup_doctor_autorun.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Episode 12.1: Setup Doctor + Autorun (guided first run)
--
-- Usage:
--  - First run: prompts for action command IDs (e.g. _RSxxxxxx) and saves to ExtState
--  - Subsequent runs: can auto-run selected steps with zero prompts
--
-- Notes:
--  - Uses Reaper Actions by command ID string:
--      reaper.NamedCommandLookup("_RS...") -> numeric command id
--  - Requires json.lua in same folder (only for other scripts; Doctor itself doesn't need json decode)
--  - Server check uses curl GET /status at API_BASE

local API_BASE = "http://127.0.0.1:8420"
local EXT_SECTION = "SG_AGENTD"

-- ExtState keys for action IDs
local K_GEN   = "action_generate"
local K_PASS  = "action_pass_regen"
local K_STRUG = "action_struggle_regen"
local K_TLINE = "action_timeline"
local K_TREND = "action_trend"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function ok(s)  msg("SG OK:  " .. s) end
local function warn(s) msg("SG WARN:" .. s) end
local function err(s) msg("SG ERR:" .. s) end

local function trim(s) return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", "")) end

-- ---------------------------------------------------------------------------
-- Script directory + json presence check (load not required here)
-- ---------------------------------------------------------------------------
local function get_script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  return p:match("(.*/)") or p:match("(.+\\)") or ""
end

local function file_exists(path)
  local f = io.open(path, "rb")
  if f then f:close(); return true end
  return false
end

-- ---------------------------------------------------------------------------
-- HTTP GET via curl, capture status code
-- ---------------------------------------------------------------------------
local function get_url(url, timeout_ms)
  local cmd = 'curl -s -X GET -w "\\n%{http_code}" "' .. url .. '"'
  local rv, out = reaper.ExecProcess(cmd, timeout_ms or 8000)
  if rv ~= 0 then return nil, nil, "curl failed (rv="..tostring(rv)..")" end
  if not out or out == "" then return nil, nil, "empty response" end
  local body, code = out:match("^(.*)\n(%d%d%d)$")
  if not code then body, code = out:match("^(.*)\r\n(%d%d%d)$") end
  if not code then return out, nil, nil end
  return body, tonumber(code), nil
end

-- ---------------------------------------------------------------------------
-- Track utilities
-- ---------------------------------------------------------------------------
local function get_or_create_track(name)
  for i = 0, reaper.CountTracks(0)-1 do
    local tr = reaper.GetTrack(0, i)
    local _, tr_name = reaper.GetTrackName(tr)
    if tr_name == name then return tr, false end
  end
  reaper.InsertTrackAtIndex(reaper.CountTracks(0), true)
  local tr = reaper.GetTrack(0, reaper.CountTracks(0)-1)
  reaper.GetSetMediaTrackInfo_String(tr, "P_NAME", name, true)
  return tr, true
end

-- ---------------------------------------------------------------------------
-- Marker check
-- ---------------------------------------------------------------------------
local function count_all_markers()
  local _, num_markers, num_regions = reaper.CountProjectMarkers(0)
  local total = (num_markers or 0) + (num_regions or 0)
  local count = 0
  local examples = {}
  for idx = 0, total-1 do
    local retval, isrgn, pos, rgnend, name = reaper.EnumProjectMarkers(idx)
    if retval and not isrgn and name and name ~= "" then
      count = count + 1
      if #examples < 5 then examples[#examples+1] = name end
    end
  end
  return count, examples
end

-- ---------------------------------------------------------------------------
-- Action ID helpers
-- ---------------------------------------------------------------------------
local function get_saved_action(key)
  local v = reaper.GetExtState(EXT_SECTION, key)
  v = trim(v)
  if v == "" then return nil end
  return v
end

local function save_action(key, val)
  reaper.SetExtState(EXT_SECTION, key, trim(val or ""), true)
end

local function resolve_named_command(cmd_id_str)
  cmd_id_str = trim(cmd_id_str or "")
  if cmd_id_str == "" then return nil end
  local num = reaper.NamedCommandLookup(cmd_id_str)
  if not num or num == 0 then return nil end
  return num
end

local function run_action(cmd_id_str, label, dry_run)
  local num = resolve_named_command(cmd_id_str)
  if not num then
    err(label .. ": invalid/missing action id: " .. tostring(cmd_id_str))
    return false
  end
  if dry_run then
    ok(label .. ": (dry-run) would run " .. tostring(cmd_id_str))
    return true
  end
  reaper.Main_OnCommand(num, 0)
  ok(label .. ": ran " .. tostring(cmd_id_str))
  return true
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Setup Doctor AUTORUN (Episode 12.1)")
msg("============================================================")

-- Prompt mode
local defaults = "0,1,0"
local ok_in, csv = reaper.GetUserInputs(
  "SG Setup Doctor Autorun",
  3,
  "configure_action_ids(0/1),autorun(0/1),dry_run(0/1)",
  defaults
)
if not ok_in then return end

local cfg_s, autorun_s, dry_s = csv:match("([^,]*),([^,]*),([^,]*)")
local configure = (tonumber(trim(cfg_s)) or 0) == 1
local autorun = (tonumber(trim(autorun_s)) or 0) == 1
local dry_run = (tonumber(trim(dry_s)) or 0) == 1

-- 1) Basic checks
local script_dir = get_script_dir()
ok("Script dir: " .. (script_dir ~= "" and script_dir or "(unknown)"))

local jf = script_dir .. "json.lua"
if file_exists(jf) then
  ok("json.lua: present")
else
  warn("json.lua: missing (recommended for timeline/trend scripts)")
  msg("      Fix: put json.lua in the same folder as scripts.")
end

do
  local body, code, e = get_url(API_BASE .. "/status", 6000)
  if not body then
    err("Server: unreachable (" .. tostring(e) .. ")")
    msg("      Fix: start sg-agentd: uvicorn sg_agentd.main:app --host 127.0.0.1 --port 8420")
  else
    if code == 200 then ok("Server: reachable (GET /status 200)") else warn("Server: HTTP " .. tostring(code or "?")) end
  end
end

do
  local _, c1 = get_or_create_track("SG_COMP")
  local _, c2 = get_or_create_track("SG_BASS")
  if c1 then ok("Track created: SG_COMP") else ok("Track exists: SG_COMP") end
  if c2 then ok("Track created: SG_BASS") else ok("Track exists: SG_BASS") end
end

do
  local mcount, ex = count_all_markers()
  if mcount > 0 then
    ok("Markers: " .. tostring(mcount) .. " (e.g., " .. table.concat(ex, ", ") .. ")")
  else
    warn("Markers: 0 (create chord markers like Dm7, G7, Cmaj7)")
  end
end

-- 2) Configure action IDs (one-time)
if configure then
  msg("------------------------------------------------------------")
  msg("Enter Reaper Action Command IDs (e.g., _RSxxxxxxxx). Leave blank to keep current.")
  local cur_gen   = get_saved_action(K_GEN)   or ""
  local cur_pass  = get_saved_action(K_PASS)  or ""
  local cur_strug = get_saved_action(K_STRUG) or ""
  local cur_tline = get_saved_action(K_TLINE) or ""
  local cur_trend = get_saved_action(K_TREND) or ""

  local defaults_ids = table.concat({cur_gen, cur_pass, cur_strug, cur_tline, cur_trend}, ",")
  local ok_ids, ids_csv = reaper.GetUserInputs(
    "SG Autorun Action IDs",
    5,
    "Generate,Pass+Regen,Struggle+Regen,Timeline,TrendSummary",
    defaults_ids
  )
  if ok_ids then
    local a,b,c,d,e = ids_csv:match("([^,]*),([^,]*),([^,]*),([^,]*),([^,]*)")
    if trim(a) ~= "" then save_action(K_GEN, a) end
    if trim(b) ~= "" then save_action(K_PASS, b) end
    if trim(c) ~= "" then save_action(K_STRUG, c) end
    if trim(d) ~= "" then save_action(K_TLINE, d) end
    if trim(e) ~= "" then save_action(K_TREND, e) end
    ok("Saved action IDs to ExtState (SG_AGENTD/*)")
  else
    warn("Action ID configuration cancelled")
  end
end

-- 3) Autorun sequence (optional)
if autorun then
  msg("------------------------------------------------------------")
  msg("AUTORUN SEQUENCE" .. (dry_run and " (dry-run)" or "") .. ":")
  local gen   = get_saved_action(K_GEN)
  local pass  = get_saved_action(K_PASS)
  local strug = get_saved_action(K_STRUG)
  local tline = get_saved_action(K_TLINE)
  local trend = get_saved_action(K_TREND)

  -- Minimal default: just run Generate if present
  if gen and gen ~= "" then
    run_action(gen, "Generate", dry_run)
  else
    warn("Generate action not configured; skipping")
  end

  -- Ask which follow-up to run (PASS or STRUGGLE) if configured
  local follow = 0
  if (pass and pass ~= "") or (strug and strug ~= "") then
    local ok_f, fcsv = reaper.GetUserInputs("Autorun follow-up", 1, "follow_up: 0=none,1=PASS,2=STRUGGLE", "0")
    if ok_f then follow = tonumber(trim(fcsv)) or 0 end
  end

  if follow == 1 then
    if pass and pass ~= "" then run_action(pass, "PASS+REGEN", dry_run) else warn("PASS action not configured") end
  elseif follow == 2 then
    if strug and strug ~= "" then run_action(strug, "STRUGGLE+REGEN", dry_run) else warn("STRUGGLE action not configured") end
  else
    ok("Follow-up: none")
  end

  -- Optional: timeline + trend
  if tline and tline ~= "" then run_action(tline, "Timeline", dry_run) else warn("Timeline action not configured; skipping") end
  if trend and trend ~= "" then run_action(trend, "Trend Summary", dry_run) else warn("Trend action not configured; skipping") end
end

msg("------------------------------------------------------------")
msg("NEXT STEPS:")
msg("  - If Generate/FAST actions are missing, run configure_action_ids=1 once.")
msg("  - Typical flow: autorun=1, choose PASS/STRUGGLE follow-up.")
msg("  - Bind this script to a hotkey for one-button setup + smoke test.")
msg("============================================================")

reaper.UpdateArrange()
