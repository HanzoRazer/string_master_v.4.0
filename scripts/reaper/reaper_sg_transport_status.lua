-- scripts/reaper/reaper_sg_transport_status.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Prints sg_http.lua transport_info() without running the full Doctor.
-- Zero prompts. Safe.

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end

local script_path = ({reaper.get_action_context()})[2] or ""
local script_dir = script_path:match("(.*/)")
                or script_path:match("(.+\\)")
                or ""

reaper.ClearConsole()
msg("============================================================")
msg("Smart Guitar — Transport Status")
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

-- Basic context
local hp = (type(sg.get_host_port) == "function") and sg.get_host_port() or "unknown"
local base = (type(sg.get_api_base) == "function") and sg.get_api_base() or "unknown"

msg("host_port: " .. tostring(hp))
msg("api_base:  " .. tostring(base))

-- Transport info
if type(sg.transport_info) ~= "function" then
  msg("SG ERR: sg_http.lua missing transport_info() (need Phase 8.5+)")
  msg("============================================================")
  return
end

local info = sg.transport_info() or {}
msg("override:  " .. tostring(info.override))
msg("chosen:    " .. tostring(info.transport))
msg("probed:    " .. tostring(info.probed))
if info.error and tostring(info.error) ~= "" then
  msg("error:     " .. tostring(info.error))
else
  msg("error:     (none)")
end

msg("------------------------------------------------------------")
msg("Tip: set override with reaper_sg_set_transport.lua (auto|curl|pwsh)")
msg("============================================================")
