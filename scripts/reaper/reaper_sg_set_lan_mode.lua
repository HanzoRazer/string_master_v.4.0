-- scripts/reaper/reaper_sg_set_lan_mode.lua
-- One-time, zero-prompt ExtState setter for LAN readiness mode.
--
-- Writes:
--   SG_AGENTD/lan_mode = true|false
--
-- Use true for per-machine localhost labs.
-- Use false for centralized LAN server labs.

local EXT_SECTION = "SG_AGENTD"
local KEY = "lan_mode"

-- ============================================================
-- EDIT THIS ONCE
-- ============================================================
local LAN_MODE = "false"  -- true | false
-- ============================================================

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end
local function lower(s) return tostring(s or ""):lower() end

local function is_valid(v)
  v = lower(trim(v))
  return v == "true" or v == "false"
end

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Set LAN Mode (one-time ExtState setter)")
msg("============================================================")

local v = lower(trim(LAN_MODE))
if not is_valid(v) then
  msg("SG ERR: invalid LAN_MODE='" .. tostring(LAN_MODE) .. "'")
  msg("       Allowed: true | false")
  msg("Fix: edit LAN_MODE in this script and run again.")
  msg("============================================================")
  return
end

reaper.SetExtState(EXT_SECTION, KEY, v, true)

msg("SG OK: saved ExtState key:")
msg("  " .. EXT_SECTION .. "/" .. KEY .. " = " .. trim(reaper.GetExtState(EXT_SECTION, KEY)))
msg("------------------------------------------------------------")
msg("Effect:")
msg("  - lan_mode=true allows localhost/127.0.0.1 to be considered LAN_READY")
msg("============================================================")
