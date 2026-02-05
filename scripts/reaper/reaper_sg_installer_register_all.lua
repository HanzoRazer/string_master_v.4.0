-- scripts/reaper/reaper_sg_installer_register_all.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- One-click installer:
-- - registers core SG scripts into Reaper Actions (Main section)
-- - captures generated command IDs (_RS...)
-- - writes ExtState keys:
--     action_generate, action_pass_regen, action_struggle_regen, action_timeline, action_trend
--     session_id, host_port
--
-- Requirements:
-- - scripts live in the same folder as this installer
-- - reaper.AddRemoveReaScript available
-- - Reaper will create action IDs on registration

local EXT_SECTION = "SG_AGENTD"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end

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

local function register_script(fullpath, section_id)
  section_id = section_id or 0 -- Main
  -- add=true, commit=true
  local cmd_id = reaper.AddRemoveReaScript(true, section_id, fullpath, true)
  if not cmd_id or cmd_id == 0 then return nil, "AddRemoveReaScript failed" end

  local rs = reaper.ReverseNamedCommandLookup(cmd_id)
  rs = trim(rs)
  if rs == "" then return nil, "ReverseNamedCommandLookup failed" end
  return rs, nil
end

local function banner()
  reaper.ClearConsole()
  msg("============================================================")
  msg("Smart Guitar — Installer (Auto-register + ExtState ship)")
  msg("============================================================")
end

-- ---------------------------------------------------------------------------
-- EDITABLE DEFAULTS (safe)
-- ---------------------------------------------------------------------------
local DEFAULT_SESSION_ID = "reaper_session"
local DEFAULT_HOST_PORT  = "127.0.0.1:8420"

-- ---------------------------------------------------------------------------
-- SCRIPT MAP
-- IMPORTANT: These filenames must exist in the same directory as this installer.
-- If your repo uses different filenames, update them here once.
-- ---------------------------------------------------------------------------
local MAP = {
  { key = "action_generate",       label = "Generate",       file = "reaper_sg_generate.lua" },
  { key = "action_pass_regen",     label = "PASS+REGEN",     file = "reaper_sg_pass_and_regen.lua" },
  { key = "action_struggle_regen", label = "STRUGGLE+REGEN", file = "reaper_sg_struggle_and_regen.lua" },
  { key = "action_timeline",       label = "Timeline",       file = "reaper_sg_session_timeline.lua" },
  { key = "action_trend",          label = "Trend",          file = "reaper_sg_session_trend_summary.lua" },
}

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
banner()

local dir = script_dir()
msg("Script dir: " .. dir)

-- Write host/session if missing (do not overwrite if user already set)
if get_ext("session_id") == "" then
  set_ext("session_id", DEFAULT_SESSION_ID)
  msg("SET: session_id = " .. get_ext("session_id"))
else
  msg("KEEP: session_id = " .. get_ext("session_id"))
end

local hp = get_ext("host_port")
if hp == "" then
  set_ext("host_port", DEFAULT_HOST_PORT)
  msg("SET: host_port = " .. get_ext("host_port"))
else
  msg("KEEP: host_port = " .. get_ext("host_port"))
end

local ok = true

for _, item in ipairs(MAP) do
  local full = dir .. item.file
  if not file_exists(full) then
    msg("SG WARN: missing file for " .. item.label .. ": " .. full)
    msg("        (If your repo uses different names, edit MAP in installer.)")
    ok = false
  else
    local rs, err = register_script(full, 0)
    if not rs then
      msg("SG FAIL: register " .. item.label .. " → " .. tostring(err))
      ok = false
    else
      set_ext(item.key, rs)
      msg("SG OK: " .. item.key .. " = " .. rs)
    end
  end
end

msg("------------------------------------------------------------")
if ok then
  msg("SG INSTALL: PASS — scripts registered and ExtState shipped.")
else
  msg("SG INSTALL: WARN/FAIL — some scripts missing or failed to register.")
  msg("Fix: verify filenames in MAP and rerun installer.")
end
msg("Next: run reaper_sg_setup_doctor.lua for full verification.")
msg("============================================================")
