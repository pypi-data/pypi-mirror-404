# Wizzlethorpe Python Client

Python client for Wizzlethorpe Labs APIs.

## Installation

Install from PyPI:

```bash
pip install wizzlethorpe
```

Or install from source for development:

```bash
git clone https://github.com/wizzlethorpe/wizzlethorpe-python.git
cd wizzlethorpe-python
pip install -e .
```

## CLI Usage

The CLI is available as both `wizzlethorpe` and the shorter `wzl` alias:

```bash
# Link your Patreon account
wzl login

# Cocktails
wzl cocktails list
wzl cocktails get "Inferno Sunrise"
wzl ingredients list
wzl ingredients list --environment Forest

# Quickbrush image generation
wzl quickbrush character --prompt "A wise elven mage"
wzl quickbrush scene --prompt "A misty forest" --context "D&D campaign" -o forest.webp
wzl quickbrush creature --prompt "A fire elemental" --reference ./ref.png
```

## Library Usage

```python
from wizzlethorpe import WizzlethorpeClient

client = WizzlethorpeClient()

# Cocktails
cocktails = client.cocktails.list()
for c in cocktails:
    print(f"{c.name}: {c.description}")

# Quickbrush (requires API key or linked account)
client = WizzlethorpeClient(api_key="your-openai-key")
image = client.quickbrush.generate(
    type="character",
    prompt="A battle-scarred dwarf warrior",
)
image.save("dwarf.webp")
```
