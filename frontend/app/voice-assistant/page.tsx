"use client";

import { useState, useRef, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  Mic, 
  Square, 
  Upload, 
  FileAudio, 
  Loader2,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RecordingStatus = "idle" | "recording" | "processing";
type TranscriptionStep = "upload" | "transcribing" | "analyzing" | "planning" | "creating" | "complete";

interface Ticket {
  id: string;
  title: string;
  summary?: string;
  priority: string;
  assignee_id?: string;
  estimated_hours?: number;
  project_id?: string;
}

interface AnalysisResult {
  tickets: Ticket[];
  project: any;
  diagram?: string;
  summary: string;
  ticket_count: number;
}

export default function VoiceAssistantPage() {
  // Recording state
  const [recordingStatus, setRecordingStatus] = useState<RecordingStatus>("idle");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // File upload state
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Transcription state
  const [transcript, setTranscript] = useState<string>("");
  const [currentStep, setCurrentStep] = useState<TranscriptionStep>("upload");
  const [error, setError] = useState<string>("");

  // AI Analysis state
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Cleanup timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);
  
  // Start recording
  const startRecording = async () => {
    try {
      setError("");
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100,
        } 
      });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') 
          ? 'audio/webm' 
          : 'audio/mp4'
      });
      
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mediaRecorder.mimeType 
        });
        setAudioBlob(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
        
        // Stop timer
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
      };
      
      mediaRecorder.start(100); // Collect data every 100ms
      mediaRecorderRef.current = mediaRecorder;
      setRecordingStatus("recording");
      setRecordingTime(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
    } catch (err: any) {
      setError(`Failed to start recording: ${err.message}`);
      console.error("Recording error:", err);
    }
  };
  
  // Stop recording
  const stopRecording = () => {
    if (mediaRecorderRef.current && recordingStatus === "recording") {
      mediaRecorderRef.current.stop();
      setRecordingStatus("idle");
    }
  };
  
  // Handle file upload
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Check if it's an audio file
      if (!file.type.startsWith('audio/')) {
        setError("Please upload an audio file (MP3, WAV, M4A, etc.)");
        return;
      }
      setUploadedFile(file);
      setError("");
      setTranscript("");
    }
  };
  
  // Transcribe audio (either recorded or uploaded)
  const transcribeAudio = async () => {
    const fileToTranscribe = uploadedFile || audioBlob;
    
    if (!fileToTranscribe) {
      setError("No audio to transcribe. Please record or upload an audio file.");
      return;
    }
    
    try {
      setRecordingStatus("processing");
      setCurrentStep("transcribing");
      setError("");
      
      // Create form data
      const formData = new FormData();
      formData.append("file", fileToTranscribe, uploadedFile?.name || "recording.webm");
      
      // Send to backend
      const response = await fetch(`${API_URL}/api/voice/transcribe-file`, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Transcription failed");
      }
      
      const data = await response.json();
      
      console.log("Deepgram response:", data);
      
      // Set transcript
      setTranscript(data.transcript || "");
      
      // Only mark as complete if we got a transcript
      if (data.transcript && data.transcript.length > 0) {
        setCurrentStep("complete");
      } else {
        setError("No speech detected in the audio. Please try again.");
      }
      
      setRecordingStatus("idle");
      
    } catch (err: any) {
      setError(`Transcription failed: ${err.message}`);
      setRecordingStatus("idle");
      setCurrentStep("upload");
      console.error("Transcription error:", err);
    }
  };
  
  // Format recording time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  // Analyze transcript with AI
  const analyzeWithAI = async () => {
    if (!transcript) {
      setError("No transcript to analyze");
      return;
    }

    try {
      setIsAnalyzing(true);
      setCurrentStep("analyzing");
      setError("");

      console.log("Sending transcript to AI for analysis...");

      // Call backend API
      const response = await fetch(`${API_URL}/api/voice/process-meeting`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          transcript: transcript,
          project_name: null, // Let AI extract project name
        }),
      });

      // Read response once
      const responseData = await response.json();

      if (!response.ok) {
        const errorMessage = responseData.detail || responseData.message || JSON.stringify(responseData) || `Server error: ${response.status} ${response.statusText}`;
        throw new Error(errorMessage);
      }

      // Update step to planning
      setCurrentStep("planning");

      const data = responseData;

      console.log("AI analysis result:", data);

      // Update step to creating
      setCurrentStep("creating");

      // Short delay to show the creating step
      await new Promise(resolve => setTimeout(resolve, 500));

      // Set results
      setAnalysisResult(data);
      setCurrentStep("complete");
      setIsAnalyzing(false);

    } catch (err: any) {
      const errorMessage = err.message || String(err);
      setError(`AI analysis failed: ${errorMessage}`);
      setIsAnalyzing(false);
      setCurrentStep("upload");
      console.error("AI analysis error:", err);
    }
  };

  // Copy transcript to clipboard
  const copyTranscript = () => {
    navigator.clipboard.writeText(transcript);
  };

  // Reset everything
  const reset = () => {
    setAudioBlob(null);
    setUploadedFile(null);
    setTranscript("");
    setCurrentStep("upload");
    setError("");
    setRecordingTime(0);
    setAnalysisResult(null);
    setIsAnalyzing(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };
  
  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-semibold text-slate-900">Voice Assistant</h1>
            <p className="text-slate-500 mt-1">
              Record or upload meeting audio to automatically generate tickets and diagrams
            </p>
          </div>
        </div>
        
        {/* Recording & Upload Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Live Recording */}
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Mic className="w-5 h-5 text-blue-600" />
                Live Recording
              </h2>
              
              <div className="space-y-4">
                {recordingStatus === "idle" && !audioBlob && (
                  <Button
                    onClick={startRecording}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                    size="lg"
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    Start Recording
                  </Button>
                )}
                
                {recordingStatus === "recording" && (
                  <div className="space-y-4">
                    <div className="flex items-center justify-center">
                      <div className="relative">
                        <div className="w-24 h-24 rounded-full bg-red-100 flex items-center justify-center animate-pulse">
                          <Mic className="w-12 h-12 text-red-600" />
                        </div>
                        <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 bg-slate-900 text-white px-3 py-1 rounded text-sm font-mono">
                          {formatTime(recordingTime)}
                        </div>
                      </div>
                    </div>
                    
                    <Button
                      onClick={stopRecording}
                      variant="outline"
                      className="w-full border-red-300 text-red-600 hover:bg-red-50"
                      size="lg"
                    >
                      <Square className="w-4 h-4 mr-2" />
                      Stop Recording
                    </Button>
                  </div>
                )}
                
                {audioBlob && recordingStatus === "idle" && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-3 rounded">
                      <CheckCircle className="w-4 h-4" />
                      Recording saved ({formatTime(recordingTime)})
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={transcribeAudio}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                        disabled={recordingStatus === "processing"}
                      >
                        {recordingStatus === "processing" ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Transcribing...
                          </>
                        ) : (
                          "Transcribe"
                        )}
                      </Button>
                      
                      <Button
                        onClick={reset}
                        variant="outline"
                        disabled={recordingStatus === "processing"}
                      >
                        Reset
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
          
          {/* File Upload */}
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Upload className="w-5 h-5 text-blue-600" />
                Upload Audio File
              </h2>
              
              <div className="space-y-4">
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors"
                >
                  <FileAudio className="w-12 h-12 text-slate-400 mx-auto mb-3" />
                  <p className="text-sm text-slate-600 mb-1">
                    Click to upload or drag and drop
                  </p>
                  <p className="text-xs text-slate-400">
                    MP3, WAV, M4A, WebM (max 100MB)
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                </div>
                
                {uploadedFile && (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded">
                      <FileAudio className="w-4 h-4" />
                      {uploadedFile.name}
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={transcribeAudio}
                        className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                        disabled={recordingStatus === "processing"}
                      >
                        {recordingStatus === "processing" ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            Transcribing...
                          </>
                        ) : (
                          "Transcribe"
                        )}
                      </Button>
                      
                      <Button
                        onClick={reset}
                        variant="outline"
                        disabled={recordingStatus === "processing"}
                      >
                        Reset
                      </Button>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Error Display */}
        {error && (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-900">Error</p>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Transcript Display */}
        {transcript && (
          <Card>
            <CardContent className="p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Transcript</h2>
              <div className="bg-slate-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                <p className="text-slate-700 whitespace-pre-wrap leading-relaxed">
                  {transcript}
                </p>
              </div>
              
              {/* AI Analysis Actions */}
              <div className="mt-4 flex gap-3">
                <Button
                  onClick={analyzeWithAI}
                  disabled={isAnalyzing}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    "Analyze with AI"
                  )}
                </Button>
                <Button variant="outline" onClick={copyTranscript}>
                  Copy Transcript
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* AI Analysis Results */}
        {analysisResult && (
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-900">Generated Tickets</h2>
                <div className="text-sm text-green-600 bg-green-50 px-3 py-1 rounded flex items-center gap-2">
                  <CheckCircle className="w-4 h-4" />
                  {analysisResult.summary}
                </div>
              </div>

              {/* Tickets List */}
              <div className="space-y-3">
                {analysisResult.tickets && analysisResult.tickets.length > 0 ? (
                  analysisResult.tickets.map((ticket, idx) => (
                  <div key={ticket.id} className="border border-slate-200 rounded-lg p-4 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-mono text-slate-500">#{idx + 1}</span>
                          <h3 className="font-medium text-slate-900">{ticket.title}</h3>
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            ticket.priority === 'urgent' ? 'bg-red-100 text-red-700' :
                            ticket.priority === 'high' ? 'bg-orange-100 text-orange-700' :
                            ticket.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                            ticket.priority === 'low' ? 'bg-green-100 text-green-700' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {ticket.priority}
                          </span>
                        </div>
                        {ticket.summary && (
                          <p className="text-sm text-slate-600 line-clamp-2">{ticket.summary}</p>
                        )}
                        {ticket.estimated_hours && (
                          <p className="text-xs text-slate-500 mt-2">
                            Estimated: {ticket.estimated_hours}h
                          </p>
                        )}
                      </div>
                      <a
                        href={`/tickets`}
                        className="text-sm text-blue-600 hover:text-blue-700 hover:underline ml-4"
                      >
                        View →
                      </a>
                    </div>
                  </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    <p>No tickets were extracted from this meeting.</p>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="mt-6 flex gap-3">
                <Button
                  onClick={() => window.location.href = "/tickets"}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  View All Tickets
                </Button>
                {analysisResult.diagram && (
                  <Button
                    onClick={() => {
                      // Store diagram in sessionStorage and navigate to board
                      sessionStorage.setItem('meeting_diagram', analysisResult.diagram || '');
                      window.location.href = "/board";
                    }}
                    variant="outline"
                  >
                    View Diagram
                  </Button>
                )}
                <Button
                  onClick={reset}
                  variant="outline"
                >
                  Start New Analysis
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Processing Steps Indicator */}
        {(recordingStatus === "processing" || isAnalyzing || currentStep !== "upload") && currentStep !== "complete" && (
          <Card>
            <CardContent className="p-6">
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Processing</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  {currentStep === "transcribing" ? (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  ) : ["analyzing", "planning", "creating", "complete"].includes(currentStep) ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                  )}
                  <span className={`text-sm ${
                    currentStep === "transcribing" ? "text-blue-600 font-medium" :
                    ["analyzing", "planning", "creating", "complete"].includes(currentStep) ? "text-green-600" :
                    "text-slate-400"
                  }`}>
                    Transcribing audio...
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  {currentStep === "analyzing" ? (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  ) : ["planning", "creating", "complete"].includes(currentStep) ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                  )}
                  <span className={`text-sm ${
                    currentStep === "analyzing" ? "text-blue-600 font-medium" :
                    ["planning", "creating", "complete"].includes(currentStep) ? "text-green-600" :
                    "text-slate-400"
                  }`}>
                    Analyzing meeting content...
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  {currentStep === "planning" ? (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  ) : ["creating", "complete"].includes(currentStep) ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                  )}
                  <span className={`text-sm ${
                    currentStep === "planning" ? "text-blue-600 font-medium" :
                    ["creating", "complete"].includes(currentStep) ? "text-green-600" :
                    "text-slate-400"
                  }`}>
                    Planning tasks...
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  {currentStep === "creating" ? (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  ) : currentStep === "complete" ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                  )}
                  <span className={`text-sm ${
                    currentStep === "creating" ? "text-blue-600 font-medium" :
                    currentStep === "complete" ? "text-green-600" :
                    "text-slate-400"
                  }`}>
                    Creating tickets...
                  </span>
                </div>
                
                <div className="flex items-center gap-3">
                  {currentStep === "complete" ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <div className="w-5 h-5 rounded-full border-2 border-slate-300" />
                  )}
                  <span className={`text-sm ${
                    currentStep === "complete" ? "text-green-600 font-medium" : "text-slate-400"
                  }`}>
                    Complete!
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

