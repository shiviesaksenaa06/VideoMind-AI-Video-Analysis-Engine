// Complete src/components/AnalysisResults.jsx - Cross-language results display
import React, { useState } from 'react';
import LoadingSpinner from './LoadingSpinner';

const AnalysisResults = ({ data, onQuery }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [query, setQuery] = useState('');
  const [queryResponse, setQueryResponse] = useState('');
  const [queryLoading, setQueryLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const handleQuery = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setQueryLoading(true);
    try {
      const response = await onQuery(query);
      setQueryResponse(response);
    } catch (error) {
      setQueryResponse('Sorry, I couldn\'t process your question. Please try again.');
    } finally {
      setQueryLoading(false);
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'text-green-600 bg-green-100';
      case 'negative': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSentimentEmoji = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return '😊';
      case 'negative': return '😞';
      default: return '😐';
    }
  };

  const highlightSearchTerm = (text, term) => {
    if (!term) return text;
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<mark class="bg-yellow-200">$1</mark>');
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence?.toLowerCase()) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-orange-600 bg-orange-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const tabs = [
    { id: 'overview', label: '📊 Overview', icon: '📊' },
    { id: 'language-info', label: '🌍 Language Info', icon: '🌍' },
    { id: 'sentiment', label: '😊 Sentiment', icon: '😊' },
    { id: 'themes', label: '🎯 Themes', icon: '🎯' },
    { id: 'wordcloud', label: '☁️ Word Cloud', icon: '☁️' },
    { id: 'transcript', label: '📄 Transcript', icon: '📄' },
    { id: 'chat', label: '💬 Ask AI', icon: '💬' },
  ];

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Enhanced Video Info Header with Language Information */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold mb-2">{data.meta?.title || 'Video Analysis'}</h2>
            <p className="opacity-90 mb-2">
              by {data.meta?.channel || 'Unknown Channel'}
            </p>
            
            {/* Language Information Banner */}
            <div className="bg-white bg-opacity-20 rounded-lg p-3 mb-3">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center">
                  <span className="mr-2">🎬</span>
                  <span className="font-medium">Video:</span>
                  <span className="ml-1">{data.video_language_name || 'Auto-detected'}</span>
                </div>
                <div className="flex items-center">
                  <span className="mr-2">🎯</span>
                  <span className="font-medium">Analysis:</span>
                  <span className="ml-1">{data.output_language_name}</span>
                </div>
                {data.transcript_source && (
                  <div className="flex items-center">
                    <span className="mr-2">📝</span>
                    <span className="text-xs opacity-80">{data.transcript_source}</span>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex flex-wrap gap-4 text-sm opacity-90">
              {data.meta?.views && (
                <span>👁️ {data.meta.views.toLocaleString()} views</span>
              )}
              {data.meta?.likes && (
                <span>👍 {data.meta.likes.toLocaleString()} likes</span>
              )}
              {data.meta?.published && (
                <span>📅 {new Date(data.meta.published).toLocaleDateString()}</span>
              )}
            </div>
          </div>
          {data.meta?.thumbnail && (
            <div className="mt-4 md:mt-0 md:ml-6">
              <img 
                src={data.meta.thumbnail} 
                alt="Video thumbnail"
                className="w-full md:w-48 h-auto rounded-lg shadow-lg"
              />
            </div>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 bg-blue-50'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-3 text-gray-800">📝 Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-gray-700 leading-relaxed">{data.summary}</p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="text-lg font-semibold mb-3 text-gray-800">😊 Sentiment</h4>
                <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${getSentimentColor(data.sentiment?.overall)}`}>
                  <span className="mr-2">{getSentimentEmoji(data.sentiment?.overall)}</span>
                  {data.sentiment?.overall?.toUpperCase()} ({(data.sentiment?.score * 100).toFixed(0)}%)
                </div>
                {data.sentiment?.confidence && (
                  <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ml-2 ${getConfidenceColor(data.sentiment.confidence)}`}>
                    {data.sentiment.confidence.toUpperCase()} CONFIDENCE
                  </div>
                )}
                <p className="text-gray-600 text-sm mt-2">{data.sentiment?.explanation}</p>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3 text-gray-800">🎯 Top Themes</h4>
                <div className="space-y-2">
                  {data.themes?.themes?.slice(0, 3).map((theme, index) => (
                    <div key={index} className="flex justify-between items-center">
                      <span className="text-gray-700">{theme.theme}</span>
                      <span className="text-sm text-gray-500">
                        {(theme.relevance * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'language-info' && (
          <div className="space-y-6">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">🌍 Cross-Language Analysis Details</h3>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold mb-3 text-blue-800 flex items-center">
                  <span className="mr-2">🎬</span>
                  Original Video
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Language:</span>
                    <span className="font-medium">{data.video_language_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Language Code:</span>
                    <span className="font-mono bg-gray-100 px-2 py-1 rounded">{data.video_language}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Transcript Source:</span>
                    <span className="text-xs">{data.transcript_source}</span>
                  </div>
                </div>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 className="font-semibold mb-3 text-green-800 flex items-center">
                  <span className="mr-2">🎯</span>
                  Analysis Output
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Language:</span>
                    <span className="font-medium">{data.output_language_name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Language Code:</span>
                    <span className="font-mono bg-gray-100 px-2 py-1 rounded">{data.output_language}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">AI Model:</span>
                    <span className="text-xs">Cross-language GPT</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-semibold mb-3 text-purple-800 flex items-center">
                <span className="mr-2">🔄</span>
                Translation Process
              </h4>
              <div className="text-sm text-gray-700">
                <p className="mb-2">
                  This analysis used advanced AI to understand content in <strong>{data.video_language_name}</strong> 
                  and provide insights in <strong>{data.output_language_name}</strong>.
                </p>
                <div className="flex items-center space-x-4 text-xs bg-white rounded p-3">
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                    <span>Video Language Detection</span>
                  </div>
                  <span>→</span>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-yellow-500 rounded-full mr-2"></div>
                    <span>Content Understanding</span>
                  </div>
                  <span>→</span>
                  <div className="flex items-center">
                    <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                    <span>Target Language Output</span>
                  </div>
                </div>
              </div>
            </div>

            {data.video_language !== data.output_language && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h4 className="font-semibold mb-2 text-yellow-800 flex items-center">
                  <span className="mr-2">⚡</span>
                  Cross-Language Analysis Active
                </h4>
                <p className="text-sm text-yellow-700">
                  This video was originally in <strong>{data.video_language_name}</strong> but all analysis, 
                  summaries, and AI responses are provided in <strong>{data.output_language_name}</strong> 
                  for your convenience.
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'sentiment' && (
          <div className="space-y-6">
            <div className="text-center">
              <div className={`inline-flex items-center px-6 py-3 rounded-full text-lg font-semibold ${getSentimentColor(data.sentiment?.overall)}`}>
                <span className="mr-3 text-2xl">{getSentimentEmoji(data.sentiment?.overall)}</span>
                {data.sentiment?.overall?.toUpperCase()}
              </div>
              {data.sentiment?.confidence && (
                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ml-3 ${getConfidenceColor(data.sentiment.confidence)}`}>
                  {data.sentiment.confidence.toUpperCase()} CONFIDENCE
                </div>
              )}
              <div className="mt-4">
                <div className="bg-gray-200 rounded-full h-4 max-w-xs mx-auto">
                  <div 
                    className="bg-gradient-to-r from-blue-500 to-purple-500 h-4 rounded-full transition-all duration-500"
                    style={{ width: `${(data.sentiment?.score || 0.5) * 100}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  Sentiment Score: {((data.sentiment?.score || 0.5) * 100).toFixed(1)}%
                </p>
              </div>
            </div>
            
            <div className="bg-gray-50 rounded-lg p-6">
              <h4 className="font-semibold mb-3 text-gray-800">Analysis Explanation</h4>
              <p className="text-gray-700 leading-relaxed">{data.sentiment?.explanation}</p>
              {data.video_language !== data.output_language && (
                <div className="mt-3 text-xs text-blue-600 bg-blue-100 rounded p-2">
                  <span className="font-medium">Cross-language note:</span> This sentiment was analyzed from {data.video_language_name} content and explained in {data.output_language_name}.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'themes' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-4 text-gray-800">🎯 Key Themes</h3>
              {data.video_language !== data.output_language && (
                <div className="mb-4 text-sm text-blue-600 bg-blue-50 rounded-lg p-3">
                  <span className="font-medium">🌍 Cross-language analysis:</span> Themes identified from {data.video_language_name} content and described in {data.output_language_name}.
                </div>
              )}
              <div className="grid gap-4">
                {data.themes?.themes?.map((theme, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex justify-between items-start mb-2">
                      <h4 className="font-semibold text-gray-800">{theme.theme}</h4>
                      <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded text-sm">
                        {(theme.relevance * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-gray-600 text-sm">{theme.description}</p>
                  </div>
                ))}
              </div>
            </div>

            {data.themes?.keywords && (
              <div>
                <h4 className="text-lg font-semibold mb-3 text-gray-800">🔑 Keywords</h4>
                <div className="flex flex-wrap gap-2">
                  {data.themes.keywords.map((keyword, index) => (
                    <span 
                      key={index}
                      className="bg-gray-100 text-gray-700 px-3 py-1 rounded-full text-sm hover:bg-gray-200 transition-colors"
                    >
                      {keyword}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'wordcloud' && (
          <div className="text-center">
            <h3 className="text-xl font-semibold mb-4 text-gray-800">☁️ Word Cloud</h3>
            {data.wordcloud_b64 ? (
              <div className="bg-gray-50 rounded-lg p-4">
                <img 
                  src={`data:image/png;base64,${data.wordcloud_b64}`}
                  alt="Word Cloud"
                  className="max-w-full h-auto mx-auto rounded-lg shadow-sm"
                />
                <p className="text-sm text-gray-500 mt-2">
                  Generated from {data.video_language_name} transcript
                </p>
              </div>
            ) : (
              <p className="text-gray-500">Word cloud not available</p>
            )}
          </div>
        )}

        {activeTab === 'transcript' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xl font-semibold text-gray-800">📄 Original Transcript</h3>
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="Search transcript..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="px-3 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <span className="text-sm text-gray-500">🔍</span>
              </div>
            </div>
            
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
              <span className="font-medium">Language:</span> {data.video_language_name} | 
              <span className="font-medium ml-2">Source:</span> {data.transcript_source}
            </div>
            
            <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
              <div 
                className="text-gray-700 leading-relaxed whitespace-pre-wrap"
                dangerouslySetInnerHTML={{
                  __html: highlightSearchTerm(data.transcript || 'No transcript available', searchTerm)
                }}
              />
            </div>
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-xl font-semibold mb-4 text-gray-800">💬 Ask AI about this video</h3>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm">
                <span className="font-medium">🤖 AI Language:</span> {data.output_language_name} | 
                <span className="font-medium ml-2">Video Language:</span> {data.video_language_name}
              </div>
              <form onSubmit={handleQuery} className="space-y-4">
                <div>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={`Ask a question about the video content in any language...`}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                    rows="3"
                    disabled={queryLoading}
                  />
                </div>
                <button
                  type="submit"
                  disabled={queryLoading || !query.trim()}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {queryLoading ? (
                    <div className="flex items-center">
                      <LoadingSpinner size="sm" color="white" />
                      <span className="ml-2">Thinking...</span>
                    </div>
                  ) : (
                    'Ask Question'
                  )}
                </button>
              </form>
            </div>

            {queryResponse && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-semibold text-blue-800 mb-2 flex items-center">
                  <span className="mr-2">🤖</span>
                  AI Response ({data.output_language_name}):
                </h4>
                <p className="text-blue-700 leading-relaxed">{queryResponse}</p>
              </div>
            )}

            <div className="text-sm text-gray-500">
              <p className="mb-2">💡 Try asking questions like:</p>
              <ul className="list-disc list-inside space-y-1 ml-4">
                <li>"What are the main takeaways from this video?"</li>
                <li>"Can you explain the key concepts discussed?"</li>
                <li>"What examples were mentioned?"</li>
                <li>"Summarize the conclusion"</li>
                <li>"What questions does this video answer?"</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisResults;