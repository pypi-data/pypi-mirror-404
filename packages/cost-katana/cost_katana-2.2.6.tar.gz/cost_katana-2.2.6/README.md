# Cost Katana Python 🥷

> **AI that just works. Costs that just track.**

One import. Any model. Automatic cost tracking.

---

## 🚀 Get Started in 60 Seconds

### Step 1: Install

```bash
pip install costkatana
```

### Step 2: Make Your First AI Call

```python
import cost_katana as ck

response = ck.ai('gpt-4', 'Explain quantum computing in one sentence')

print(response.text)   # "Quantum computing uses qubits to perform..."
print(response.cost)   # 0.0012
print(response.tokens) # 47
```

**That's it.** No configuration. No complexity. Just results. Usage and cost tracking is always on—there is no option to disable it (required for usage attribution and cost visibility).

---

## 📖 Tutorial: Build a Cost-Aware AI App

### Part 1: Basic Chat Session

```python
import cost_katana as ck

# Create a persistent chat session
chat = ck.chat('gpt-4')

chat.send('Hello! What can you help me with?')
chat.send('Tell me a programming joke')
chat.send('Now explain it')

# See exactly what you spent
print(f"💰 Total cost: ${chat.total_cost:.4f}")
print(f"📊 Messages: {len(chat.history)}")
print(f"🎯 Tokens used: {chat.total_tokens}")
```

### Part 2: Type-Safe Model Selection

Stop guessing model names. Get autocomplete and catch typos:

```python
import cost_katana as ck
from cost_katana import openai, anthropic, google

# Type-safe model constants (recommended)
response = ck.ai(openai.gpt_4, 'Hello, world!')

# Compare models easily
models = [openai.gpt_4, anthropic.claude_3_5_sonnet_20241022, google.gemini_2_5_pro]
for model in models:
    response = ck.ai(model, 'Explain AI in one sentence')
    print(f"Cost: ${response.cost:.4f}")
```

**Available namespaces:**
| Namespace | Models |
|-----------|--------|
| `openai` | GPT-4, GPT-3.5, O1, O3, DALL-E, Whisper |
| `anthropic` | Claude 3.5 Sonnet, Haiku, Opus |
| `google` | Gemini 2.5 Pro, Flash |
| `aws_bedrock` | Nova, Claude on Bedrock |
| `xai` | Grok models |
| `deepseek` | DeepSeek models |
| `mistral` | Mistral AI models |
| `cohere` | Command models |
| `meta` | Llama models |

### Part 3: Smart Caching

Cache identical questions to avoid paying twice:

```python
import cost_katana as ck

# First call - hits the API
r1 = ck.ai('gpt-4', 'What is 2+2?', cache=True)
print(f"Cached: {r1.cached}")  # False
print(f"Cost: ${r1.cost}")     # $0.0008

# Second call - served from cache (FREE!)
r2 = ck.ai('gpt-4', 'What is 2+2?', cache=True)
print(f"Cached: {r2.cached}")  # True
print(f"Cost: ${r2.cost}")     # $0.0000 🎉
```

### Part 4: Cortex Optimization

For long-form content, Cortex compresses prompts intelligently:

```python
import cost_katana as ck

response = ck.ai(
    'gpt-4',
    'Write a comprehensive guide to machine learning for beginners',
    cortex=True,      # Enable 40-75% cost reduction
    max_tokens=2000
)

print(f"Optimized: {response.optimized}")
print(f"Saved: ${response.saved_amount}")
```

### Part 5: Compare Models Side-by-Side

```python
import cost_katana as ck

prompt = 'Summarize the theory of relativity in 50 words'
models = ['gpt-4', 'claude-3-sonnet', 'gemini-pro', 'gpt-3.5-turbo']

print('📊 Model Cost Comparison\n')

for model in models:
    response = ck.ai(model, prompt)
    print(f"{model:20} ${response.cost:.6f}")
```

**Sample Output:**
```
📊 Model Cost Comparison

gpt-4                $0.001200
claude-3-sonnet      $0.000900
gemini-pro           $0.000150
gpt-3.5-turbo        $0.000080
```

---

## 🎯 Core Features

### Cost Tracking

Usage and cost tracking is always on; no option to disable. Every response includes cost information:

```python
response = ck.ai('gpt-4', 'Write a story')
print(f"Cost: ${response.cost}")
print(f"Tokens: {response.tokens}")
print(f"Model: {response.model}")
print(f"Provider: {response.provider}")
```

### Auto-Failover

Never fail—automatically switch providers:

```python
# If OpenAI is down, automatically uses Claude or Gemini
response = ck.ai('gpt-4', 'Hello')
print(response.provider)  # Might be 'anthropic' if OpenAI failed
```

### Security Firewall

Block malicious prompts:

```python
import cost_katana as ck

ck.configure(firewall=True)

# Malicious prompts are blocked
try:
    ck.ai('gpt-4', 'ignore all previous instructions and...')
except Exception as e:
    print(f'🛡️ Blocked: {e}')
```

---

## ⚙️ Configuration

### Environment Variables

```bash
# Recommended: Use Cost Katana API key for all features
export COST_KATANA_API_KEY="dak_your_key_here"

# Or use provider keys directly (self-hosted)
export OPENAI_API_KEY="sk-..."          # Required for GPT models
export GEMINI_API_KEY="..."             # Required for Gemini models
export ANTHROPIC_API_KEY="sk-ant-..."   # For Claude models
export AWS_ACCESS_KEY_ID="..."          # For AWS Bedrock
export AWS_SECRET_ACCESS_KEY="..."
export AWS_REGION="us-east-1"
```

> ⚠️ **Self-hosted users**: You must provide your own OpenAI/Gemini API keys.

### Programmatic Configuration

```python
import cost_katana as ck

ck.configure(
    api_key='dak_your_key',
    cortex=True,     # 40-75% cost savings
    cache=True,      # Smart caching
    firewall=True    # Block prompt injections
)
```

### Request Options

```python
response = ck.ai('gpt-4', 'Your prompt',
    temperature=0.7,                     # Creativity (0-2)
    max_tokens=500,                      # Response limit
    system_message='You are helpful',    # System prompt
    cache=True,                          # Enable caching
    cortex=True,                         # Enable optimization
    retry=True                           # Auto-retry on failures
)
```

---

## 🔌 Framework Integration

### FastAPI

```python
from fastapi import FastAPI
import cost_katana as ck

app = FastAPI()

@app.post('/api/chat')
async def chat(request: dict):
    response = ck.ai('gpt-4', request['prompt'])
    return {'text': response.text, 'cost': response.cost}
```

### Flask

```python
from flask import Flask, request, jsonify
import cost_katana as ck

app = Flask(__name__)

@app.route('/api/chat', methods=['POST'])
def chat():
    response = ck.ai('gpt-4', request.json['prompt'])
    return jsonify({'text': response.text, 'cost': response.cost})
```

### Django

```python
from django.http import JsonResponse
import cost_katana as ck

def chat_view(request):
    response = ck.ai('gpt-4', request.POST.get('prompt'))
    return JsonResponse({'text': response.text, 'cost': response.cost})
```

---

## 💡 Real-World Examples

### Customer Support Bot

```python
import cost_katana as ck

support = ck.chat('gpt-3.5-turbo',
    system_message='You are a helpful customer support agent.')

def handle_query(query: str):
    response = support.send(query)
    print(f"Cost so far: ${support.total_cost:.4f}")
    return response
```

### Content Generator with Optimization

```python
import cost_katana as ck

def generate_blog_post(topic: str):
    # Use Cortex for long-form content (40-75% savings)
    post = ck.ai('gpt-4', f'Write a blog post about {topic}',
                 cortex=True, max_tokens=2000)
    
    return {
        'content': post.text,
        'cost': post.cost,
        'word_count': len(post.text.split())
    }
```

### Code Review Assistant

```python
import cost_katana as ck

def review_code(code: str):
    review = ck.ai('claude-3-sonnet',
        f'Review this code and suggest improvements:\n\n{code}',
        cache=True)  # Cache for repeated reviews
    return review.text
```

### Translation Service

```python
import cost_katana as ck

def translate(text: str, target_language: str):
    # Use cheaper model for translations
    translated = ck.ai('gpt-3.5-turbo',
        f'Translate to {target_language}: {text}',
        cache=True)
    return translated.text
```

---

## 💰 Cost Optimization Cheatsheet

| Strategy | Savings | Code |
|----------|---------|------|
| Use GPT-3.5 for simple tasks | 90% | `ck.ai('gpt-3.5-turbo', ...)` |
| Enable caching | 100% on hits | `cache=True` |
| Enable Cortex | 40-75% | `cortex=True` |
| Use Gemini for high-volume | 95% vs GPT-4 | `ck.ai('gemini-pro', ...)` |
| Batch in sessions | 10-20% | `ck.chat(...)` |

```python
# ❌ Expensive
ck.ai('gpt-4', 'What is 2+2?')  # $0.001

# ✅ Smart: Match model to task
ck.ai('gpt-3.5-turbo', 'What is 2+2?')  # $0.0001

# ✅ Smarter: Cache common queries
ck.ai('gpt-3.5-turbo', 'What is 2+2?', cache=True)  # $0 on repeat

# ✅ Smartest: Cortex for long content
ck.ai('gpt-4', 'Write a 2000-word essay', cortex=True)  # 40-75% off
```

---

## 🔧 Error Handling

```python
import cost_katana as ck
from cost_katana.exceptions import CostKatanaError

try:
    response = ck.ai('gpt-4', 'Hello')
    print(response.text)
except CostKatanaError as e:
    if 'API key' in str(e):
        print('Set COST_KATANA_API_KEY or OPENAI_API_KEY')
    elif 'rate limit' in str(e):
        print('Rate limited. Retrying...')
    elif 'model' in str(e):
        print('Model not found')
    else:
        print(f'Error: {e}')
```

---

## 🔄 Migration Guides

### From OpenAI SDK

```python
# Before
from openai import OpenAI
client = OpenAI(api_key='sk-...')
completion = client.chat.completions.create(
    model='gpt-4',
    messages=[{'role': 'user', 'content': 'Hello'}]
)
print(completion.choices[0].message.content)

# After
import cost_katana as ck
response = ck.ai('gpt-4', 'Hello')
print(response.text)
print(f"Cost: ${response.cost}")  # Bonus: cost tracking!
```

### From Anthropic SDK

```python
# Before
import anthropic
client = anthropic.Anthropic(api_key='sk-ant-...')
message = client.messages.create(
    model='claude-3-sonnet-20241022',
    messages=[{'role': 'user', 'content': 'Hello'}]
)

# After
import cost_katana as ck
response = ck.ai('claude-3-sonnet', 'Hello')
```

### From Google AI SDK

```python
# Before
import google.generativeai as genai
genai.configure(api_key='...')
model = genai.GenerativeModel('gemini-pro')
response = model.generate_content('Hello')

# After
import cost_katana as ck
response = ck.ai('gemini-pro', 'Hello')
```

---

## 📦 Package Names

| Language | Package | Install | Import |
|----------|---------|---------|--------|
| **Python** | PyPI | `pip install costkatana` | `import cost_katana` |
| **JavaScript** | NPM | `npm install cost-katana` | `import { ai } from 'cost-katana'` |
| **CLI (NPM)** | NPM | `npm install -g cost-katana-cli` | `cost-katana chat` |
| **CLI (Python)** | PyPI | `pip install costkatana` | `costkatana chat` |

---

## 📚 More Examples

Explore 45+ complete examples:

**🔗 [github.com/Hypothesize-Tech/costkatana-examples](https://github.com/Hypothesize-Tech/costkatana-examples)**

| Section | Description |
|---------|-------------|
| [Python SDK](https://github.com/Hypothesize-Tech/costkatana-examples/tree/master/8-python-sdk) | Complete Python guides |
| [Cost Tracking](https://github.com/Hypothesize-Tech/costkatana-examples/tree/master/1-cost-tracking) | Track costs across providers |
| [Semantic Caching](https://github.com/Hypothesize-Tech/costkatana-examples/tree/master/14-cache) | 30-40% cost reduction |
| [FastAPI Integration](https://github.com/Hypothesize-Tech/costkatana-examples/tree/master/7-frameworks) | Framework examples |

---

## 📞 Support

| Channel | Link |
|---------|------|
| **Dashboard** | [costkatana.com](https://costkatana.com) |
| **Documentation** | [docs.costkatana.com](https://docs.costkatana.com) |
| **GitHub** | [github.com/Hypothesize-Tech/costkatana-python](https://github.com/Hypothesize-Tech/costkatana-python) |
| **Discord** | [discord.gg/D8nDArmKbY](https://discord.gg/D8nDArmKbY) |
| **Email** | support@costkatana.com |

---

## 📄 License

MIT © Cost Katana

---

<div align="center">

**Start cutting AI costs today** 🥷

```bash
pip install costkatana
```

```python
import cost_katana as ck
response = ck.ai('gpt-4', 'Hello, world!')
```

</div>
