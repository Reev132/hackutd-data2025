"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to voice assistant page
    router.push("/voice-assistant");
  }, [router]);
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-slate-500">Redirecting to Voice Assistant...</p>
    </div>
  );
}
