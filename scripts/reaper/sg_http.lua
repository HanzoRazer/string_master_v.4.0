-- ------------------------------ transport ----------------------------------

function M.has_curl()
  local rv, out = M.exec("curl --version", 2000)
  return (rv == 0) and (out and out:lower():find("curl", 1, true) ~= nil)
end

function M.has_powershell()
  if not M.is_windows() then return false end
  local rv, _ = M.exec("powershell -NoProfile -Command \"exit 0\"", 1500)
  return rv == 0
end

-- cached transport decision: "curl" | "pwsh" | "none"
local _transport = nil
local _transport_probed = false
local _transport_probe_error = nil

-- Admin transport override via ExtState (Phase 8.5)
function M.get_transport_override()
  local v = M.get_ext("transport")
  v = trim(v):lower()
  if v == "" then return "auto" end
  if v ~= "auto" and v ~= "curl" and v ~= "pwsh" then
    return "auto"
  end
  return v
end

function M.reset_transport_cache()
  _transport = nil
  _transport_probed = false
  _transport_probe_error = nil
end

function M.choose_transport()
  local override = M.get_transport_override()

  -- Forced modes: do NOT probe other transports; fail fast if forced transport can't work.
  if override == "curl" then
    if not M.has_curl() then
      _transport = "none"
      _transport_probed = true
      _transport_probe_error = "transport forced=curl but curl is missing"
      return _transport
    end
    local ok, err = try_transport_get_status("curl", 1500)
    if ok then
      _transport = "curl"
      _transport_probed = true
      _transport_probe_error = nil
      return _transport
    end
    _transport = "none"
    _transport_probed = true
    _transport_probe_error = "transport forced=curl but probe failed: " .. tostring(err)
    return _transport
  end

  if override == "pwsh" then
    if not M.has_powershell() then
      _transport = "none"
      _transport_probed = true
      _transport_probe_error = "transport forced=pwsh but powershell is unavailable"
      return _transport
    end
    local ok, err = try_transport_get_status("pwsh", 1500)
    if ok then
      _transport = "pwsh"
      _transport_probed = true
      _transport_probe_error = nil
      return _transport
    end
    _transport = "none"
    _transport_probed = true
    _transport_probe_error = "transport forced=pwsh but probe failed: " .. tostring(err)
    return _transport
  end

  -- AUTO mode (default): cached probe behavior
  if _transport_probed then
    return _transport
  end

  _transport_probed = true
  _transport_probe_error = nil

  local candidates = {}
  if M.has_curl() then table.insert(candidates, "curl") end
  if M.has_powershell() then table.insert(candidates, "pwsh") end

  if #candidates == 0 then
    _transport = "none"
    _transport_probe_error = "no HTTP transport available (need curl or powershell)"
    return _transport
  end

  for _, t in ipairs(candidates) do
    local ok, err = try_transport_get_status(t, 1500)
    if ok then
      _transport = t
      return _transport
    else
      _transport_probe_error = "transport " .. t .. " failed: " .. tostring(err)
    end
  end

  _transport = "none"
  if not _transport_probe_error then
    _transport_probe_error = "no working HTTP transport (all probes failed)"
  end
  return _transport
end

function try_transport_get_status(transport, timeout_ms)
  timeout_ms = timeout_ms or 1500

  -- Use only safe, internal URL construction
  local url = M.get_api_base() .. "/status"

  local cmd
  if transport == "curl" then
    cmd = "curl -s -X GET -w " .. M.shell_quote_arg("\n%{http_code}") .. " " .. M.shell_quote_arg(url)
  elseif transport == "pwsh" then
    cmd = ps_get(url)
  else
    return false, "unknown transport"
  end

  local rv, out = M.exec(cmd, timeout_ms)
  if rv ~= 0 or not out then
    return false, "exec failed/timeout (rv=" .. tostring(rv) .. ")"
  end

  local _, code = parse_body_code(out)
  if not code then
    return false, "no status code parsed"
  end
  if code >= 200 and code < 300 then
    return true, nil
  end
  return false, "HTTP " .. tostring(code)
end

-- PowerShell quoting for -Command string.
-- We'll pass a single -Command "...", so we must escape embedded quotes safely.
local function ps_escape(s)
  s = tostring(s or "")
  -- escape double quotes for PowerShell -Command "..."
  s = s:gsub("`", "``")
  s = s:gsub('"', '`"')
  return s
end

local function ps_cmd(command_inner)
  -- Use -NoProfile to reduce variance. -ExecutionPolicy Bypass for locked-down machines.
  return 'powershell -NoProfile -ExecutionPolicy Bypass -Command "' .. ps_escape(command_inner) .. '"'
end

-- PowerShell GET: prints body then newline + status code
local function ps_get(url)
  -- Invoke-WebRequest returns an object. We output Content, then StatusCode.
  -- Use -UseBasicParsing for older Windows PowerShell compatibility.
  local inner =
    "$r = Invoke-WebRequest -UseBasicParsing -Method GET -Uri '" .. url .. "';" ..
    "if ($null -ne $r.Content) { $r.Content };" ..
    "Write-Output ''; " ..
    "Write-Output $r.StatusCode"
  return ps_cmd(inner)
end

-- PowerShell POST JSON: prints body then newline + status code
local function ps_post_json(url, json_str)
  -- Put JSON into a here-string to avoid quoting issues.
  -- Ensure ContentType application/json.
  local inner =
    "$body = @'\n" .. json_str .. "\n'@;" ..
    "$r = Invoke-WebRequest -UseBasicParsing -Method POST -Uri '" .. url .. "' -ContentType 'application/json' -Body $body;" ..
    "if ($null -ne $r.Content) { $r.Content };" ..
    "Write-Output ''; " ..
    "Write-Output $r.StatusCode"
  return ps_cmd(inner)
end

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

-- Strict allowlist for host:port (prevents shell injection via host_port)
function M.is_safe_host_port(hp)
  hp = trim(hp)
  if hp == "" then return false end
  -- allow: letters, digits, dot, dash only in host; numeric port 1-65535
  local host, port = hp:match("^([%w%.%-]+):(%d+)$")
  if not host or not port then return false end
  local p = tonumber(port)
  if not p or p < 1 or p > 65535 then return false end
  return true
end

-- Strict allowlist for URL paths and query strings.
-- Permits: / ? & = % - _ . ~ and alnum
function M.is_safe_path(path)
  path = tostring(path or "")
  if path == "" then return false end
  -- must start with /
  if path:sub(1,1) ~= "/" then return false end
  -- forbid quotes/backticks and common shell metacharacters outright (add caret ^ for Windows)
  if path:find("[\"'`\\;%|<>%^]", 1) then return false end
  -- allow safe URL chars
  if not path:match("^/[A-Za-z0-9%/%?&=%%%-_%.~]*$") then return false end
  return true
end


-- Detect Windows (Reaper on Windows typically uses cmd.exe semantics)
function M.is_windows()
  local sep = package.config:sub(1,1)
  return sep == "\\"
end

-- Quote an argument safely for the current OS shell.
-- Note: ExecProcess uses a command string; this makes arguments safe within it.
function M.shell_quote_arg(arg)
  arg = tostring(arg or "")

  if M.is_windows() then
    -- Windows cmd.exe quoting:
    -- - wrap in double quotes
    -- - escape embedded double quotes by doubling them
    -- - escape carets, ampersands, pipes, <, > by caret-prefix (defense)
    arg = arg:gsub('"', '""')
    arg = arg:gsub("([%^&|<>])", "^%1")
    return '"' .. arg .. '"'
  else
    -- POSIX shell quoting using single quotes:
    -- ' becomes '\'' sequence
    if arg == "" then return "''" end
    arg = arg:gsub("'", [['"'"']])
    return "'" .. arg .. "'"
  end
end

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
  if not M.is_safe_host_port(hp) then
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
  timeout_ms = timeout_ms or 2500

  if not M.is_safe_path(path) then
    return nil, nil, "unsafe path (blocked)"
  end

  local url = M.get_api_base() .. path
  local transport = M.choose_transport()

  if transport == "none" then
    return nil, nil, _transport_probe_error or "no working HTTP transport"
  end

  local cmd
  if transport == "curl" then
    cmd =
      "curl -s -X GET -w " .. M.shell_quote_arg("\n%{http_code}") .. " " .. M.shell_quote_arg(url)
  elseif transport == "pwsh" then
    cmd = ps_get(url)
  else
    return nil, nil, "no HTTP transport (need curl or powershell)"
  end

  local rv, out = M.exec(cmd, timeout_ms)
  if rv ~= 0 or not out then
    return nil, nil, "HTTP failed/timeout (rv=" .. tostring(rv) .. ")"
  end

  local body, code = out:match("^(.*)\n(%d%d%d)%s*$")
  if not code then body, code = out:match("^(.*)\r\n(%d%d%d)%s*$") end
  return body or "", tonumber(code), nil
end

function M.http_post_json(path, json_body_str, timeout_ms)
  timeout_ms = timeout_ms or 5000

  if not M.is_safe_path(path) then
    return nil, nil, "unsafe path (blocked)"
  end

  local url = M.get_api_base() .. path
  local transport = M.choose_transport()

  if transport == "none" then
    return nil, nil, _transport_probe_error or "no working HTTP transport"
  end

  local cmd

  if transport == "curl" then
    local tmp = os.tmpname()
    local f = io.open(tmp, "w")
    if not f then return nil, nil, "temp file error" end
    f:write(tostring(json_body_str or ""))
    f:close()

    cmd =
      "curl -s -X POST " ..
      M.shell_quote_arg(url) ..
      " -H " .. M.shell_quote_arg("Content-Type: application/json") ..
      " --data-binary @" .. M.shell_quote_arg(tmp) ..
      " -w " .. M.shell_quote_arg("\n%{http_code}")

    local rv, out = M.exec(cmd, timeout_ms)
    os.remove(tmp)

    if rv ~= 0 or not out then
      return nil, nil, "HTTP failed/timeout (rv=" .. tostring(rv) .. ")"
    end

    local body, code = out:match("^(.*)\n(%d%d%d)%s*$")
    if not code then body, code = out:match("^(.*)\r\n(%d%d%d)%s*$") end
    return body or "", tonumber(code), nil

  elseif transport == "pwsh" then
    -- PowerShell path: embed body in here-string (safe enough given path validation + local origin)
    cmd = ps_post_json(url, tostring(json_body_str or ""))
    local rv, out = M.exec(cmd, timeout_ms)
    if rv ~= 0 or not out then
      return nil, nil, "HTTP failed/timeout (rv=" .. tostring(rv) .. ")"
    end
    local body, code = out:match("^(.*)\n(%d%d%d)%s*$")
    if not code then body, code = out:match("^(.*)\r\n(%d%d%d)%s*$") end
    return body or "", tonumber(code), nil

  else
    return nil, nil, "no HTTP transport (need curl or powershell)"
  end
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

-- URL encode (minimal; safe for query parameters)
function M.url_encode(s)
  s = tostring(s or "")
  s = s:gsub("\n", "\r\n")
  s = s:gsub("([^%w%-_%.~])", function(c)
    return string.format("%%%02X", string.byte(c))
  end)
  return s
end

function M.qs(params)
  if type(params) ~= "table" then return "" end
  local parts = {}
  for k, v in pairs(params) do
    local kk = M.url_encode(k)
    local vv = M.url_encode(v)
    parts[#parts + 1] = kk .. "=" .. vv
  end
  table.sort(parts)
  return table.concat(parts, "&")
end

-- JSON GET helper: returns decoded table or nil
function M.http_get_json(path, timeout_ms, jsonlib)
  local body, code, err = M.http_get(path, timeout_ms)
  if not body then return nil, code, err end
  if code and code >= 400 then return nil, code, body end
  if not jsonlib then
    local j, jerr = M.load_json()
    if not j then return nil, code, jerr end
    jsonlib = j
  end
  local ok, decoded = pcall(jsonlib.decode, body)
  if not ok then return nil, code, "json decode failed" end
  return decoded, code, nil
end

-- JSON POST helper: returns decoded table or nil
function M.http_post_json_decoded(path, payload_table, timeout_ms, jsonlib)
  if not jsonlib then
    local j, jerr = M.load_json()
    if not j then return nil, nil, jerr end
    jsonlib = j
  end
  local body_str = jsonlib.encode(payload_table or {})
  local body, code, err = M.http_post_json(path, body_str, timeout_ms)
  if not body then return nil, code, err end
  if code and code >= 400 then return nil, code, body end
  local ok, decoded = pcall(jsonlib.decode, body)
  if not ok then return nil, code, "json decode failed" end
  return decoded, code, nil
end

return M
