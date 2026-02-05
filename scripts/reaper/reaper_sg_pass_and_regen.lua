-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--[[
  Smart Guitar: PASS and Regenerate (FAST)
  
  Reports a PASS verdict to sg-agentd and requests regeneration
  with updated difficulty/tempo based on policy.
  
  Episode 11: Displays coach_hint narrative after success.
  Phase 6: Uses shared sg_http.lua helper for HTTP + ExtState.
  
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
-- Load shared sg_http.lua helper (Phase 6)
-- ============================================================================
local script_dir = ({reaper.get_action_context()})[2]:match("(.*/)")
                or ({reaper.get_action_context()})[2]:match("(.+\\)")
                or ""
local sg = dofile(script_dir .. "sg_http.lua")
local json, jerr = sg.load_json()
if not json then
  reaper.ShowConsoleMsg("SG ERR: " .. tostring(jerr) .. "\n")
  return
end

-- ============================================================================
-- Configuration
-- ============================================================================

local ENDPOINT = "/feedback_and_regen"
local VERDICT = "pass"

-- ============================================================================
-- Helpers
-- ============================================================================

local function msg(s)
  reaper.ShowConsoleMsg(tostring(s) .. "\n")
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
  
  -- Send request via shared helper
  local response, code, err = sg.http_post_json(ENDPOINT, body, 5000)
  if not response then
    msg("SG ERR: " .. tostring(err))
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
  
  -- Episode 11: Print coach hint via shared helper
  local coach_hint = sg.pick_coach_hint(decoded)
  if coach_hint and tostring(coach_hint) ~= "" then
    msg("SG: coach \226\134\146 " .. tostring(coach_hint))
  end
end

main()
