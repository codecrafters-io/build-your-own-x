"""
Generate text from a saved checkpoint.

Usage:
    python generate.py --checkpoint ckpt.pt --prompt "First Citizen:" --tokens 300
"""

import argparse
import torch
from model import LLM


def generate(args):
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    config = ckpt["config"]
    tokenizer = ckpt["tokenizer"]

    model = LLM(config).to(device)
    model.load_state_dict(ckpt["model"])
    model.eval()

    prompt = args.prompt or ""
    if prompt:
        idx = torch.tensor(tokenizer.encode(prompt), dtype=torch.long, device=device).unsqueeze(0)
    else:
        # Start from a single newline token
        idx = torch.zeros((1, 1), dtype=torch.long, device=device)

    out = model.generate(idx, max_new_tokens=args.tokens,
                         temperature=args.temperature, top_k=args.top_k)
    print(tokenizer.decode(out[0].tolist()))


def parse_args():
    p = argparse.ArgumentParser(description="Generate text from a trained LLM checkpoint")
    p.add_argument("--checkpoint",   type=str,   default="ckpt.pt", help="Path to checkpoint")
    p.add_argument("--prompt",       type=str,   default="",        help="Seed text")
    p.add_argument("--tokens",       type=int,   default=300,       help="Tokens to generate")
    p.add_argument("--temperature",  type=float, default=0.8,       help="Sampling temperature")
    p.add_argument("--top_k",        type=int,   default=20,        help="Top-k sampling (0 = off)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.top_k == 0:
        args.top_k = None
    generate(args)
