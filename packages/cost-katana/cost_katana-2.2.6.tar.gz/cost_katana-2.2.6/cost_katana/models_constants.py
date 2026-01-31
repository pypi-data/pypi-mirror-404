"""
Type-Safe Model Constants for Cost Katana Python SDK

Use these constants instead of strings to prevent typos and get IDE autocomplete.

Example:
    import cost_katana as ck
    from cost_katana.models_constants import openai, anthropic, google
    
    # Type-safe model selection (recommended)
    response = ck.ai(openai.gpt_4, 'Hello world')
    
    # Old way still works but shows deprecation warning
    response = ck.ai('gpt-4', 'Hello world')
"""


# ============================================================================
# OPENAI MODELS
# ============================================================================

class openai:
    """OpenAI model constants"""
    
    # GPT-5.2 Series (Latest)
    gpt_5_2 = 'gpt-5.2'
    gpt_5_2_pro = 'gpt-5.2-pro'
    gpt_5_2_codex = 'gpt-5.2-codex'
    gpt_5_2_chat_latest = 'gpt-5.2-chat-latest'
    
    # GPT-5 Series
    gpt_5 = 'gpt-5'
    gpt_5_mini = 'gpt-5-mini'
    gpt_5_nano = 'gpt-5-nano'
    gpt_5_pro = 'gpt-5-pro'
    gpt_5_codex = 'gpt-5-codex'
    gpt_5_chat_latest = 'gpt-5-chat-latest'
    
    # GPT-4.1 Series
    gpt_4_1 = 'gpt-4.1'
    gpt_4_1_mini = 'gpt-4.1-mini'
    gpt_4_1_nano = 'gpt-4.1-nano'
    
    # GPT-4o Series
    gpt_4o = 'gpt-4o'
    gpt_4o_2024_08_06 = 'gpt-4o-2024-08-06'
    gpt_4o_2024_05_13 = 'gpt-4o-2024-05-13'
    gpt_4o_audio_preview = 'gpt-4o-audio-preview'
    gpt_4o_realtime_preview = 'gpt-4o-realtime-preview'
    gpt_4o_mini = 'gpt-4o-mini'
    gpt_4o_mini_2024_07_18 = 'gpt-4o-mini-2024-07-18'
    gpt_4o_mini_audio_preview = 'gpt-4o-mini-audio-preview'
    gpt_4o_mini_realtime_preview = 'gpt-4o-mini-realtime-preview'
    
    # O-Series Models
    o3_pro = 'o3-pro'
    o3_deep_research = 'o3-deep-research'
    o4_mini = 'o4-mini'
    o4_mini_deep_research = 'o4-mini-deep-research'
    o3 = 'o3'
    o1_pro = 'o1-pro'
    o1 = 'o1'
    o3_mini = 'o3-mini'
    o1_mini = 'o1-mini'
    o1_preview = 'o1-preview'
    
    # Video Generation
    sora_2 = 'sora-2'
    sora_2_pro = 'sora-2-pro'
    
    # Image Generation
    gpt_image_1 = 'gpt-image-1'
    gpt_image_1_mini = 'gpt-image-1-mini'
    dall_e_3 = 'dall-e-3'
    dall_e_2 = 'dall-e-2'
    
    # Audio & Realtime
    gpt_realtime = 'gpt-realtime'
    gpt_realtime_mini = 'gpt-realtime-mini'
    gpt_audio = 'gpt-audio'
    gpt_audio_mini = 'gpt-audio-mini'
    
    # Transcription
    gpt_4o_transcribe = 'gpt-4o-transcribe'
    gpt_4o_transcribe_diarize = 'gpt-4o-transcribe-diarize'
    gpt_4o_mini_transcribe = 'gpt-4o-mini-transcribe'
    whisper_1 = 'whisper-1'
    
    # Text-to-Speech
    gpt_4o_mini_tts = 'gpt-4o-mini-tts'
    tts_1 = 'tts-1'
    tts_1_hd = 'tts-1-hd'
    
    # Open-Weight Models
    gpt_oss_120b = 'gpt-oss-120b'
    gpt_oss_20b = 'gpt-oss-20b'
    
    # Specialized
    codex_mini_latest = 'codex-mini-latest'
    omni_moderation_latest = 'omni-moderation-latest'
    gpt_4o_mini_search_preview = 'gpt-4o-mini-search-preview-2025-03-11'
    gpt_4o_search_preview = 'gpt-4o-search-preview-2025-03-11'
    computer_use_preview = 'computer-use-preview-2025-03-11'
    
    # Embeddings
    text_embedding_3_small = 'text-embedding-3-small'
    text_embedding_3_large = 'text-embedding-3-large'
    text_embedding_ada_002 = 'text-embedding-ada-002'
    
    # ChatGPT Models
    chatgpt_4o_latest = 'chatgpt-4o-latest'
    
    # Legacy Models
    gpt_4_turbo = 'gpt-4-turbo'
    gpt_4_turbo_2024_04_09 = 'gpt-4-turbo-2024-04-09'
    gpt_4_0125_preview = 'gpt-4-0125-preview'
    gpt_4_1106_preview = 'gpt-4-1106-preview'
    gpt_4_1106_vision_preview = 'gpt-4-1106-vision-preview'
    gpt_4 = 'gpt-4'
    gpt_3_5_turbo = 'gpt-3.5-turbo'
    gpt_3_5_turbo_0125 = 'gpt-3.5-turbo-0125'
    gpt_3_5_turbo_1106 = 'gpt-3.5-turbo-1106'
    gpt_3_5_turbo_16k_0613 = 'gpt-3.5-turbo-16k-0613'
    gpt_3_5_turbo_instruct = 'gpt-3.5-turbo-instruct'
    babbage_002 = 'babbage-002'
    davinci_002 = 'davinci-002'


# ============================================================================
# ANTHROPIC MODELS
# ============================================================================

class anthropic:
    """Anthropic model constants"""
    
    # Claude 4.5 Series (Latest)
    claude_sonnet_4_5_20250929 = 'claude-sonnet-4-5-20250929'
    claude_sonnet_4_5 = 'claude-sonnet-4-5'
    claude_haiku_4_5_20251001 = 'claude-haiku-4-5-20251001'
    claude_haiku_4_5 = 'claude-haiku-4-5'
    claude_opus_4_5_20251101 = 'claude-opus-4-5-20251101'
    claude_opus_4_5 = 'claude-opus-4-5'
    
    # Claude 4 Series (Legacy)
    claude_opus_4_1_20250805 = 'claude-opus-4-1-20250805'
    claude_opus_4_20250514 = 'claude-opus-4-20250514'
    claude_sonnet_4_20250514 = 'claude-sonnet-4-20250514'
    
    # Claude 3.7 Series (Deprecated)
    claude_3_7_sonnet_20250219 = 'claude-3-7-sonnet-20250219'
    
    # Claude 3.5 Series
    claude_3_5_sonnet_20241022 = 'claude-3-5-sonnet-20241022'
    claude_3_5_haiku_20241022 = 'claude-3-5-haiku-20241022'
    
    # Claude 3 Series (Legacy)
    claude_3_haiku_20240307 = 'claude-3-haiku-20240307'
    claude_3_opus_20240229 = 'claude-3-opus-20240229'


# ============================================================================
# GOOGLE (GEMINI) MODELS
# ============================================================================

class google:
    """Google AI model constants"""
    
    # Gemini 3 Series (Latest)
    gemini_3_pro_preview = 'gemini-3-pro-preview'
    gemini_3_pro_image_preview = 'gemini-3-pro-image-preview'
    gemini_3_flash_preview = 'gemini-3-flash-preview'
    
    # Gemini 2.5 Series (Latest)
    gemini_2_5_pro = 'gemini-2.5-pro'
    gemini_2_5_pro_computer_use_preview = 'gemini-2.5-pro-computer-use-preview'
    gemini_2_5_flash = 'gemini-2.5-flash'
    gemini_2_5_flash_lite_preview = 'gemini-2.5-flash-lite-preview'
    gemini_2_5_flash_preview_09_2025 = 'gemini-2.5-flash-preview-09-2025'
    
    # Gemini 2.0 Series
    gemini_2_0_flash = 'gemini-2.0-flash'
    gemini_2_0_flash_image_generation = 'gemini-2.0-flash-image-generation'
    gemini_2_0_flash_lite = 'gemini-2.0-flash-lite'
    gemini_2_0_flash_audio = 'gemini-2.0-flash-audio'
    
    # Gemini 1.5 Series
    gemini_1_5_flash = 'gemini-1.5-flash'
    gemini_1_5_flash_8b = 'gemini-1.5-flash-8b'
    gemini_1_5_pro = 'gemini-1.5-pro'
    
    # Gemini 1.0 Series
    gemini_1_0_pro = 'gemini-1.0-pro'
    gemini_1_0_pro_vision = 'gemini-1.0-pro-vision'
    
    # Legacy Names
    gemini_pro = 'gemini-pro'
    gemini_pro_vision = 'gemini-pro-vision'
    
    # Gemma Models (Open Source)
    gemma_3n = 'gemma-3n'
    gemma_3 = 'gemma-3'
    gemma_2_27b_it = 'gemma-2-27b-it'
    gemma_2_9b_it = 'gemma-2-9b-it'
    gemma_2_2b_it = 'gemma-2-2b-it'
    shieldgemma_27b = 'shieldgemma-27b'
    shieldgemma_9b = 'shieldgemma-9b'
    shieldgemma_2b = 'shieldgemma-2b'
    paligemma_3b_mix_448 = 'paligemma-3b-mix-448'
    paligemma_3b_mix_896 = 'paligemma-3b-mix-896'
    codegemma_7b_it = 'codegemma-7b-it'
    codegemma_2b = 'codegemma-2b'
    txgemma = 'txgemma'
    medgemma = 'medgemma'
    medsiglip = 'medsiglip'
    t5gemma = 't5gemma'
    
    # Embeddings
    gemini_embedding_001 = 'gemini-embedding-001'
    text_embedding_004 = 'text-embedding-004'
    text_multilingual_embedding_002 = 'text-multilingual-embedding-002'
    
    # Imagen (Image Generation)
    imagen_4_generation = 'imagen-4-generation'
    imagen_4_fast_generation = 'imagen-4-fast-generation'
    imagen_4_ultra_generation = 'imagen-4-ultra-generation'
    imagen_4_upscaling = 'imagen-4-upscaling'
    imagen_3_generation = 'imagen-3-generation'
    imagen_3_editing_customization = 'imagen-3-editing-customization'
    imagen_3_fast_generation = 'imagen-3-fast-generation'
    imagen_1_generation = 'imagen-1-generation'
    imagen_1_editing = 'imagen-1-editing'
    imagen_1_upscaling = 'imagen-1-upscaling'
    imagen_visual_captioning = 'imagen-visual-captioning'
    imagen_visual_qa = 'imagen-visual-qa'
    
    # Veo (Video Generation)
    veo_3_1_fast_video_audio_4k = 'veo-3.1-fast-video-audio-4k'
    veo_3_1_fast_video_720p_1080p = 'veo-3.1-fast-video-720p-1080p'
    veo_3_1_fast_video_4k = 'veo-3.1-fast-video-4k'
    veo_3_video_audio = 'veo-3-video-audio'
    veo_3_video = 'veo-3-video'
    veo_2 = 'veo-2'
    veo_2_advanced_controls = 'veo-2-advanced-controls'
    veo_3_preview = 'veo-3-preview'
    veo_3_fast_preview = 'veo-3-fast-preview'
    
    # Preview Models
    virtual_try_on = 'virtual-try-on'


# ============================================================================
# AWS BEDROCK MODELS
# ============================================================================

class aws_bedrock:
    """AWS Bedrock model constants"""
    
    # AI21 Labs Models
    jamba_1_5_large = 'ai21.jamba-1-5-large-v1:0'
    jamba_1_5_mini = 'ai21.jamba-1-5-mini-v1:0'
    jamba_instruct = 'ai21.jamba-instruct-v1:0'
    j2_mid = 'ai21.j2-mid-v1'
    j2_ultra = 'ai21.j2-ultra-v1'
    
    # Amazon Nova Models
    nova_pro = 'amazon.nova-pro-v1:0'
    nova_lite = 'amazon.nova-lite-v1:0'
    nova_micro = 'amazon.nova-micro-v1:0'
    nova_premier = 'amazon.nova-premier-v1:0'
    nova_sonic = 'amazon.nova-sonic-v1:0'
    nova_canvas = 'amazon.nova-canvas-v1:0'
    nova_reel = 'amazon.nova-reel-v1:0'
    
    # Anthropic Claude on Bedrock
    claude_sonnet_4_5 = 'anthropic.claude-sonnet-4-5-v1:0'
    claude_haiku_4_5 = 'anthropic.claude-haiku-4-5-v1:0'
    claude_opus_4_1_20250805 = 'anthropic.claude-opus-4-1-20250805-v1:0'
    claude_opus_4_20250514 = 'anthropic.claude-opus-4-20250514-v1:0'
    claude_sonnet_4_20250514 = 'anthropic.claude-sonnet-4-20250514-v1:0'
    claude_3_7_sonnet_20250219 = 'anthropic.claude-3-7-sonnet-20250219-v1:0'
    claude_3_5_sonnet_20241022 = 'anthropic.claude-3-5-sonnet-20241022-v1:0'
    claude_3_5_sonnet_20240620 = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
    claude_3_5_haiku_20241022 = 'anthropic.claude-3-5-haiku-20241022-v1:0'
    claude_3_5_sonnet_extended_access = 'anthropic.claude-3-5-sonnet-extended-access-v1:0'
    claude_3_5_sonnet_v2_extended_access = 'anthropic.claude-3-5-sonnet-v2-extended-access-v1:0'
    claude_3_haiku_20240307 = 'anthropic.claude-3-haiku-20240307-v1:0'
    claude_3_opus_20240229 = 'anthropic.claude-3-opus-20240229-v1:0'
    claude_3_sonnet_20240229 = 'anthropic.claude-3-sonnet-20240229-v1:0'
    claude_2_1 = 'anthropic.claude-2-1-v1:0'
    claude_instant_1_2 = 'anthropic.claude-instant-1-2-v1:0'
    
    # Global Inference Profiles
    global_claude_3_5_haiku = 'global.anthropic.claude-haiku-4-5-20251001-v1:0'
    
    # Inference Profiles
    us_claude_3_5_haiku_20241022 = 'us.anthropic.claude-3-5-haiku-20241022-v1:0'
    
    # Meta Llama Models on Bedrock
    llama_3_3_70b_instruct = 'meta.llama3-3-70b-instruct-v1:0'
    llama_3_2_1b_instruct = 'meta.llama3-2-1b-instruct-v1:0'
    llama_3_2_3b_instruct = 'meta.llama3-2-3b-instruct-v1:0'
    llama_3_2_11b_vision_instruct = 'meta.llama3-2-11b-vision-instruct-v1:0'
    llama_3_2_90b_vision_instruct = 'meta.llama3-2-90b-vision-instruct-v1:0'
    llama_3_1_8b_instruct = 'meta.llama3-1-8b-instruct-v1:0'
    llama_3_1_70b_instruct = 'meta.llama3-1-70b-instruct-v1:0'
    llama_3_1_405b_instruct = 'meta.llama3-1-405b-instruct-v1:0'
    
    # OpenAI Models on Bedrock
    gpt_oss_120b = 'openai.gpt-oss-120b-v1:0'
    
    # DeepSeek Models on Bedrock
    deepseek_r1 = 'deepseek.r1-v1:0'
    deepseek_v3_1 = 'deepseek.v3-1-v1:0'
    
    # Mistral Models on Bedrock
    mistral_large_3 = 'mistral.mistral-large-3-v1:0'
    mistral_large_2407 = 'mistral.mistral-large-2407-v1:0'
    mistral_7b_instruct = 'mistral.mistral-7b-instruct-v0:2'
    mixtral_8x7b_instruct = 'mistral.mixtral-8x7b-instruct-v0:1'
    mistral_large_2402 = 'mistral.mistral-large-2402-v1:0'
    mistral_small_2402 = 'mistral.mistral-small-2402-v1:0'
    
    # Cohere Models on Bedrock
    command_r_plus = 'cohere.command-r-plus-v1:0'
    command_r = 'cohere.command-r-v1:0'
    embed_english_v3 = 'cohere.embed-english-v3'
    embed_multilingual_v3 = 'cohere.embed-multilingual-v3'
    embed_4 = 'cohere.embed-4-v1:0'
    rerank_3_5 = 'cohere.rerank-3-5-v1:0'
    
    # Stability AI Models
    stable_diffusion_3_5_large = 'stability.stable-diffusion-3-5-large-v1:0'
    stable_diffusion_xl = 'stability.stable-diffusion-xl-v1:0'
    stable_image_style_transfer = 'stability.stable-image-style-transfer-v1:0'
    stable_image_conservative_upscale = 'stability.stable-image-conservative-upscale-v1:0'
    stable_image_creative_upscale = 'stability.stable-image-creative-upscale-v1:0'
    stable_image_fast_upscale = 'stability.stable-image-fast-upscale-v1:0'
    stable_image_style_guide = 'stability.stable-image-style-guide-v1:0'
    stable_image_search_and_replace = 'stability.stable-image-search-and-replace-v1:0'
    stable_image_inpaint = 'stability.stable-image-inpaint-v1:0'
    stable_image_search_and_recolor = 'stability.stable-image-search-and-recolor-v1:0'
    stable_image_outpaint = 'stability.stable-image-outpaint-v1:0'
    
    # TwelveLabs Models
    pegasus_1_2 = 'twelvelabs.pegasus-1-2-v1:0'
    marengo_embed_2_7 = 'twelvelabs.marengo-embed-2-7-v1:0'


# ============================================================================
# XAI (GROK) MODELS
# ============================================================================

class xai:
    """xAI model constants"""
    
    # Grok 4.1 Fast Series (Latest)
    grok_4_1_fast_reasoning = 'grok-4-1-fast-reasoning'
    grok_4_1_fast_non_reasoning = 'grok-4-1-fast-non-reasoning'
    
    # Grok 4 Fast Series
    grok_4_fast_reasoning = 'grok-4-fast-reasoning'
    grok_4_fast_non_reasoning = 'grok-4-fast-non-reasoning'
    grok_code_fast_1 = 'grok-code-fast-1'
    
    # Grok 4 Series
    grok_4_0709 = 'grok-4-0709'
    grok_4 = 'grok-4'
    grok_4_latest = 'grok-4-latest'
    
    # Grok 3 Series
    grok_3 = 'grok-3'
    grok_3_mini = 'grok-3-mini'
    
    # Grok 2 Vision Series
    grok_2_vision_1212 = 'grok-2-vision-1212'
    grok_2_vision_1212_us_east_1 = 'grok-2-vision-1212-us-east-1'
    grok_2_vision_1212_eu_west_1 = 'grok-2-vision-1212-eu-west-1'
    
    # Grok 2 Image Generation
    grok_2_image_1212 = 'grok-2-image-1212'
    grok_2_image = 'grok-2-image'
    grok_2_image_latest = 'grok-2-image-latest'


# ============================================================================
# DEEPSEEK MODELS
# ============================================================================

class deepseek:
    """DeepSeek model constants"""
    
    # DeepSeek Standard Models
    deepseek_chat = 'deepseek-chat'
    deepseek_chat_cached = 'deepseek-chat-cached'
    deepseek_reasoner = 'deepseek-reasoner'
    deepseek_reasoner_cached = 'deepseek-reasoner-cached'
    
    # DeepSeek Off-Peak Models (UTC 16:30-00:30)
    deepseek_chat_offpeak = 'deepseek-chat-offpeak'
    deepseek_chat_cached_offpeak = 'deepseek-chat-cached-offpeak'
    deepseek_reasoner_offpeak = 'deepseek-reasoner-offpeak'
    deepseek_reasoner_cached_offpeak = 'deepseek-reasoner-cached-offpeak'

# ============================================================================
# MISTRAL MODELS
# ============================================================================

class mistral:
    """Mistral AI model constants"""
    
    mistral_large_latest = 'mistral-large-latest'
    mistral_small_latest = 'mistral-small-latest'
    codestral_latest = 'codestral-latest'
    ministral_8b_latest = 'ministral-8b-latest'
    ministral_3b_latest = 'ministral-3b-latest'
    pixtral_large_latest = 'pixtral-large-latest'
    pixtral_12b = 'pixtral-12b-2409'


# ============================================================================
# COHERE MODELS
# ============================================================================

class mistral:
    """Mistral AI model constants"""
    
    # Premier Models
    mistral_medium_2508 = 'mistral-medium-2508'
    mistral_medium_latest = 'mistral-medium-latest'
    magistral_medium_2509 = 'magistral-medium-2509'
    magistral_medium_latest = 'magistral-medium-latest'
    magistral_medium_2507 = 'magistral-medium-2507'
    
    # Large Models
    mistral_large_2411 = 'mistral-large-2411'
    mistral_large_latest = 'mistral-large-latest'
    pixtral_large_2411 = 'pixtral-large-2411'
    pixtral_large_latest = 'pixtral-large-latest'
    
    # Small Models
    magistral_small_2509 = 'magistral-small-2509'
    magistral_small_latest = 'magistral-small-latest'
    magistral_small_2507 = 'magistral-small-2507'
    voxtral_small_2507 = 'voxtral-small-2507'
    voxtral_small_latest = 'voxtral-small-latest'
    voxtral_mini_2507 = 'voxtral-mini-2507'
    voxtral_mini_latest = 'voxtral-mini-latest'
    mistral_small_2506 = 'mistral-small-2506'
    mistral_small_2503 = 'mistral-small-2503'
    mistral_small_2409 = 'mistral-small-2409'
    mistral_small_2407 = 'mistral-small-2407'
    
    # Code Models
    codestral_2508 = 'codestral-2508'
    codestral_latest = 'codestral-latest'
    devstral_medium_2507 = 'devstral-medium-2507'
    devstral_medium_latest = 'devstral-medium-latest'
    devstral_small_latest = 'devstral-small-latest'
    devstral_small_2505 = 'devstral-small-2505'
    
    # Vision Models
    pixtral_12b_2409 = 'pixtral-12b-2409'
    pixtral_12b = 'pixtral-12b'
    
    # OCR Models
    mistral_ocr_2505 = 'mistral-ocr-2505'
    mistral_ocr_latest = 'mistral-ocr-latest'
    
    # Edge Models
    ministral_3b = 'ministral-3b'
    ministral_8b = 'ministral-8b'
    
    # Open Source Models
    open_mistral_nemo_2407 = 'open-mistral-nemo-2407'
    open_mistral_nemo = 'open-mistral-nemo'
    mistral_nemo = 'mistral-nemo'
    open_mistral_7b = 'open-mistral-7b'
    open_mixtral_8x7b = 'open-mixtral-8x7b'
    open_mixtral_8x22b = 'open-mixtral-8x22b'
    
    # Embedding Models
    mistral_embed = 'mistral-embed'
    codestral_embed_2505 = 'codestral-embed-2505'


# ============================================================================
# COHERE MODELS
# ============================================================================

class cohere:
    """Cohere model constants"""
    
    # Command A Series (Latest)
    command_a_03_2025 = 'command-a-03-2025'
    command_a_reasoning_08_2025 = 'command-a-reasoning-08-2025'
    command_a_vision_07_2025 = 'command-a-vision-07-2025'
    
    # Command R+ Series
    command_r_plus_04_2024 = 'command-r-plus-04-2024'
    
    # Command R Series
    command_r_08_2024 = 'command-r-08-2024'
    command_r_03_2024 = 'command-r-03-2024'
    command_r7b_12_2024 = 'command-r7b-12-2024'
    
    # Command Series (Legacy)
    command = 'command'
    command_nightly = 'command-nightly'
    command_light = 'command-light'
    command_light_nightly = 'command-light-nightly'
    
    # Embed Models
    embed_v4_0 = 'embed-v4.0'
    embed_english_v3_0 = 'embed-english-v3.0'
    embed_english_light_v3_0 = 'embed-english-light-v3.0'
    embed_multilingual_v3_0 = 'embed-multilingual-v3.0'
    embed_multilingual_light_v3_0 = 'embed-multilingual-light-v3.0'
    
    # Rerank Models
    rerank_v3_5 = 'rerank-v3.5'
    rerank_english_v3_0 = 'rerank-english-v3.0'
    rerank_multilingual_v3_0 = 'rerank-multilingual-v3.0'
    
    # Aya Models
    c4ai_aya_expanse_8b = 'c4ai-aya-expanse-8b'
    c4ai_aya_expanse_32b = 'c4ai-aya-expanse-32b'
    c4ai_aya_vision_8b = 'c4ai-aya-vision-8b'
    c4ai_aya_vision_32b = 'c4ai-aya-vision-32b'
    
    # AWS Bedrock Models
    cohere_command_r_plus_v1_0 = 'cohere.command-r-plus-v1:0'
    cohere_command_r_v1_0 = 'cohere.command-r-v1:0'
    cohere_embed_english_v3 = 'cohere.embed-english-v3'
    cohere_embed_multilingual_v3 = 'cohere.embed-multilingual-v3'


# ============================================================================
# META MODELS
# ============================================================================

class meta:
    """Meta model constants"""
    
    # Llama 4 Series (Latest)
    llama_4_scout = 'llama-4-scout'
    llama_4_maverick = 'llama-4-maverick'
    llama_4_behemoth_preview = 'llama-4-behemoth-preview'
    
    # Llama 3.3 Series
    llama_3_3_70b_instruct = 'llama-3.3-70b-instruct'
    
    # Llama 3.2 Series
    llama_3_2_1b_instruct = 'llama-3.2-1b-instruct'
    llama_3_2_3b_instruct = 'llama-3.2-3b-instruct'
    llama_3_2_11b_vision_instruct = 'llama-3.2-11b-vision-instruct'
    llama_3_2_90b_vision_instruct = 'llama-3.2-90b-vision-instruct'
    
    # Llama 3.1 Series
    llama_3_1_8b_instruct = 'llama-3.1-8b-instruct'
    llama_3_1_70b_instruct = 'llama-3.1-70b-instruct'
    llama_3_1_405b_instruct = 'llama-3.1-405b-instruct'
    
    # Llama 3 Series (Legacy)
    llama_3_70b_instruct = 'llama-3-70b-instruct'
    llama_3_8b_instruct = 'llama-3-8b-instruct'


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

# Collect all model values
_ALL_MODEL_VALUES = set()

for cls in [openai, anthropic, google, aws_bedrock, xai, deepseek, mistral, cohere, meta]:
    for attr in dir(cls):
        if not attr.startswith('_'):
            value = getattr(cls, attr)
            if isinstance(value, str):
                _ALL_MODEL_VALUES.add(value)


def is_model_constant(value: str) -> bool:
    """
    Check if a string is a known model constant value.
    
    Args:
        value: The model string to check
        
    Returns:
        True if the value matches a known model constant
    """
    return value in _ALL_MODEL_VALUES


def get_all_model_constants() -> list:
    """
    Get all available model constants as a list.
    
    Returns:
        List of all model constant values
    """
    return list(_ALL_MODEL_VALUES)


def get_provider_from_model(model_id: str) -> str:
    """
    Get provider name from model ID.
    
    Args:
        model_id: The model ID to check
        
    Returns:
        Provider name or 'unknown'
    """
    # Check each class's attributes
    for attr in dir(openai):
        if not attr.startswith('_') and getattr(openai, attr, None) == model_id:
            return 'OpenAI'
    
    for attr in dir(anthropic):
        if not attr.startswith('_') and getattr(anthropic, attr, None) == model_id:
            return 'Anthropic'
    
    for attr in dir(google):
        if not attr.startswith('_') and getattr(google, attr, None) == model_id:
            return 'Google AI'
    
    for attr in dir(aws_bedrock):
        if not attr.startswith('_') and getattr(aws_bedrock, attr, None) == model_id:
            return 'AWS Bedrock'
    
    for attr in dir(xai):
        if not attr.startswith('_') and getattr(xai, attr, None) == model_id:
            return 'xAI'
    
    for attr in dir(deepseek):
        if not attr.startswith('_') and getattr(deepseek, attr, None) == model_id:
            return 'DeepSeek'
    
    for attr in dir(mistral):
        if not attr.startswith('_') and getattr(mistral, attr, None) == model_id:
            return 'Mistral AI'
    
    for attr in dir(cohere):
        if not attr.startswith('_') and getattr(cohere, attr, None) == model_id:
            return 'Cohere'
    
    for attr in dir(groq):
        if not attr.startswith('_') and getattr(groq, attr, None) == model_id:
            return 'Grok'
    
    for attr in dir(meta):
        if not attr.startswith('_') and getattr(meta, attr, None) == model_id:
            return 'Meta'
    
    return 'unknown'


__all__ = [
    'openai',
    'anthropic',
    'google',
    'aws_bedrock',
    'xai',
    'deepseek',
    'mistral',
    'cohere',
    'meta',
    'is_model_constant',
    'get_all_model_constants',
    'get_provider_from_model',
]

