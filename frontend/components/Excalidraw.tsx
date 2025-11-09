"use client";

import { Excalidraw } from "@excalidraw/excalidraw";
import "@excalidraw/excalidraw/index.css";

export default function ExcalidrawComponent() {
    return (
        <div style={{ width: "100%", height: "650px" }}>
            <Excalidraw />
        </div>
    );
}