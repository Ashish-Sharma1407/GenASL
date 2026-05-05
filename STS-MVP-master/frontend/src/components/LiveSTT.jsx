import { useState, useRef, useEffect } from "react";
import { Mic, Send, AlertCircle, CheckCheck, Clock } from "lucide-react";

export default function LiveSTT() {
  const [recording, setRecording] = useState(false);
  const [textInput, setTextInput] = useState("");
  const [messages, setMessages] = useState([
    { id: 0, sender: "system", text: "👋 Welcome! Click the mic button to start chatting.", timestamp: new Date() }
  ]);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);

  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const workletNodeRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const chatWindowRef = useRef(null);
  const messageCountRef = useRef(1);
  const pollingIntervalsRef = useRef({}); // Keep track of polling intervals

  const addMessage = (sender, text) => {
    if (!text) return;
    const id = messageCountRef.current++;
    setMessages(prev => [
      ...prev,
      { 
        id,
        sender, 
        text,
        timestamp: new Date(),
        status: sender === "user" ? "sending" : "received",
        isTranslating: false, // NEW STATE
        videoUrl: null // NEW STATE
      }
    ]);
    return id;
  };

  useEffect(() => {
    if (chatWindowRef.current) {
      setTimeout(() => {
        chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
      }, 0);
    }
  }, [messages]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      Object.values(pollingIntervalsRef.current).forEach(clearInterval);
    };
  }, []);

  const startRecording = async () => {
    setError(null);
    setIsConnecting(true);
    addMessage("system", "🎤 Connecting to microphone...");

    wsRef.current = new WebSocket("ws://127.0.0.1:8000/ws/transcribe");

    wsRef.current.onopen = () => {
      addMessage("system", "✅ Listening... Speak clearly into your microphone");
      setRecording(true);
      setIsConnecting(false);
    };

    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📩 From backend:", data);

        if (data.text && data.text.trim()) {
          if (workletNodeRef.current) {
            workletNodeRef.current.port.close();
            workletNodeRef.current.disconnect();
          }

          if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach(track => track.stop());
          }

          if (audioContextRef.current) {
            audioContextRef.current.close();
          }

          addMessage("user", data.text);
          setRecording(false);
        }

      } catch (error) {
        console.error("Error parsing message:", error);
      }
    };

    wsRef.current.onclose = () => {
      console.log("🔌 WebSocket closed");
      setRecording(false);
      setIsConnecting(false);
    };

    wsRef.current.onerror = () => {
      console.error("WebSocket error");
      const errorMsg = "❌ Connection error. Please check your backend is running.";
      addMessage("system", errorMsg);
      setError(errorMsg);
      setRecording(false);
      setIsConnecting(false);
    };

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      audioContextRef.current = new AudioContext({ sampleRate: 16000 });
      
      await audioContextRef.current.audioWorklet.addModule("/recorder-worklet.js");
      const source = audioContextRef.current.createMediaStreamSource(stream);
      workletNodeRef.current = new AudioWorkletNode(audioContextRef.current, "recorder-processor");

      workletNodeRef.current.port.onmessage = (event) => {
        if (wsRef.current?.readyState === 1) {
          wsRef.current.send(event.data);
        }
      };

      source.connect(workletNodeRef.current).connect(audioContextRef.current.destination);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      const errorMsg = "🚫 Microphone access denied. Please allow microphone access and try again.";
      addMessage("system", errorMsg);
      setError(errorMsg);
      setIsConnecting(false);
    }
  };

  const stopRecording = () => {
    addMessage("system", "⏹️ Processing your message...");

    if (wsRef.current?.readyState === 1) {
      wsRef.current.send(JSON.stringify({ text: "STOP" }));
    }

    setRecording(false);
  };

  const submitText = () => {
    const value = textInput.trim();
    if (!value) return;
    const messageId = addMessage("user", value);
    setTextInput("");

    // Auto-start translation on text submit for immediate feedback.
    if (typeof messageId === "number") {
      generateASLVideo(messageId, value);
    }
  };

  const getStatusIcon = (status) => {
    if (status === "sending") return <Clock size={14} className="text-gray-400" />;
    if (status === "sent") return <CheckCheck size={14} className="text-blue-400" />;
    return null;
  };

  // ==========================================================
  // NEW: TRANSLATION LOGIC
  // ==========================================================
  const generateASLVideo = async (messageId, textToTranslate) => {
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, isTranslating: true, error: null } : msg
    ));

    try {
      // 1. Submit the job
      const response = await fetch("http://127.0.0.1:8000/jobs/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textToTranslate })
      });

      if (!response.ok) throw new Error("Failed to start translation job");

      const data = await response.json();
      const jobId = data.job_id;

      // 2. Poll the job status
      const intervalId = setInterval(async () => {
        try {
          const pollRes = await fetch(`http://127.0.0.1:8000/jobs/${jobId}`);
          if (!pollRes.ok) throw new Error("Failed to poll job status");
          
          const pollData = await pollRes.json();
          console.log("Polling Job:", pollData);

          if (pollData.status === "DONE") {
            clearInterval(intervalId);
            delete pollingIntervalsRef.current[jobId];
            
            setMessages(prev => prev.map(msg => 
              msg.id === messageId ? { 
                ...msg, 
                isTranslating: false, 
                status: "sent",
                videoUrl: pollData.result.video,      // Grabs the RGB video
                skeletonUrl: pollData.result.skeleton, // Grabs the Pose video
                glosses: pollData.result.glosses,       // Grabs the canonical glosses
                skeletonError: pollData.result.skeleton_error || null
              } : msg
            ));
          } else if (pollData.status === "FAILED") {
            clearInterval(intervalId);
            delete pollingIntervalsRef.current[jobId];
            throw new Error(pollData.error || "Generation failed on server");
          }
          // If RUNNING or PENDING, it will just loop again
        } catch (err) {
          clearInterval(intervalId);
          delete pollingIntervalsRef.current[jobId];
          handleTranslationError(messageId, err.message);
        }
      }, 2000); // Poll every 2 seconds

      pollingIntervalsRef.current[jobId] = intervalId;

    } catch (err) {
      handleTranslationError(messageId, err.message);
    }
  };

  const handleTranslationError = (messageId, errorMsg) => {
    console.error("Translation Error:", errorMsg);
    setMessages(prev => prev.map(msg => 
      msg.id === messageId ? { ...msg, isTranslating: false, status: "sent", error: errorMsg } : msg
    ));
  };


  return (
    <div className="w-full h-full bg-gradient-to-b from-slate-900 to-slate-800 flex flex-col rounded-lg shadow-2xl overflow-hidden">
      
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-emerald-700 px-6 py-4 flex items-center justify-between border-b border-emerald-600/50">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center text-emerald-600 font-bold text-lg">
            A
          </div>
          <div>
            <h2 className="text-base font-semibold text-white">Aura AI</h2>
            <p className={`text-xs font-medium transition-colors ${
              recording ? "text-emerald-100 animate-pulse" : "text-emerald-200"
            }`}>
              {recording ? "🎤 Recording..." : isConnecting ? "Connecting..." : "Ready to chat"}
            </p>
          </div>
        </div>
        <div className={`w-3 h-3 rounded-full transition-all ${
          recording ? "bg-red-400 animate-pulse" : "bg-emerald-300"
        }`} />
      </div>

      {/* Messages Window */}
      <div
        ref={chatWindowRef}
        className="flex-1 overflow-y-auto p-4 space-y-3 bg-gradient-to-b from-slate-900 to-slate-800 scrollbar-hide"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-2 animate-fadeIn ${
              msg.sender === "user" ? "justify-end" : "justify-start"
            }`}
          >
            {msg.sender === "system" && (
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center flex-shrink-0">
                <AlertCircle size={16} className="text-yellow-400" />
              </div>
            )}
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow-md text-sm transition-all duration-200 ${
                msg.sender === "user"
                  ? "bg-gradient-to-r from-emerald-500 to-emerald-600 text-white rounded-br-none"
                  : "bg-slate-700 text-gray-100 rounded-bl-none"
              }`}
            >
              <p className="break-words">{msg.text}</p>
              
              {/* ========================================================== */}
              {/* NEW: ASL GENERATION UI */}
              {/* ========================================================== */}
              {msg.sender === "user" && (
                <div className="mt-3 border-t border-emerald-400/30 pt-2">
                  {msg.videoUrl ? (
                    <div className="space-y-3">
                      
                      {/* NEW: GLOSS TRACK */}
                      {msg.glosses && (
                        <div className="flex flex-wrap gap-1 mb-2">
                          {msg.glosses.map((gloss, idx) => (
                            <span 
                              key={idx} 
                              className="bg-emerald-900/40 text-emerald-300 px-2 py-0.5 rounded text-[10px] font-mono border border-emerald-500/20"
                            >
                              {gloss}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* SIDE-BY-SIDE VIDEO PLAYERS */}
                      <div className="grid grid-cols-2 gap-2">
                        <div className="rounded-lg overflow-hidden bg-black relative border border-slate-700">
                          <span className="absolute top-1 left-2 text-[9px] text-emerald-400 font-bold bg-black/60 px-1 rounded z-10 uppercase">Video</span>
                          <video src={msg.videoUrl} controls autoPlay className="w-full h-auto" />
                        </div>
                        
                        <div className="rounded-lg overflow-hidden bg-black relative border border-slate-700">
                          <span className="absolute top-1 left-2 text-[9px] text-blue-400 font-bold bg-black/60 px-1 rounded z-10 uppercase">Skeleton</span>
                          {msg.skeletonUrl ? (
                            <video src={msg.skeletonUrl} controls autoPlay className="w-full h-auto" />
                          ) : (
                            <div className="h-full min-h-24 flex items-center justify-center text-[10px] text-blue-200 px-2 text-center bg-slate-900/70">
                              Skeleton unavailable on this machine
                            </div>
                          )}
                        </div>
                      </div>

                      {msg.skeletonError && (
                        <div className="text-[10px] text-yellow-200 bg-yellow-900/20 border border-yellow-700/40 rounded px-2 py-1">
                          {msg.skeletonError}
                        </div>
                      )}
                    </div>
                  ) : msg.isTranslating ? (
                    <div className="flex items-center justify-center gap-2 py-3 text-emerald-100 text-xs font-medium bg-emerald-700/30 rounded-lg animate-pulse">
                      <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Analyzing ASL Syntax...
                    </div>
                  ) : (
                    <button
                      onClick={() => generateASLVideo(msg.id, msg.text)}
                      className="w-full bg-emerald-600/20 hover:bg-emerald-600/40 text-emerald-400 text-xs font-bold py-2 rounded-lg transition-all border border-emerald-500/30 flex items-center justify-center gap-2"
                    >
                      ✨ Generate ASL Translation
                    </button>
                  )}

                  {msg.error && (
                    <div className="mt-2 text-[10px] text-red-200 bg-red-900/20 border border-red-700/40 rounded px-2 py-1">
                      {msg.error}
                    </div>
                  )}
                </div>
              )}
              
              <div className={`text-xs mt-1 flex items-center gap-1 ${
                msg.sender === "user" ? "text-emerald-100" : "text-gray-400"
              }`}>
                <span>{msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                {msg.sender === "user" && getStatusIcon(msg.status)}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer & Input */}
      <div className="bg-slate-900 px-4 py-3 border-t border-slate-700 flex items-center gap-3">
        <input
          type="text"
          value={textInput}
          onChange={(e) => setTextInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submitText();
          }}
          placeholder={recording ? "Listening..." : "Type text or tap mic to speak..."}
          className="flex-1 bg-slate-800 text-gray-300 rounded-full px-5 py-3 text-sm border border-slate-700 placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
        />

        <button
          onClick={submitText}
          disabled={!textInput.trim()}
          className="w-12 h-12 rounded-full flex items-center justify-center bg-blue-500 hover:bg-blue-600 disabled:bg-gray-600 disabled:cursor-not-allowed transition-all duration-300 active:scale-95 shadow-lg shadow-blue-500/30"
          title="Send text"
        >
          <Send size={18} className="text-white" />
        </button>
        
        <button
          onClick={recording ? stopRecording : startRecording}
          disabled={isConnecting}
          className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 font-semibold flex-shrink-0 ${
            isConnecting
              ? "bg-gray-600 cursor-not-allowed"
              : recording
              ? "bg-red-500 hover:bg-red-600 active:scale-95 shadow-lg shadow-red-500/50"
              : "bg-emerald-500 hover:bg-emerald-600 active:scale-95 shadow-lg shadow-emerald-500/50"
          }`}
          title={recording ? "Stop recording" : "Start recording"}
        >
          {isConnecting ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : recording ? (
            <div className="w-4 h-4 bg-white rounded-sm" />
          ) : (
            <Mic size={20} className="text-white" />
          )}
        </button>
      </div>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.3s ease-out; }
        .scrollbar-hide::-webkit-scrollbar { display: none; }
        .scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
      `}</style>
    </div>
  );
}