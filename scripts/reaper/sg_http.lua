-- scripts/reaper/sg_http.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Shared helper for:
-- - ExtState reads (host_port/session_id/action ids)
-- - safe curl HTTP calls via reaper.ExecProcess (timeouts)
-- - JSON encode/decode helpers (expects json.lua in same directory)

local M = {}

M.EXT_SECTION = "SG_AGENTD"
M.DEFAULT_HOST_PORT = "127.0.0.1:8420"

local function trim(s)
  return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$",""))
end
M.trim = trim

local function get_script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  return p:match("(.*/)") or p:match("(.+\\)") or ""
end
M.get_script_dir = get_script_dir

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close(); return true end
  return false
end
M.file_exists = file_exists

function M.load_json()
  local script_dir = get_script_dir()
  local path = script_dir .. "json.lua"
  if not file_exists(path) then
    return nil, "json.lua missing: " .. path
  end
  local ok, lib = pcall(dofile, path)
  if not ok or type(lib) ~= "table" or type(lib.encode) ~= "function" or type(lib.decode) ~= "function" then
    return nil, "json.lua failed to load or missing encode/decode"
  end
  return lib, nil
end

function M.get_ext(key)
  return trim(reaper.GetExtState(M.EXT_SECTION, key))
end

function M.set_ext(key, val, persist)
  persist = (persist ~= false)
  reaper.SetExtState(M.EXT_SECTION, key, trim(val), persist)
end

function M.get_host_port()
  local hp = M.get_ext("host_port")
  if hp == "" then hp = M.DEFAULT_HOST_PORT end
  -- sanitize: host:port only
  if not hp:match("^[%w%.%-]+:%d+$") then
    hp = M.DEFAULT_HOST_PORT
  end
  return hp
end

function M.get_api_base()
  return "http://" .. M.get_host_port()
end

function M.exec(cmd, timeout_ms)
  timeout_ms = timeout_ms or 2500
  local rv, out = reaper.ExecProcess(cmd, timeout_ms)
  return rv, out
end

-- curl helpers (stdout contains: body \n statuscode)
local function parse_body_code(out)
  if not out then return nil, nil end
  local body, code = out:match("^(.*)\n(%d%d%d)$")
  if not code then body, code = out:match("^(.*)\r\n(%d%d%d)$") end
  if not code then return out, nil end
  return body or "", tonumber(code)
end

function M.http_get(path, timeout_ms)
  local url = M.get_api_base() .. path
  local cmd = 'curl -s -X GET -w "\\n%{http_code}" "' .. url .. '"'
  local rv, out = M.exec(cmd, timeout_ms or 2500)
  if rv ~= 0 then
    return nil, nil, "curl failed/timeout (rv=" .. tostring(rv) .. ")"
  end
  local body, code = parse_body_code(out)
  return body, code, nil
end

function M.http_post_json(path, json_body_str, timeout_ms)
  timeout_ms = timeout_ms or 5000

  local tmp = os.tmpname()
  local f = io.open(tmp, "w")
  if not f then return nil, nil, "temp file error" end
  f:write(tostring(json_body_str or ""))
  f:close()

  local url = M.get_api_base() .. path
  local cmd = string.format(
    'curl -s -X POST "%s" -H "Content-Type: application/json" --data-binary @"%s" -w "\\n%%{http_code}"',
    url, tmp
  )

  local rv, out = M.exec(cmd, timeout_ms)
  os.remove(tmp)

  if rv ~= 0 then
    return nil, nil, "curl failed/timeout (rv=" .. tostring(rv) .. ")"
  end

  local body, code = parse_body_code(out)
  return body or "", code, nil
end

-- canonical coach_hint picker (V1 + back-compat)
function M.pick_coach_hint(decoded)
  if type(decoded) ~= "table" then return nil end

  if type(decoded.suggested_adjustment) == "table" and type(decoded.suggested_adjustment.coach_hint) == "string" then
    local s = trim(decoded.suggested_adjustment.coach_hint)
    if s ~= "" then return s end
  end

  if type(decoded.regen) == "table"
    and type(decoded.regen.suggested) == "table"
    and type(decoded.regen.suggested.coach_hint) == "string" then
    local s = trim(decoded.regen.suggested.coach_hint)
    if s ~= "" then return s end
  end

  if type(decoded.coach_hint) == "string" then
    local s = trim(decoded.coach_hint)
    if s ~= "" then return s end
  end

  return nil
end

return M
