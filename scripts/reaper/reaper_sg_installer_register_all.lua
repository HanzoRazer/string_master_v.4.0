-- scripts/reaper/reaper_sg_installer_register_all.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- One-click installer (self-validating + duplicate-avoid + repair mode):
-- - Writes ExtState keys:
--     action_generate, action_pass_regen, action_struggle_regen, action_timeline, action_trend
--     session_id, host_port
-- - Self-validating MAP:
--     If preferred file missing, scans folder for reaper_sg_*.lua and auto-selects best match by keywords.
-- - Avoid duplicates:
--     Prevents the same script filename being selected for multiple action keys (prints FAIL).
-- - Repair mode (no prompts):
--     If ExtState has a resolvable command ID but it does NOT point to the current folder version,
--     it will re-register from THIS folder and update ExtState.
--
-- Rationale:
-- - Reaper action IDs depend on script path. Moving/copying scripts can leave ExtState pointing to old IDs.
-- - This script makes "re-copy bundle then run installer" always fix itself.

local EXT_SECTION = "SG_AGENTD"

local function msg(s) reaper.ShowConsoleMsg(tostring(s) .. "\n") end
local function trim(s) return (tostring(s or ""):gsub("^%s+",""):gsub("%s+$","")) end
local function lower(s) return tostring(s or ""):lower() end

local function script_dir()
  local p = ({reaper.get_action_context()})[2] or ""
  return p:match("(.*/)") or p:match("(.+\\)") or ""
end

local function file_exists(path)
  local f = io.open(path, "r")
  if f then f:close(); return true end
  return false
end

local function list_dir_lua_files(dir)
  local out = {}
  local i = 0
  while true do
    local fn = reaper.EnumerateFiles(dir, i)
    if not fn then break end
    if lower(fn):match("%.lua$") then
      table.insert(out, fn)
    end
    i = i + 1
  end
  return out
end

local function set_ext(key, val)
  reaper.SetExtState(EXT_SECTION, key, trim(val), true)
end

local function get_ext(key)
  return trim(reaper.GetExtState(EXT_SECTION, key))
end

local function resolve_rs_id(rs)
  rs = trim(rs)
  if rs == "" then return nil end
  local cmd = reaper.NamedCommandLookup(rs)
  if not cmd or cmd == 0 then return nil end
  return cmd
end

local function register_script(fullpath, section_id)
  section_id = section_id or 0 -- Main
  local cmd_id = reaper.AddRemoveReaScript(true, section_id, fullpath, true)
  if not cmd_id or cmd_id == 0 then return nil, "AddRemoveReaScript failed" end

  local rs = reaper.ReverseNamedCommandLookup(cmd_id)
  rs = trim(rs)
  if rs == "" then return nil, "ReverseNamedCommandLookup failed" end
  return rs, nil
end

local function banner()
  reaper.ClearConsole()
  msg("============================================================")
  msg("Smart Guitar — Installer (Register + ExtState ship) [6.4 repair]")
  msg("============================================================")
end

-- ---------------------------------------------------------------------------
-- EDITABLE DEFAULTS (safe)
-- ---------------------------------------------------------------------------
local DEFAULT_SESSION_ID = "reaper_session"
local DEFAULT_HOST_PORT  = "127.0.0.1:8420"

-- ---------------------------------------------------------------------------
-- MAP (preferred filenames + keywords)
-- ---------------------------------------------------------------------------
local MAP = {
  { key = "action_generate",       label = "Generate",       file = "reaper_sg_generate.lua",            keywords = {"generate"} },
  { key = "action_pass_regen",     label = "PASS+REGEN",     file = "reaper_sg_pass_and_regen.lua",     keywords = {"pass", "regen"} },
  { key = "action_struggle_regen", label = "STRUGGLE+REGEN", file = "reaper_sg_struggle_and_regen.lua", keywords = {"struggle", "regen"} },
  { key = "action_timeline",       label = "Timeline",       file = "reaper_sg_timeline.lua",           keywords = {"timeline"} },
  { key = "action_trend",          label = "Trend",          file = "reaper_sg_trend.lua",              keywords = {"trend"} },
}

-- ---------------------------------------------------------------------------
-- Matching logic (self-validating MAP)
-- ---------------------------------------------------------------------------
local function score_filename(fn, keywords)
  fn = lower(fn)
  local score = 0
  if fn:find("reaper_sg_", 1, true) == 1 then score = score + 2 end
  for _, kw in ipairs(keywords or {}) do
    kw = lower(kw)
    if kw ~= "" and fn:find(kw, 1, true) then
      score = score + 10
    end
  end
  if fn:find("_and_", 1, true) then score = score + 1 end
  return score
end

local function choose_best_candidate(keywords, lua_files)
  local best_fn = nil
  local best_score = -1
  for _, fn in ipairs(lua_files) do
    local s = score_filename(fn, keywords)
    if s > best_score then
      best_score = s
      best_fn = fn
    end
  end
  if not best_fn or best_score < 5 then
    return nil, 0
  end
  return best_fn, best_score
end

local function validate_or_autofix(dir, item, lua_files)
  local preferred_full = dir .. item.file
  if file_exists(preferred_full) then
    return item.file, "preferred"
  end
  local best_fn, score = choose_best_candidate(item.keywords, lua_files)
  if best_fn then
    return best_fn, ("auto-selected (score=%d)"):format(score)
  end
  return nil, "missing"
end

-- ---------------------------------------------------------------------------
-- Repair detection: does an existing _RS id point to THIS folder version?
-- We do this by comparing the stored ExtState _RS id to what ReverseNamedCommandLookup returns
-- AFTER registering the script from the current folder (without prompts).
--
-- Key idea:
-- - If ExtState resolves, that only proves it's registered somewhere.
-- - We want it registered for the current folder path.
-- - So we compute the "desired" _RS id by registering current file, then compare.
--
-- Duplicate risk:
-- - AddRemoveReaScript(true, ...) is idempotent-ish: it will add if not there; if already added it may
--   still return an existing command id. Practically, it is safe to call for repair.
--
-- We will only call "repair registration" when:
--   - ExtState resolves, AND
--   - ExtState _RS id != desired _RS id for this folder file
-- ---------------------------------------------------------------------------
local function compute_desired_rs_for_file(fullpath)
  local rs, err = register_script(fullpath, 0)
  return rs, err
end

-- ---------------------------------------------------------------------------
-- MAIN
-- ---------------------------------------------------------------------------
banner()

local dir = script_dir()
msg("Script dir: " .. dir)

local lua_files = list_dir_lua_files(dir)

-- Write host/session if missing (do not overwrite if user already set)
if get_ext("session_id") == "" then
  set_ext("session_id", DEFAULT_SESSION_ID)
  msg("SET:  session_id = " .. get_ext("session_id"))
else
  msg("KEEP: session_id = " .. get_ext("session_id"))
end

if get_ext("host_port") == "" then
  set_ext("host_port", DEFAULT_HOST_PORT)
  msg("SET:  host_port  = " .. get_ext("host_port"))
else
  msg("KEEP: host_port  = " .. get_ext("host_port"))
end

msg("------------------------------------------------------------")
msg("Registering scripts (self-validating + repair mode)...")
msg("------------------------------------------------------------")

local ok = true
local used_files = {}  -- prevent mapping multiple keys to same filename

for _, item in ipairs(MAP) do
  local chosen_fn, reason = validate_or_autofix(dir, item, lua_files)
  if not chosen_fn then
    msg("SG FAIL: " .. item.label .. " → missing file (preferred: " .. item.file .. ")")
    msg("        Files present: " .. table.concat(lua_files, ", "))
    ok = false
  else
    if used_files[chosen_fn] then
      msg("SG FAIL: " .. item.label .. " → ambiguous mapping. '" .. chosen_fn .. "' already used for " .. used_files[chosen_fn])
      msg("        Fix: ensure distinct script filenames exist for each action in MAP.")
      ok = false
    else
      used_files[chosen_fn] = item.label

      local full = dir .. chosen_fn
      local existing_rs = get_ext(item.key)
      local existing_cmd = resolve_rs_id(existing_rs)

      -- Always compute desired _RS for THIS folder file (repair detection)
      local desired_rs, derr = compute_desired_rs_for_file(full)
      if not desired_rs then
        msg("SG FAIL: " .. item.label .. " → could not register current file to compute desired id: " .. tostring(derr))
        ok = false
      else
        if existing_cmd then
          if existing_rs == desired_rs then
            msg("SG OK:   " .. item.label .. " already correct (ExtState " .. item.key .. " = " .. existing_rs .. ")")
          else
            msg("SG WARN: " .. item.label .. " repairing stale id:")
            msg("        was: " .. existing_rs)
            msg("        now: " .. desired_rs)
            set_ext(item.key, desired_rs)
            msg("SG OK:   " .. item.key .. " = " .. get_ext(item.key))
          end
        else
          -- missing/invalid ExtState; set to desired id (already registered)
          if chosen_fn ~= item.file then
            msg("SG WARN: " .. item.label .. " preferred " .. item.file .. " not found; using " .. chosen_fn .. " (" .. reason .. ")")
          else
            msg("SG OK:   " .. item.label .. " found: " .. chosen_fn)
          end
          set_ext(item.key, desired_rs)
          msg("SG OK:   " .. item.key .. " = " .. get_ext(item.key))
        end
      end
    end
  end
end

msg("------------------------------------------------------------")
if ok then
  msg("SG INSTALL: PASS — ExtState shipped; repaired stale IDs when needed.")
else
  msg("SG INSTALL: FAIL — missing/ambiguous scripts or registration failures.")
  msg("Fix: ensure required scripts exist in this folder, then rerun installer.")
end
msg("Next: run reaper_sg_setup_doctor.lua for full verification.")
msg("============================================================")
