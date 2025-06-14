import React, { useState } from "react";
import axios from "axios";
import { Card, CardContent } from "./components/ui/card";
import { Input } from "./components/ui/input";
import { Button } from "./components/ui/button";
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "./components/ui/tabs";
import { Textarea } from "./components/ui/textarea";
import { Loader2, Youtube } from "lucide-react";
import { motion } from "framer-motion";

const App = () => {
  const [inputUrl, setInputUrl] = useState("");
  const [responseText, setResponseText] = useState("");
  const [transcript, setTranscript] = useState(""); // 🆕 keep transcript
  const [loading, setLoading] = useState(false);
  const [activeAgent, setActiveAgent] = useState("agent1");
  const [userQuery, setUserQuery] = useState("");
  const [queryResponse, setQueryResponse] = useState("");

  const agents = {
    agent1: "gemini",
    agent2: "gpt-3.5-turbo",
    agent3: "claude",
  };

  /* -------- POST /api/summary -------- */
  const handleSubmit = async () => {
    if (!inputUrl) return;
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/summary", {
        url: inputUrl,
        agent: agents[activeAgent],
      });
      setResponseText(res.data.summary || "");
      setTranscript(res.data.transcript || ""); // 🆕 store transcript
    } catch (err) {
      console.error("Error fetching summary:", err);
    }
    setLoading(false);
  };

  /* -------- POST /api/query -------- */
  const handleQuery = async () => {
    if (!userQuery || !transcript) return;
    setLoading(true);
    try {
      const res = await axios.post("http://localhost:8000/api/query", {
        transcript,          // 🆕 backend expects this
        query: userQuery,
      });
      setQueryResponse(res.data.response || "");
    } catch (err) {
      console.error("Error answering query:", err);
    }
    setLoading(false);
  };

  return (
    <main className="min-h-screen bg-zinc-900 text-white flex flex-col items-center justify-start p-6">
      <motion.h1
        initial={{ opacity: 0, y: -30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-4xl font-bold mb-4"
      >
        🎥 YouTube Summary AI
      </motion.h1>

      {/* -------- URL + Summarize -------- */}
      <Card className="w-full max-w-3xl shadow-xl border border-zinc-700">
        <CardContent className="p-4 space-y-4">
          <div className="flex items-center gap-2">
            <Youtube className="text-red-500" />
            <Input
              placeholder="Paste a YouTube video URL..."
              value={inputUrl}
              onChange={(e) => setInputUrl(e.target.value)}
            />
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? <Loader2 className="animate-spin" /> : "Summarize"}
            </Button>
          </div>
          <Textarea
            className="w-full min-h-[150px] bg-zinc-800 border border-zinc-700"
            value={responseText}
            readOnly
          />
        </CardContent>
      </Card>

      {/* -------- Agent Tabs -------- */}
      <Tabs
        defaultValue={activeAgent}
        onValueChange={setActiveAgent}
        className="w-full max-w-3xl mt-10"
      >
        <TabsList>
          <TabsTrigger value="agent1">Gemini</TabsTrigger>
          <TabsTrigger value="agent2">GPT-4</TabsTrigger>
          <TabsTrigger value="agent3">Claude</TabsTrigger>
        </TabsList>

        <TabsContent value="agent1">
          <p className="text-sm text-gray-300">You're using Gemini AI.</p>
        </TabsContent>
        <TabsContent value="agent2">
          <p className="text-sm text-gray-300">You're using OpenAI GPT-4.</p>
        </TabsContent>
        <TabsContent value="agent3">
          <p className="text-sm text-gray-300">You're using Anthropic Claude.</p>
        </TabsContent>
      </Tabs>

      {/* -------- Q&A -------- */}
      <Card className="w-full max-w-3xl mt-10 shadow-lg border border-zinc-700">
        <CardContent className="p-4 space-y-4">
          <h2 className="text-xl font-semibold">Ask anything about the video</h2>
          <Textarea
            placeholder="Enter your open-ended query..."
            value={userQuery}
            onChange={(e) => setUserQuery(e.target.value)}
          />
          <Button onClick={handleQuery} disabled={loading || !transcript}>
            {loading ? <Loader2 className="animate-spin" /> : "Ask AI"}
          </Button>

          {queryResponse && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm text-gray-300 whitespace-pre-line border-t border-zinc-700 pt-4"
            >
              {queryResponse}
            </motion.div>
          )}
        </CardContent>
      </Card>

      <footer className="mt-10 text-zinc-500 text-sm text-center">
        Made by Team 2 | Multi-Agent | Multi-LLM | Scalable UI 🚀
      </footer>
    </main>
  );
};

export default App;


