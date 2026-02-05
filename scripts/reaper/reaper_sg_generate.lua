-- scripts/reaper/reaper_sg_generate.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Minimal Generate action:
-- - POST http://{host_port}/generate
-- - Payload (minimal): { session_id, request_id }
-- - Prints HTTP status + response body
-- - If response includes coach_hint (via contract chain), prints it

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local script_dir = ({reaper.get_action_context()})[2]:match("(.*/)")
                or ({reaper.get_action_context()})[2]:match("(.+\\)")
                or ""

local sg = dofile(script_dir .. "sg_http.lua")
local json, jerr = sg.load_json()
if not json then
  msg("SG ERR: " .. tostring(jerr))
  return
end

local function gen_request_id()
  -- Simple deterministic-ish ID: time + random
  math.randomseed((reaper.time_precise() * 1000) % 2147483647)
  local t = tostring(math.floor(reaper.time_precise() * 1000))
  local r = tostring(math.random(100000, 999999))
  return "reaper_" .. t .. "_" .. r
end

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Generate (minimal)")
msg("============================================================")

local session_id = sg.get_ext("session_id")
if session_id == "" then session_id = "reaper_session" end

local payload = {
  session_id = session_id,
  request_id = gen_request_id(),
}

local body_str = json.encode(payload)

-- Endpoint assumption for minimal v2:
-- If your sg-agentd uses a different route, change PATH here once.
local PATH = "/generate"

msg("Target: " .. sg.get_api_base() .. PATH)
msg("session_id=" .. tostring(session_id))
msg("request_id=" .. tostring(payload.request_id))

local resp, code, err = sg.http_post_json(PATH, body_str, 8000)
if not resp then
  msg("SG ERR: " .. tostring(err))
  msg("============================================================")
  return
end

msg("HTTP " .. tostring(code or "???"))
if sg.trim(resp) ~= "" then
  msg(resp)
end

-- Best-effort decode + coach hint
local ok_dec, decoded = pcall(json.decode, resp)
if ok_dec and type(decoded) == "table" then
  local coach = sg.pick_coach_hint(decoded)
  if coach then
    msg("SG: coach → " .. coach)
  end
end

msg("============================================================")
