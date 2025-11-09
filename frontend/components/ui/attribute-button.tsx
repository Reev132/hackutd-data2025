"use client";

import * as React from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import { Dropdown, DropdownOption } from "./dropdown";

interface AttributeButtonProps {
  label: string;
  value?: string;
  options: DropdownOption[];
  onSelect: (value: string) => void;
  icon?: React.ComponentType<{ className?: string }>;
  placeholder?: string;
  className?: string;
}

export function AttributeButton({
  label,
  value,
  options,
  onSelect,
  icon: Icon,
  placeholder,
  className,
}: AttributeButtonProps) {
  const selectedOption = options.find((opt) => opt.value === value);

  return (
    <Dropdown
      options={options}
      value={value}
      onSelect={onSelect}
      placeholder={placeholder || label}
      icon={Icon}
      label={selectedOption ? selectedOption.label : label}
      className={cn("relative", className)}
      buttonClassName={cn(
        "inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100",
        !selectedOption && "text-slate-500"
      )}
    />
  );
}
