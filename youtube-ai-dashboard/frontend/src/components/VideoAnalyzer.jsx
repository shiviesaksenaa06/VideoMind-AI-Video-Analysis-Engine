// Advanced src/components/VideoAnalyzer.jsx - Cross-language analysis
import React, { useState, useEffect } from 'react';
import LoadingSpinner from './LoadingSpinner';
import { getSupportedLanguages } from '../services/api';

const VideoAnalyzer = ({ onAnalyze, loading }) => {
  const [url, setUrl] = useState('');
  const [outputLanguage, setOutputLanguage] = useState('en'); // Language for results
  const [videoLanguageHint, setVideoLanguageHint] = useState(''); // Optional video language hint
  const [supportedLanguages, setSupportedLanguages] = useState([]);
  const [isValidUrl, setIsValidUrl] = useState(true);
  const [loadingLanguages, setLoadingLanguages] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState(false);

  // Load supported languages on component mount
  useEffect(() => {
    const loadLanguages = async () => {
      setLoadingLanguages(true);
      try {
        const data = await getSupportedLanguages();
        setSupportedLanguages(data.languages);
      } catch (error) {
        console.error('Failed to load languages:', error);
      } finally {
        setLoadingLanguages(false);
      }
    };
    
    loadLanguages();
  }, []);

  const validateYouTubeUrl = (url) => {
    const patterns = [
      /(?:youtube\.com\/watch\?v=)([0-9A-Za-z_-]{11})/,
      /(?:youtu\.be\/)([0-9A-Za-z_-]{11})/,
      /(?:youtube\.com\/embed\/)([0-9A-Za-z_-]{11})/,
      /(?:youtube\.com\/v\/)([0-9A-Za-z_-]{11})/,
    ];
    
    return patterns.some(pattern => pattern.test(url));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!url.trim()) {
      setIsValidUrl(false);
      return;
    }

    if (!validateYouTubeUrl(url)) {
      setIsValidUrl(false);
      return;
    }

    setIsValidUrl(true);
    onAnalyze(url, outputLanguage, videoLanguageHint || null);
  };

  const handleUrlChange = (e) => {
    const newUrl = e.target.value;
    setUrl(newUrl);
    
    if (newUrl && !validateYouTubeUrl(newUrl)) {
      setIsValidUrl(false);
    } else {
      setIsValidUrl(true);
    }
  };

  const getLanguageByCode = (code) => {
    return supportedLanguages.find(lang => lang.code === code);
  };

  const popularLanguages = ['en', 'es', 'fr', 'de', 'ja', 'ko', 'zh', 'hi', 'ar', 'pt'];
  const popularLangs = popularLanguages.map(code => getLanguageByCode(code)).filter(Boolean);
  const otherLangs = supportedLanguages.filter(lang => !popularLanguages.includes(lang.code));

  const getLanguageFlag = (langCode) => {
    const flags = {
      'en': '🇺🇸', 'es': '🇪🇸', 'fr': '🇫🇷', 'de': '🇩🇪', 'it': '🇮🇹',
      'pt': '🇧🇷', 'ru': '🇷🇺', 'ja': '🇯🇵', 'ko': '🇰🇷', 'zh': '🇨🇳',
      'hi': '🇮🇳', 'ar': '🇸🇦', 'nl': '🇳🇱', 'sv': '🇸🇪', 'no': '🇳🇴',
      'da': '🇩🇰', 'fi': '🇫🇮', 'pl': '🇵🇱', 'tr': '🇹🇷', 'th': '🇹🇭',
      'vi': '🇻🇳'
    };
    return flags[langCode] || '🌐';
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-100">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          🌍 Cross-Language Video Analysis
        </h2>
        <p className="text-gray-600">
          Analyze ANY video in ANY language and get insights in YOUR preferred language
        </p>
        <div className="mt-3 text-sm text-blue-600 bg-blue-50 rounded-lg p-3">
          <strong>Examples:</strong> Spanish video → Korean summary | English video → Arabic analysis | Japanese video → French insights
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* URL Input */}
        <div>
          <label htmlFor="youtube-url" className="block text-sm font-medium text-gray-700 mb-2">
            🎥 YouTube Video URL (Any Language)
          </label>
          <div className="relative">
            <input
              id="youtube-url"
              type="text"
              value={url}
              onChange={handleUrlChange}
              placeholder="https://www.youtube.com/watch?v=... (video can be in any language)"
              className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors ${
                !isValidUrl ? 'border-red-300 bg-red-50' : 'border-gray-300'
              }`}
              disabled={loading}
            />
            <div className="absolute right-3 top-3">
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                <span className="text-gray-400">🎥</span>
              )}
            </div>
          </div>
          
          {!isValidUrl && (
            <p className="mt-2 text-sm text-red-600">
              Please enter a valid YouTube URL
            </p>
          )}
        </div>

        {/* Output Language Selection */}
        <div>
          <label htmlFor="output-language-select" className="block text-sm font-medium text-gray-700 mb-2">
            🎯 Get Results In (Your Language)
          </label>
          <div className="relative">
            <select
              id="output-language-select"
              value={outputLanguage}
              onChange={(e) => setOutputLanguage(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white"
              disabled={loading || loadingLanguages}
            >
              {loadingLanguages ? (
                <option>Loading languages...</option>
              ) : (
                <>
                  <optgroup label="🌟 Popular Languages">
                    {popularLangs.map((lang) => (
                      <option key={lang.code} value={lang.code}>
                        {lang.display}
                      </option>
                    ))}
                  </optgroup>
                  {otherLangs.length > 0 && (
                    <optgroup label="🌐 All Languages">
                      {otherLangs.map((lang) => (
                        <option key={lang.code} value={lang.code}>
                          {lang.display}
                        </option>
                      ))}
                    </optgroup>
                  )}
                </>
              )}
            </select>
            <div className="absolute right-3 top-3 pointer-events-none">
              {loadingLanguages ? (
                <LoadingSpinner size="sm" />
              ) : (
                <span className="text-gray-400">🔽</span>
              )}
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Summary, themes, sentiment analysis, and AI chat will be in this language
          </p>
        </div>

        {/* Advanced Options Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvancedOptions(!showAdvancedOptions)}
            className="flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors"
          >
            <span className="mr-2">{showAdvancedOptions ? '🔽' : '▶️'}</span>
            Advanced Options (Optional)
          </button>
        </div>

        {/* Advanced Options */}
        {showAdvancedOptions && (
          <div className="bg-gray-50 rounded-lg p-4 space-y-4">
            <div>
              <label htmlFor="video-language-hint" className="block text-sm font-medium text-gray-700 mb-2">
                🎬 Video Language Hint (Optional)
              </label>
              <select
                id="video-language-hint"
                value={videoLanguageHint}
                onChange={(e) => setVideoLanguageHint(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none bg-white text-sm"
                disabled={loading || loadingLanguages}
              >
                <option value="">Auto-detect video language</option>
                {supportedLanguages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.display}
                  </option>
                ))}
              </select>
              <p className="mt-1 text-xs text-gray-500">
                If you know the video language, selecting it can improve analysis accuracy
              </p>
            </div>
          </div>
        )}

        {/* Analysis Preview */}
        {outputLanguage && supportedLanguages.length > 0 && (
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <span className="text-2xl mr-3">
                  {getLanguageByCode(outputLanguage)?.flag || '🌐'}
                </span>
                <div>
                  <h4 className="text-blue-800 font-medium">
                    Analysis Language: {getLanguageByCode(outputLanguage)?.native_name}
                  </h4>
                  <p className="text-blue-600 text-sm">
                    All AI insights will be provided in this language
                  </p>
                </div>
              </div>
              {videoLanguageHint && (
                <div className="flex items-center text-sm text-gray-600">
                  <span className="mr-2">
                    {getLanguageByCode(videoLanguageHint)?.flag}
                  </span>
                  <span>
                    Video: {getLanguageByCode(videoLanguageHint)?.native_name}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !url.trim() || !isValidUrl || loadingLanguages}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-3 px-6 rounded-lg font-semibold hover:from-blue-700 hover:to-purple-700 focus:ring-4 focus:ring-blue-200 transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
        >
          {loading ? (
            <div className="flex items-center justify-center">
              <LoadingSpinner size="sm" color="white" />
              <span className="ml-2">Analyzing Video...</span>
            </div>
          ) : (
            <div className="flex items-center justify-center">
              <span className="mr-2">🔍</span>
              Analyze Video
              {outputLanguage && getLanguageByCode(outputLanguage) && (
                <span className="ml-2">
                  → {getLanguageByCode(outputLanguage).flag} {getLanguageByCode(outputLanguage).native_name}
                </span>
              )}
            </div>
          )}
        </button>
      </form>

      {/* Popular Use Cases */}
      <div className="mt-6 text-center">
        <p className="text-xs text-gray-500 mb-3">
          🌟 Popular Cross-Language Analysis Examples:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-50 rounded p-2">
            <span className="font-medium">🇪🇸 Spanish video</span> → <span className="text-blue-600">🇰🇷 Korean insights</span>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <span className="font-medium">🇺🇸 English video</span> → <span className="text-blue-600">🇯🇵 Japanese summary</span>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <span className="font-medium">🇫🇷 French video</span> → <span className="text-blue-600">🇮🇳 Hindi analysis</span>
          </div>
          <div className="bg-gray-50 rounded p-2">
            <span className="font-medium">🇯🇵 Japanese video</span> → <span className="text-blue-600">🇸🇦 Arabic insights</span>
          </div>
        </div>
      </div>

      {loading && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center">
            <LoadingSpinner size="sm" />
            <div className="ml-3">
              <h4 className="text-blue-800 font-medium">
                Cross-language analysis in progress...
              </h4>
              <p className="text-blue-600 text-sm mt-1">
                {videoLanguageHint ? 
                  `Processing ${getLanguageByCode(videoLanguageHint)?.native_name || 'video'} → ${getLanguageByCode(outputLanguage)?.native_name || 'analysis'}` :
                  `Auto-detecting video language and analyzing in ${getLanguageByCode(outputLanguage)?.native_name || 'selected language'}`
                }
              </p>
            </div>
          </div>
          
          <div className="mt-4 bg-white rounded p-3">
            <div className="text-xs text-gray-600 space-y-1">
              <div>✓ Extracting video metadata</div>
              <div>⏳ Auto-detecting video language</div>
              <div>⏳ Fetching transcript</div>
              <div>⏳ Cross-language sentiment analysis</div>
              <div>⏳ Multilingual theme extraction</div>
              <div>⏳ Generating summary in target language</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VideoAnalyzer;