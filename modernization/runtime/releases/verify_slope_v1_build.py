"""Normalize PE build timestamps and verify exact user-accepted slope DLL bytes."""
import hashlib
from pathlib import Path
import sys

path = Path(sys.argv[1])
data = bytearray(path.read_bytes())
if len(data) != 120832 or data[256:260] != data[108540:108544]:
    raise SystemExit("Unexpected release DLL layout; refusing normalization")
data[256:260] = data[108540:108544] = bytes.fromhex("4f5ab86a")
digest = hashlib.sha256(data).hexdigest()
if digest != "a1afc242539db725e28fe506ec321098416d9b0b2ff3d4e301f5b79c1e8d871e":
    raise SystemExit(f"Release DLL differs from accepted bytes: {digest}")
path.write_bytes(data)
print("User-accepted slope module reproduced:", digest)
