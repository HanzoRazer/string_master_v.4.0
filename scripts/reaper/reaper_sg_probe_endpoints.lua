-- scripts/reaper/reaper_sg_probe_endpoints.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Phase 9: Endpoint Inventory Probe + Compatibility Matrix
-- Uses sg_http.lua chosen transport (auto|curl|pwsh) to test sg-agentd endpoints.
-- Zero prompts. Safe. Uses minimal payloads.

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local function trim(s)
  return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$",""))
end

local function now_ms()
  return math.floor(reaper.time_precise() * 1000)
end

local function truncate(s, max_chars)
  s = tostring(s or "")
  max_chars = tonumber(max_chars or 2000)
  if #s <= max_chars then return s, false end
  return s:sub(1, max_chars), true
end

local function iso_stamp()
  -- Local time-ish stamp: YYYYMMDD_HHMMSS
  local t = os.date("*t")
  return string.format("%04d%02d%02d_%02d%02d%02d",
    t.year, t.month, t.day, t.hour, t.min, t.sec)
end

local function get_reaper_version()
  -- Returns version string like "7.XX" (exact formatting depends on Reaper)
  return tostring(reaper.GetAppVersion() or "unknown")
end

local function get_os_name()
  -- package.config path separator is "\" on Windows
  local sep = package.config:sub(1,1)
  if sep == "\\" then return "Windows" end
  -- Reaper exposes OS in GetOS(); keep as extra signal if available
  if type(reaper.GetOS) == "function" then
    local os = tostring(reaper.GetOS() or "")
    if os ~= "" then return os end
  end
  return "macOS/Linux"
end

local function parse_host_port(hp)
  hp = trim(hp or "")
  local host, port = hp:match("^(.+):(%%d+)$")
  return host, tonumber(port)
end

local function is_ipv4(host)
  if not host then return false end
  local a,b,c,d = host:match("^(%%d+)%%.(%%d+)%%.(%%d+)%%.(%%d+)$")
  a,b,c,d = tonumber(a), tonumber(b), tonumber(c), tonumber(d)
  if not a then return false end
  if a<0 or a>255 or b<0 or b>255 or c<0 or c>255 or d<0 or d>255 then return false end
  return true
end

local function is_private_ipv4(host)
  if not is_ipv4(host) then return false end
  local a,b,c,d = host:match("^(%%d+)%%.(%%d+)%%.(%%d+)%%.(%%d+)$")
  a,b,c,d = tonumber(a), tonumber(b), tonumber(c), tonumber(d)
  if a == 10 then return true end
  if a == 172 and b >= 16 and b <= 31 then return true end
  if a == 192 and b == 168 then return true end
  return false
end

local function host_kind(host)
  host = tostring(host or ""):lower()
  if host == "localhost" or host == "127.0.0.1" then return "loopback" end
  if is_ipv4(host) then return "ipv4" end
  return "hostname"
end

local function lan_misconfig_warnings(host)
  local warns = {}

  local hk = host_kind(host)
  local h = tostring(host or ""):lower()

  if hk == "loopback" then
    warns[#warns+1] = "host is loopback (localhost/127.0.0.1). If sg-agentd runs on a LAN server, set host_port to that LAN IP/hostname."
  end

  if hk == "hostname" then
    -- hostnames without dots often rely on local search domains and fail in labs
    if not h:find("%%.", 1, true) and h ~= "localhost" then
      warns[#warns+1] = "hostname has no dot. DNS/search-domain may fail in labs; prefer a LAN IP (e.g., 192.168.x.x) or a full hostname."
    end
  end

  if hk == "ipv4" then
    if not is_private_ipv4(host) and h ~= "127.0.0.1" then
      warns[#warns+1] = "IPv4 is not private RFC1918. In classrooms this is unusual; confirm routing/firewall rules."
    end
  end

  return warns
end

local function lan_ready(host_kind_str, status_code, transport_chosen, transport_error, host_warns)
  local ok_status = (type(status_code) == "number") and (status_code >= 200 and status_code < 300)
  local ok_transport = (tostring(transport_chosen) ~= "" and tostring(transport_chosen) ~= "none" and tostring(transport_chosen) ~= "unknown")
  local ok_transport_err = (trim(transport_error or "") == "")

  -- LAN-ready implies the target is not loopback (unless you explicitly want localhost labs)
  local not_loopback = (tostring(host_kind_str) ~= "loopback")

  -- If there are any host_port sanity warnings, treat as not LAN-ready by default
  local warns = (type(host_warns) == "table") and #host_warns or 0
  local ok_host = (warns == 0) and not_loopback

  local ready = ok_status and ok_transport and ok_transport_err and ok_host
  return ready, {
    ok_status = ok_status,
    ok_transport = ok_transport,
    ok_transport_err = ok_transport_err,
    ok_host = ok_host,
    warns = warns,
  }
end

local function ensure_dir(path)
  if reaper.RecursiveCreateDirectory then
    reaper.RecursiveCreateDirectory(path, 0)
    return true
  end
  return true
end

local function read_file(path)
  local f = io.open(path, "r")
  if not f then return nil end
  local t = f:read("*a")
  f:close()
  return t
end

local function read_bundle_version(script_dir)
  local p = script_dir .. "SG_BUNDLE_VERSION.txt"
  local t = read_file(p)
  t = trim(t or "")
  if t == "" then return "unknown" end
  return t
end

local function ext_get(section, key)
  return trim(reaper.GetExtState(section, key))
end

local function write_known_extstate_snapshot(f)
  local S = "SG_AGENTD"
  local known = {
    "host_port",
    "session_id",
    "transport",
    "last_clip_id",
    "action_generate",
    "action_pass_regen",
    "action_struggle_regen",
    "action_timeline",
    "action_trend",
  }

  f:write("ExtState Snapshot (Known Keys)\n")
  f:write("------------------------------------------------------------\n")
  for _, k in ipairs(known) do
    local v = ext_get(S, k)
    if v == "" then v = "(empty)" end
    f:write(string.format("%s/%s = %s\n", S, k, v))
  end
end

local function write_full_extstate_snapshot_if_possible(f)
  local S = "SG_AGENTD"

  -- Some environments may have enumeration (not guaranteed).
  -- If unavailable, we report that and still provide Known Keys above.
  if type(reaper.EnumExtState) ~= "function" then
    f:write("\nExtState Snapshot (Full Enumeration)\n")
    f:write("------------------------------------------------------------\n")
    f:write("EnumExtState unavailable in this Reaper build; full key enumeration not possible.\n")
    return
  end

  f:write("\nExtState Snapshot (Full Enumeration)\n")
  f:write("------------------------------------------------------------\n")
  local i = 0
  while true do
    local key = reaper.EnumExtState(S, i)
    if not key then break end
    local v = ext_get(S, key)
    if v == "" then v = "(empty)" end
    f:write(string.format("%s/%s = %s\n", S, key, v))
    i = i + 1
    if i > 5000 then
      f:write("...stopped after 5000 keys (safety cap)\n")
      break
    end
  end
end

local script_path = ({reaper.get_action_context()})[2] or ""
local script_dir = script_path:match("(.*/)")
                or script_path:match("(.+\\)")
                or ""

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Endpoint Probe (Compatibility Matrix)")
msg("============================================================")

-- Load sg_http.lua
local ok_sg, sg = pcall(dofile, script_dir .. "sg_http.lua")
if not ok_sg or type(sg) ~= "table" then
  msg("SG ERR: failed to load sg_http.lua")
  msg("       expected at: " .. (script_dir .. "sg_http.lua"))
  msg("       error: " .. tostring(sg))
  msg("============================================================")
  return
end

-- Load json.lua (optional; probe can run without it for GETs, but needed for POST bodies)
local json = nil
if type(sg.load_json) == "function" then
  local j, jerr = sg.load_json()
  if not j then
    msg("SG WARN: json.lua not available (" .. tostring(jerr) .. ") — POST probes may be limited")
  else
    json = j
  end
end

local api_base = (type(sg.get_api_base) == "function") and sg.get_api_base() or "unknown"
local host_port = (type(sg.get_host_port) == "function") and sg.get_host_port() or "unknown"
local bundle_ver = read_bundle_version(script_dir)
local reaper_ver = get_reaper_version()
local os_name = get_os_name()
local resource_path = tostring(reaper.GetResourcePath() or "unknown")

msg("bundle_version: " .. tostring(bundle_ver))
msg("api_base:       " .. tostring(api_base))

local hp_host, hp_port = parse_host_port(host_port)
msg("host:          " .. tostring(hp_host or "unknown"))
msg("port:          " .. tostring(hp_port or "unknown"))
msg("host_kind:     " .. tostring(host_kind(hp_host)))

local hp_warns = lan_misconfig_warnings(hp_host)
for _, w in ipairs(hp_warns) do
  msg("SG WARN: host_port sanity: " .. w)
end

local host_kind_str = tostring(host_kind(hp_host))
local hp_warns_list = hp_warns

-- Capture transport probe timing
local probe_t0 = now_ms()
if type(sg.choose_transport) == "function" then
  sg.choose_transport()
end
local probe_dt = now_ms() - probe_t0
local transport_probe_ms = probe_dt

-- Transport info (Phase 8.5+)
local transport_override, transport_chosen, transport_error = "unknown", "unknown", ""
if type(sg.transport_info) == "function" then
  local info = sg.transport_info() or {}
  transport_override = tostring(info.override)
  transport_chosen = tostring(info.transport)
  transport_error = tostring(info.error or "")
  msg("transport_override: " .. transport_override)
  msg("transport_chosen:   " .. transport_chosen)
  msg("transport_probe_ms: " .. tostring(transport_probe_ms))
  if transport_error ~= "" then
    msg("transport_error:    " .. transport_error)
  end
end

local session_id = (type(sg.get_ext) == "function") and sg.get_ext("session_id") or ""
if session_id == "" then session_id = "reaper_session" end
msg("session_id:    " .. tostring(session_id))
msg("------------------------------------------------------------")

-- Report buffer (string builder)
local report = {}
local function rep(s) report[#report + 1] = tostring(s) end

local function classify(code, err)
  if err then return "FAIL", err end
  if not code then return "FAIL", "no http code" end
  if code >= 200 and code < 300 then return "OK", "" end
  if code >= 300 and code < 400 then return "WARN", "redirect" end
  if code >= 400 and code < 500 then return "WARN", "client error" end
  if code >= 500 then return "FAIL", "server error" end
  return "WARN", "unknown"
end

local function row(method, path, code, result, note, ms)
  msg(string.format("%-4s  %-38s  %-4s  %-5s  %5dms  %s",
    tostring(method),
    tostring(path),
    tostring(code or "---"),
    tostring(result),
    tonumber(ms or 0),
    tostring(note or "")
  ))
end

local function probe_get(path, timeout_ms)
  local t0 = now_ms()
  local body, code, err = sg.http_get(path, timeout_ms or 2500)
  local dt = now_ms() - t0
  local result, note = classify(code, err)
  if result == "OK" and trim(body) == "" then note = "empty body" end
  row("GET", path, code, result, note, dt)
  return body, code, err
end

local function probe_post(path, payload_table, timeout_ms)
  local t0 = now_ms()

  if not json then
    local dt = now_ms() - t0
    row("POST", path, nil, "FAIL", "json.lua missing (cannot encode payload)", dt)
    return nil, nil, "json missing"
  end

  if type(sg.http_post_json) ~= "function" then
    local dt = now_ms() - t0
    row("POST", path, nil, "FAIL", "sg_http.lua missing http_post_json()", dt)
    return nil, nil, "no post"
  end

  local body_str = json.encode(payload_table or {})
  local body, code, err = sg.http_post_json(path, body_str, timeout_ms or 5000)
  local dt = now_ms() - t0
  local result, note = classify(code, err)

  -- If JSON response and contains coach_hint, print short hint line
  if result == "OK" and body and trim(body) ~= "" then
    local ok_dec, decoded = pcall(json.decode, body)
    if ok_dec and type(decoded) == "table" and type(sg.pick_coach_hint) == "function" then
      local coach = sg.pick_coach_hint(decoded)
      if coach and coach ~= "" then
        note = "coach_hint present"
      end
    end
  end

  row("POST", path, code, result, note, dt)
  return body, code, err
end

-- ---------------------------
-- PROBE SET
-- ---------------------------

local header = string.format("%-4s  %-38s  %-4s  %-5s  %7s  %s", "METH", "PATH", "HTTP", "RES", "TIME", "NOTE")
msg(header); rep(header)
local sep = string.rep("-", 86)
msg(sep); rep(sep)

-- 1) Health - capture raw /status body
local status_t0 = now_ms()
local status_body, status_code, status_err = sg.http_get("/status", 2500)
local status_dt = now_ms() - status_t0

do
  local result, note = classify(status_code, status_err)
  if result == "OK" and trim(status_body or "") == "" then note = "empty body" end
  local line = row_line("GET", "/status", status_code, result, note, status_dt)
  msg(line); rep(line)
end

-- 2) Session index + optional trend/timeline
local qs = (type(sg.qs) == "function") and sg.qs({ session_id = session_id }) or ("session_id=" .. session_id)
probe_get("/session_index?" .. qs, 2500)
probe_get("/timeline?" .. qs, 2500)
probe_get("/trend?" .. qs, 2500)

-- 3) Generation
probe_post("/generate", {
  session_id = session_id,
  request_id = "probe_" .. tostring(now_ms())
}, 8000)

-- 4) Feedback/regen candidates (PASS/STRUGGLE)
local base_payload = {
  session_id = session_id,
  clip_id = "probe_clip",
}

probe_post("/feedback_and_regen",  { session_id=session_id, clip_id="probe_clip", verdict="PASS" }, 5000)
probe_post("/pass_and_regen",      { session_id=session_id, clip_id="probe_clip", verdict="PASS" }, 5000)
probe_post("/struggle_and_regen",  { session_id=session_id, clip_id="probe_clip", verdict="STRUGGLE" }, 5000)
probe_post("/regen",              { session_id=session_id, clip_id="probe_clip", verdict="PASS" }, 5000)

msg("------------------------------------------------------------")
msg("Interpretation:")
msg("  OK   = endpoint reachable + responded 2xx")
msg("  WARN = endpoint responded but may require different params/body (4xx) or redirected (3xx)")
msg("  FAIL = timeout/transport failure or server error (5xx)")
msg("============================================================")

-- ---------------------------
-- Write report file
-- ---------------------------
local resource = reaper.GetResourcePath()
local out_dir = resource .. (resource:sub(-1) == "\\" and "" or "") .. "/SG_reports"
out_dir = out_dir:gsub("\\/", "/")
ensure_dir(out_dir)

local fname = "SG_probe_" .. iso_stamp() .. ".txt"
local out_path = out_dir .. "/" .. fname

local f = io.open(out_path, "w")
if not f then
  msg("SG WARN: could not write report file: " .. tostring(out_path))
  return
end

f:write("Smart Guitar — Endpoint Probe Report\n")
f:write("============================================================\n")
f:write("date_local: " .. os.date("%Y-%m-%d %H:%M:%S") .. "\n")
f:write("os: " .. tostring(os_name) .. "\n")
f:write("reaper_version: " .. tostring(reaper_ver) .. "\n")
f:write("reaper_resource_path: " .. tostring(resource_path) .. "\n")
f:write("bundle_script_dir: " .. tostring(script_dir) .. "\n")
f:write("bundle_version: " .. tostring(bundle_ver) .. "\n")
f:write("host_port: " .. tostring(host_port) .. "\n")
f:write("host: " .. tostring(hp_host or "unknown") .. "\n")
f:write("port: " .. tostring(hp_port or "unknown") .. "\n")
f:write("host_kind: " .. tostring(host_kind_str or "unknown") .. "\n")
if hp_warns_list and #hp_warns_list > 0 then
  f:write("host_port_warnings:\n")
  for _, w in ipairs(hp_warns_list) do
    f:write("  - " .. tostring(w) .. "\n")
  end
end
f:write("route_hint: ")
if host_kind(hp_host) == "loopback" then
  f:write("requests stay on this machine\n")
elseif host_kind(hp_host) == "ipv4" and is_private_ipv4(hp_host) then
  f:write("LAN private IP target (check same subnet/VLAN + firewall)\n")
else
  f:write("hostname target (check DNS/search domain)\n")
end
f:write("api_base: " .. tostring(api_base) .. "\n")
f:write("session_id: " .. tostring(session_id) .. "\n")
f:write("transport_override: " .. tostring(transport_override) .. "\n")
f:write("transport_chosen: " .. tostring(transport_chosen) .. "\n")
f:write("transport_probe_ms: " .. tostring(transport_probe_ms or 0) .. "\n")
if trim(transport_error) ~= "" then
  f:write("transport_error: " .. tostring(transport_error) .. "\n")
end
f:write("------------------------------------------------------------\n")
f:write("/status raw (truncated)\n")
f:write("status_http: " .. tostring(status_code or "nil") .. "\n")
f:write("status_time_ms: " .. tostring(status_dt or 0) .. "\n")
if status_err and tostring(status_err) ~= "" then
  f:write("status_error: " .. tostring(status_err) .. "\n")
end

local raw, truncated = truncate(status_body or "", 2000)
f:write("status_body:\n")
f:write(raw .. "\n")
if truncated then
  f:write("(truncated)\n")
end
f:write("------------------------------------------------------------\n")
for _, line in ipairs(report) do
  f:write(line .. "\n")
end
f:write("------------------------------------------------------------\n")
f:write("Legend: OK=2xx WARN=3xx/4xx FAIL=timeout/transport/5xx\n")

f:write("============================================================\n")
write_known_extstate_snapshot(f)
write_full_extstate_snapshot_if_possible(f)
f:write("============================================================\n")

local ready, bits = lan_ready(host_kind_str, status_code, transport_chosen, transport_error, hp_warns_list)
local lan_ready_str = ready and "yes" or "no"
f:write("LAN_READY: " .. lan_ready_str .. "\n")
f:write(string.format("LAN_READY_DETAIL: status_ok=%s transport_ok=%s transport_err_ok=%s host_ok=%s host_warns=%d\n",
  tostring(bits.ok_status),
  tostring(bits.ok_transport),
  tostring(bits.ok_transport_err),
  tostring(bits.ok_host),
  tonumber(bits.warns or 0)
))

f:close()

msg("SG OK: wrote report → " .. out_path)
msg("LAN_READY: " .. lan_ready_str)
