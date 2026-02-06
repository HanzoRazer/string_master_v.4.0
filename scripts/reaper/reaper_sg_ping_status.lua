-- scripts/reaper/reaper_sg_ping_status.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Quick ping: GET /status using sg_http.lua chosen transport.
-- Prints API base, transport info, HTTP code, and response body.
-- Zero prompts. Safe.

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local function trim(s)
  return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$",""))
end

local script_path = ({reaper.get_action_context()})[2] or ""
local script_dir = script_path:match("(.*/)")
                or script_path:match("(.+\\)")
                or ""

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Ping /status")
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
else
  msg("transport_info: (missing; need Phase 8.5+ sg_http.lua)")
end

-- Ping
if type(sg.http_get) ~= "function" then
  msg("SG ERR: sg_http.lua missing http_get()")
  msg("============================================================")
  return
end

msg("------------------------------------------------------------")
msg("GET /status ...")

local body, code, err = sg.http_get("/status", 2500)
if not body then
  msg("SG ERR: " .. tostring(err))
  msg("============================================================")
  return
end

msg("HTTP " .. tostring(code or "???"))

local b = tostring(body or "")
b = trim(b)

-- Prevent console spam
local MAX_CHARS = 4000
if #b > MAX_CHARS then
  msg(b:sub(1, MAX_CHARS))
  msg(("...(truncated; %d chars total)"):format(#b))
else
  if b == "" then
    msg("(empty body)")
  else
    msg(b)
  end
end

msg("============================================================")
msg("Result: " .. ((code and code >= 200 and code < 300) and "OK" or "NOT OK"))
msg("============================================================")
