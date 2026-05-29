import os
import json
import asyncio
import re

# Use the new google-genai SDK (replaces deprecated google-generativeai)
from google import genai
from google.genai import types
from google.genai.errors import ClientError

# Read environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model fallback chain: try best available model, fall back if quota exceeded
GEMINI_MODEL_CHAIN = [
    os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash-lite",
]


class GeminiService:
    @staticmethod
    async def generate_search_query(text: str) -> str:
        """
        Uses a fast, low-temperature Gemini call to extract a 3-6 word search query
        representing the core factual claim of the input article.
        """
        api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        if not api_key:
            return " ".join(text.split()[:8])  # Fallback to first 8 words
            
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are a search query generator. Extract the single most important factual claim "
            "from the text and convert it into a concise 3 to 6 word search query suitable for Google News. "
            "Focus only on proper nouns, key events, and entities. Do not include opinion words, "
            "introductory phrases (like 'according to', 'breaking', 'shocking'), or punctuation. "
            "Return ONLY the plain text search query."
        )
        
        model_name = GEMINI_MODEL_CHAIN[0]
        try:
            def _call_api():
                return client.models.generate_content(
                    model=model_name,
                    contents=f"Extract search query from this text:\n\n{text[:1200]}",
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        max_output_tokens=20,
                    ),
                )
            loop = asyncio.get_running_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, _call_api),
                timeout=4.0,
            )
            query = response.text.strip().strip('"\'')
            query = re.sub(r'[^a-zA-Z0-9\s-]', '', query)
            return query
        except Exception as e:
            print(f"[Gemini Query Gen Warning] Failed to generate search query: {e}")
            # Fallback to smart heuristic: first sentence, up to 8 words
            first_sentence = text.split('.')[0]
            words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', first_sentence).split() if len(w) > 1]
            return " ".join(words[:8])

    @staticmethod
    async def analyze_article(
        text: str,
        search_results: list = None,
        feedback_samples: list = None,
        retries: int = 2,
        timeout: float = 30.0,
    ) -> dict:
        """
        Asynchronously analyzes an article using the Gemini API with structured JSON output,
        live search grounding context, dynamic user-corrected feedback training data,
        timeout handling, retries, and automatic model fallback on quota errors.
        """
        api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

        # Initialize the new google-genai client
        client = genai.Client(api_key=api_key)

        # System instruction for the model
        system_instruction = (
            "You are a professional misinformation detection engine. Analyze the article for fake "
            "news indicators including emotional manipulation, propaganda, clickbait, missing "
            "evidence, political bias, misleading claims, logical inconsistencies, fear tactics, "
            "and suspicious language patterns. "
            "CRITICAL RULE: Factual, well-known statements (e.g. 'there are 7 continents', "
            "'water is H2O', 'the earth orbits the sun') are ALWAYS 'Real'. "
            "Only return valid JSON matching the requested schema."
        )

        # Formulate live search context grounding
        search_context = ""
        if search_results:
            search_context = "=== LIVE SEARCH FACT-CHECKING GROUNDING ===\n"
            search_context += (
                "We queried live search indexes to find news coverage and fact-checking "
                "statements for this claim. Use these search results to verify the facts:\n\n"
            )
            for idx, res in enumerate(search_results):
                search_context += f"Search Result {idx+1}:\n"
                search_context += f"- Title: {res.get('title', 'N/A')}\n"
                search_context += f"- Snippet: {res.get('snippet', 'N/A')}\n"
                search_context += f"- Source URL: {res.get('url', 'N/A')}\n\n"
            search_context += "========================================\n\n"
            search_context += "INSTRUCTIONS FOR SEARCH CROSS-REFERENCING:\n"
            search_context += (
                "1. If multiple reputable global news outlets (Reuters, AP, BBC, NYT, Bloomberg) "
                "cover this with matching facts, classify as 'Real'.\n"
            )
            search_context += (
                "2. If fact-checking sites or reputable search results state this is a hoax, "
                "rumor, or debunked claim, classify as 'Fake'.\n"
            )
            search_context += (
                "3. If search results are empty but the claim is a basic factual statement "
                "(geography, science, history), classify as 'Real'.\n\n"
            )
        else:
            search_context = "=== LIVE SEARCH FACT-CHECKING GROUNDING ===\n"
            search_context += (
                "Note: No search cross-references were found. Perform analysis based on "
                "linguistic style, bias, clickbait features, logical consistency, and "
                "factual plausibility. Well-known factual statements should be classified "
                "as 'Real' even without search grounding.\n"
                "========================================\n\n"
            )

        # Formulate dynamic active-learning feedback loop context
        feedback_context = ""
        if feedback_samples:
            active_corrections = feedback_samples[-3:]
            feedback_context = "=== DYNAMIC USER-CORRECTED CALIBRATION ===\n"
            feedback_context += (
                "The user has actively corrected predictions on these items. "
                "Treat as high-priority calibration:\n\n"
            )
            for idx, sample in enumerate(active_corrections):
                lbl_name = "Fake" if sample.get("label") == 1 else "Real"
                snippet_text = sample.get("text", "")
                short_text = (
                    snippet_text if len(snippet_text) <= 300 else snippet_text[:300] + "..."
                )
                feedback_context += f"User-Corrected Case {idx+1}:\n"
                feedback_context += f'- Article Text: "{short_text}"\n'
                feedback_context += f"- Correct Prediction: {lbl_name}\n\n"
            feedback_context += "========================================\n\n"

        prompt = (
            "You are a professional misinformation detection and fact-checking engine.\n"
            "Analyze the article text systematically for fake news indicators.\n\n"
            "CRITICAL GUIDELINES:\n"
            "1. Basic factual statements (e.g. 'there are 7 continents', 'the sun is a star', "
            "'water boils at 100C') are ALWAYS 'Real' — do NOT flag these as fake.\n"
            "2. Look for clickbait terms, excessive capitalization, dramatic punctuation.\n"
            "3. Evaluate emotional bias: loaded adjectives, fear-mongering, one-sided spin.\n"
            "4. Assess logical soundness: inconsistencies, extraordinary claims, conspiracies.\n"
            "5. Verify factual grounding: lack of citations, institutional coverage.\n\n"
            "--- EXAMPLE 1 (FAKE NEWS) ---\n"
            'Article: "SHOCKING! Drinking lemon water cures stage-4 cancer! '
            'The medical industry is hiding the truth! SHARE before it gets banned!"\n'
            "Output: "
            '{"prediction":"Fake","confidence":98,"bias_detected":true,"clickbait_score":95,'
            '"emotional_tone":"Sensational","risk_factors":["Misleading claims","Sensationalist language",'
            '"Missing evidence"],"explanation":"Makes extraordinary medical claims without clinical evidence."}\n\n'
            "--- EXAMPLE 2 (REAL NEWS) ---\n"
            'Article: "The Federal Reserve kept benchmark interest rates steady, '
            'citing moderate inflation. Economists expect rates to remain flat."\n'
            "Output: "
            '{"prediction":"Real","confidence":95,"bias_detected":false,"clickbait_score":5,'
            '"emotional_tone":"Neutral","risk_factors":[],"explanation":"Uses neutral language to describe '
            'real policy actions. No sensationalism or extraordinary claims."}\n\n'
            "--- EXAMPLE 3 (BASIC FACT - REAL) ---\n"
            'Article: "there are 7 continents in the planet earth"\n'
            "Output: "
            '{"prediction":"Real","confidence":99,"bias_detected":false,"clickbait_score":0,'
            '"emotional_tone":"Neutral","risk_factors":[],"explanation":"This is a well-established '
            'geographical fact. Earth has 7 continents: Africa, Antarctica, Asia, Australia/Oceania, '
            'Europe, North America, and South America."}\n\n'
            "--- EXAMPLE 4 (CONSPIRACY - FAKE) ---\n"
            'Article: "LEAKED: Military bunker confirms humanoid androids replaced all mayors! '
            'Space invasion scheduled for Tuesday!"\n'
            "Output: "
            '{"prediction":"Fake","confidence":99,"bias_detected":true,"clickbait_score":90,'
            '"emotional_tone":"Fear","risk_factors":["Conspiracy theory","Logically impossible claims"],'
            '"explanation":"Describes impossible scenarios with no verifiable sources."}\n\n'
            f"{search_context}"
            f"{feedback_context}"
            "Now analyze the following article and return ONLY valid JSON matching this EXACT schema:\n"
            "{\n"
            '  "prediction": "Fake" | "Real",\n'
            '  "confidence": <integer 50-100>,\n'
            '  "bias_detected": <boolean>,\n'
            '  "clickbait_score": <integer 0-100>,\n'
            '  "emotional_tone": <string>,\n'
            '  "risk_factors": [<array of strings>],\n'
            '  "explanation": <string>\n'
            "}\n\n"
            f'Article text to analyze:\n"""\n{text}\n"""'
        )

        last_error = None

        # Try each model in the fallback chain
        for model_name in GEMINI_MODEL_CHAIN:
            for attempt in range(retries):
                try:

                    def _call_api(mn=model_name):
                        return client.models.generate_content(
                            model=mn,
                            contents=prompt,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction,
                                response_mime_type="application/json",
                                temperature=0.1,
                            ),
                        )

                    loop = asyncio.get_running_loop()
                    response = await asyncio.wait_for(
                        loop.run_in_executor(None, _call_api),
                        timeout=timeout + 2.0,
                    )

                    content = response.text.strip()
                    # Handle markdown-wrapped JSON from the model
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                        content = content.strip()

                    data = json.loads(content)

                    # Sanitize and validate fields
                    pred_raw = str(data.get("prediction", "Fake")).strip().capitalize()
                    prediction = (
                        "Fake"
                        if "Fake" in pred_raw or "Misinformation" in pred_raw
                        else "Real"
                    )

                    confidence = data.get("confidence", 75)
                    try:
                        confidence = max(50, min(100, int(confidence)))
                    except (ValueError, TypeError):
                        confidence = 75

                    bias_detected = bool(data.get("bias_detected", False))

                    clickbait_score = data.get("clickbait_score", 0)
                    try:
                        clickbait_score = max(0, min(100, int(clickbait_score)))
                    except (ValueError, TypeError):
                        clickbait_score = 0

                    emotional_tone = str(data.get("emotional_tone", "Neutral"))
                    risk_factors = list(data.get("risk_factors", []))
                    explanation = str(data.get("explanation", ""))

                    print(
                        f"[Gemini Service] Success with model={model_name}, "
                        f"prediction={prediction}, confidence={confidence}"
                    )

                    return {
                        "prediction": prediction,
                        "confidence": confidence,
                        "bias_detected": bias_detected,
                        "clickbait_score": clickbait_score,
                        "emotional_tone": emotional_tone,
                        "risk_factors": risk_factors,
                        "explanation": explanation,
                    }

                except asyncio.TimeoutError:
                    print(
                        f"[Gemini Service] Timeout on model={model_name} attempt {attempt+1}/{retries}"
                    )
                    last_error = TimeoutError("Gemini API request timed out.")
                    break  # Timeout → try next model

                except ClientError as e:
                    error_str = str(e)
                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        print(
                            f"[Gemini Service] Rate limit on model={model_name}. "
                            f"Trying next fallback model..."
                        )
                        last_error = e
                        break  # Quota exceeded → try next model in chain
                    else:
                        print(
                            f"[Gemini Service] API error on model={model_name} "
                            f"attempt {attempt+1}/{retries}: {e}"
                        )
                        last_error = e
                        if attempt < retries - 1:
                            await asyncio.sleep(1.5**attempt)

                except Exception as e:
                    print(
                        f"[Gemini Service] Error on model={model_name} "
                        f"attempt {attempt+1}/{retries}: {e}"
                    )
                    last_error = e
                    if attempt < retries - 1:
                        await asyncio.sleep(1.5**attempt)

        # All models exhausted
        raise last_error or RuntimeError("All Gemini models failed.")
