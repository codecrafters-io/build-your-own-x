"""
Training script for the basic LLM.

Usage:
    # Train on a text file (defaults to a tiny built-in dataset if omitted)
    python train.py --data path/to/corpus.txt

    # Quick smoke-test on the built-in dataset
    python train.py
"""

import argparse
import types
import random
import torch
from model import LLM
from tokenizer import CharTokenizer

# ---------------------------------------------------------------------------
# Tiny built-in corpus (Shakespeare excerpt) used when no file is provided
# ---------------------------------------------------------------------------
BUILTIN_TEXT = """\
First Citizen: Before we proceed any further, hear me speak.
All: Speak, speak.
First Citizen: You are all resolved rather to die than to famish?
All: Resolved. Resolved.
First Citizen: First, you know Caius Marcius is chief enemy to the people.
All: We know't, we know't.
First Citizen: Let us kill him, and we'll have corn at our own price.
Is't a verdict?
All: No more talking on't; let it be done: away, away!
Second Citizen: One word, good citizens.
First Citizen: We are accounted poor citizens, the patricians good.
What authority surfeits on would relieve us: if they
would yield us but the superfluity, while it were wholesome,
we might guess they relieved us humanely; but they think we are
too dear: the leanness that afflicts us, the object of our
misery, is as an inventory to particularise their abundance;
our sufferance is a gain to them. Let us revenge this with
our pikes, ere we become rakes: for the gods know I speak this
in hunger for bread, not in thirst for revenge.
"""


def get_batch(data: torch.Tensor, block_size: int, batch_size: int, device: str):
    """Sample a random batch of (input, target) sequences."""
    ix = torch.randint(len(data) - block_size, (batch_size,))
    x = torch.stack([data[i : i + block_size] for i in ix])
    y = torch.stack([data[i + 1 : i + block_size + 1] for i in ix])
    return x.to(device), y.to(device)


def train(args):
    # ------------------------------------------------------------------
    # 1. Load / prepare data
    # ------------------------------------------------------------------
    if args.data:
        with open(args.data, encoding="utf-8") as f:
            text = f.read()
    else:
        print("No --data file provided. Using built-in Shakespeare excerpt.")
        text = BUILTIN_TEXT

    tokenizer = CharTokenizer(text)
    data = torch.tensor(tokenizer.encode(text), dtype=torch.long)

    split = int(0.9 * len(data))
    train_data, val_data = data[:split], data[split:]

    print(f"Corpus: {len(text):,} chars | vocab: {tokenizer.vocab_size} | "
          f"train tokens: {len(train_data):,} | val tokens: {len(val_data):,}")

    # ------------------------------------------------------------------
    # 2. Build model
    # ------------------------------------------------------------------
    device = "cuda" if torch.cuda.is_available() else "cpu"

    config = types.SimpleNamespace(
        vocab_size=tokenizer.vocab_size,
        block_size=args.block_size,
        n_embd=args.n_embd,
        n_heads=args.n_heads,
        n_layers=args.n_layers,
        dropout=args.dropout,
    )

    model = LLM(config).to(device)
    print(f"Model: {model.num_params():,} parameters | device: {device}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)

    # ------------------------------------------------------------------
    # 3. Training loop
    # ------------------------------------------------------------------
    best_val_loss = float("inf")

    for step in range(1, args.steps + 1):
        model.train()
        x, y = get_batch(train_data, args.block_size, args.batch_size, device)
        _, loss = model(x, y)
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()

        if step % args.eval_interval == 0 or step == args.steps:
            model.eval()
            with torch.no_grad():
                vx, vy = get_batch(val_data, args.block_size, args.batch_size, device)
                _, val_loss = model(vx, vy)

            print(f"step {step:>6} | train loss {loss.item():.4f} | val loss {val_loss.item():.4f}")

            if val_loss.item() < best_val_loss:
                best_val_loss = val_loss.item()
                torch.save({"model": model.state_dict(), "config": config, "tokenizer": tokenizer},
                           args.checkpoint)

    # ------------------------------------------------------------------
    # 4. Sample from the trained model
    # ------------------------------------------------------------------
    print("\n--- Generated sample ---")
    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(ckpt["model"])
    model.eval()

    seed_text = text[:args.block_size] if len(text) >= args.block_size else text
    idx = torch.tensor(tokenizer.encode(seed_text), dtype=torch.long, device=device).unsqueeze(0)
    out = model.generate(idx, max_new_tokens=200, temperature=0.8, top_k=20)
    print(tokenizer.decode(out[0].tolist()))


def parse_args():
    p = argparse.ArgumentParser(description="Train a basic character-level LLM")
    p.add_argument("--data",          type=str,   default=None,           help="Path to training text file")
    p.add_argument("--checkpoint",    type=str,   default="ckpt.pt",      help="Where to save the best model")
    p.add_argument("--block_size",    type=int,   default=64,             help="Context length")
    p.add_argument("--batch_size",    type=int,   default=32,             help="Batch size")
    p.add_argument("--n_embd",        type=int,   default=128,            help="Embedding dimension")
    p.add_argument("--n_heads",       type=int,   default=4,              help="Number of attention heads")
    p.add_argument("--n_layers",      type=int,   default=4,              help="Number of Transformer blocks")
    p.add_argument("--dropout",       type=float, default=0.1,            help="Dropout probability")
    p.add_argument("--lr",            type=float, default=3e-4,           help="Learning rate")
    p.add_argument("--steps",         type=int,   default=2000,           help="Training steps")
    p.add_argument("--eval_interval", type=int,   default=200,            help="Steps between evaluations")
    return p.parse_args()


if __name__ == "__main__":
    train(parse_args())
