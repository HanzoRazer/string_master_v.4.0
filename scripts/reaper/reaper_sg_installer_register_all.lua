-- scripts/reaper/reaper_sg_installer_register_all.lua
-- CONTRACT: SG_REAPER_CONTRACT_V1 (see docs/contracts/SG_REAPER_CONTRACT_V1.md)
--
-- One-click installer (self-validating + duplicate-avoid + repair + optional cleanup):
-- - Writes ExtState keys:
--     action_generate, action_pass_regen, action_struggle_regen, action_timeline, action_trend
--     session_id, host_port
-- - Self-validating MAP:
--     If preferred file missing, scans folder for reaper_sg_*.lua and auto-selects best match by keywords.
-- - Avoid duplicates:
--     Prevents the same script filename being selected for multiple action keys.
-- - Repair mode (no prompts):
--     If ExtState resolves but doesn't match current folder version, re-registers current file and updates ExtState.
-- - Cleanup mode (optional, no prompts, safe):
--     Attempts to remove stale script registrations that point to old paths.
--     Best-effort: if a path can't be determined, it prints WARN and continues.
--
-- Safety model:
-- - Never deletes files. Only unregisters scripts from Actions.
-- - Cleanup is conservative: only targets scripts matching our known filenames.

local EXT_SECTION = "SG_AGENTD"

-- ---------------------------------------------------------------------------
-- OPTIONAL CLEANUP TOGGLES
-- ---------------------------------------------------------------------------
local CLEANUP_STALE_REGISTRATIONS = true      -- master toggle
local CLEANUP_SCAN_ACTION_LIST    = true      -- scan action list for duplicates by filename
local CLEANUP_SECTION_ID          = 0         -- Main section

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
  section_id = section_id or CLEANUP_SECTION_ID
  local cmd_id = reaper.AddRemoveReaScript(true, section_id, fullpath, true)
  if not cmd_id or cmd_id == 0 then return nil, "AddRemoveReaScript(add) failed" end

  local rs = reaper.ReverseNamedCommandLookup(cmd_id)
  rs = trim(rs)
  if rs == "" then return nil, "ReverseNamedCommandLookup failed" end
  return rs, nil
end

local function unregister_script(fullpath, section_id)
  section_id = section_id or CLEANUP_SECTION_ID
  local cmd_id = reaper.AddRemoveReaScript(false, section_id, fullpath, true)
  if not cmd_id then
    return false, "AddRemoveReaScript(remove) returned nil"
  end
  -- returns command id (0 if not removed / not found), behavior varies; treat nonzero as success
  if cmd_id ~= 0 then
    return true, nil
  end
  return false, "not removed (maybe not registered for this path)"
end

local function banner()
  reaper.ClearConsole()
  msg("============================================================")
  msg("Smart Guitar — Installer (Register + Repair + Cleanup) [6.5]")
  msg("============================================================")
end

-- ---------------------------------------------------------------------------
-- DEFAULTS
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
-- Cleanup helpers
-- ---------------------------------------------------------------------------

-- Attempt to extract a script path from the action text.
-- Often includes "Script: <path>".
local function extract_lua_path_from_action_text(txt)
  txt = tostring(txt or "")
  local lo = lower(txt)
  local lua_pos = lo:find(".lua", 1, true)
  if not lua_pos then return nil end

  -- Try common format: "Script: /path/to/file.lua"
  local script_tag = lo:find("script:", 1, true)
  if script_tag then
    local after = txt:sub(script_tag + 7)
    -- trim leading spaces
    after = after:gsub("^%s+", "")
    -- take up to .lua
    local endpos = lower(after):find(".lua", 1, true)
    if endpos then
      local cand = after:sub(1, endpos + 3)
      cand = trim(cand)
      if cand ~= "" then return cand end
    end
  end

  -- Fallback: take last token ending in .lua (handles some variants)
  local best = nil
  for token in txt:gmatch("%S+") do
    if lower(token):match("%.lua$") then
      best = token
    end
  end
  if best then
    best = best:gsub('^"+', ""):gsub('"+$', "")
    best = trim(best)
    if best ~= "" then return best end
  end
  return nil
end

local function action_text_from_cmd(cmd_id, section_id)
  section_id = section_id or CLEANUP_SECTION_ID
  -- returns a user-facing name for the command; for scripts it typically includes "Script: ..."
  local txt = reaper.kbd_getTextFromCmd(cmd_id, section_id)
  return txt
end

local function try_remove_by_cmd_id(cmd_id, current_fullpath, expected_filename)
  if not CLEANUP_STALE_REGISTRATIONS then return end

  local txt = action_text_from_cmd(cmd_id, CLEANUP_SECTION_ID)
  local p = extract_lua_path_from_action_text(txt)
  if not p then
    msg("SG WARN: cleanup: could not determine old script path from action text for cmd_id=" .. tostring(cmd_id))
    return
  end

  -- Normalize quotes
  p = p:gsub('^"+', ""):gsub('"+$', "")
  p = trim(p)

  -- Only remove if it looks like the script we're managing (by filename)
  if expected_filename and lower(p):find(lower(expected_filename), 1, true) == nil then
    msg("SG WARN: cleanup: extracted path doesn't match expected filename; skipping remove")
    msg("        expected: " .. tostring(expected_filename))
    msg("        extracted: " .. tostring(p))
    return
  end

  -- Never remove the current folder file registration
  if current_fullpath and lower(p) == lower(current_fullpath) then
    return
  end

  local ok_rm, err = unregister_script(p, CLEANUP_SECTION_ID)
  if ok_rm then
    msg("SG OK:   cleanup: unregistered stale script: " .. p)
  else
    msg("SG WARN: cleanup: failed to unregister: " .. p .. " (" .. tostring(err) .. ")")
  end
end

local function scan_and_cleanup_duplicates(current_fullpath, expected_filename, desired_rs)
  if not (CLEANUP_STALE_REGISTRATIONS and CLEANUP_SCAN_ACTION_LIST) then return end
  if not expected_filename or expected_filename == "" then return end

  local removed = 0
  local scanned = 0
  local max_scan = 20000

  for i = 0, max_scan do
    local cmd = reaper.EnumerateActions(CLEANUP_SECTION_ID, i)
    if not cmd or cmd == 0 then break end
    scanned = scanned + 1

    local txt = action_text_from_cmd(cmd, CLEANUP_SECTION_ID)
    if txt and lower(txt):find(lower(expected_filename), 1, true) then
      local rs = trim(reaper.ReverseNamedCommandLookup(cmd))
      -- Only consider removing if it's not the desired id for current folder
      if rs ~= "" and desired_rs and rs ~= desired_rs then
        local p = extract_lua_path_from_action_text(txt)
        if p then
          p = p:gsub('^"+', ""):gsub('"+$', "")
          p = trim(p)
          if current_fullpath and lower(p) ~= lower(current_fullpath) then
            local ok_rm = unregister_script(p, CLEANUP_SECTION_ID)
            if ok_rm then
              removed = removed + 1
              msg("SG OK:   cleanup: removed duplicate registration: " .. p)
            end
          end
        end
      end
    end
  end

  if removed > 0 then
    msg("SG OK:   cleanup summary: removed " .. tostring(removed) .. " duplicates for " .. expected_filename .. " (scanned " .. tostring(scanned) .. ")")
  end
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
msg("Registering scripts (self-validating + repair + cleanup)...")
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

      -- Compute desired _RS id for THIS folder file (register if needed, idempotent)
      local desired_rs, derr = register_script(full, CLEANUP_SECTION_ID)
      if not desired_rs then
        msg("SG FAIL: " .. item.label .. " → could not register current file: " .. tostring(derr))
        ok = false
      else
        local existing_rs = get_ext(item.key)
        local existing_cmd = resolve_rs_id(existing_rs)
        local desired_cmd = resolve_rs_id(desired_rs)

        if existing_cmd then
          if existing_rs == desired_rs then
            msg("SG OK:   " .. item.label .. " already correct (" .. item.key .. " = " .. existing_rs .. ")")
          else
            msg("SG WARN: " .. item.label .. " repairing stale id:")
            msg("        was: " .. existing_rs)
            msg("        now: " .. desired_rs)
            -- Attempt cleanup of the old registration (best-effort)
            try_remove_by_cmd_id(existing_cmd, full, chosen_fn)
            set_ext(item.key, desired_rs)
            msg("SG OK:   " .. item.key .. " = " .. get_ext(item.key))
          end
        else
          -- missing/invalid ExtState; set to desired id
          if chosen_fn ~= item.file then
            msg("SG WARN: " .. item.label .. " preferred " .. item.file .. " not found; using " .. chosen_fn .. " (" .. reason .. ")")
          else
            msg("SG OK:   " .. item.label .. " found: " .. chosen_fn)
          end
          set_ext(item.key, desired_rs)
          msg("SG OK:   " .. item.key .. " = " .. get_ext(item.key))
        end

        -- Optional: remove other duplicates of the same script filename in other folders
        scan_and_cleanup_duplicates(full, chosen_fn, desired_rs)
      end
    end
  end
end

msg("------------------------------------------------------------")
if ok then
  msg("SG INSTALL: PASS — ExtState shipped; repaired stale IDs; cleanup best-effort complete.")
else
  msg("SG INSTALL: FAIL — missing/ambiguous scripts or registration failures.")
  msg("Fix: ensure required scripts exist in this folder, then rerun installer.")
end
msg("Next: run reaper_sg_setup_doctor.lua for full verification.")
msg("============================================================")
