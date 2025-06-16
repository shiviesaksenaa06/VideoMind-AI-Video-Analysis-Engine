import React, { useState } from 'react';
import VideoAnalyzer from './components/VideoAnalyzer';
import AnalysisResults from './components/AnalysisResults';
import ErrorBoundary from './components/ErrorBoundary';
import { analyzeVideoAdvanced, queryTranscriptAdvanced } from './services/api';

function App() {
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');

  const handleAnalyzeVideo = async (url, outputLanguage = 'en', videoLanguageHint = null) => {
    setLoading(true);
    setError(null);
    setAnalysisData(null);
    setSelectedLanguage(outputLanguage);

    try {
      const data = await analyzeVideoAdvanced(url, outputLanguage, videoLanguageHint);
      setAnalysisData(data);
    } catch (err) {
      setError(err.message || 'Failed to analyze video');
    } finally {
      setLoading(false);
    }
  };

  const handleQuery = async (query) => {
    if (!analysisData?.transcript) return null;
    
    try {
      const response = await queryTranscriptAdvanced(
        analysisData.transcript, 
        query, 
        selectedLanguage
      );
      return response.response;
    } catch (err) {
      throw new Error('Failed to query transcript');
    }
  };

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              🌍 YouTube AI Analyzer
            </h1>
            <p className="text-gray-600 mt-2">
              Extract insights from YouTube videos using advanced AI in 25+ languages
            </p>
            <div className="mt-3 text-sm text-blue-600">
              <span className="bg-blue-100 px-3 py-1 rounded-full">
                ✨ Cross-Language Analysis: Any Video → Any Language
              </span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <div className="space-y-8">
            {/* Video Input Section */}
            <VideoAnalyzer 
              onAnalyze={handleAnalyzeVideo}
              loading={loading}
            />

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center">
                  <div className="text-red-400 mr-3">⚠️</div>
                  <div>
                    <h3 className="text-red-800 font-medium">Analysis Failed</h3>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Results Section */}
            {analysisData && (
              <AnalysisResults 
                data={analysisData}
                onQuery={handleQuery}
              />
            )}
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white border-t mt-16">
          <div className="max-w-7xl mx-auto px-4 py-6 text-center text-gray-500">
            <p>Powered by OpenAI GPT & FastAPI • Built with React & Tailwind CSS</p>
            <p className="text-sm mt-2">🌍 Breaking language barriers with AI • 25+ languages supported</p>
          </div>
        </footer>
      </div>
    </ErrorBoundary>
  );
}

export default App;