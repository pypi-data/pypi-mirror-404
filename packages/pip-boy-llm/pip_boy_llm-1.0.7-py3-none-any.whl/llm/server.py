"""
Local LLM Chat Server - Multi-model support
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import torch
import warnings
import sys
import os
import re

warnings.filterwarnings("ignore")

app = Flask(__name__)
CORS(app)

# Available models
# use_4bit: False = float16 (faster for small models), True = 4-bit (needed for large models)
MODELS = {
    "gemma-1b": {
        "name": "google/gemma-3-1b-it",
        "prompt_format": "gemma3",
        "description": "Gemma 3 1B - Fast",
        "use_4bit": False  # 1B = float16
    },
    "llama-1b": {
        "name": "meta-llama/Llama-3.2-1B-Instruct",
        "prompt_format": "llama3",
        "description": "Llama 3.2 1B - Fast",
        "use_4bit": False  # 1B = float16
    },
    "mistral-7b": {
        "name": "mistralai/Mistral-7B-Instruct-v0.1",
        "prompt_format": "mistral",
        "description": "Mistral 7B - Best quality",
        "use_4bit": True  # 7B = 4-bit
    },
    "deepseek-1.5b": {
        "name": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
        "prompt_format": "qwen",
        "description": "DeepSeek R1 1.5B - Reasoning",
        "use_4bit": False  # 1.5B = float16
    },
}

# Current model config
current_model_id = os.environ.get("LLM_MODEL", "mistral-7b")
model = None
tokenizer = None

# Conversation history
conversation_history = []

def load_model():
    global model, tokenizer, current_model_id

    model_config = MODELS.get(current_model_id, MODELS["mistral-7b"])
    model_name = model_config["name"]
    use_4bit = model_config.get("use_4bit", True)

    mode = "4-bit" if use_4bit else "float16"
    print(f"[*] Loading {current_model_id} ({model_name}) in {mode}...")

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    if use_4bit:
        try:
            config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=config,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            print("[+] 4-bit model loaded!")
        except Exception as e:
            print(f"[!] 4-bit failed ({e}), falling back to float16...")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                low_cpu_mem_usage=True
            )
            print("[+] Float16 model loaded!")
    else:
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto",
            low_cpu_mem_usage=True
        )
        print("[+] Float16 model loaded!")

def get_system_prompt():
    """Get system prompt with user's name if configured."""
    try:
        from llm.config import get_config_value
        user_name = get_config_value("user_name", "")
        if user_name and user_name != "VAULT DWELLER":
            return f"You are a helpful assistant. The user's name is {user_name}. Address them by name when appropriate. Give complete, concise answers. Always finish your thoughts - never stop mid-sentence."
    except Exception:
        pass
    return "You are a helpful assistant. Give complete, concise answers. Always finish your thoughts - never stop mid-sentence."


def format_prompt(message, prompt_format, history=None):
    """Format prompt based on model type, including conversation history"""
    if history is None:
        history = []

    system_prompt = get_system_prompt()

    if prompt_format == "mistral":
        # Mistral format with system instruction
        prompt = f"[INST] {system_prompt}\n\n"
        for turn in history:
            prompt += f"{turn['user']} [/INST] {turn['assistant']} [INST] "
        prompt += f"{message} [/INST]"
        return prompt

    elif prompt_format == "gemma3":
        # Gemma 3 uses chat template - return messages list with system
        messages = [{"role": "user", "content": f"{system_prompt}\n\n{message}"}] if not history else []
        if history:
            # Add system to first message
            first_msg = f"{system_prompt}\n\n{history[0]['user']}"
            messages.append({"role": "user", "content": first_msg})
            messages.append({"role": "assistant", "content": history[0]['assistant']})
            for turn in history[1:]:
                messages.append({"role": "user", "content": turn['user']})
                messages.append({"role": "assistant", "content": turn['assistant']})
            messages.append({"role": "user", "content": message})
        return messages

    elif prompt_format == "llama3":
        # Llama 3.2 uses chat template with system role
        messages = [{"role": "system", "content": system_prompt}]
        for turn in history:
            messages.append({"role": "user", "content": turn['user']})
            messages.append({"role": "assistant", "content": turn['assistant']})
        messages.append({"role": "user", "content": message})
        return messages

    elif prompt_format == "qwen":
        # Qwen/DeepSeek uses chat template - embed system in first user message
        messages = [{"role": "user", "content": f"{system_prompt}\n\n{message}"}] if not history else []
        if history:
            first_msg = f"{system_prompt}\n\n{history[0]['user']}"
            messages.append({"role": "user", "content": first_msg})
            messages.append({"role": "assistant", "content": history[0]['assistant']})
            for turn in history[1:]:
                messages.append({"role": "user", "content": turn['user']})
                messages.append({"role": "assistant", "content": turn['assistant']})
            messages.append({"role": "user", "content": message})
        return messages

    else:
        return message

@app.route('/chat', methods=['POST'])
def chat():
    global conversation_history

    try:
        data = request.json
        message = data.get('message', '').strip()

        if not message:
            return jsonify({'error': 'No message'}), 400

        model_config = MODELS.get(current_model_id, MODELS["mistral-7b"])
        prompt_format = model_config["prompt_format"]

        # Build prompt with conversation history
        prompt = format_prompt(message, prompt_format, conversation_history)

        # Handle models with chat template (Gemma 3, Llama 3, Qwen/DeepSeek)
        if prompt_format in ("gemma3", "llama3", "qwen"):
            inputs = tokenizer.apply_chat_template(
                prompt,  # This is actually a messages list
                add_generation_prompt=True,
                tokenize=True,
                return_dict=True,
                return_tensors="pt"
            ).to(model.device)
            input_len = inputs["input_ids"].shape[-1]
        else:
            inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
            input_len = inputs['input_ids'].shape[1]

        # Limit context length to avoid OOM
        max_context = 2048
        if input_len > max_context:
            # Trim history if too long
            while conversation_history and input_len > max_context:
                conversation_history.pop(0)
                prompt = format_prompt(message, prompt_format, conversation_history)
                if prompt_format in ("gemma3", "llama3", "qwen"):
                    inputs = tokenizer.apply_chat_template(
                        prompt,
                        add_generation_prompt=True,
                        tokenize=True,
                        return_dict=True,
                        return_tensors="pt"
                    ).to(model.device)
                    input_len = inputs["input_ids"].shape[-1]
                else:
                    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
                    input_len = inputs['input_ids'].shape[1]

        with torch.no_grad():
            output = model.generate(
                **inputs,
                max_new_tokens=1024,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )

        # Decode only the new tokens (skip the input prompt)
        response = tokenizer.decode(output[0][input_len:], skip_special_tokens=True).strip()

        # Strip <think>...</think> tags from reasoning models (DeepSeek R1)
        response = re.sub(r'<think>.*?</think>\s*', '', response, flags=re.DOTALL).strip()

        # Add to conversation history
        conversation_history.append({
            'user': message,
            'assistant': response
        })

        # Keep history manageable (last 10 turns)
        if len(conversation_history) > 10:
            conversation_history.pop(0)

        return jsonify({
            'response': response,
            'history_length': len(conversation_history)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear', methods=['POST'])
def clear_history():
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'ok', 'message': 'History cleared'})

@app.route('/health', methods=['GET'])
def health():
    model_config = MODELS.get(current_model_id, MODELS["mistral-7b"])
    return jsonify({
        'status': 'ok',
        'model': current_model_id,
        'model_name': model_config["name"]
    })

def main():
    load_model()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    main()
