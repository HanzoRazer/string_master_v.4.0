-- scripts/reaper_sg_set_action_ids_once.lua
-- One-time, zero-prompt setter for Smart Guitar autorun action IDs.
--
-- What it sets (ExtState):
--   SG_AGENTD/action_generate   = <Generate action command id string, e.g. _RSxxxxxx>
--   SG_AGENTD/action_pass_regen = <PASS+REGEN action command id string, e.g. _RSxxxxxx>
--
-- How to use:
--   1) Open Reaper Actions list.
--   2) Find your actions (Generate script action + PASS+REGEN FAST script action).
--   3) Right-click each action -> Copy selected action command ID.
--   4) Paste them below into GEN_ID / PASS_ID.
--   5) Run this script once.
--
-- After running, your zero-prompt autorun script can run Generate -> PASS automatically.

local EXT_SECTION = "SG_AGENTD"
local K_GEN  = "action_generate"
local K_PASS = "action_pass_regen"

-- ============================================================
-- EDIT THESE TWO LINES (paste your command IDs exactly)
-- Examples look like: _RS1234567890abcdef1234567890abcdef
-- ============================================================
local GEN_ID  = "_RS_PASTE_GENERATE_ID_HERE"
local PASS_ID = "_RS_PASTE_PASS_REGEN_ID_HERE"

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

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — One-time Action ID Setter (Zero-prompt)")
msg("============================================================")

GEN_ID  = trim(GEN_ID)
PASS_ID = trim(PASS_ID)

-- Basic placeholder guard (prevents silently saving the template text)
if GEN_ID:find("PASTE_GENERATE_ID_HERE", 1, true) or PASS_ID:find("PASTE_PASS_REGEN_ID_HERE", 1, true) then
  msg("SG ERR: You must edit GEN_ID and PASS_ID in this script before running.")
  msg("Fix:")
  msg("  1) Actions -> find your Generate script action")
  msg("  2) Right-click -> Copy selected action command ID")
  msg("  3) Paste into GEN_ID")
  msg("  4) Repeat for PASS+REGEN FAST action into PASS_ID")
  msg("============================================================")
  return
end

-- Validate the IDs actually resolve inside Reaper
local gen_num  = resolve_named_command(GEN_ID)
local pass_num = resolve_named_command(PASS_ID)

if not gen_num then
  msg("SG ERR: Generate command ID does not resolve: " .. tostring(GEN_ID))
  msg("Tip: command IDs must include the leading underscore, e.g. _RSxxxxxxxx...")
  msg("============================================================")
  return
end

if not pass_num then
  msg("SG ERR: PASS+REGEN command ID does not resolve: " .. tostring(PASS_ID))
  msg("Tip: make sure you copied the Action command ID, not the script filename.")
  msg("============================================================")
  return
end

-- Persist to ExtState
set_ext(K_GEN, GEN_ID)
set_ext(K_PASS, PASS_ID)

msg("SG OK: Saved ExtState keys:")
msg("  " .. EXT_SECTION .. "/" .. K_GEN  .. " = " .. get_ext(K_GEN))
msg("  " .. EXT_SECTION .. "/" .. K_PASS .. " = " .. get_ext(K_PASS))

msg("------------------------------------------------------------")
msg("Verification:")
msg("  - Reaper resolved Generate -> numeric command: " .. tostring(gen_num))
msg("  - Reaper resolved PASS+REGEN -> numeric command: " .. tostring(pass_num))
msg("")
msg("Next step:")
msg("  - Run: reaper_sg_setup_autorun_generate_then_pass.lua")
msg("    It will read these ExtState keys and run Generate -> PASS with no prompts.")
msg("============================================================")
