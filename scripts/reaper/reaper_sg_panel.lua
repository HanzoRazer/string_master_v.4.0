-- scripts/reaper/reaper_sg_panel.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- Episode 13A: Visual SG Panel (Reaper gfx window)
--
-- Requirements:
--   - json.lua in same folder as script
--   - Reaper ExtState keys set for action IDs (optional but recommended):
--       SG_AGENTD/action_generate
--       SG_AGENTD/action_pass_regen
--       SG_AGENTD/action_struggle_regen
--       SG_AGENTD/action_timeline
--       SG_AGENTD/action_trend
--   - sg-agentd running for /session_index refresh (optional; panel still shows coach file if present)
--
-- ============================================================================
-- CONTRACT NOTES (v1.0.0-offline)
-- ============================================================================
--
-- Data sources (priority order):
--   1. ExtState (fast): last_clip_id, session_id, action IDs
--   2. Bundle file: clip.coach.json for "Now" fields
--   3. /session_index: for last N + trends
--
-- ExtState keys read:
--   SG_AGENTD/last_clip_id
--   SG_AGENTD/session_id
--   SG_AGENTD/action_generate
--   SG_AGENTD/action_pass_regen
--   SG_AGENTD/action_struggle_regen
--   SG_AGENTD/action_timeline
--   SG_AGENTD/action_trend
--   SG_AGENTD/host_port
--
-- Failure behavior:
--   - If anything fails, show "stale" state but don't crash
--   - Panel continues running even without server
-- ============================================================================

local EXT_SECTION = "SG_AGENTD"

-- Build API_BASE from ExtState host_port (fallback to 127.0.0.1:8420 if not set)
local function get_api_base()
  local hp = reaper.GetExtState(EXT_SECTION, "host_port")
  if hp == nil or hp == "" then hp = "127.0.0.1:8420" end
  return "http://" .. hp
end
local API_BASE = get_api_base()
local EXT_LAST_CLIP = "last_clip_id"
local EXT_SESSION_ID = "session_id"

local K_GEN   = "action_generate"
local K_PASS  = "action_pass_regen"
local K_STRUG = "action_struggle_regen"
local K_TLINE = "action_timeline"
local K_TREND = "action_trend"

-- ------------------------------- utils -------------------------------------
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end
local function short_id(x)
  x = tostring(x or "")
  if x == "" then return "?" end
  if #x <= 14 then return x end
  return x:sub(1, 9) .. "…" .. x:sub(-6)
end
local function fmt(x, dec)
  local n = tonumber(x); if not n then return "?" end
  return string.format("%."..tostring(dec or 0).."f", n)
end
local function file_read(path)
  local f = io.open(path, "rb")
  if not f then return nil end
  local t = f:read("*a")
  f:close()
  return t
end
local function file_exists(path)
  local f = io.open(path, "rb")
  if f then f:close(); return true end
  return false
end

-- ------------------------------ json (canonical loader) --------------------
-- CONTRACT V1: json.lua only (no dkjson fallback)
local json
do
  local script_path = ({reaper.get_action_context()})[2] or ""
  local script_dir = script_path:match("(.*[\\/])") or ""
  
  local json_path = script_dir .. "json.lua"
  local f = io.open(json_path, "r")
  if f then
    f:close()
    json = dofile(json_path)
  end
  
  -- Fallback: stub that fails gracefully
  if not json then
    json = {
      encode = function() return "{}" end,
      decode = function() return nil, "json.lua not found" end,
    }
  end
end

-- ------------------------------ http ---------------------------------------
local function url_encode(s)
  s = tostring(s or "")
  s = s:gsub("\n", "\r\n")
  s = s:gsub("([^%w %-%_%.%~])", function(c) return string.format("%%%02X", string.byte(c)) end)
  s = s:gsub(" ", "%%20")
  return s
end

local function http_get(url, timeout_ms)
  local cmd = 'curl -s -X GET -w "\\n%{http_code}" "' .. url .. '"'
  local rv, out = reaper.ExecProcess(cmd, timeout_ms or 8000)
  if rv ~= 0 or not out then return nil, nil end
  local body, code = out:match("^(.*)\n(%d%d%d)$")
  if not code then body, code = out:match("^(.*)\r\n(%d%d%d)$") end
  return body, tonumber(code)
end

-- ------------------------------ actions ------------------------------------
local function get_ext(key) return trim(reaper.GetExtState(EXT_SECTION, key)) end
local function resolve_named(cmd_str)
  cmd_str = trim(cmd_str)
  if cmd_str == "" then return nil end
  local n = reaper.NamedCommandLookup(cmd_str)
  if not n or n == 0 then return nil end
  return n
end
local function run_action(ext_key)
  local cmd = get_ext(ext_key)
  local n = resolve_named(cmd)
  if n then reaper.Main_OnCommand(n, 0) end
end

-- ------------------------------ state --------------------------------------
local state = {
  last_clip_id = "",
  coach_path = "",
  coach = nil,
  coach_err = "",
  session = nil,
  session_err = "",
  last_session_fetch = 0.0,
  last_coach_fetch = 0.0,
}

-- Coach path strategy:
-- 1) If clip_id is known, derive from last seen bundle dir if present in session entry
-- 2) Else fallback to commonly persisted bundle path in ExtState if you add it later
-- For now: prefer session index entry; otherwise do nothing.

local function coach_from_doc(doc)
  -- supports either your deterministic coach format:
  -- doc.assignment.* + lineage.* OR "decision" format if you migrate later.
  local a = doc.assignment or doc.assignment_block or nil
  local lineage = doc.lineage or {}

  local out = {
    objective = a and a.objective or doc.objective or "timing_and_chord_hits",
    tempo = a and (a.target_tempo_bpm or a.target_tempo) or doc.target_tempo_bpm or nil,
    tempo_delta = a and a.tempo_delta_bpm or doc.tempo_delta_bpm or nil,
    loop_bars = a and a.loop_bars or doc.loop_bars or nil,
    chord_count = a and a.chord_count or doc.chord_count or nil,
    density = a and (a.density_bucket or a.density) or doc.density_bucket or doc.applied_density or nil,
    sync_bucket = a and (a.syncopation_bucket or a.sync_bucket) or doc.syncopation_bucket or doc.applied_syncopation_bucket or nil,
    sync_scalar = a and (a.syncopation_scalar or a.applied_syncopation) or doc.applied_syncopation or nil,
    score = doc.score or (a and a.score) or nil,
    gen = lineage.generation_number or doc.generation_number or nil,
    parent = lineage.parent_clip_id or doc.parent_clip_id or nil,
    hint = doc.coach_hint or doc.hint or "",
  }
  return out
end

local function compute_counts(entries)
  local take = {pass=0, struggle=0, other=0}
  local dens = {sparse=0, medium=0, dense=0, other=0}
  local sync = {straight=0, light=0, heavy=0, other=0}

  local score_sum, score_n = 0.0, 0
  local tempo_first, tempo_last = nil, nil

  for _, e in ipairs(entries) do
    local tr = e.take_result or e.verdict
    if tr == "pass" then take.pass = take.pass + 1
    elseif tr == "struggle" then take.struggle = take.struggle + 1
    else take.other = take.other + 1 end

    local d = e.density_bucket or e.applied_density
    if d == "sparse" then dens.sparse = dens.sparse + 1
    elseif d == "medium" then dens.medium = dens.medium + 1
    elseif d == "dense" then dens.dense = dens.dense + 1
    else dens.other = dens.other + 1 end

    local sb = e.syncopation_bucket or e.applied_syncopation_bucket
    if sb == "straight" then sync.straight = sync.straight + 1
    elseif sb == "light" then sync.light = sync.light + 1
    elseif sb == "heavy" then sync.heavy = sync.heavy + 1
    else sync.other = sync.other + 1 end

    if e.score ~= nil then
      local s = tonumber(e.score)
      if s then score_sum = score_sum + s; score_n = score_n + 1 end
    end

    local tp = e.target_tempo_bpm or e.applied_tempo_bpm or e.tempo_bpm
    local tpn = tonumber(tp)
    if tpn then
      if not tempo_first then tempo_first = tpn end
      tempo_last = tpn
    end
  end

  local score_avg = (score_n > 0) and (score_sum / score_n) or nil
  local tempo_drift = (tempo_first and tempo_last) and (tempo_last - tempo_first) or nil

  return take, dens, sync, score_avg, tempo_first, tempo_last, tempo_drift
end

-- ------------------------------ refresh ------------------------------------
local function refresh_session_if_needed(now)
  local session_id = get_ext(EXT_SESSION_ID)
  if session_id == "" then session_id = "reaper_session" end

  if (now - state.last_session_fetch) < 1.0 then return end
  state.last_session_fetch = now

  local url = API_BASE .. "/session_index?session_id=" .. url_encode(session_id)
  local body, code = http_get(url, 1000)
  if not body or (code and code ~= 200) then
    state.session = nil
    state.session_err = "session_index unavailable"
    return
  end

  local doc, _, dec_err = json.decode(body, 1, nil)
  if not doc then
    state.session = nil
    state.session_err = "session_index decode failed"
    return
  end

  state.session = doc
  state.session_err = ""
end

local function resolve_coach_path_from_session(clip_id)
  if not state.session or not state.session.entries then return nil end
  for i = #state.session.entries, 1, -1 do
    local e = state.session.entries[i]
    if e.clip_id == clip_id and e.bundle_dir and e.bundle_dir ~= "" then
      local sep = package.config:sub(1, 1) or "\\"
      return tostring(e.bundle_dir) .. sep .. "clip.coach.json"
    end
  end
  return nil
end

local function refresh_coach_if_needed(now)
  local clip_id = get_ext(EXT_LAST_CLIP)
  if clip_id == "" then
    state.coach = nil
    state.coach_err = "No last_clip_id yet (run Generate)"
    state.last_clip_id = ""
    return
  end

  if clip_id ~= state.last_clip_id then
    state.last_clip_id = clip_id
    state.coach = nil
    state.coach_err = ""
    state.coach_path = ""
  end

  if (now - state.last_coach_fetch) < 0.5 then return end
  state.last_coach_fetch = now

  local path = resolve_coach_path_from_session(clip_id)
  if not path then
    state.coach = nil
    state.coach_err = "Coach path unknown (need session_index or bundle path)"
    return
  end

  if not file_exists(path) then
    state.coach = nil
    state.coach_err = "clip.coach.json missing"
    return
  end

  local text = file_read(path)
  if not text then
    state.coach = nil
    state.coach_err = "coach read failed"
    return
  end

  local doc, _, dec_err = json.decode(text, 1, nil)
  if not doc then
    state.coach = nil
    state.coach_err = "coach decode failed"
    return
  end

  state.coach_path = path
  state.coach = coach_from_doc(doc)
  state.coach_err = ""
end

-- ------------------------------ drawing ------------------------------------
local W, H = 560, 260
gfx.init("Smart Guitar Panel", W, H, 0)

local function draw_text(x, y, s)
  gfx.x, gfx.y = x, y
  gfx.drawstr(tostring(s or ""))
end

local function draw_button(x, y, w, h, label)
  local mx, my = gfx.mouse_x, gfx.mouse_y
  local hot = (mx >= x and mx <= x+w and my >= y and my <= y+h)
  gfx.rect(x, y, w, h, 0)
  draw_text(x + 8, y + 6, label)
  return hot
end

local function clip_hint(s)
  s = tostring(s or "")
  if #s <= 120 then return s end
  return s:sub(1, 117) .. "..."
end

local function render()
  gfx.set(0.12, 0.12, 0.12, 1.0)
  gfx.rect(0, 0, W, H, 1)

  gfx.set(1, 1, 1, 1.0)
  draw_text(12, 10, "Smart Guitar — Panel (Episode 13A)")

  local y = 34

  -- Now block
  if state.coach then
    local c = state.coach
    draw_text(12, y, "Now: clip=" .. short_id(state.last_clip_id) .. "  gen#" .. tostring(c.gen or "?"))
    y = y + 18
    local tempo_line = "tempo=" .. tostring(c.tempo or "?")
    if c.tempo_delta ~= nil then tempo_line = tempo_line .. " (Δ " .. fmt(c.tempo_delta, 0) .. ")" end
    draw_text(12, y, "objective=" .. tostring(c.objective or "?") .. " | " .. tempo_line .. " | loop_bars=" .. tostring(c.loop_bars or "?"))
    y = y + 18
    draw_text(12, y, "density=" .. tostring(c.density or "?") .. " | sync=" .. tostring(c.sync_bucket or "?") .. (c.sync_scalar and (" ("..fmt(c.sync_scalar,2)..")") or "") .. " | score=" .. (c.score and fmt(c.score,1) or "?"))
    y = y + 18
    draw_text(12, y, "coach → " .. clip_hint(c.hint))
    y = y + 24
  else
    draw_text(12, y, "Now: " .. (state.coach_err ~= "" and state.coach_err or "loading..."))
    y = y + 24
  end

  -- Session block
  if state.session and state.session.entries then
    local entries = state.session.entries
    local N = #entries
    local start = N - 10 + 1
    if start < 1 then start = 1 end
    local window = {}
    for i = start, N do window[#window+1] = entries[i] end

    local take, dens, sync, score_avg, tf, tl, drift = compute_counts(window)
    draw_text(12, y, "Session(last " .. tostring(#window) .. "): score_avg=" .. (score_avg and fmt(score_avg,2) or "?")
      .. " | tempo " .. (tf and fmt(tf,0) or "?") .. "→" .. (tl and fmt(tl,0) or "?")
      .. " (Δ " .. (drift and fmt(drift,0) or "?") .. ")")
    y = y + 18
    draw_text(12, y, "take p="..take.pass.." s="..take.struggle.." | dens sp="..dens.sparse.." md="..dens.medium.." dn="..dens.dense
      .. " | sync st="..sync.straight.." lt="..sync.light.." hv="..sync.heavy)
    y = y + 22
  else
    draw_text(12, y, "Session: " .. (state.session_err ~= "" and state.session_err or "loading..."))
    y = y + 22
  end

  -- Buttons
  local bx, by = 12, H - 44
  local bw, bh, gap = 100, 28, 10
  gfx.set(1, 1, 1, 1)

  local hot_gen   = draw_button(bx + 0*(bw+gap), by, bw, bh, "Generate")
  local hot_pass  = draw_button(bx + 1*(bw+gap), by, bw, bh, "PASS+REGEN")
  local hot_strug = draw_button(bx + 2*(bw+gap), by, bw, bh, "STRUGGLE")
  local hot_tline = draw_button(bx + 3*(bw+gap), by, bw, bh, "Timeline")
  local hot_trend = draw_button(bx + 4*(bw+gap), by, bw, bh, "Trend")

  -- Click handling (left mouse release)
  if gfx.mouse_cap & 1 == 0 and state._mouse_was_down then
    if hot_gen then run_action(K_GEN) end
    if hot_pass then run_action(K_PASS) end
    if hot_strug then run_action(K_STRUG) end
    if hot_tline then run_action(K_TLINE) end
    if hot_trend then run_action(K_TREND) end
  end
  state._mouse_was_down = (gfx.mouse_cap & 1 == 1)
end

-- ------------------------------ main loop ----------------------------------
local function loop()
  -- Hot-reload host_port from ExtState (allows live switching between localhost/LAN Pi)
  API_BASE = "http://" .. (reaper.GetExtState(EXT_SECTION, "host_port") ~= "" and reaper.GetExtState(EXT_SECTION, "host_port") or "127.0.0.1:8420")

  local now = reaper.time_precise()
  refresh_session_if_needed(now)
  refresh_coach_if_needed(now)

  render()
  gfx.update()

  if gfx.getchar() >= 0 then
    reaper.defer(loop)
  end
end

loop()
