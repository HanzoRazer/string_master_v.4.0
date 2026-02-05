-- scripts/reaper/reaper_sg_setup_doctor.lua
-- Smart Guitar — Setup Doctor (Gatekeeper)
--
-- Produces a single PASS/FAIL receipt line at end.
-- Checks:
--   1) curl present
--   2) json.lua present + loadable
--   3) host_port sane (ExtState) or fallback
--   4) sg-agentd reachable (/status)
--   5) session_id present
--   6-10) action IDs resolve (generate, pass, struggle, timeline, trend)
--
-- Notes:
-- - This script is safe: no side effects (no Generate/Pass calls).
-- - It uses curl via reaper.ExecProcess with timeouts (no hangs).

local EXT_SECTION = "SG_AGENTD"
local DEFAULT_HOST_PORT = "127.0.0.1:8420"

local function trim(s)
  return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$",""))
end

local function msg(s)
  reaper.ShowConsoleMsg(tostring(s) .. "\n")
end

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close(); return true end
  return false
end

local function get_script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  local dir = p:match("(.*/)") or p:match("(.+\\)") or ""
  return dir
end

local function get_host_port()
  local hp = trim(reaper.GetExtState(EXT_SECTION, "host_port"))
  if hp == "" then hp = DEFAULT_HOST_PORT end
  if not hp:match("^[%w%.%-]+:%d+$") then
    hp = DEFAULT_HOST_PORT
  end
  return hp
end

local function get_session_id()
  return trim(reaper.GetExtState(EXT_SECTION, "session_id"))
end

local function get_action_id(key)
  return trim(reaper.GetExtState(EXT_SECTION, key))
end

-- ---------------------------------------------------------------------------
-- Gatekeeper result tracking
-- ---------------------------------------------------------------------------
local total_checks = 0
local ok_count = 0
local warn_count = 0
local fail_count = 0

local function OK(s)
  ok_count = ok_count + 1
  total_checks = total_checks + 1
  msg("SG OK:   " .. s)
end

local function WARN(s)
  warn_count = warn_count + 1
  total_checks = total_checks + 1
  msg("SG WARN: " .. s)
end

local function FAIL(s)
  fail_count = fail_count + 1
  total_checks = total_checks + 1
  msg("SG FAIL: " .. s)
end

local function run_cmd(cmd, timeout_ms)
  timeout_ms = timeout_ms or 2000
  local rv, out = reaper.ExecProcess(cmd, timeout_ms)
  return rv, out
end

local function check_curl()
  local rv, out = run_cmd('curl --version', 2000)
  if rv == 0 and out and out:lower():find("curl", 1, true) then
    OK("curl: present")
    return true
  end
  FAIL("curl: missing (must be in PATH)")
  return false
end

local function check_json()
  local script_dir = get_script_dir()
  local path = script_dir .. "json.lua"
  if not file_exists(path) then
    FAIL("json.lua: missing (" .. path .. ")")
    return false
  end
  local ok_load, lib = pcall(dofile, path)
  if not ok_load or type(lib) ~= "table" or type(lib.decode) ~= "function" or type(lib.encode) ~= "function" then
    FAIL("json.lua: present but failed to load or missing encode/decode")
    return false
  end
  OK("json.lua: present + loadable")
  return true
end

local function check_host_port()
  local hp = trim(reaper.GetExtState(EXT_SECTION, "host_port"))
  if hp == "" then
    WARN("host_port: not set (using fallback " .. DEFAULT_HOST_PORT .. ")")
    return true
  end
  if not hp:match("^[%w%.%-]+:%d+$") then
    FAIL("host_port: invalid (must look like host:port). got=" .. tostring(hp))
    return false
  end
  OK("host_port: " .. hp)
  return true
end

local function check_session_id()
  local sid = get_session_id()
  if sid == "" then
    WARN("session_id: not set (panel/session_index may be limited)")
    return true
  end
  OK("session_id: " .. sid)
  return true
end

local function http_get_status(host_port)
  local url = 'http://' .. host_port .. '/status'
  local cmd = 'curl -s -X GET -w "\\n%{http_code}" "' .. url .. '"'
  local rv, out = run_cmd(cmd, 2500)
  if rv ~= 0 or not out then return nil, nil end
  local body, code = out:match("^(.*)\n(%d%d%d)$")
  if not code then body, code = out:match("^(.*)\r\n(%d%d%d)$") end
  return body or "", tonumber(code)
end

local function check_agentd_reachable()
  local hp = get_host_port()
  local body, code = http_get_status(hp)
  if not code then
    FAIL("sg-agentd: unreachable at http://" .. hp .. " (curl failed or timed out)")
    return false
  end
  if code >= 200 and code < 300 then
    OK("sg-agentd: reachable (/status) at http://" .. hp)
    return true
  end
  FAIL("sg-agentd: HTTP " .. tostring(code) .. " at http://" .. hp .. "/status")
  if trim(body) ~= "" then msg("         body: " .. trim(body)) end
  return false
end

local function resolve_action(id_str)
  id_str = trim(id_str)
  if id_str == "" then return nil end
  local n = reaper.NamedCommandLookup(id_str)
  if not n or n == 0 then return nil end
  return n
end

local function check_action(key, label)
  local id_str = get_action_id(key)
  if id_str == "" then
    WARN(label .. ": missing ExtState " .. EXT_SECTION .. "/" .. key)
    return true
  end
  if not id_str:match("^_RS") then
    WARN(label .. ": looks non-_RS id (" .. id_str .. ")")
    return true
  end
  local n = resolve_action(id_str)
  if not n then
    FAIL(label .. ": does not resolve in Reaper (" .. id_str .. ")")
    return false
  end
  OK(label .. ": resolves (" .. id_str .. ")")
  return true
end

local function check_actions_all()
  local ok_all = true
  ok_all = check_action("action_generate",       "Action Generate")       and ok_all
  ok_all = check_action("action_pass_regen",     "Action PASS+REGEN")     and ok_all
  ok_all = check_action("action_struggle_regen", "Action STRUGGLE+REGEN") and ok_all
  ok_all = check_action("action_timeline",       "Action Timeline")       and ok_all
  ok_all = check_action("action_trend",          "Action Trend")          and ok_all
  return ok_all
end

-- ---------------------------------------------------------------------------
-- Optional legacy checks (safe stubs)
-- If your repo already has track/marker checks, keep them below and call them.
-- These stubs do nothing but won't break installs.
-- ---------------------------------------------------------------------------
local function optional_checks()
  -- If you already had track checks like SG_COMP / SG_BASS, markers, etc.,
  -- paste them here and convert their outputs to OK/WARN/FAIL calls.
  return true
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Setup Doctor (Gatekeeper)")
msg("============================================================")

local pass_all = true

pass_all = check_curl() and pass_all
pass_all = check_json() and pass_all
pass_all = check_host_port() and pass_all
pass_all = check_agentd_reachable() and pass_all
pass_all = check_session_id() and pass_all
pass_all = check_actions_all() and pass_all
pass_all = optional_checks() and pass_all

msg("------------------------------------------------------------")
local checks = total_checks
local good = ok_count
local bad  = fail_count
local warn = warn_count

if bad == 0 then
  msg(("SG DOCTOR: PASS (%d/%d checks) — %d warn"):format(good, checks, warn))
else
  msg(("SG DOCTOR: FAIL (%d/%d checks) — %d fail, %d warn"):format(good, checks, bad, warn))
end
msg("============================================================")
