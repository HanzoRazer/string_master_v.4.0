-- scripts/reaper/reaper_sg_lab_bootstrap.lua
-- Phase 10: Lab Bootstrap (zero prompts, one-run)
--
-- Sets ExtState keys:
--   SG_AGENTD/host_port
--   SG_AGENTD/session_id
--   SG_AGENTD/transport   (auto|curl|pwsh)
--   SG_AGENTD/lan_mode    (true|false)
--
-- Then runs:
--   1) reaper_sg_setup_doctor.lua   (may AUTOFIX)
--   2) reaper_sg_probe_endpoints.lua (writes report to REAPER_RESOURCE_PATH/SG_reports/)
--
-- Finally writes a single bootstrap receipt file into SG_reports.

local EXT_SECTION = "SG_AGENTD"

-- ============================================================
-- EDIT THESE ONCE PER LAB
-- ============================================================
local HOST_PORT  = "127.0.0.1:8420"   -- e.g. "192.168.1.50:8420"
local SESSION_ID = "reaper_session"   -- e.g. "labA_week1"
local TRANSPORT  = "auto"             -- auto|curl|pwsh
local LAN_MODE   = "false"            -- true|false (true allows localhost labs as LAN_READY)
-- ============================================================

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end
local function lower(s) return tostring(s or ""):lower() end

local function script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  return p:match("(.*/)") or p:match("(.+\\)") or ""
end

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close(); return true end
  return false
end

local function set_ext(key, val)
  reaper.SetExtState(EXT_SECTION, key, trim(val), true)
end

local function get_ext(key)
  return trim(reaper.GetExtState(EXT_SECTION, key))
end

local function is_valid_host_port(hp)
  hp = trim(hp)
  local host, port = hp:match("^([%w%.%-]+):(%d+)$")
  if not host or not port then return false end
  local p = tonumber(port)
  if not p or p < 1 or p > 65535 then return false end
  return true
end

local function is_valid_transport(v)
  v = lower(trim(v))
  return v == "auto" or v == "curl" or v == "pwsh"
end

local function is_valid_bool(v)
  v = lower(trim(v))
  return v == "true" or v == "false"
end

local function ensure_reports_dir()
  local resource = reaper.GetResourcePath()
  local out_dir = (resource:gsub("\\", "/")) .. "/SG_reports"
  if reaper.RecursiveCreateDirectory then
    reaper.RecursiveCreateDirectory(out_dir, 0)
  end
  return out_dir
end

local function iso_stamp()
  local t = os.date("*t")
  return string.format("%04d%02d%02d_%02d%02d%02d",
    t.year, t.month, t.day, t.hour, t.min, t.sec)
end

local function read_last_probe_report_path(out_dir)
  -- Best-effort: find newest SG_probe_*.txt in SG_reports by scanning directory.
  -- Reaper only offers EnumerateFiles; we'll pick the lexicographically max (timestamp format makes that work).
  local best = nil
  local i = 0
  while true do
    local fn = reaper.EnumerateFiles(out_dir, i)
    if not fn then break end
    if fn:match("^SG_probe_%d%d%d%d%d%d%d%d_%d%d%d%d%d%d%.txt$") then
      if not best or fn > best then best = fn end
    end
    i = i + 1
  end
  if best then return out_dir .. "/" .. best end
  return nil
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — LAB BOOTSTRAP (Phase 10)")
msg("============================================================")

-- Validate inputs
if not is_valid_host_port(HOST_PORT) then
  msg("SG FAIL: invalid HOST_PORT: " .. tostring(HOST_PORT))
  msg("        Expected host:port (example 127.0.0.1:8420 or 192.168.1.50:8420)")
  msg("============================================================")
  return
end
if trim(SESSION_ID) == "" then
  msg("SG FAIL: SESSION_ID is empty")
  msg("============================================================")
  return
end
if not is_valid_transport(TRANSPORT) then
  msg("SG FAIL: invalid TRANSPORT: " .. tostring(TRANSPORT) .. " (auto|curl|pwsh)")
  msg("============================================================")
  return
end
if not is_valid_bool(LAN_MODE) then
  msg("SG FAIL: invalid LAN_MODE: " .. tostring(LAN_MODE) .. " (true|false)")
  msg("============================================================")
  return
end

-- Set ExtState
set_ext("host_port", HOST_PORT)
set_ext("session_id", SESSION_ID)
set_ext("transport", lower(TRANSPORT))
set_ext("lan_mode", lower(LAN_MODE))

msg("SG OK: ExtState set:")
msg("  " .. EXT_SECTION .. "/host_port  = " .. get_ext("host_port"))
msg("  " .. EXT_SECTION .. "/session_id = " .. get_ext("session_id"))
msg("  " .. EXT_SECTION .. "/transport  = " .. get_ext("transport"))
msg("  " .. EXT_SECTION .. "/lan_mode   = " .. get_ext("lan_mode"))

local dir = script_dir()

-- Run Doctor (with AUTOFIX inside doctor)
local doctor = dir .. "reaper_sg_setup_doctor.lua"
if file_exists(doctor) then
  msg("------------------------------------------------------------")
  msg("Running DOCTOR...")
  local ok, err = pcall(dofile, doctor)
  if not ok then
    msg("SG WARN: Doctor error: " .. tostring(err))
  end
else
  msg("SG WARN: Doctor missing: " .. doctor)
end

-- Run Probe (writes report)
local probe = dir .. "reaper_sg_probe_endpoints.lua"
if file_exists(probe) then
  msg("------------------------------------------------------------")
  msg("Running PROBE...")
  local ok, err = pcall(dofile, probe)
  if not ok then
    msg("SG WARN: Probe error: " .. tostring(err))
  end
else
  msg("SG WARN: Probe missing: " .. probe)
end

-- Write one bootstrap receipt artifact
local out_dir = ensure_reports_dir()
local receipt_path = out_dir .. "/SG_bootstrap_" .. iso_stamp() .. ".txt"
local last_probe = read_last_probe_report_path(out_dir) or "(none found)"

local f = io.open(receipt_path, "w")
if f then
  f:write("Smart Guitar — Lab Bootstrap Receipt\n")
  f:write("============================================================\n")
  f:write("date_local: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
  f:write("reaper_version: " .. tostring(reaper.GetAppVersion() or "unknown") .. "\n")
  f:write("resource_path: " .. tostring(reaper.GetResourcePath() or "unknown") .. "\n")
  f:write("script_dir: " .. tostring(dir) .. "\n")
  f:write("------------------------------------------------------------\n")
  f:write(EXT_SECTION .. "/host_port  = " .. get_ext("host_port") .. "\n")
  f:write(EXT_SECTION .. "/session_id = " .. get_ext("session_id") .. "\n")
  f:write(EXT_SECTION .. "/transport  = " .. get_ext("transport") .. "\n")
  f:write(EXT_SECTION .. "/lan_mode   = " .. get_ext("lan_mode") .. "\n")
  f:write("------------------------------------------------------------\n")
  f:write("probe_report_latest: " .. tostring(last_probe) .. "\n")
  f:write("============================================================\n")
  f:close()
end

msg("------------------------------------------------------------")
msg("SG OK: Bootstrap complete.")
msg("Receipt: " .. receipt_path)
msg("Latest probe: " .. tostring(last_probe))
msg("============================================================")
