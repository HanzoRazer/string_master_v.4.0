import json
import argparse
from groove_layer import compute_groove_layer_control

ap = argparse.ArgumentParser()
ap.add_argument("vector_path")
ap.add_argument("--debug", action="store_true")
args = ap.parse_args()

with open(args.vector_path, "r", encoding="utf-8") as f:
    payload = json.load(f)

out = compute_groove_layer_control(payload, debug=args.debug)
print(json.dumps(out, indent=2))
