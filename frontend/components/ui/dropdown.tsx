"use client";

import * as React from "react";
import { Search, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface DropdownOption {
  value: string;
  label: string;
  icon?: React.ComponentType<{ className?: string }>;
  description?: string;
}

interface DropdownProps {
  options: DropdownOption[];
  value?: string;
  onSelect: (value: string) => void;
  placeholder?: string;
  searchable?: boolean;
  className?: string;
  buttonClassName?: string;
  icon?: React.ComponentType<{ className?: string }>;
  label?: string;
}

export function Dropdown({
  options,
  value,
  onSelect,
  placeholder = "Select...",
  searchable = true,
  className,
  buttonClassName,
  icon: Icon,
  label,
}: DropdownProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [searchQuery, setSearchQuery] = React.useState("");
  const dropdownRef = React.useRef<HTMLDivElement>(null);

  const selectedOption = options.find((opt) => opt.value === value);

  const filteredOptions = searchable
    ? options.filter((opt) =>
        opt.label.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : options;

  React.useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
        setSearchQuery("");
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  const handleSelect = (optionValue: string) => {
    onSelect(optionValue);
    setIsOpen(false);
    setSearchQuery("");
  };

  return (
    <div ref={dropdownRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border border-border bg-muted px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted/80",
          selectedOption && "bg-muted",
          buttonClassName
        )}
      >
        {Icon && <Icon className="h-4 w-4" />}
        {selectedOption ? (
          <>
            {selectedOption.icon && (
              <selectedOption.icon className="h-4 w-4" />
            )}
            <span>{selectedOption.label}</span>
          </>
        ) : (
          <span className="text-muted-foreground">
            {label || placeholder}
          </span>
        )}
        <ChevronDown className="h-4 w-4 opacity-50" />
      </button>

      {isOpen && (
        <div className="absolute left-0 top-full z-50 mt-1 w-full min-w-[200px] rounded-md border border-slate-200 bg-white shadow-lg">
          {searchable && (
            <div className="border-b border-slate-200 p-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full rounded-md bg-slate-50 px-8 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      setIsOpen(false);
                      setSearchQuery("");
                    }
                  }}
                />
              </div>
            </div>
          )}
          <div className="max-h-[300px] overflow-y-auto p-1">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-2 text-sm text-slate-500">
                No options found
              </div>
            ) : (
              filteredOptions.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleSelect(option.value)}
                  className={cn(
                    "w-full flex items-center gap-2 rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-slate-100",
                    value === option.value
                      ? "bg-slate-100 text-slate-900"
                      : "text-slate-700"
                  )}
                >
                  {option.icon && <option.icon className="h-4 w-4 shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{option.label}</div>
                    {option.description && option.description !== option.label && (
                      <div className="text-xs text-slate-500 truncate">
                        {option.description}
                      </div>
                    )}
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
