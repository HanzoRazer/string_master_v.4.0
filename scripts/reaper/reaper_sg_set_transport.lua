-- scripts/reaper/reaper_sg_set_transport.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- One-time, zero-prompt ExtState setter for HTTP transport override.
--
-- Writes persistent ExtState key:
--   SG_AGENTD/transport = auto | curl | pwsh
--
-- Usage:
--   1) Edit TRANSPORT below to: "auto" or "curl" or "pwsh"
--   2) Run once in Reaper
--
-- Notes:
-- - "pwsh" only makes sense on Windows (PowerShell Invoke-WebRequest fallback)
-- - "curl" forces curl and fails fast later if curl missing
-- - "auto" (default) probes and caches a working transport via sg_http.lua

local EXT_SECTION = "SG_AGENTD"
local KEY = "transport"

-- ============================================================
-- EDIT THIS ONCE
-- ============================================================
local TRANSPORT = "auto"  -- auto | curl | pwsh
-- ============================================================

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end
local function lower(s) return tostring(s or ""):lower() end

local function is_valid(v)
  v = lower(trim(v))
  return v == "auto" or v == "curl" or v == "pwsh"
end

local function set_ext(key, val)
  reaper.SetExtState(EXT_SECTION, key, trim(val), true)
end

local function get_ext(key)
  return trim(reaper.GetExtState(EXT_SECTION, key))
end

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Set Transport (one-time ExtState setter)")
msg("============================================================")

local v = lower(trim(TRANSPORT))

if not is_valid(v) then
  msg("SG ERR: invalid TRANSPORT='" .. tostring(TRANSPORT) .. "'")
  msg("       Allowed: auto | curl | pwsh")
  msg("Fix: edit TRANSPORT in this script and run again.")
  msg("============================================================")
  return
end

set_ext(KEY, v)

msg("SG OK: saved ExtState key:")
msg("  " .. EXT_SECTION .. "/" .. KEY .. " = " .. get_ext(KEY))
msg("------------------------------------------------------------")
msg("Next:")
msg("  - Run reaper_sg_setup_doctor.lua (it will report transport_info)")
msg("  - Or run the panel; sg_http.lua will honor this override")
msg("============================================================")
