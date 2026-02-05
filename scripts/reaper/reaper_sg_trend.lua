-- scripts/reaper/reaper_sg_trend.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Minimal Trend action:
-- - GET http://{host_port}/session_index?session_id=...
-- - Prints HTTP status + body
-- - Stub that can later be upgraded to a dedicated /trend endpoint.

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local script_dir = ({reaper.get_action_context()})[2]:match("(.*/)")
                or ({reaper.get_action_context()})[2]:match("(.+\\)")
                or ""

local sg = dofile(script_dir .. "sg_http.lua")

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Trend (minimal)")
msg("============================================================")

local session_id = sg.get_ext("session_id")
if session_id == "" then session_id = "reaper_session" end

-- Endpoint assumption (minimal v2 uses same session_index endpoint):
-- If your server has /trend, update PATH here.
local PATH = "/session_index?session_id=" .. session_id

msg("Target: " .. sg.get_api_base() .. PATH)

local body, code, err = sg.http_get(PATH, 4000)
if not body then
  msg("SG ERR: " .. tostring(err))
  msg("============================================================")
  return
end

msg("HTTP " .. tostring(code or "???"))
if sg.trim(body) ~= "" then
  msg(body)
else
  msg("(empty body)")
end

msg("============================================================")
