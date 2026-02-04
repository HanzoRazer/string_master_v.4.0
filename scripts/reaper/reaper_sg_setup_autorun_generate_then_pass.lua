-- scripts/reaper_sg_setup_autorun_generate_then_pass.lua
-- Episode 12.1 (Zero-prompt): Always run Generate then PASS+REGEN
--
-- Requirements:
--   - You have already loaded your Generate script as a Reaper Action
--   - You have already loaded your PASS+REGEN FAST script as a Reaper Action
--   - Their Reaper Command IDs (e.g., _RSxxxxxxxx) are stored in ExtState:
--       SG_AGENTD/action_generate
--       SG_AGENTD/action_pass_regen
--
-- Behavior:
--   - No prompts, no UI dialogs
--   - Runs Generate, then PASS+REGEN
--   - If IDs are missing/invalid, prints exact fix instructions

local EXT_SECTION = "SG_AGENTD"
local K_GEN  = "action_generate"
local K_PASS = "action_pass_regen"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function ok(s)  msg("SG OK:  " .. s) end
local function err(s) msg("SG ERR:" .. s) end

local function trim(s)
  return (tostring(s or ""):gsub("^%s+", ""):gsub("%s+$", ""))
end

local function get_action_id(key)
  local v = trim(reaper.GetExtState(EXT_SECTION, key))
  if v == "" then return nil end
  return v
end

local function resolve_named_command(cmd_id_str)
  cmd_id_str = trim(cmd_id_str or "")
  if cmd_id_str == "" then return nil end
  local num = reaper.NamedCommandLookup(cmd_id_str)
  if not num or num == 0 then return nil end
  return num
end

local function run_action(cmd_id_str, label)
  local num = resolve_named_command(cmd_id_str)
  if not num then
    err(label .. ": invalid/missing action id: " .. tostring(cmd_id_str))
    return false
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
msg("Smart Guitar — Zero-Prompt Autorun (Generate → PASS+REGEN)")
msg("============================================================")

local gen_id  = get_action_id(K_GEN)
local pass_id = get_action_id(K_PASS)

if not gen_id or not pass_id then
  err("Missing ExtState action IDs.")
  msg("Fix (one-time): set these ExtState keys (via your config script or Reaper console helper):")
  msg('  SG_AGENTD/' .. K_GEN  .. '  = _RSxxxxxxxx   (Generate action)')
  msg('  SG_AGENTD/' .. K_PASS .. '  = _RSxxxxxxxx   (PASS+REGEN FAST action)')
  msg("")
  msg("Tip: Use the non-zero-prompt Setup Doctor Autorun once to save them, then run this script forever.")
  msg("============================================================")
  return
end

-- Run Generate then PASS+REGEN
local ok_gen = run_action(gen_id, "Generate")
if not ok_gen then
  msg("============================================================")
  return
end

-- Optional: small defer so Generate has time to finish network I/O before PASS fires.
-- Keep tiny to avoid annoying delays; PASS+REGEN will no-op safely if last_clip_id isn't ready.
reaper.defer(function()
  run_action(pass_id, "PASS+REGEN")
  msg("============================================================")
end)
