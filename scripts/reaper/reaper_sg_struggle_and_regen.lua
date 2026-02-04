--[[
  Smart Guitar: STRUGGLE and Regenerate (FAST)
  
  Reports a STRUGGLE verdict to sg-agentd and requests regeneration
  with reduced difficulty/tempo based on policy.
  
  Episode 11: Displays coach_hint narrative after success.
  
  Usage: Bind to a key (e.g., F10) in Reaper Actions.
  
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

local json = require("json")

-- ============================================================================
-- Configuration
-- ============================================================================

local SG_AGENTD_URL = "http://localhost:7878"
local ENDPOINT = "/feedback_and_regen"
local VERDICT = "struggle"

-- ============================================================================
-- Helpers
-- ============================================================================

local function msg(s)
  reaper.ShowConsoleMsg(tostring(s) .. "\n")
end

local function http_post(url, body)
  -- Use ReaScript's built-in HTTP (requires js_ReaScriptAPI or similar)
  -- Fallback: use curl via os.execute
  local tmp_in = os.tmpname()
  local tmp_out = os.tmpname()
  
  local f = io.open(tmp_in, "w")
  f:write(body)
  f:close()
  
  local cmd = string.format(
    'curl -s -X POST "%s" -H "Content-Type: application/json" -d @"%s" -o "%s"',
    url, tmp_in, tmp_out
  )
  os.execute(cmd)
  
  local f2 = io.open(tmp_out, "r")
  local response = f2 and f2:read("*a") or ""
  if f2 then f2:close() end
  
  os.remove(tmp_in)
  os.remove(tmp_out)
  
  return response
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
  msg("SG: Submitting STRUGGLE verdict...")
  
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
  local url = SG_AGENTD_URL .. ENDPOINT
  
  -- Send request
  local response = http_post(url, body)
  
  if not response or response == "" then
    msg("SG: ERROR - No response from server")
    return
  end
  
  -- Decode response
  local ok, decoded = pcall(json.decode, response)
  if not ok then
    msg("SG: ERROR - Failed to parse response: " .. tostring(decoded))
    return
  end
  
  -- Check status
  if decoded.status ~= "ok" then
    msg("SG: ERROR - Server returned: " .. tostring(decoded.error or decoded.status))
    return
  end
  
  -- Success receipt
  local regen = decoded.regen
  if regen then
    msg(string.format("SG: STRUGGLE → regen queued (clip_id=%s)", regen.clip_id or "?"))
  else
    msg("SG: STRUGGLE → acknowledged")
  end
  
  -- Episode 11: Print coach hint
  local coach_hint = extract_coach_hint(decoded)
  if coach_hint and tostring(coach_hint) ~= "" then
    msg("SG: coach \226\134\146 " .. tostring(coach_hint))
  end
end

main()
