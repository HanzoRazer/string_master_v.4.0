-- scripts/reaper_sg_setup_doctor.lua
-- Episode 12: FTUE / Setup Doctor (guided first run)
--
-- What it does:
--  1) Verifies script directory + dkjson.lua presence/load
--  2) Checks sg-agentd reachable (GET /status) on http://127.0.0.1:8420
--  3) Ensures SG_COMP / SG_BASS tracks exist (creates if missing)
--  4) Checks chord markers (and time selection chord markers) exist
--  5) Checks ExtState last_clip_id presence (regen/feedback readiness)
--  6) Reports project meter at cursor + warns if unknown/missing
--  7) Prints next steps (Generate → PASS/STRUGGLE FAST → Timeline/Trend)
--
-- No server changes required.

local API_BASE = "http://127.0.0.1:8420"
local EXT_SECTION = "SG_AGENTD"
local EXT_LAST_CLIP = "last_clip_id"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

-- Pretty status tags (ASCII-safe)
local function ok(s)  msg("SG OK:  " .. s) end
local function warn(s) msg("SG WARN:" .. s) end
local function err(s) msg("SG ERR:" .. s) end

-- ---------------------------------------------------------------------------
-- Script directory + dkjson load
-- ---------------------------------------------------------------------------
local function get_script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  local dir = p:match("(.*/)")
          or p:match("(.+\\)")
          or ""
  return dir
end

local function file_exists(path)
  local f = io.open(path, "rb")
  if f then f:close(); return true end
  return false
end

local function try_load_dkjson(script_dir)
  local path = script_dir .. "dkjson.lua"
  if not file_exists(path) then return nil, "dkjson.lua not found: " .. path end
  local ok_load, lib = pcall(dofile, path)
  if not ok_load then return nil, "dkjson.lua failed to load: " .. tostring(lib) end
  return lib, nil
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
  if not code then
    -- couldn't parse code; return raw
    return out, nil, nil
  end
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
-- Time selection + chord marker check
-- ---------------------------------------------------------------------------
local function get_time_selection()
  local s, e = reaper.GetSet_LoopTimeRange(false, false, 0, 0, false)
  if s and e and (e - s) > 0.000001 then return s, e, true end
  return 0.0, 0.0, false
end

local function count_markers_in_range(sel_only)
  local sel_s, sel_e, has_sel = get_time_selection()
  local _, num_markers, num_regions = reaper.CountProjectMarkers(0)
  local total = (num_markers or 0) + (num_regions or 0)

  local count = 0
  local examples = {}

  for idx = 0, total-1 do
    local retval, isrgn, pos, rgnend, name = reaper.EnumProjectMarkers(idx)
    if retval and not isrgn then
      local in_range = true
      if sel_only and has_sel then
        in_range = (pos >= sel_s and pos <= sel_e)
      elseif sel_only and not has_sel then
        in_range = false
      end

      if in_range then
        if name and name ~= "" then
          count = count + 1
          if #examples < 5 then
            examples[#examples+1] = name
          end
        end
      end
    end
  end

  return count, has_sel, examples
end

-- ---------------------------------------------------------------------------
-- Meter check at cursor
-- ---------------------------------------------------------------------------
local function get_time_sig_at_time(time)
  local ok1, retval, num, denom = pcall(reaper.TimeMap2_GetTimeSigAtTime, 0, time)
  if ok1 and retval ~= nil then
    num = tonumber(num) or 4
    denom = tonumber(denom) or 4
    if num < 1 then num = 4 end
    if denom < 1 then denom = 4 end
    return num, denom
  end
  local ok2, num2, denom2 = pcall(reaper.GetProjectTimeSignature2, 0)
  if ok2 and num2 ~= nil then
    num2 = tonumber(num2) or 4
    denom2 = tonumber(denom2) or 4
    if num2 < 1 then num2 = 4 end
    if denom2 < 1 then denom2 = 4 end
    return num2, denom2
  end
  return 4, 4
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Setup Doctor (Episode 12 FTUE)")
msg("============================================================")

local script_dir = get_script_dir()
ok("Script dir: " .. (script_dir ~= "" and script_dir or "(unknown)"))

-- 1) dkjson
local json, json_err = try_load_dkjson(script_dir)
if json then
  ok("dkjson.lua: present + loadable")
else
  err("dkjson.lua: " .. tostring(json_err))
  msg("      Fix: put dkjson.lua in the same folder as this script.")
end

-- 2) Server status
do
  local body, code, e = get_url(API_BASE .. "/status", 6000)
  if not body then
    err("Server: unreachable (" .. tostring(e) .. ")")
    msg("      Fix: start sg-agentd: uvicorn sg_agentd.main:app --host 127.0.0.1 --port 8420")
  else
    if code == 200 then
      ok("Server: reachable (GET /status 200)")
    elseif code then
      warn("Server: responded HTTP " .. tostring(code))
      msg("      Body: " .. tostring(body))
    else
      warn("Server: response received, but HTTP code parse failed")
      msg("      Body: " .. tostring(body))
    end
  end
end

-- 3) Tracks
do
  local _, created_comp = get_or_create_track("SG_COMP")
  local _, created_bass = get_or_create_track("SG_BASS")
  if created_comp then ok("Track created: SG_COMP") else ok("Track exists: SG_COMP") end
  if created_bass then ok("Track created: SG_BASS") else ok("Track exists: SG_BASS") end
end

-- 4) Markers (time selection and full project)
do
  local sel_count, has_sel, sel_examples = count_markers_in_range(true)
  local all_count, _, all_examples = count_markers_in_range(false)

  if has_sel then
    if sel_count > 0 then
      ok("Chord markers in time selection: " .. tostring(sel_count) .. " (e.g., " .. table.concat(sel_examples, ", ") .. ")")
    else
      warn("Time selection active but has 0 markers")
      msg("      Fix: add chord markers (Dm7, G7, Cmaj7...) within the selection, or clear time selection.")
    end
  else
    ok("Time selection: none")
  end

  if all_count > 0 then
    ok("Chord markers in project: " .. tostring(all_count) .. " (e.g., " .. table.concat(all_examples, ", ") .. ")")
  else
    err("Chord markers in project: 0")
    msg("      Fix: create markers named like chords at bar lines: Dm7, G7, Cmaj7 ...")
  end
end

-- 5) ExtState chain readiness
do
  local last_clip = reaper.GetExtState(EXT_SECTION, EXT_LAST_CLIP)
  if last_clip and last_clip ~= "" then
    ok("ExtState last_clip_id: " .. tostring(last_clip) .. " (regen/feedback ready)")
  else
    warn("ExtState last_clip_id: missing")
    msg("      Expected on first run. Run Generate once to establish the chain.")
  end
end

-- 6) Meter check
do
  local t = reaper.GetCursorPosition()
  local num, denom = get_time_sig_at_time(t)
  ok("Project meter @ cursor: " .. tostring(num) .. "/" .. tostring(denom))
  if denom ~= 2 and denom ~= 4 and denom ~= 8 and denom ~= 16 then
    warn("Unusual denominator detected; bar alignment might be odd depending on project map")
  end
end

-- Footer: Next steps (guided)
msg("------------------------------------------------------------")
msg("NEXT STEPS (first run):")
msg("  1) Start server if needed:")
msg("     uvicorn sg_agentd.main:app --host 127.0.0.1 --port 8420")
msg("  2) Create chord markers at bar lines (examples): Dm7, G7, Cmaj7")
msg("  3) Run: SG Generate (queued next bar)")
msg("  4) Practice, then run FAST scripts:")
msg("     - PASS+REGEN  (one key)")
msg("     - STRUGGLE+REGEN (one key)")
msg("  5) Optional: run timeline/trend scripts to inspect session history")
msg("------------------------------------------------------------")
msg("Setup Doctor complete.")
msg("============================================================")

reaper.UpdateArrange()
