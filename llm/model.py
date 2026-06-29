"""
Basic LLM: a character-level GPT-style Transformer built from scratch.

Architecture:
  - Token + positional embeddings
  - N Transformer blocks (masked multi-head self-attention + feed-forward)
  - Layer norm + linear head
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class CausalSelfAttention(nn.Module):
    """Multi-head self-attention with a causal (look-ahead) mask."""

    def __init__(self, config):
        super().__init__()
        assert config.n_embd % config.n_heads == 0
        self.n_heads = config.n_heads
        self.head_dim = config.n_embd // config.n_heads
        self.n_embd = config.n_embd

        # Fused Q/K/V projection
        self.qkv = nn.Linear(config.n_embd, 3 * config.n_embd, bias=False)
        self.proj = nn.Linear(config.n_embd, config.n_embd, bias=False)
        self.dropout = nn.Dropout(config.dropout)

        # Causal mask: upper-triangular, registered as a non-parameter buffer
        mask = torch.triu(torch.ones(config.block_size, config.block_size), diagonal=1).bool()
        self.register_buffer("mask", mask)

    def forward(self, x):
        B, T, C = x.shape

        q, k, v = self.qkv(x).split(self.n_embd, dim=2)

        # Reshape to (B, n_heads, T, head_dim)
        def reshape(t):
            return t.view(B, T, self.n_heads, self.head_dim).transpose(1, 2)

        q, k, v = reshape(q), reshape(k), reshape(v)

        # Scaled dot-product attention
        scale = math.sqrt(self.head_dim)
        scores = (q @ k.transpose(-2, -1)) / scale          # (B, nh, T, T)
        scores = scores.masked_fill(self.mask[:T, :T], float("-inf"))
        weights = F.softmax(scores, dim=-1)
        weights = self.dropout(weights)

        out = weights @ v                                     # (B, nh, T, hd)
        out = out.transpose(1, 2).contiguous().view(B, T, C) # (B, T, C)
        return self.proj(out)


class FeedForward(nn.Module):
    """Position-wise feed-forward network (expand → GELU → contract)."""

    def __init__(self, config):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(config.n_embd, 4 * config.n_embd),
            nn.GELU(),
            nn.Linear(4 * config.n_embd, config.n_embd),
            nn.Dropout(config.dropout),
        )

    def forward(self, x):
        return self.net(x)


class TransformerBlock(nn.Module):
    """Self-attention + feed-forward with pre-layer-norm residual connections."""

    def __init__(self, config):
        super().__init__()
        self.ln1 = nn.LayerNorm(config.n_embd)
        self.attn = CausalSelfAttention(config)
        self.ln2 = nn.LayerNorm(config.n_embd)
        self.ff = FeedForward(config)

    def forward(self, x):
        x = x + self.attn(self.ln1(x))
        x = x + self.ff(self.ln2(x))
        return x


class LLM(nn.Module):
    """
    Tiny GPT-style language model.

    config fields:
        vocab_size  – number of tokens
        block_size  – maximum context length
        n_embd      – embedding dimension
        n_heads     – number of attention heads
        n_layers    – number of Transformer blocks
        dropout     – dropout probability
    """

    def __init__(self, config):
        super().__init__()
        self.config = config

        self.tok_emb = nn.Embedding(config.vocab_size, config.n_embd)
        self.pos_emb = nn.Embedding(config.block_size, config.n_embd)
        self.drop = nn.Dropout(config.dropout)
        self.blocks = nn.Sequential(*[TransformerBlock(config) for _ in range(config.n_layers)])
        self.ln_f = nn.LayerNorm(config.n_embd)
        self.head = nn.Linear(config.n_embd, config.vocab_size, bias=False)

        # Weight tying: share token embedding and output projection weights
        self.head.weight = self.tok_emb.weight

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.shape
        assert T <= self.config.block_size, "Sequence longer than block_size"

        positions = torch.arange(T, device=idx.device)
        x = self.drop(self.tok_emb(idx) + self.pos_emb(positions))
        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)  # (B, T, vocab_size)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), targets.view(-1))

        return logits, loss

    @torch.no_grad()
    def generate(self, idx, max_new_tokens, temperature=1.0, top_k=None):
        """
        Autoregressively generate tokens given a conditioning sequence.

        Args:
            idx            – (1, T) tensor of starting token ids
            max_new_tokens – number of tokens to generate
            temperature    – >1 = more random, <1 = more focused
            top_k          – if set, restrict sampling to the top-k logits
        """
        for _ in range(max_new_tokens):
            # Crop to block_size if needed
            idx_cond = idx[:, -self.config.block_size:]
            logits, _ = self(idx_cond)
            logits = logits[:, -1, :] / temperature  # last time-step

            if top_k is not None:
                v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                logits[logits < v[:, [-1]]] = float("-inf")

            probs = F.softmax(logits, dim=-1)
            next_token = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, next_token], dim=1)

        return idx

    def num_params(self):
        return sum(p.numel() for p in self.parameters())
