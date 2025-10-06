import os
import asyncio
import json
import shutil
import httpx
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, ValidationError, model_validator
from typing import List, Literal, Union, Optional
from pathlib import Path  # <-- ADD THIS IMPORT FOR THE FIX
from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeVideoClip, 
                            concatenate_videoclips, TextClip)
from pexels_api import API
from gtts import gTTS
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
app = FastAPI()

# --- FIX: Define absolute path to the static directory for deployment ---
STATIC_DIR = Path(__file__).parent / "static"
# --------------------------------------------------------------------


# --- CONFIGURE ALL APIS ---
try:
    # OpenRouter (Primary)
    OPENROUTER_API_KEY = os.environ["OPENROUTER_API_KEY"] 
    OPENROUTER_API_BASE = os.environ.get("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1")
    PRIMARY_MODEL = "deepseek/deepseek-chat"
    
    # Gemini (Fallback)
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel('gemini-pro')

except KeyError as e:
    print(f"ERROR: Missing API Key in environment variables: {e}")
    exit()

# --- DATA MODELS ---
class GenerationRequest(BaseModel):
    idea: str
    platform: str
    tone: str
    creativity: float
    formality: float
    smart_emojis: bool
    auto_hashtag: bool
    contextual_suggestions: bool
    target_audience: str = ""

class InstagramContent(BaseModel):
    caption: str
    script: str

class XContent(BaseModel):
    thread: List[str]
    
class RefineRequest(GenerationRequest):
    original_content: Union[str, InstagramContent, XContent]
    refinement_instruction: str

    @model_validator(mode='before')
    @classmethod
    def check_original_content_type(cls, data):
        if isinstance(data, dict):
            original_content = data.get('original_content')
            platform = data.get('platform')
            if isinstance(original_content, dict):
                if platform == 'Instagram' and 'caption' in original_content and 'script' in original_content:
                    data['original_content'] = InstagramContent(**original_content)
                elif platform == 'X' and 'thread' in original_content:
                    data['original_content'] = XContent(**original_content)
        return data

class AnalysisScores(BaseModel):
    readability: int
    engagement_potential: int = Field(alias="engagement_potential")
    human_likeness: int = Field(alias="human_likeness")

class Version(BaseModel):
    content: Union[str, InstagramContent, XContent]
    analysis: AnalysisScores
    virality_score: Optional[int] = None
    justification: Optional[str] = None

class MultiVersionResponse(BaseModel):
    versions: List[Version]

class HumanizeRequest(BaseModel):
    text: str

class HumanizeResponse(BaseModel):
    humanized_text: str

class VideoRequest(BaseModel):
    script: str
    idea: str

Version.model_rebuild()
RefineRequest.model_rebuild()

# --- HELPER FUNCTION ---
def build_prompt(request: Union[GenerationRequest, RefineRequest]) -> str:
    if request.creativity <= 33: creativity_level = "safe"
    elif request.creativity <= 66: creativity_level = "balanced"
    else: creativity_level = "inventive"
        
    if request.formality <= 33: formality_level = "very casual"
    elif request.formality <= 66: formality_level = "neutral"
    else: formality_level = "very formal"

    platform_specific_instruction = ""
    if request.platform == "X":
        platform_specific_instruction = "- Critical: Ensure each tweet in the thread is under 280 characters."

    if request.platform == "Instagram": content_structure = '"content": {"caption": "Your generated caption.", "script": "A short video script."}'
    elif request.platform == "X": content_structure = '"content": {"thread": ["Tweet 1.", "Tweet 2."]}'
    else: content_structure = '"content": "Your full generated text post."'

    base_prompt = f"""
    You are an expert social media content creator. Generate content and analysis based on these specs:
    - Idea: "{request.idea}"
    - Platform: {request.platform}
    {'- Target Audience: ' + request.target_audience if request.target_audience else ''}
    {platform_specific_instruction}
    - Tone: "{request.tone}"
    - Formality: {formality_level}
    - Creativity: {creativity_level}
    {'- Add smart emojis.' if request.smart_emojis else ''}
    {'- Add relevant hashtags.' if request.auto_hashtag else ''}
    {'- Add a suggestion.' if request.contextual_suggestions else ''}

    Your entire response must be a single, valid JSON object with "content" and "analysis" keys.
    The "content" key's value must follow this structure: {{{content_structure}}}.
    
    The "analysis" key must contain a JSON object with three integer scores. CRITICAL: Generate scores on a human-like scale where 75 is average, 85 is good, and 95 is excellent. Do not give unusually low scores unless the content is extremely flawed. The keys must be exactly: "readability", "engagement_potential", and "human_likeness".
    
    Do not include any other text or markdown.
    """

    if isinstance(request, RefineRequest):
        original_content_json = json.dumps(request.original_content.dict() if isinstance(request.original_content, (InstagramContent, XContent)) else request.original_content)
        return f"""
        {base_prompt}

        You are now REFINING the following content based on a user's instruction.
        ---
        ORIGINAL CONTENT:
        {original_content_json}
        ---
        USER'S REFINEMENT INSTRUCTION: "{request.refinement_instruction}"
        ---
        Apply the instruction to the original content and provide the new, refined content and its new analysis in the required JSON format.
        """
    return base_prompt

# --- API ENDPOINTS ---
@app.post("/generate", response_model=MultiVersionResponse)
async def generate_versions(request: GenerationRequest):
    print(f"\n--- [START] AI Generation for {request.platform} ---")
    prompt = build_prompt(request)
    async def generate_single_version(client, version_num):
        full_content_str = None
        try:
            print(f"Ver {version_num}: Attempting Primary (DeepSeek)...")
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            payload = {"model": PRIMARY_MODEL, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "max_tokens": 2048}
            response = await client.post(f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            full_content_str = response.json()['choices'][0]['message']['content']
            print(f"Ver {version_num}: Primary (DeepSeek) Succeeded.")
        except Exception as e_deepseek:
            print(f"Ver {version_num}: Primary Failed. Falling back. Reason: {e_deepseek}")
            try:
                print(f"Ver {version_num}: Attempting Fallback (Gemini)...")
                response = await gemini_model.generate_content_async(contents=prompt)
                full_content_str = response.text
                print(f"Ver {version_num}: Fallback (Gemini) Succeeded.")
            except Exception as e_gemini:
                return {"content": f"Error: Both APIs failed. DeepSeek: {e_deepseek}, Gemini: {e_gemini}", "analysis": {"readability": 0, "engagement_potential": 0, "human_likeness": 0}}

        try:
            json_str_cleaned = full_content_str.strip().replace("```json", "").replace("```", "")
            data = json.loads(json_str_cleaned)
            content_payload = data['content']
            if request.platform not in ["Instagram", "X"]:
                if isinstance(content_payload, dict) and 'content' in content_payload and isinstance(content_payload.get('content'), str):
                    print("--> Backend Correction: Un-nesting a malformed content object from the AI.")
                    content_payload = content_payload['content']
            if request.platform == "Instagram":
                content_payload = InstagramContent(**content_payload)
            elif request.platform == "X":
                content_payload = XContent(**content_payload)
            return Version(content=content_payload, analysis=AnalysisScores(**data['analysis']))
        except (json.JSONDecodeError, ValidationError, Exception) as parse_e:
            return {"content": f"Error parsing response: {parse_e}\nRaw: {full_content_str}", "analysis": {"readability": 0, "engagement_potential": 0, "human_likeness": 0}}

    async with httpx.AsyncClient() as client:
        tasks = [generate_single_version(client, i + 1) for i in range(3)]
        versions_data = await asyncio.gather(*tasks)

    versions = [v for v in versions_data if isinstance(v, Version)]
    if not versions:
        error_details = [str(v.get('content', 'Unknown error')) for v in versions_data if not isinstance(v, Version)]
        raise HTTPException(status_code=500, detail=f"The AI failed to generate any valid content after 3 attempts. Please try rephrasing your idea or check the AI model status. Raw errors: {error_details}")

    if len(versions) > 0:
        try:
            print("\n--- [START] Performance Prediction Analysis ---")
            content_to_analyze = ""
            for i, version in enumerate(versions):
                content_text = ""
                if isinstance(version.content, str): content_text = version.content
                elif isinstance(version.content, InstagramContent): content_text = f"Caption: {version.content.caption}\nScript: {version.content.script}"
                elif isinstance(version.content, XContent): content_text = "\n".join(version.content.thread)
                content_to_analyze += f"--- VERSION {i+1} ---\n{content_text}\n\n"
            prediction_prompt = f"""You are a viral social media strategist. Analyze the following {len(versions)} content options for a {request.platform} post. For each, provide a "virality_score" (0-100) and a brief "justification". Your response must be ONLY a valid JSON list of objects. Example: [{{"version_index": 0, "virality_score": 88, "justification": "Strong hook."}}] \n\nContent to analyze:\n{content_to_analyze}"""
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            payload = {"model": PRIMARY_MODEL, "messages": [{"role": "user", "content": prediction_prompt}], "response_format": {"type": "json_object"}, "max_tokens": 1024}
            async with httpx.AsyncClient() as client:
                response = await client.post(f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
                response.raise_for_status()
                prediction_data = json.loads(response.json()['choices'][0]['message']['content'])
            for prediction in prediction_data:
                idx = prediction.get("version_index")
                if idx is not None and 0 <= idx < len(versions):
                    versions[idx].virality_score = prediction.get("virality_score")
                    versions[idx].justification = prediction.get("justification")
            print("--- [END] Performance Prediction Complete ---")
        except Exception as e:
            print(f"Performance prediction step failed: {e}")
    return {"versions": [v.dict() for v in versions]}

@app.post("/refine", response_model=Version)
async def refine_version(request: RefineRequest):
    print(f"\n--- [START] AI Refinement for {request.platform} ---")
    prompt = build_prompt(request)
    full_content_str = None
    try:
        print("Attempting Primary (DeepSeek)...")
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        payload = {"model": PRIMARY_MODEL, "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}, "max_tokens": 2048}
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            full_content_str = response.json()['choices'][0]['message']['content']
        print("Primary (DeepSeek) Succeeded.")
    except Exception as e_deepseek:
        print(f"Primary Failed. Falling back. Reason: {e_deepseek}")
        try:
            print("Attempting Fallback (Gemini)...")
            response = await gemini_model.generate_content_async(contents=prompt)
            full_content_str = response.text
            print("Fallback (Gemini) Succeeded.")
        except Exception as e_gemini:
            raise HTTPException(status_code=500, detail=f"Both APIs failed on refinement. DeepSeek: {e_deepseek}, Gemini: {e_gemini}")
    try:
        json_str_cleaned = full_content_str.strip().replace("```json", "").replace("```", "")
        data = json.loads(json_str_cleaned)
        content_payload = data['content']
        if request.platform == "Instagram": content_payload = InstagramContent(**data['content'])
        elif request.platform == "X": content_payload = XContent(**data['content'])
        return Version(content=content_payload, analysis=AnalysisScores(**data['analysis']))
    except Exception as parse_e:
        raise HTTPException(status_code=500, detail=f"Error parsing AI response. Raw: {full_content_str}")

@app.post("/humanize", response_model=HumanizeResponse)
async def humanize_text(request: HumanizeRequest):
    print("\n--- [START] Humanizing Text ---")
    humanize_prompt = f"""
    You are an expert editor. Your task is to rewrite the following AI-generated text to make it sound authentically human and evade AI detection.
    Focus on increasing "perplexity" and "burstiness".
    1.  **Increase Perplexity:** Rewrite sentences to be less predictable. Use a richer vocabulary and occasionally choose a less common but still correct synonym. Introduce idioms or metaphors.
    2.  **Increase Burstiness:** Vary the sentence structure dramatically. Mix very short, punchy sentences with much longer, more complex sentences to create a dynamic reading rhythm.
    3.  **Add a Human Touch:** Incorporate subtle colloquialisms, rhetorical questions, or asides to break the flow. Frame the text as a personal thought or observation.
    Preserve the core meaning. Only return the rewritten text. Do not include any introductory phrases like "Here is the rewritten text:", titles, or markdown.
    TEXT TO REWRITE:
    ---
    {request.text}
    ---
    """
    humanized_text = None
    try:
        print("Attempting to humanize with Primary API (DeepSeek)...")
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            payload = {"model": PRIMARY_MODEL, "messages": [{"role": "user", "content": humanize_prompt}], "max_tokens": 2048}
            response = await client.post(f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            humanized_text = response.json()['choices'][0]['message']['content']
            print("Primary API (DeepSeek) Succeeded.")
    except Exception as e:
        print(f"Primary API (DeepSeek) Failed. Reason: {e}")
        print("Attempting to humanize with Fallback API (Gemini)...")
        try:
            response = await gemini_model.generate_content_async(humanize_prompt)
            humanized_text = response.text
            print("Fallback API (Gemini) Succeeded.")
        except Exception as fallback_e:
            print(f"Fallback API also failed. Reason: {fallback_e}")
            raise HTTPException(status_code=500, detail="Both APIs failed to humanize the text.")
    return HumanizeResponse(humanized_text=humanized_text.strip())


# --- VIDEO GENERATION ENDPOINT ---
@app.post("/generate-video")
async def generate_video(request: VideoRequest):
    print("\n--- [START] Video Generation ---")
    
    video_dir = "static/videos"
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
        
    unique_id = httpx.get("https://www.uuidgenerator.net/api/version4").text
    audio_path = os.path.join(video_dir, f"{unique_id}_audio.mp3")
    video_path = os.path.join(video_dir, f"{unique_id}_final.mp4")
    temp_video_files = []
    final_clips = []
    audio_clip = None

    try:
        print("Step 1: Generating audio from script...")
        tts = gTTS(text=request.script, lang='en', slow=False)
        tts.save(audio_path)
        audio_clip = AudioFileClip(audio_path)
        audio_duration = audio_clip.duration
        print(f"Audio duration: {audio_duration:.2f} seconds")

        print("Step 2: Searching for stock videos...")
        PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")
        if not PEXELS_API_KEY:
            raise HTTPException(status_code=500, detail="PEXELS_API_KEY not found in environment variables.")
            
        api = API(PEXELS_API_KEY)
        
        api.search(request.idea, media_type='videos', page=1, results_per_page=5)
        videos = api.get_entries()
        
        if not videos:
            raise HTTPException(status_code=404, detail=f"Could not find any stock videos for the idea: '{request.idea}'")
        
        print(f"Found {len(videos)} potential videos.")

        print("Step 3: Downloading and assembling video clips...")
        total_duration = 0
        for video in videos:
            if total_duration >= audio_duration:
                break
            
            video_file = next((vf for vf in sorted(video.video_files, key=lambda x: x.height or 0, reverse=True) if vf.height and 720 <= vf.height <= 1920), None)
            
            if video_file:
                try:
                    temp_path = os.path.join(video_dir, f"temp_{video.id}.mp4")
                    async with httpx.AsyncClient() as client:
                        async with client.stream("GET", video_file.link, follow_redirects=True, timeout=60) as response:
                            response.raise_for_status()
                            with open(temp_path, "wb") as f:
                                async for chunk in response.aiter_bytes():
                                    f.write(chunk)
                    
                    temp_video_files.append(temp_path)

                    clip = VideoFileClip(temp_path).set_fps(24)
                    clip = clip.resize(height=1920)
                    clip = clip.crop(x_center=clip.w/2, width=1080)

                    final_clips.append(clip)
                    total_duration += clip.duration
                except Exception as e:
                    print(f"Warning: Could not process video {video.id}. Reason: {e}")

        if not final_clips:
            raise HTTPException(status_code=500, detail="Failed to download or process any video clips.")

        final_video_clip = concatenate_videoclips(final_clips).subclip(0, audio_duration)
        final_video_clip = final_video_clip.set_audio(audio_clip)

        print("Step 4: Exporting final video...")
        final_video_clip.write_videofile(video_path, codec="libx264", audio_codec="aac", threads=4)
        
        print("--- [SUCCESS] Video Generation Complete ---")
        return {"video_url": f"/{video_path}"}

    except Exception as e:
        print(f"--- [ERROR] Video Generation Failed ---")
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        print("Cleaning up temporary files...")
        if audio_clip: audio_clip.close()
        for clip in final_clips: clip.close()
        if 'final_video_clip' in locals() and final_video_clip: final_video_clip.close()
        
        for f in [audio_path] + temp_video_files:
             if f and os.path.exists(f):
                try: os.remove(f)
                except Exception as e: print(f"Error cleaning up file {f}: {e}")

# --- FILE SERVING (FIXED FOR DEPLOYMENT) ---
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
@app.get("/")
async def read_index():
    return FileResponse(STATIC_DIR / "index.html")

