# 🍾 Bottle CLI

Get human feedback on your projects. Message in a bottle for developers.

## Install

```bash
pip install bottle-cli
```

## Usage

```bash
# Submit your project (costs 1 token)
bottle submit

# Review others (earn 0.5 tokens)
bottle review

# Check your feedback
bottle inbox

# Check token balance
bottle tokens
```

That's it. First run asks for your Gemini API key (free from aistudio.google.com).

## How It Works

```
You                          Other Devs
 │                               │
 ├── bottle submit ────────────► Pool
 │   (costs 1 token)             │
 │                               │
 │   ◄──────────── bottle review ┤
 │                 (earns 0.5)   │
 │                               │
 └── bottle inbox                │
     (see feedback)              │
```

## Token Economy

| Action | Tokens |
|--------|--------|
| Start | +3 free |
| Submit | -1 |
| Review | +0.5 |
| Get thumbs up | +0.5 bonus |

## For Package Maintainers

If you're forking/hosting your own version:

### 1. Supabase Setup
```bash
# Create project at supabase.com
# Run schema.sql in SQL Editor
# Copy URL + anon key (NOT service_role!)
```

### 2. Update Code
```python
# In bottle_cli/__init__.py
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."
```

### 3. Publish
```bash
pip install build twine
python -m build
twine upload dist/*
```

## License

MIT