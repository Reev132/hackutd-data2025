"use client";

import { Card, CardContent } from "@/components/ui/card";
import ExcalidrawComponent from "@/components/Excalidraw";
import AIPromptInput from "@/components/PromptInput";
import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function DrawingBoardPage() {
    const [mermaidCode, setMermaidCode] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load diagram from session storage if available (from voice assistant)
    useEffect(() => {
        const savedDiagram = sessionStorage.getItem('meeting_diagram');
        if (savedDiagram && savedDiagram.trim()) {
            setMermaidCode(savedDiagram);
            // Clear after loading
            sessionStorage.removeItem('meeting_diagram');
        }
    }, []);

    const handlePromptSubmit = async (prompt: string) => {
        setIsGenerating(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_URL}/mermaid/generate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ prompt }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "Failed to generate diagram");
            }

            const data = await response.json();
            setMermaidCode(data.mermaid);
        } catch (err) {
            console.error("Error generating Mermaid diagram:", err);
            setError(err instanceof Error ? err.message : "Failed to generate diagram");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                <Card>
                    <CardContent className="p-6">
                        <ExcalidrawComponent mermaidCode={mermaidCode} />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <AIPromptInput
                            onSubmit={handlePromptSubmit}
                            placeholder="Describe what you want to draw (e.g., 'A user logs in, then views dashboard')..."
                            disabled={isGenerating}
                        />
                        {error && (
                            <div className="mt-4 p-3 bg-destructive/10 text-destructive rounded-md text-sm">
                                {error}
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}