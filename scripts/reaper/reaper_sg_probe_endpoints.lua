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

local function iso_stamp()
  -- Local time-ish stamp: YYYYMMDD_HHMMSS
  local t = os.date("*t")
  return string.format("%04d%02d%02d_%02d%02d%02d",
    t.year, t.month, t.day, t.hour, t.min, t.sec)
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

msg("bundle_version: " .. tostring(bundle_ver))
msg("api_base:       " .. tostring(api_base))

-- Transport info (Phase 8.5+)
local transport_override, transport_chosen, transport_error = "unknown", "unknown", ""
if type(sg.transport_info) == "function" then
  local info = sg.transport_info() or {}
  transport_override = tostring(info.override)
  transport_chosen = tostring(info.transport)
  transport_error = tostring(info.error or "")
  msg("transport_override: " .. transport_override)
  msg("transport_chosen:   " .. transport_chosen)
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

-- 1) Health
probe_get("/status", 2500)

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
f:write("bundle_version: " .. tostring(bundle_ver) .. "\n")
f:write("host_port: " .. tostring(host_port) .. "\n")
f:write("api_base: " .. tostring(api_base) .. "\n")
f:write("session_id: " .. tostring(session_id) .. "\n")
f:write("transport_override: " .. tostring(transport_override) .. "\n")
f:write("transport_chosen: " .. tostring(transport_chosen) .. "\n")
if trim(transport_error) ~= "" then
  f:write("transport_error: " .. tostring(transport_error) .. "\n")
end
f:write("------------------------------------------------------------\n")
for _, line in ipairs(report) do
  f:write(line .. "\n")
end
f:write("------------------------------------------------------------\n")
f:write("Legend: OK=2xx WARN=3xx/4xx FAIL=timeout/transport/5xx\n")
f:close()

msg("SG OK: wrote report → " .. out_path)
