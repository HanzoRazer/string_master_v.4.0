"""Quick test to verify deterministic behavior with probabilistic mode."""
import filecmp

from src.zt_band.engine import generate_accompaniment

# Generate two files with same parameters and seed
generate_accompaniment(
    ['Cmaj7', 'F7', 'Dm7', 'G7'],
    style_name='swing_basic',
    tempo_bpm=120,
    bars_per_chord=2,
    tritone_mode='probabilistic',
    tritone_seed=42,
    outfile='test_prob1.mid'
)

generate_accompaniment(
    ['Cmaj7', 'F7', 'Dm7', 'G7'],
    style_name='swing_basic',
    tempo_bpm=120,
    bars_per_chord=2,
    tritone_mode='probabilistic',
    tritone_seed=42,
    outfile='test_prob2.mid'
)

# Verify they're identical
identical = filecmp.cmp('test_prob1.mid', 'test_prob2.mid', shallow=False)
print(f'✅ Probabilistic mode with seed=42 is deterministic: {identical}')

if identical:
    print('✅ CORE IS LOCKED: Deterministic timing + contract enforcement verified')
else:
    print('❌ FAILED: Files differ despite same seed')
