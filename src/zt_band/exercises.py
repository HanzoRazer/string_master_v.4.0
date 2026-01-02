from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml  # type: ignore[import-not-found]

from .config import ProgramConfig, load_program_config
from .engine import generate_accompaniment

TaskMode = Literal[
    "play_roots",        # student plays roots
    "play_shells",       # 3rds/7ths
    "improvise_scale",   # improv within a scale/mode
    "identify_function", # call out I / ii / V etc.
    "custom"             # free-text instructions
]

InteractionMode = Literal[
    "none",         # audio-only, no tracking (for now)
    "self_report",  # student answers questions/checklist manually
    "future_audio"  # reserved hook for later audio analysis
]


@dataclass
class TaskSpec:
    """
    What the student is supposed to *do* during the exercise.

    This is the pedagogical intent: 'play roots', 'sing guide tones', etc.
    """
    mode: TaskMode
    instructions: str
    prompts: list[str]


@dataclass
class InteractionSpec:
    """
    How the exercise *interacts* with the student.

    For now this is purely descriptive + console text output,
    but these fields are the canonical hook for later:

    - UI forms / checklists
    - audio analysis
    - scoring & progress tracking
    """
    mode: InteractionMode
    questions: list[str]


@dataclass
class ExerciseConfig:
    """
    A single exercise definition (.ztex), layered on top of a .ztprog program.

    Typical YAML/JSON:

    name: "Cycle of Fifths — Roots"
    program: "c_major_cycle.ztprog"
    exercise_type: "cycle_fifths_roots"

    task:
      mode: "play_roots"
      instructions: "Play the root of each chord as it sounds."
      prompts:
        - "Say the chord name out loud before you play."
        - "Keep steady time with the backing."

    interaction:
      mode: "self_report"
      questions:
        - "Were there any keys that felt unstable?"
        - "Could you predict the next chord root?"
    """
    name: str
    program_path: Path
    exercise_type: str
    task: TaskSpec
    interaction: InteractionSpec


# -----------------
# Parsing helpers
# -----------------


def _ensure_dict(obj: Any, ctx: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        raise TypeError(f"{ctx} must be a mapping/object, got {type(obj)!r}")
    return obj


def _parse_task(raw: Any) -> TaskSpec:
    data = _ensure_dict(raw, "exercise.task")
    mode = data.get("mode", "custom")
    instructions = data.get("instructions", "").strip()
    prompts_raw = data.get("prompts", [])

    if not isinstance(prompts_raw, list):
        raise TypeError("exercise.task.prompts must be a list of strings.")

    prompts: list[str] = []
    for item in prompts_raw:
        if isinstance(item, str) and item.strip():
            prompts.append(item.strip())

    if not instructions:
        instructions = "Follow the prompts while the backing track plays."

    return TaskSpec(
        mode=mode,  # type: ignore[arg-type]
        instructions=instructions,
        prompts=prompts,
    )


def _parse_interaction(raw: Any) -> InteractionSpec:
    if raw is None:
        # default: self-report shell, no scoring yet
        return InteractionSpec(
            mode="self_report",
            questions=[
                "Which part of the exercise felt most difficult?",
                "Could you stay in time with the backing?",
            ],
        )

    data = _ensure_dict(raw, "exercise.interaction")
    mode = data.get("mode", "self_report")
    questions_raw = data.get("questions", [])

    if not isinstance(questions_raw, list):
        raise TypeError("exercise.interaction.questions must be a list of strings.")

    questions: list[str] = []
    for q in questions_raw:
        if isinstance(q, str) and q.strip():
            questions.append(q.strip())

    if not questions:
        questions = ["How did the exercise feel? Where did you struggle?"]

    return InteractionSpec(
        mode=mode,  # type: ignore[arg-type]
        questions=questions,
    )


def load_exercise_config(path: str | Path) -> ExerciseConfig:
    """
    Load a .ztex exercise file (JSON or YAML).

    Required fields:
      - name
      - program  (path to .ztprog)
      - exercise_type
      - task.mode

    Optional:
      - task.instructions
      - task.prompts
      - interaction.mode
      - interaction.questions
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Exercise file not found: {p}")

    text = p.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"Exercise file is empty: {p}")

    first = text[0]
    try:
        if first in ("{", "["):
            parsed = json.loads(text)
        else:
            parsed = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise ValueError(
            f"Failed to parse exercise file {p}. Ensure it is valid JSON or YAML."
        ) from exc

    data = _ensure_dict(parsed, "exercise root")

    name = str(data.get("name") or "").strip()
    if not name:
        raise ValueError("Exercise config must have a non-empty 'name' field.")

    program_raw = data.get("program")
    if not program_raw:
        raise ValueError("Exercise config must include a 'program' field pointing to a .ztprog file.")

    program_path = Path(program_raw)
    if not program_path.is_absolute():
        program_path = p.parent / program_path

    exercise_type = str(data.get("exercise_type") or "").strip()
    if not exercise_type:
        raise ValueError("Exercise config must specify 'exercise_type' for classification.")

    task = _parse_task(data.get("task", {}))
    interaction = _parse_interaction(data.get("interaction"))

    return ExerciseConfig(
        name=name,
        program_path=program_path,
        exercise_type=exercise_type,
        task=task,
        interaction=interaction,
    )


# -----------------
# Execution hook
# -----------------


def run_exercise(ex: ExerciseConfig, outfile: str | None = None) -> str:
    """
    Run an exercise by:

    1) Loading the underlying .ztprog program
    2) Generating a backing track
    3) Printing clear, canonical instructions + interaction prompts

    For now, this only creates audio output and console text. But this function
    is the *official hook* where future interactivity (audio input, scoring,
    UI flows) will be layered in.

    Returns the path of the generated MIDI file.
    """
    if not ex.program_path.exists():
        raise FileNotFoundError(f"Exercise program config not found: {ex.program_path}")

    program: ProgramConfig = load_program_config(ex.program_path)

    midi_out = outfile or program.outfile or "exercise.mid"

    # Generate backing using existing engine
    generate_accompaniment(
        chord_symbols=program.chords,
        style_name=program.style,
        tempo_bpm=program.tempo,
        bars_per_chord=program.bars_per_chord,
        outfile=midi_out,
        tritone_mode=program.tritone_mode,
        tritone_strength=program.tritone_strength,
        tritone_seed=program.tritone_seed,
    )

    # --- INTERACTIVITY HOOK (text only for now) -------------------------
    # This block is intentionally explicit so future UI/audio layers can
    # hook in here or mirror this structure.
    print(f"Exercise: {ex.name}")
    print(f"Type: {ex.exercise_type}")
    print("")
    print("TASK:")
    print(ex.task.instructions)
    if ex.task.prompts:
        print("")
        print("Prompts:")
        for idx, p in enumerate(ex.task.prompts, start=1):
            print(f"  {idx}. {p}")

    print("")
    print(f"Backing track file: {midi_out}")
    print("")
    print(f"Interaction mode: {ex.interaction.mode}")
    if ex.interaction.questions:
        print("Self-reflection questions (for journaling / instructor review):")
        for idx, q in enumerate(ex.interaction.questions, start=1):
            print(f"  {idx}. {q}")

    # TODO (future):
    # - If interaction.mode == "future_audio": start an audio capture session
    # - Log completion events to a learner profile
    # - Emit JSON report for SaaS dashboards / Smart Guitar integration

    return midi_out
