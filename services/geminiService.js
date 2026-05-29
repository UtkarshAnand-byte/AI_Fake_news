/**
 * Reusable Google Gemini AI Misinformation Analysis Service (Client Reference)
 * 
 * IMPORTANT FOR SECURITY:
 * To avoid exposing your `GEMINI_API_KEY` to the public frontend browser, 
 * this project is configured to run all production Gemini analysis securely 
 * in the Python FastAPI backend (`backend/services/gemini_service.py`).
 * 
 * If you decide to transition to a Node.js/Express server in the future,
 * this file provides a premium, fully implemented production-ready SDK reference.
 */

import { GoogleGenAI } from '@google/generative-ai';

/**
 * Asynchronously analyzes an article for misinformation indicators using Google Gemini AI.
 * 
 * @param {string} articleText - The raw article context to inspect.
 * @param {string} apiKey - The Google Gemini API key.
 * @param {object} options - Configuration overrides (model name, timeout, retries).
 * @returns {Promise<object>} Parsed structured JSON audit report.
 */
export async function analyzeArticleWithGemini(articleText, apiKey = process.env.GEMINI_API_KEY, options = {}) {
  const modelName = options.modelName || process.env.GEMINI_MODEL || 'gemini-2.5-flash';
  const retries = options.retries || 3;
  const timeoutMs = options.timeout || 8000;

  if (!apiKey) {
    throw new Error("GEMINI_API_KEY is not defined in the environment secrets.");
  }

  // Initialize official Gemini Generative AI client
  const ai = new GoogleGenAI({ apiKey });
  
  const systemInstruction = 
    "You are a professional misinformation detection AI. Analyze the article for fake news " +
    "indicators including emotional manipulation, propaganda, clickbait, missing evidence, " +
    "political bias, misleading claims, logical inconsistencies, fear tactics, and suspicious " +
    "language patterns. Return only valid JSON.";

  const prompt = `
    Analyze the following article text and return a structured JSON response.
    The JSON MUST exactly follow this schema:
    {
      "prediction": "Fake" | "Real",
      "confidence": <integer between 50 and 100>,
      "bias_detected": <boolean>,
      "clickbait_score": <integer between 0 and 100>,
      "emotional_tone": <string, e.g., "Fear", "Neutral", "Sensational">,
      "risk_factors": [<array of strings specifying key misinformation indicators found>],
      "explanation": <string summarizing the core analysis and justification>
    }

    Article text to analyze:
    """
    ${articleText}
    """
  `;

  let lastError = null;
  
  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      // Enforce response_mime_type for structured outputs
      const model = ai.getGenerativeModel({
        model: modelName,
        systemInstruction,
        generationConfig: {
          responseMimeType: 'application/json',
          temperature: 0.1,
        }
      });

      // Implement timeout protection using Promise.race
      const apiCall = model.generateContent({ contents: prompt });
      const timeoutCall = new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Gemini API request timed out")), timeoutMs)
      );

      const response = await Promise.race([apiCall, timeoutCall]);
      const jsonText = response.text().trim();
      const parsedData = JSON.parse(jsonText);

      // Verify and validate schema response before returning
      return {
        prediction: parsedData.prediction === 'Fake' || parsedData.prediction === 'Misinformation' ? 'Fake' : 'Real',
        confidence: Math.max(50, Math.min(100, parseInt(parsedData.confidence) || 75)),
        bias_detected: Boolean(parsedData.bias_detected),
        clickbait_score: Math.max(0, Math.min(100, parseInt(parsedData.clickbait_score) || 0)),
        emotional_tone: String(parsedData.emotional_tone || 'Neutral'),
        risk_factors: Array.isArray(parsedData.risk_factors) ? parsedData.risk_factors : [],
        explanation: String(parsedData.explanation || '')
      };

    } catch (error) {
      console.warn(`[Gemini Service JS Reference] Attempt ${attempt}/${retries} failed: ${error.message}`);
      lastError = error;
      
      // Exponential backoff
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, Math.pow(1.5, attempt) * 1000));
      }
    }
  }

  throw lastError;
}
