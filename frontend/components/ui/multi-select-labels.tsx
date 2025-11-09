"use client";

import * as React from "react";
import { Tag, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Dropdown, DropdownOption } from "./dropdown";

interface MultiSelectLabelsProps {
  selectedLabelIds: number[];
  availableLabels: Array<{ id: number; name: string; color?: string }>;
  onSelect: (labelId: number) => void;
  onRemove: (labelId: number) => void;
  placeholder?: string;
  className?: string;
}

export function MultiSelectLabels({
  selectedLabelIds,
  availableLabels,
  onSelect,
  onRemove,
  placeholder = "Labels",
  className,
}: MultiSelectLabelsProps) {
  const [isOpen, setIsOpen] = React.useState(false);

  const selectedLabels = availableLabels.filter((label) =>
    selectedLabelIds.includes(label.id)
  );

  const availableOptions: DropdownOption[] = availableLabels
    .filter((label) => !selectedLabelIds.includes(label.id))
    .map((label) => ({
      value: label.id.toString(),
      label: label.name,
      icon: Tag,
      description: label.name,
    }));

  const handleSelect = (value: string) => {
    const labelId = parseInt(value);
    if (labelId && !selectedLabelIds.includes(labelId)) {
      onSelect(labelId);
    }
    setIsOpen(false);
  };

  return (
    <div className={cn("relative", className)}>
      <div className="flex flex-wrap gap-2 items-center">
        {selectedLabels.map((label) => (
          <div
            key={label.id}
            className="inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium text-white"
            style={{
              backgroundColor: label.color || "#6b7280",
            }}
          >
            <Tag className="h-3 w-3" />
            <span>{label.name}</span>
            <button
              type="button"
              onClick={() => onRemove(label.id)}
              className="ml-1 hover:bg-black/20 rounded-full p-0.5"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        ))}
        <Dropdown
          options={availableOptions}
          value=""
          onSelect={handleSelect}
          placeholder={placeholder}
          icon={Tag}
          searchable={true}
          className="relative"
          buttonClassName={cn(
            "inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-100",
            selectedLabels.length === 0 && "text-slate-500"
          )}
        />
      </div>
    </div>
  );
}
