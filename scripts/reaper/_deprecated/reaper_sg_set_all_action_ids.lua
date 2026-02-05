-- scripts/reaper_sg_set_all_action_ids.lua
-- One-time, zero-prompt setter for ALL Smart Guitar action IDs.
--
-- What it sets (ExtState):
--   SG_AGENTD/action_generate        = Generate action
--   SG_AGENTD/action_pass_regen      = PASS+REGEN action
--   SG_AGENTD/action_struggle_regen  = STRUGGLE+REGEN action
--   SG_AGENTD/action_timeline        = Timeline action
--   SG_AGENTD/action_trend           = Trend action
--
-- How to use:
--   1) Open Reaper Actions list.
--   2) Find each action (Generate, PASS+REGEN, STRUGGLE+REGEN, Timeline, Trend).
--   3) Right-click each action -> Copy selected action command ID.
--   4) Paste them below into the corresponding *_ID variables.
--   5) Run this script once.
--
-- After running, the SG Panel buttons will work.

local EXT_SECTION = "SG_AGENTD"

local K_GEN   = "action_generate"
local K_PASS  = "action_pass_regen"
local K_STRUG = "action_struggle_regen"
local K_TLINE = "action_timeline"
local K_TREND = "action_trend"

-- ============================================================
-- EDIT THESE LINES (paste your command IDs exactly)
-- Examples look like: _RS1234567890abcdef1234567890abcdef
-- Leave blank ("") to skip setting that action.
-- ============================================================
local GEN_ID   = "_RS_PASTE_GENERATE_ID_HERE"
local PASS_ID  = "_RS_PASTE_PASS_REGEN_ID_HERE"
local STRUG_ID = "_RS_PASTE_STRUGGLE_REGEN_ID_HERE"
local TLINE_ID = "_RS_PASTE_TIMELINE_ID_HERE"
local TREND_ID = "_RS_PASTE_TREND_ID_HERE"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local function trim(s)
  return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", ""))
end

local function resolve_named_command(cmd_id_str)
  cmd_id_str = trim(cmd_id_str or "")
  if cmd_id_str == "" then return nil end
  local num = reaper.NamedCommandLookup(cmd_id_str)
  if not num or num == 0 then return nil end
  return num
end

local function set_ext(key, val)
  reaper.SetExtState(EXT_SECTION, key, tostring(val or ""), true) -- persist=true
end

local function get_ext(key)
  local v = reaper.GetExtState(EXT_SECTION, key)
  return trim(v)
end

local function has_placeholder(s)
  s = tostring(s or "")
  return s:find("PASTE_", 1, true) ~= nil
end

local function try_set(label, key, id)
  id = trim(id)
  if id == "" then
    msg("  " .. label .. ": skipped (blank)")
    return true
  end
  if has_placeholder(id) then
    msg("  " .. label .. ": placeholder not replaced!")
    return false
  end
  local num = resolve_named_command(id)
  if not num then
    msg("  " .. label .. ": INVALID (does not resolve): " .. id)
    return false
  end
  set_ext(key, id)
  msg("  " .. label .. ": OK -> " .. id .. " (cmd#" .. tostring(num) .. ")")
  return true
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Set ALL Action IDs (Zero-prompt)")
msg("============================================================")

local all_ok = true

all_ok = try_set("Generate", K_GEN, GEN_ID) and all_ok
all_ok = try_set("PASS+REGEN", K_PASS, PASS_ID) and all_ok
all_ok = try_set("STRUGGLE+REGEN", K_STRUG, STRUG_ID) and all_ok
all_ok = try_set("Timeline", K_TLINE, TLINE_ID) and all_ok
all_ok = try_set("Trend", K_TREND, TREND_ID) and all_ok

msg("------------------------------------------------------------")
if all_ok then
  msg("SG OK: All action IDs saved to ExtState.")
  msg("")
  msg("Next step:")
  msg("  - Run: reaper_sg_panel.lua")
  msg("    The panel buttons will now trigger these actions.")
else
  msg("SG WARN: Some action IDs could not be set.")
  msg("")
  msg("Fix:")
  msg("  1) Edit this script")
  msg("  2) Replace placeholder text with real _RS... IDs")
  msg("  3) Run again")
end
msg("============================================================")
