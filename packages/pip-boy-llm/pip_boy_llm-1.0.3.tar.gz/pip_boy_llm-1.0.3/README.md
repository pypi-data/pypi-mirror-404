# PIP-BOY LLM

**Vault-Tec Local AI Terminal** - Run local LLMs with a retro Fallout PIP-BOY themed interface.

## Installation

```bash
pip install pip-boy-llm
```

### Optional Dependencies

```bash
# For 4-bit quantization (Mistral 7B)
pip install pip-boy-llm[quantization]

# For PDF file support
pip install pip-boy-llm[pdf]

# For Windows readline support
pip install pip-boy-llm[readline]

# Install all optional dependencies
pip install pip-boy-llm[all]
```

## Quick Start

1. **Run the setup wizard** (recommended for first-time users):
   ```bash
   pip-boy-setup
   ```

2. **Start the terminal**:
   ```bash
   pip-boy-llm
   ```

3. **Select a model** and start chatting!

## Models

| Model | Description | Requirements |
|-------|-------------|--------------|
| Gemma 3 1B | Fast, lightweight | HuggingFace login |
| Llama 3.2 1B | Fast, good quality | HuggingFace login + license |
| Mistral 7B | Best quality, 4-bit | bitsandbytes (optional) |

## HuggingFace Login

Some models require HuggingFace authentication:

1. Create an account at [huggingface.co](https://huggingface.co)
2. Generate a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
3. Run `pip-boy-setup` and enter your token

### License Agreements

Llama and Gemma models require accepting license agreements:

- **Llama 3.2**: [Accept license](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct)
- **Gemma 3**: [Accept license](https://huggingface.co/google/gemma-3-1b-it)

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/exit` | Quit the terminal |
| `/clear` | Clear conversation history |
| `/reset` | Reset the AI model |
| `/model` | Show current model info |
| `@filepath` | Include file contents in message |

## File References

Include file contents in your messages using `@`:

```
> Explain this code: @main.py
> Summarize these files: @src/app.py @src/utils.py
> Review @"path with spaces/file.py"
```

## Commands Reference

### pip-boy-llm

Main terminal interface. Select a model and start chatting.

```bash
pip-boy-llm
```

### pip-boy-setup

Setup wizard for first-time configuration:
- Checks dependencies (PyTorch, Transformers, etc.)
- Configures HuggingFace authentication
- Verifies model access
- Creates config directory

```bash
pip-boy-setup
```

### pip-boy-update

Check for package updates:

```bash
pip-boy-update
```

## Configuration

Config files are stored in `~/.airllm/`:

- `config.yaml` - User preferences
- `history.yaml` - Chat history

## System Requirements

- Python 3.9+
- CUDA-capable GPU recommended (CPU mode available)
- 4GB+ VRAM for 1B models
- 8GB+ VRAM for Mistral 7B (4-bit)

## License

MIT License
