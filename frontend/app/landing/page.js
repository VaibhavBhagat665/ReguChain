'use client';

import { useState } from 'react';
import { Shield, Zap, BarChart3, Brain, FileText, Search, Eye, Bot, Sparkles, Upload, ArrowRight, CheckCircle, Globe, Clock, TrendingUp } from 'lucide-react';
import { uploadPdf } from '../../lib/api';

export default function Landing() {
  const [pdfUploading, setPdfUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);

  const handlePdfUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setPdfUploading(true);
    setUploadResult(null);

    try {
      const result = await uploadPdf(file);
      setUploadResult({ success: true, message: `PDF "${result.title}" ingested with ${result.chunks} chunks` });
    } catch (error) {
      setUploadResult({ success: false, message: `Upload failed: ${error.message}` });
    } finally {
      setPdfUploading(false);
    }
  };

  const features = [
    {
      icon: Clock,
      title: "Real-time Compliance",
      description: "Continuous monitoring of regulatory updates from SEC, CFTC, OFAC, and other agencies with instant alerts.",
      color: "from-blue-500 to-cyan-500"
    },
    {
      icon: Eye,
      title: "Know Your Transaction (KYT)",
      description: "Real-time transaction analysis and risk scoring with sanctions screening and AML compliance.",
      color: "from-purple-500 to-pink-500"
    },
    {
      icon: TrendingUp,
      title: "Regulatory Change Management",
      description: "Automated identification and impact analysis of new regulations with AI-powered insights.",
      color: "from-green-500 to-emerald-500"
    },
    {
      icon: Brain,
      title: "RAG-Powered Intelligence",
      description: "Advanced retrieval-augmented generation with real-time news correlation and document analysis.",
      color: "from-orange-500 to-red-500"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/20 dark:from-gray-950 dark:via-slate-900 dark:to-indigo-950/50">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/60 dark:bg-gray-900/60 backdrop-blur-xl shadow-sm border-b border-gray-200/30 dark:border-gray-700/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative p-3 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl shadow-lg">
                <Shield className="w-8 h-8 text-white" />
                <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-2xl blur-lg opacity-50 -z-10"></div>
              </div>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                  ReguChain
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-purple-500" />
                  Real-time Regulatory Compliance Intelligence
                </p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="/"
                className="px-6 py-2.5 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl text-sm font-semibold hover:shadow-lg hover:scale-105 transition-all duration-300"
              >
                Go to Dashboard
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900/20 dark:to-purple-900/20 rounded-full text-blue-700 dark:text-blue-300 text-sm font-medium mb-8">
              <Globe className="w-4 h-4" />
              Powered by Pathway, LangChain & Real-time Data Streams
            </div>
            
            <h1 className="text-5xl md:text-7xl font-bold mb-8">
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
                Regulatory
              </span>
              <br />
              <span className="text-gray-900 dark:text-white">
                Compliance
              </span>
              <br />
              <span className="bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                Reimagined
              </span>
            </h1>
            
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
              ReguChain shifts from backward-looking risk assessment to proactive, real-time decision intelligence. 
              Our AI-powered platform continuously monitors regulatory changes, analyzes blockchain transactions, 
              and provides instant compliance insights.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <a
                href="/"
                className="group px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl text-lg font-semibold hover:shadow-2xl hover:scale-105 transition-all duration-300 flex items-center gap-3"
              >
                Connect Wallet & Start
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
              
              <a
                href="#features"
                className="px-8 py-4 bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl border border-gray-200/30 dark:border-gray-700/30 rounded-2xl text-lg font-semibold text-gray-900 dark:text-white hover:shadow-xl hover:scale-105 transition-all duration-300"
              >
                Learn More
              </a>
            </div>
          </div>

          {/* PDF Upload Section */}
          <div className="max-w-md mx-auto mb-16">
            <div className="bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-2xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-6">
              <div className="flex items-center gap-3 mb-4">
                <Upload className="w-5 h-5 text-purple-600" />
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Upload Compliance Report</h3>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Upload PDF reports to enhance our AI knowledge base for more accurate compliance analysis.
              </p>
              
              <div className="relative">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handlePdfUpload}
                  disabled={pdfUploading}
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-700 dark:text-white disabled:opacity-50"
                />
                {pdfUploading && (
                  <div className="absolute inset-0 bg-white/80 dark:bg-gray-800/80 rounded-lg flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-600"></div>
                  </div>
                )}
              </div>
              
              {uploadResult && (
                <div className={`mt-3 p-3 rounded-lg text-sm ${
                  uploadResult.success 
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400' 
                    : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400'
                }`}>
                  <div className="flex items-center gap-2">
                    {uploadResult.success ? (
                      <CheckCircle className="w-4 h-4" />
                    ) : (
                      <div className="w-4 h-4 rounded-full bg-current opacity-20" />
                    )}
                    {uploadResult.message}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Core Capabilities
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Built with production-grade architecture combining Pathway streaming, 
              LangChain RAG, and real-time blockchain analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => {
              const IconComponent = feature.icon;
              return (
                <div
                  key={index}
                  className="group bg-white/50 dark:bg-gray-800/50 backdrop-blur-xl rounded-3xl shadow-lg border border-gray-200/30 dark:border-gray-700/30 p-8 hover:shadow-2xl hover:scale-[1.02] transition-all duration-500"
                >
                  <div className="flex items-start gap-6">
                    <div className={`relative p-4 bg-gradient-to-br ${feature.color} rounded-2xl shadow-md group-hover:scale-110 transition-transform duration-500`}>
                      <IconComponent className="w-8 h-8 text-white" />
                      <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} rounded-2xl blur-md opacity-0 group-hover:opacity-40 transition-opacity duration-500 -z-10`}></div>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-3 group-hover:text-transparent group-hover:bg-gradient-to-r group-hover:from-blue-600 group-hover:via-purple-600 group-hover:to-pink-600 group-hover:bg-clip-text transition-all duration-300">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-400 leading-relaxed">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Architecture Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Enterprise-Grade Architecture
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
              Modular FastAPI backend with Next.js frontend, containerized for scalability and maintainability.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="p-6 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl shadow-lg mb-4 mx-auto w-fit">
                <Zap className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Real-time Streaming</h3>
              <p className="text-gray-600 dark:text-gray-400">Pathway-powered continuous data ingestion with fallback processing</p>
            </div>
            
            <div className="text-center">
              <div className="p-6 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl shadow-lg mb-4 mx-auto w-fit">
                <Brain className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">AI-Powered RAG</h3>
              <p className="text-gray-600 dark:text-gray-400">LangChain with FAISS vector store and OpenRouter LLM integration</p>
            </div>
            
            <div className="text-center">
              <div className="p-6 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl shadow-lg mb-4 mx-auto w-fit">
                <BarChart3 className="w-12 h-12 text-white" />
              </div>
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Blockchain Analytics</h3>
              <p className="text-gray-600 dark:text-gray-400">Real-time transaction monitoring with risk scoring and compliance checks</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl p-12 shadow-2xl">
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to Transform Your Compliance?
            </h2>
            <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
              Experience the future of regulatory technology with real-time intelligence, 
              AI-powered insights, and enterprise-grade reliability.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a
                href="/"
                className="group px-8 py-4 bg-white text-purple-600 rounded-2xl text-lg font-semibold hover:shadow-2xl hover:scale-105 transition-all duration-300 flex items-center justify-center gap-3"
              >
                <Shield className="w-5 h-5" />
                Start Demo
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 border-t border-gray-200/30 dark:border-gray-700/30">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="p-2 bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 rounded-xl">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              ReguChain
            </span>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time Regulatory Compliance Intelligence Platform
          </p>
        </div>
      </footer>
    </div>
  );
}


// 
