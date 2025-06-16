// Enhanced src/services/api.js - Advanced multilingual support

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 90000, // Increased timeout for multilingual processing
});

// Request interceptor for logging
api.interceptors.request.use((config) => {
  console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error(`❌ API Error: ${error.message}`);
    
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || error.message;
      throw new Error(`API Error (${error.response.status}): ${message}`);
    } else if (error.request) {
      // Network error
      throw new Error('Network Error: Unable to connect to the API server. Make sure the backend is running on http://localhost:8000');
    } else {
      throw new Error(`Request Error: ${error.message}`);
    }
  }
);

/**
 * Get supported languages with enhanced info
 */
export const getSupportedLanguages = async () => {
  try {
    const response = await api.get('/api/languages');
    return response.data;
  } catch (error) {
    console.error('Failed to get supported languages:', error);
    // Fallback languages
    return {
      languages: [
        { code: 'en', name: 'English', native_name: 'English', flag: '🇺🇸', display: '🇺🇸 English' },
        { code: 'es', name: 'Spanish', native_name: 'Español', flag: '🇪🇸', display: '🇪🇸 Español' },
        { code: 'fr', name: 'French', native_name: 'Français', flag: '🇫🇷', display: '🇫🇷 Français' },
        { code: 'de', name: 'German', native_name: 'Deutsch', flag: '🇩🇪', display: '🇩🇪 Deutsch' },
        { code: 'it', name: 'Italian', native_name: 'Italiano', flag: '🇮🇹', display: '🇮🇹 Italiano' },
        { code: 'ja', name: 'Japanese', native_name: '日本語', flag: '🇯🇵', display: '🇯🇵 日本語' },
        { code: 'ko', name: 'Korean', native_name: '한국어', flag: '🇰🇷', display: '🇰🇷 한국어' },
        { code: 'zh', name: 'Chinese', native_name: '中文', flag: '🇨🇳', display: '🇨🇳 中文' },
        { code: 'hi', name: 'Hindi', native_name: 'हिन्दी', flag: '🇮🇳', display: '🇮🇳 हिन्दी' },
        { code: 'ar', name: 'Arabic', native_name: 'العربية', flag: '🇸🇦', display: '🇸🇦 العربية' }
      ],
      total_languages: 10
    };
  }
};

/**
 * Advanced multilingual video analysis
 * @param {string} url - YouTube video URL
 * @param {string} outputLanguage - Language for analysis output
 * @param {string} videoLanguageHint - Optional hint for video language
 * @returns {Promise<Object>} Analysis results
 */
export const analyzeVideoAdvanced = async (url, outputLanguage = 'en', videoLanguageHint = null) => {
  try {
    const response = await api.post('/api/advanced-summary', {
      url,
      output_language: outputLanguage,
      auto_detect_video_language: true,
      video_language_hint: videoLanguageHint
    });
    return response.data;
  } catch (error) {
    console.error('Failed to analyze video:', error);
    throw error;
  }
};

/**
 * Advanced multilingual Q&A
 * @param {string} transcript - Video transcript
 * @param {string} query - User question
 * @param {string} outputLanguage - Language for response
 * @param {string} queryLanguage - Language of the question
 * @returns {Promise<Object>} Query response
 */
export const queryTranscriptAdvanced = async (transcript, query, outputLanguage = 'en', queryLanguage = null) => {
  try {
    const response = await api.post('/api/advanced-query', {
      transcript,
      query,
      output_language: outputLanguage,
      query_language: queryLanguage
    });
    return response.data;
  } catch (error) {
    console.error('Failed to query transcript:', error);
    throw error;
  }
};

// Backward compatibility functions
export const analyzeVideo = (url, language = 'en') => analyzeVideoAdvanced(url, language);
export const queryTranscript = (transcript, query, language = 'en') => queryTranscriptAdvanced(transcript, query, language);

/**
 * Health check for the API
 * @returns {Promise<boolean>} API health status
 */
export const checkApiHealth = async () => {
  try {
    const response = await api.get('/health');
    return response.status === 200;
  } catch (error) {
    return false;
  }
};

export default api;