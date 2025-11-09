"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface User {
  id: number;
  name: string;
  email?: string;
  avatar_url?: string | null;
  initials?: string;
  color?: string;
}

interface UserAvatarProps {
  user: User | null | undefined;
  size?: "sm" | "md" | "lg";
  className?: string;
  showName?: boolean;
}

// Generate consistent color based on user ID
const getUserColor = (userId: number): string => {
  const colors = [
    "#3b82f6", // blue
    "#22c55e", // green
    "#a855f7", // purple
    "#f97316", // orange
    "#ec4899", // pink
    "#06b6d4", // cyan
    "#eab308", // yellow
    "#6366f1", // indigo
    "#14b8a6", // teal
    "#f43f5e", // rose
    "#f59e0b", // amber
    "#10b981", // emerald
    "#8b5cf6", // violet
    "#d946ef", // fuchsia
    "#0ea5e9", // sky
    "#84cc16", // lime
  ];
  return colors[userId % colors.length];
};

// Generate initials from name
const getInitials = (name: string): string => {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

export function UserAvatar({ user, size = "md", className, showName = false }: UserAvatarProps) {
  if (!user) {
    return (
      <div
        className={cn(
          "rounded-full bg-slate-200 flex items-center justify-center text-slate-500",
          size === "sm" && "w-6 h-6 text-xs",
          size === "md" && "w-8 h-8 text-sm",
          size === "lg" && "w-10 h-10 text-base",
          className
        )}
      >
        ?
      </div>
    );
  }

  const initials = user.initials || getInitials(user.name);
  const color = user.color || getUserColor(user.id);
  const sizeClasses = {
    sm: "w-6 h-6 text-xs",
    md: "w-8 h-8 text-sm",
    lg: "w-10 h-10 text-base",
  };

  return (
    <div className={cn("flex items-center gap-2", className)}>
      {user.avatar_url ? (
        <img
          src={user.avatar_url}
          alt={user.name}
          className={cn("rounded-full object-cover", sizeClasses[size])}
        />
      ) : (
        <div
          className={cn(
            "rounded-full flex items-center justify-center text-white font-medium",
            sizeClasses[size]
          )}
          style={{ backgroundColor: color }}
        >
          {initials}
        </div>
      )}
      {showName && <span className="text-sm text-slate-700">{user.name}</span>}
    </div>
  );
}


