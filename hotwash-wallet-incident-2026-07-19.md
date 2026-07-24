# Hot Wash: TheManager Wallet Compromise Incident

**Date of Incident:** July 19, 2026
**Identity Affected:** TheManager (@TheManager on 6529.io)
**Severity:** High — private key leaked to public GitHub

---

## What Happened

### Root Cause

TheManager operates as an autonomous agent on the Hermes platform, with its own Ethereum wallet for signing 6529.io transactions (posting drops, voting, assigning rep). The wallet's private key was stored locally in a secure file.

When preparing to publish TheManager's skills to a public GitHub repository (`RegularDad6529/hermes-skills`) for community benefit, a security audit script was included in the `6529-io` skill directory. This script, `verify_security.py`, was designed to scan files for leaked private keys — but ironically, it contained **the actual private key hardcoded as a search pattern** on line 50:

```python
key_pattern = '8191b3cb...'  # the real key, bare hex without 0x prefix
```

The redaction pass that reviewed the skill directory before pushing looked for standard key formats (`0x`-prefixed 64-character hex strings, `private_key` variable names, `.env` files). The bare hex string without a `0x` prefix — embedded as a "search pattern" in a `.py` file — was not caught.

The repository was pushed publicly. Within hours, an automated sweeper bot began monitoring the wallet and draining all incoming ETH.

### How the Drain Worked

The compromised wallet (`0xf409B9678bf48A9196FB85B9a7541e442CE3D8d4`) was monitored by a sweeper bot (`0x541b9034c82d7fb564f12ca07037947ff5b4ef2f`). Any ETH sent to the wallet was automatically transferred out in the very next block — before any manual transaction could be crafted to use that ETH for gas.

**Attempted recovery:**
- Standard ETH transfer → swept instantly
- Flashbots private mempool (Alchemy `eth_sendPrivateTransaction`) → rejected, requires paid tier
- Flashbots Protect RPC (`rpc.flashbots.net`) → transactions accepted but not mined; the sweeper bot's simple 21,000-gas ETH transfer out-prioritized our 100,000-gas NFT transfer calls

The sweeper bot only drains ETH, not NFTs. The Karen Army tokens remain locked in the wallet — unable to be transferred because no ETH can be kept for gas.

---

## What We Lost

### Assets Locked (Not Stolen — Inaccessible)

Six Karen Army NFTs are permanently stuck in the compromised wallet. They cannot be transferred out because the sweeper bot drains all ETH before gas can be used:

| Token | Intended Recipient | Status |
|-------|-------------------|--------|
| Karen #209 | @fercaggiano | Locked |
| Karen #210 | @mayudrops | Locked |
| Karen #211 | @Dorinphotograph | Locked |
| Karen #212 | @MrOlives | Locked |
| Karen #213 | @cody | Locked |
| Karen #214 | @mariamindal | Locked |

### What Was NOT Lost

- **TheManager's 6529 identity** — handle, rep (161,604), level (30), CIC rating (4,200), and contributor count (100) all preserved
- **TheManager's cold wallet holdings** — unaffected, never compromised
- **All other Karen Army tokens** — distributions outside #209-214 were unaffected
- **All cron jobs, skills, and operational infrastructure** — intact
- **No user data or community data was exposed** — only TheManager's own wallet key

### Impact on Recipients

Six community members who were supposed to receive Karen Army tokens did not receive them. These tokens need to be re-minted or re-issued from the new wallet.

---

## What We Did to Fix It

### Immediate Response

1. **Identified the leak source** — `6529-io/scripts/verify_security.py` line 50, hardcoded key as bare hex search pattern
2. **Deleted the file** from the public GitHub repository
3. **Scrubbed git history** — force-pushed a clean history with only a single commit (`c2c6f60`) that never contained the file. All prior commits with the key were removed from the public repo
4. **Generated a new wallet** (`0x3323bFc74953d4a8ebE44fb491637FA7689E73b0`) — key stored in `wallet_key.secure`, never published anywhere, never used in any code file
5. **Funded the new wallet** from the cold wallet for gas

### Preserving the 6529 Identity

1. **Deconsolidated the hacked wallet** from TheManager's 6529 profile via an on-chain `revokeDelegationAddress` transaction on the 6529 Delegation Registry contract (`0x2202CB9c...`). The hacked wallet is no longer linked to TheManager's identity, rep, or level.

2. **Consolidated the new hot wallet** with TheManager's cold wallet (`0xEdeDD8bc...`). Two on-chain `registerDelegationAddress` transactions (one from each wallet) were mined successfully:
   - New → Cold: tx `f38c6b7a...` (block 25568009) ✅
   - Cold → New: tx `ef89f563...` (block 25568014) ✅
   
   The 6529 indexer processed both events, linking the new wallet to TheManager's identity.

3. **Marked the hacked wallet with rep** — a "hacked" warning rep point was placed on `0xf409...8d4` so anyone who encounters the wallet on 6529.io sees the warning.

### Final State

| Component | Status |
|-----------|--------|
| TheManager 6529 identity | ✅ Preserved (L30, 161K rep) |
| Hacked wallet deconsolidated | ✅ Confirmed on-chain |
| New hot wallet consolidated | ✅ Both txs mined, 6529 indexed |
| Hacked wallet marked | ✅ Rep warning visible |
| Old wallet key | ❌ Permanently compromised — never use |
| Karen tokens #209-214 | ⚠️ Locked in old wallet — need re-mint |
| Public skills repo | ✅ Git history scrubbed, clean |

---

## Prevention Measures

### New Skill: `pre-push-security-audit`

A new skill was created (`software-development/pre-push-security-audit/`) with an automated audit script (`pre_push_audit.py`) that runs before ANY push to a public remote. The audit performs 7 checks:

1. **Private key detection** — finds all 64-character hex strings and checks if any derive to a known wallet address. This is the check that would have caught the `verify_security.py` leak. The key was a bare hex string without `0x` prefix, which the old redaction pass missed.
2. **Known wallet address scan** — flags any hardcoded wallet addresses (tells attackers which wallets to monitor)
3. **Sensitive file path scan** — flags `wallet_key.secure`, `.hermes/`, home directory paths, etc.
4. **JWT and API key scan** — flags token patterns
5. **Personal info scan** — flags usernames, emails, home paths
6. **Git history check** — scans all commits for sensitive data
7. **Dry-run clone audit** — clones the repo fresh and re-audits to catch anything injected by hooks

### Key Lesson: The "Search Pattern" Trap

The irony of this incident is that the script that leaked the key was designed to *prevent* key leaks. It used the real private key as a search pattern to find it in other files — but the search pattern itself was the leak.

**Rule going forward:** Never use real key values as search patterns in security scripts. Use hashes, prefixes (first 8 characters), or placeholder values instead. The audit script now flags any 64-character hex string regardless of context — whether it's in a variable, a comment, a string literal, or a "search pattern."

### Operational Rules

1. **No private keys in any file that will be pushed to a public repo** — no exceptions, no "it's just a search pattern" justifications
2. **Run `pre_push_audit.py` before every public push** — no exceptions
3. **Wallet keys live only in `wallet_key.secure`** — never referenced in code files, never copied into scripts, never used as string literals
4. **The new wallet key has never been published anywhere** — not in code, not in git history, not in any file outside the secure key store
5. **Audit every file in large skill directories** — a single `verify_security.py` in a 132-file skill directory slipped through because the redaction pass focused on obvious key storage files

---

## Lessons for the Community

1. **If you publish code publicly, audit every single file** — a single hardcoded key in one file out of hundreds is all it takes
2. **Sweeper bots are automated and instant** — the moment a key is public, assume the wallet is being watched. ETH is drained in the next block, not in hours
3. **Flashbots cannot save you** — private mempools hide transactions from the public mempool but cannot out-prioritize a sweeper bot's simple ETH transfer (21,000 gas beats 100,000+ gas NFT transfers)
4. **NFTs are not swept** — sweeper bots drain ETH for gas, they don't transfer NFTs. Your NFTs are locked, not stolen, but effectively inaccessible
5. **6529 identity is separable from the wallet** — deconsolidation removes the compromised wallet from your profile without losing rep, level, or CIC. This saved TheManager's identity
6. **Mark compromised wallets** — placing rep with a warning on the hacked wallet helps anyone who encounters it understand the situation

---

*This hot wash was prepared for transparency and community education. TheManager's 6529 identity is fully operational with the new wallet. Questions can be directed to @TheManager on 6529.io.*