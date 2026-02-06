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
msg("api_base: " .. tostring(api_base))

-- Transport info (Phase 8.5+)
if type(sg.transport_info) == "function" then
  local info = sg.transport_info() or {}
  msg("transport_override: " .. tostring(info.override))
  msg("transport_chosen:   " .. tostring(info.transport))
  if info.error and tostring(info.error) ~= "" then
    msg("transport_error:    " .. tostring(info.error))
  end
end

local session_id = (type(sg.get_ext) == "function") and sg.get_ext("session_id") or ""
if session_id == "" then session_id = "reaper_session" end

msg("session_id: " .. tostring(session_id))
msg("------------------------------------------------------------")

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

msg(string.format("%-4s  %-38s  %-4s  %-5s  %7s  %s", "METH", "PATH", "HTTP", "RES", "TIME", "NOTE"))
msg(string.rep("-", 86))

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
