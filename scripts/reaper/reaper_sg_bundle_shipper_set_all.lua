-- scripts/reaper/reaper_sg_bundle_shipper_set_all.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Zero-prompt "bundle shipper" setter:
--   - stores all 5 action IDs
--   - stores session_id + host_port
--
-- ExtState (persist=true):
--   SG_AGENTD/action_generate
--   SG_AGENTD/action_pass_regen
--   SG_AGENTD/action_struggle_regen
--   SG_AGENTD/action_timeline
--   SG_AGENTD/action_trend
--   SG_AGENTD/session_id
--   SG_AGENTD/host_port
--
-- How to use (one-time):
--   1) Reaper Actions list -> select each action -> right-click -> Copy selected action command ID
--   2) Paste the 5 _RS... IDs below
--   3) Set SESSION_ID and HOST_PORT below
--   4) Run this script once
--
-- After this:
--   - Zero-prompt autorun scripts can run without prompts
--   - The Episode 13 panel can call actions and fetch session_index (if it uses host_port)

local EXT_SECTION = "SG_AGENTD"

-- Keys
local K_GEN    = "action_generate"
local K_PASS   = "action_pass_regen"
local K_STRUG  = "action_struggle_regen"
local K_TLINE  = "action_timeline"
local K_TREND  = "action_trend"
local K_SID    = "session_id"
local K_HOST   = "host_port"

-- ============================================================
-- EDIT THESE VALUES ONCE (paste exactly; keep the leading "_")
-- ============================================================
local GEN_ID    = "_RS_PASTE_GENERATE_ID_HERE"
local PASS_ID   = "_RS_PASTE_PASS_REGEN_ID_HERE"
local STRUG_ID  = "_RS_PASTE_STRUGGLE_REGEN_ID_HERE"
local TLINE_ID  = "_RS_PASTE_TIMELINE_ID_HERE"
local TREND_ID  = "_RS_PASTE_TREND_ID_HERE"

-- Session identity (offline-first): choose a stable name per Reaper project/user/device
-- Examples: "reaper_session", "lab_a_station_3", "school_guitar_01"
local SESSION_ID = "reaper_session"

-- Host + port for sg-agentd (used by scripts that call /status, /session_index, etc.)
-- Examples: "127.0.0.1:8420" or "192.168.1.50:8420"
local HOST_PORT = "127.0.0.1:8420"

-- ----------------------------- utils ---------------------------------------
local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end

local function is_placeholder(v)
  v = tostring(v or "")
  return v:find("PASTE_", 1, true) ~= nil
end

local function resolve(cmd_str)
  cmd_str = trim(cmd_str)
  if cmd_str == "" then return nil end
  local n = reaper.NamedCommandLookup(cmd_str)
  if not n or n == 0 then return nil end
  return n
end

local function set_ext(key, val)
  reaper.SetExtState(EXT_SECTION, key, trim(val), true)
end

local function get_ext(key)
  return trim(reaper.GetExtState(EXT_SECTION, key))
end

local function validate_action_or_fail(label, id_str)
  id_str = trim(id_str)
  if id_str == "" or is_placeholder(id_str) then
    msg("SG ERR: " .. label .. " is missing. Paste the _RS... command ID into this script.")
    return false
  end
  local n = resolve(id_str)
  if not n then
    msg("SG ERR: " .. label .. " does not resolve in Reaper: " .. tostring(id_str))
    msg("       Fix: in Actions list, right-click the action -> Copy selected action command ID.")
    msg("       Paste the ID starting with _RS into this script.")
    return false
  end
  return true
end

local function validate_host_port(hp)
  hp = trim(hp)
  if hp == "" then return false, "host_port is empty" end
  -- very light validation: must contain colon and a numeric port
  local host, port = hp:match("^(.+):(%d+)$")
  if not host or not port then return false, "host_port must look like 127.0.0.1:8420" end
  local p = tonumber(port)
  if not p or p < 1 or p > 65535 then return false, "port out of range" end
  return true, nil
end

-- ----------------------------- MAIN ----------------------------------------
reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Bundle Shipper Setter (ALL 5 + session_id + host_port)")
msg("============================================================")

local ok_all = true
ok_all = validate_action_or_fail("Generate",       GEN_ID)   and ok_all
ok_all = validate_action_or_fail("PASS+REGEN",     PASS_ID)  and ok_all
ok_all = validate_action_or_fail("STRUGGLE+REGEN", STRUG_ID) and ok_all
ok_all = validate_action_or_fail("Timeline",       TLINE_ID) and ok_all
ok_all = validate_action_or_fail("Trend",          TREND_ID) and ok_all

SESSION_ID = trim(SESSION_ID)
if SESSION_ID == "" then
  msg("SG ERR: session_id is empty. Set SESSION_ID in this script (e.g., reaper_session).")
  ok_all = false
end

HOST_PORT = trim(HOST_PORT)
local hp_ok, hp_err = validate_host_port(HOST_PORT)
if not hp_ok then
  msg("SG ERR: host_port invalid: " .. tostring(hp_err))
  msg("       Set HOST_PORT like 127.0.0.1:8420 or 192.168.1.50:8420")
  ok_all = false
end

if not ok_all then
  msg("------------------------------------------------------------")
  msg("Nothing saved. Fix the fields above and run again.")
  msg("============================================================")
  return
end

-- Persist all keys
set_ext(K_GEN,   GEN_ID)
set_ext(K_PASS,  PASS_ID)
set_ext(K_STRUG, STRUG_ID)
set_ext(K_TLINE, TLINE_ID)
set_ext(K_TREND, TREND_ID)
set_ext(K_SID,   SESSION_ID)
set_ext(K_HOST,  HOST_PORT)

msg("SG OK: Saved ExtState keys (persisted):")
msg("  " .. EXT_SECTION .. "/" .. K_GEN   .. " = " .. get_ext(K_GEN))
msg("  " .. EXT_SECTION .. "/" .. K_PASS  .. " = " .. get_ext(K_PASS))
msg("  " .. EXT_SECTION .. "/" .. K_STRUG .. " = " .. get_ext(K_STRUG))
msg("  " .. EXT_SECTION .. "/" .. K_TLINE .. " = " .. get_ext(K_TLINE))
msg("  " .. EXT_SECTION .. "/" .. K_TREND .. " = " .. get_ext(K_TREND))
msg("  " .. EXT_SECTION .. "/" .. K_SID   .. " = " .. get_ext(K_SID))
msg("  " .. EXT_SECTION .. "/" .. K_HOST  .. " = " .. get_ext(K_HOST))

msg("------------------------------------------------------------")
msg("What this enables immediately:")
msg("  - Zero-prompt autorun (Generate → PASS) reads action_generate/action_pass_regen")
msg("  - SG Panel reads session_id and host_port to fetch /session_index and display trends")
msg("  - FAST scripts can be invoked via panel buttons without any prompts")
msg("------------------------------------------------------------")
msg("Quick verification steps:")
msg("  1) Run your zero-prompt autorun script (Generate → PASS) and confirm it fires both actions.")
msg("  2) Run SG Panel and confirm it shows session_id=" .. get_ext(K_SID) .. " and fetches from host_port=" .. get_ext(K_HOST))
msg("  3) If panel shows session_index unavailable, confirm sg-agentd is running on " .. get_ext(K_HOST))
msg("============================================================")
