"use client";

import { Card, CardContent } from "@/components/ui/card";
import ExcalidrawComponent from "@/components/Excalidraw";
import AIPromptInput from "@/components/PromptInput";

export default function DrawingBoardPage() {
    const handlePromptSubmit = (prompt: string) => {
        console.log("AI Prompt submitted:", prompt);
        // TODO: Implement AI prompt handling logic here
    };

    return (
        <div className="min-h-screen bg-background p-6">
            <div className="max-w-7xl mx-auto space-y-6">

                <Card>
                    <CardContent className="p-6">
                        <ExcalidrawComponent />
                    </CardContent>
                </Card>
                <Card>
                    <CardContent className="p-6">
                        <AIPromptInput
                            onSubmit={handlePromptSubmit}
                            placeholder="Describe what you want to draw..."
                        />
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}