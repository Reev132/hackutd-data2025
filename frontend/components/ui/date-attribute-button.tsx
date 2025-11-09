"use client";

import * as React from "react";
import { Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

interface DateAttributeButtonProps {
  label: string;
  value?: string | null;
  onChange: (value: string | null) => void;
  placeholder?: string;
  className?: string;
}

export function DateAttributeButton({
  label,
  value,
  onChange,
  placeholder,
  className,
}: DateAttributeButtonProps) {
  const dateInputRef = React.useRef<HTMLInputElement>(null);

  // Convert date value to YYYY-MM-DD format for input
  const formatDateForInput = (dateValue: string | null | undefined): string => {
    if (!dateValue) return "";
    try {
      // If it's already in YYYY-MM-DD format, return as is
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
        return dateValue;
      }
      // Otherwise, parse and format
      const date = new Date(dateValue);
      if (isNaN(date.getTime())) return "";
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0");
      const day = String(date.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    } catch {
      return "";
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value || null);
  };

  const handleContainerClick = () => {
    // Trigger the date picker when container is clicked
    if (dateInputRef.current) {
      // Try showPicker first (modern browsers)
      if ("showPicker" in dateInputRef.current) {
        try {
          (dateInputRef.current as any).showPicker();
        } catch (err) {
          // Fallback: focus and click
          dateInputRef.current.focus();
          dateInputRef.current.click();
        }
      } else {
        // Fallback: focus and click
        dateInputRef.current.focus();
        dateInputRef.current.click();
      }
    }
  };

  const displayValue = value
    ? (() => {
        try {
          const date = new Date(value);
          if (isNaN(date.getTime())) return placeholder || label;
          return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          });
        } catch {
          return placeholder || label;
        }
      })()
    : placeholder || label;

  const inputValue = formatDateForInput(value);

  return (
    <div 
      className={cn("relative inline-block cursor-pointer", className)}
      onClick={handleContainerClick}
    >
      <div className="relative inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100 pointer-events-none">
        <Calendar className="h-4 w-4 shrink-0" />
        <span className={cn(!value && "text-slate-500")}>
          {displayValue}
        </span>
      </div>
      <input
        ref={dateInputRef}
        type="date"
        value={inputValue}
        onChange={handleChange}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        style={{ 
          zIndex: 10,
          fontSize: "16px"
        }}
        onClick={(e) => {
          e.stopPropagation();
          handleContainerClick();
        }}
      />
    </div>
  );
}
