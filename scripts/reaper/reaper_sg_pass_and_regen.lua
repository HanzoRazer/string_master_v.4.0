--[[
  Smart Guitar: PASS and Regenerate (FAST)
  
  Reports a PASS verdict to sg-agentd and requests regeneration
  with updated difficulty/tempo based on policy.
  
  Episode 11: Displays coach_hint narrative after success.
  
  Usage: Bind to a key (e.g., F9) in Reaper Actions.
  
  ============================================================================
  CONTRACT NOTES (v1.0.0-offline)
  ============================================================================
  
  Response fields used:
    - status: "ok" | "partial" | "failed"
    - suggested_adjustment.coach_hint: string (deterministic narrative)
    - clip_id: new clip identifier
    - bundle_dir: path to generated bundle
  
  ExtState keys:
    - READ:  SG_AGENTD/last_clip_id
    - WRITE: SG_AGENTD/last_clip_id (updated to new clip)
  
  Bundle files read:
    - (none - reads from server response)
  
  Optional fields are optional - script must not fail if extras are missing.
  ============================================================================
]]

-- ============================================================================
-- Canonical JSON loader (same as reaper_sg_panel.lua)
-- ============================================================================
local json
do
  local script_path = ({reaper.get_action_context()})[2] or ""
  local script_dir = script_path:match("(.*[\\/])") or ""
  
  -- Try 1: json.lua in same folder
  local json_path = script_dir .. "json.lua"
  local f = io.open(json_path, "r")
  if f then
    f:close()
    json = dofile(json_path)
  end
  
  -- Try 2: dkjson (Reaper bundled)
  if not json then
    local ok, dkjson = pcall(require, "dkjson")
    if ok and dkjson then json = dkjson end
  end
  
  -- Fallback: stub that fails gracefully
  if not json then
    json = {
      encode = function() return "{}" end,
      decode = function() return nil, "no JSON library available" end,
    }
  end
end

-- ============================================================================
-- Configuration
-- ============================================================================

local EXT_SECTION = "SG_AGENTD"
local DEFAULT_HOST_PORT = "127.0.0.1:8420"

local function get_host_port()
  local hp = reaper.GetExtState(EXT_SECTION, "host_port")
  hp = tostring(hp or ""):gsub("^%s+",""):gsub("%s+$","")
  if hp == "" then hp = DEFAULT_HOST_PORT end
  if not hp:match("^[%w%.%-]+:%d+$") then
    hp = DEFAULT_HOST_PORT
  end
  return hp
end
local ENDPOINT = "/feedback_and_regen"
local VERDICT = "pass"

-- ============================================================================
-- Helpers
-- ============================================================================

local function msg(s)
  reaper.ShowConsoleMsg(tostring(s) .. "\n")
end

local function http_post(url, body, timeout_ms)
  timeout_ms = timeout_ms or 5000

  local tmp = os.tmpname()
  local f = io.open(tmp, "w")
  if not f then return nil, nil, "temp file error" end
  f:write(body)
  f:close()

  local cmd = string.format(
    'curl -s -X POST "%s" -H "Content-Type: application/json" --data-binary @"%s" -w "
%%{http_code}"',
    url, tmp
  )

  local rv, out = reaper.ExecProcess(cmd, timeout_ms)
  os.remove(tmp)

  if rv ~= 0 or not out then
    return nil, nil, "timeout or curl failure"
  end

  local resp, code = out:match("^(.*)
(%d%d%d)$")
  return resp or "", tonumber(code), nil
end

local function get_current_clip_id()
  -- Try to get clip_id from project notes or selected item
  -- For now, return a placeholder or parse from item name
  local item = reaper.GetSelectedMediaItem(0, 0)
  if item then
    local take = reaper.GetActiveTake(item)
    if take then
      local _, name = reaper.GetSetMediaItemTakeInfo_String(take, "P_NAME", "", false)
      -- Extract clip_id from name like "gen_abc123_comp"
      local clip_id = name:match("gen_([%w_]+)")
      if clip_id then return clip_id end
    end
  end
  return nil
end

local function extract_coach_hint(decoded)
  -- Episode 11: Extract coach_hint from response
  local coach_hint = nil
  
  -- Preferred: server returns top-level suggested block
  if decoded.suggested and decoded.suggested.coach_hint then
    coach_hint = decoded.suggested.coach_hint
  end
  
  -- Alternate: nested under regen
  if (not coach_hint) and decoded.regen and decoded.regen.suggested and decoded.regen.suggested.coach_hint then
    coach_hint = decoded.regen.suggested.coach_hint
  end
  
  -- Alternate: top-level coach_hint (ultra-minimal)
  if (not coach_hint) and decoded.coach_hint then
    coach_hint = decoded.coach_hint
  end
  
  return coach_hint
end

-- ============================================================================
-- Main
-- ============================================================================

local function main()
  msg("SG: Submitting PASS verdict...")
  
  local clip_id = get_current_clip_id()
  if not clip_id then
    msg("SG: ERROR - No clip selected or clip_id not found")
    return
  end
  
  -- Build request
  local request = {
    clip_id = clip_id,
    verdict = VERDICT,
  }
  
  local body = json.encode(request)
  local url = "http://" .. get_host_port() .. ENDPOINT
  
  -- Send request
  local response, code, post_err = http_post(url, body, 5000)
  if not response then
    msg("SG ERR: " .. tostring(post_err))
    return
  end
  if code and code >= 400 then
    msg("SG ERR: HTTP " .. tostring(code))
    msg(response)
    return
  end
  
  -- Decode response
  local decoded = json.decode(response)
  
  -- Check status
  if decoded.status ~= "ok" then
    msg("SG: ERROR - Server returned: " .. tostring(decoded.error or decoded.status))
    return
  end
  
  -- Success receipt
  local regen = decoded.regen
  if regen then
    msg(string.format("SG: PASS → regen queued (clip_id=%s)", regen.clip_id or "?"))
  else
    msg("SG: PASS → acknowledged")
  end
  
  -- Episode 11: Print coach hint
  local coach_hint = extract_coach_hint(decoded)
  if coach_hint and tostring(coach_hint) ~= "" then
    msg("SG: coach \226\134\146 " .. tostring(coach_hint))
  end
end

main()
