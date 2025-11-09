"use client";

import { useState, useMemo, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  ChevronLeft, 
  ChevronRight, 
  Plus, 
  Search, 
  Filter, 
  Upload, 
  List,
  RefreshCw,
  Maximize2,
} from "lucide-react";
import { AttributeButton } from "@/components/ui/attribute-button";
import { DropdownOption } from "@/components/ui/dropdown";
import { UserAvatar, User } from "@/components/ui/user-avatar";

// Backend types matching tickets page
type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
type Priority = "urgent" | "high" | "medium" | "low" | "none";

interface Ticket {
  id: string; // Firestore uses string IDs
  title: string;
  summary: string | null;
  start_date: string | null;
  end_date: string | null;
  assignee: string | null; // Keep for backward compatibility
  assignee_id?: string | null;
  status: TicketStatus;
  priority: Priority;
  estimated_hours?: number | null;
  project_id?: string | null;
  cycle_id?: string | null;
  module_id?: string | null;
  parent_ticket_id?: string | null;
  created_at: string;
  updated_at: string;
  project?: { id: string; name: string; identifier: string };
  cycle?: { id: string; name: string; start_date: string; end_date: string };
  module?: { id: string; name: string };
  labels?: Array<{ id: string; name: string; color?: string }>;
  assignee_user?: User | null;
}

interface Project {
  id: string; // Firestore uses string IDs
  name: string;
  identifier: string;
  description?: string;
}

interface CalendarEvent {
  id: string;
  title: string;
  date: string;
  hours: number;
  color: string;
  assignee?: string | null; // Keep for backward compatibility
  assignee_user?: User | null;
  status: TicketStatus;
  ticketId: string; // Firestore uses string IDs
  project?: { id: string; name: string; identifier: string };
}

// Expanded color palette for more visual variety
const COLOR_PALETTE = [
  { className: "bg-blue-500", hex: "#3b82f6" },
  { className: "bg-green-500", hex: "#22c55e" },
  { className: "bg-purple-500", hex: "#a855f7" },
  { className: "bg-orange-500", hex: "#f97316" },
  { className: "bg-pink-500", hex: "#ec4899" },
  { className: "bg-cyan-500", hex: "#06b6d4" },
  { className: "bg-yellow-500", hex: "#eab308" },
  { className: "bg-indigo-500", hex: "#6366f1" },
  { className: "bg-teal-500", hex: "#14b8a6" },
  { className: "bg-rose-500", hex: "#f43f5e" },
  { className: "bg-amber-500", hex: "#f59e0b" },
  { className: "bg-emerald-500", hex: "#10b981" },
  { className: "bg-violet-500", hex: "#8b5cf6" },
  { className: "bg-fuchsia-500", hex: "#d946ef" },
  { className: "bg-sky-500", hex: "#0ea5e9" },
  { className: "bg-lime-500", hex: "#84cc16" },
  { className: "bg-red-500", hex: "#ef4444" },
  { className: "bg-blue-600", hex: "#2563eb" },
  { className: "bg-green-600", hex: "#16a34a" },
  { className: "bg-purple-600", hex: "#9333ea" },
];

// Helper function to get color based on label, priority, status, or hash-based assignment
const getEventColor = (ticket: Ticket): { className: string; style?: React.CSSProperties } => {
  // First try to use label color (use inline style for hex colors)
  if (ticket.labels && ticket.labels.length > 0 && ticket.labels[0].color) {
    const labelColor = ticket.labels[0].color;
    // If it's a hex color, use inline style
    if (labelColor.startsWith("#")) {
      return {
        className: "",
        style: { backgroundColor: labelColor }
      };
    }
    // Otherwise try to map common color names
    const colorMap: Record<string, string> = {
      "cyan": "bg-cyan-500",
      "purple": "bg-purple-500",
      "yellow": "bg-yellow-500",
      "green": "bg-green-500",
      "red": "bg-red-500",
      "blue": "bg-blue-500",
      "orange": "bg-orange-500",
      "pink": "bg-pink-500",
      "indigo": "bg-indigo-500",
      "teal": "bg-teal-500",
      "lime": "bg-lime-500",
      "amber": "bg-amber-500",
      "emerald": "bg-emerald-500",
      "sky": "bg-sky-500",
      "violet": "bg-violet-500",
      "fuchsia": "bg-fuchsia-500",
      "rose": "bg-rose-500",
    };
    return { className: colorMap[labelColor.toLowerCase()] || "bg-slate-500" };
  }
  
  // Fallback to priority-based colors with variety
  switch (ticket.priority) {
    case "urgent":
      return { className: "bg-red-500" };
    case "high":
      return { className: "bg-orange-500" };
    case "medium":
      return { className: "bg-yellow-500" };
    case "low":
      return { className: "bg-blue-300" };
    default:
      // Use hash-based color assignment for consistent coloring per ticket
      // This ensures the same ticket always gets the same color
      // Convert string ID to hash number
      const hashString = (str: string) => {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
          hash = ((hash << 5) - hash) + str.charCodeAt(i);
          hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash);
      };
      
      const hash = hashString(ticket.id) % COLOR_PALETTE.length;
      const color = COLOR_PALETTE[hash];
      
      // But still consider status for some variation
      switch (ticket.status) {
        case "open":
          return { className: color.className };
        case "in_progress":
          // Use a slightly different shade for in-progress
          const inProgressIndex = (hash + 1) % COLOR_PALETTE.length;
          return { className: COLOR_PALETTE[inProgressIndex].className };
        case "resolved":
          return { className: "bg-green-500" };
        case "closed":
          return { className: "bg-slate-600" };
        default:
          return { className: color.className };
      }
  }
};

export default function CalendarPage() {
  const router = useRouter();
  const pathname = usePathname();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedProject, setSelectedProject] = useState<string>("");
  const [selectedAssignee, setSelectedAssignee] = useState<string>("");
  const [selectedStatus, setSelectedStatus] = useState<string>("");
  const [selectedPlanned, setSelectedPlanned] = useState<string>("");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch tickets and projects
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      await Promise.all([fetchTickets(), fetchProjects(), fetchUsers()]);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTickets = async () => {
    try {
      const response = await fetch(`${API_URL}/tickets/`);
      if (!response.ok) throw new Error("Failed to fetch tickets");
      const data = await response.json();
      setTickets(data.tickets || []);
    } catch (error) {
      console.error("Error fetching tickets:", error);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      const data = await response.json();
      setProjects(data.projects || []);
    } catch (error) {
      console.error("Error fetching projects:", error);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${API_URL}/users/`);
      if (!response.ok) throw new Error("Failed to fetch users");
      const data = await response.json();
      setUsers(data.users || []);
    } catch (error) {
      console.error("Error fetching users:", error);
    }
  };

  // Convert tickets to calendar events
  const events: CalendarEvent[] = useMemo(() => {
    const eventMap = new Map<string, CalendarEvent[]>();

    tickets.forEach((ticket) => {
      // Only include tickets with start_date or end_date
      if (!ticket.start_date && !ticket.end_date) return;

      const hours = ticket.estimated_hours || 8; // Default to 8 hours if not specified
      const color = getEventColor(ticket);
      
      // If ticket has start_date, create event for that date
      if (ticket.start_date) {
        const dateStr = ticket.start_date.split("T")[0]; // Get YYYY-MM-DD part
        if (!eventMap.has(dateStr)) {
          eventMap.set(dateStr, []);
        }
        eventMap.get(dateStr)!.push({
          id: `start-${ticket.id}`,
          title: ticket.title.length > 20 ? ticket.title.substring(0, 17) + "..." : ticket.title,
          date: dateStr,
          hours,
          color,
          assignee: ticket.assignee, // Keep for backward compatibility
          assignee_user: ticket.assignee_user,
          status: ticket.status,
          ticketId: ticket.id,
          project: ticket.project,
        });
      }

      // If ticket has end_date and it's different from start_date, also show it
      if (ticket.end_date && ticket.end_date !== ticket.start_date) {
        const dateStr = ticket.end_date.split("T")[0];
        if (!eventMap.has(dateStr)) {
          eventMap.set(dateStr, []);
        }
        // Only add if not already added (avoid duplicates)
        const existing = eventMap.get(dateStr)!.find(e => e.ticketId === ticket.id);
        if (!existing) {
          eventMap.get(dateStr)!.push({
            id: `end-${ticket.id}`,
            title: ticket.title.length > 20 ? ticket.title.substring(0, 17) + "..." : ticket.title,
            date: dateStr,
            hours,
            color,
            assignee: ticket.assignee, // Keep for backward compatibility
            assignee_user: ticket.assignee_user,
            status: ticket.status,
            ticketId: ticket.id,
            project: ticket.project,
          });
        }
      }
    });

    // Flatten the map to array
    const allEvents: CalendarEvent[] = [];
    eventMap.forEach((events) => {
      allEvents.push(...events);
    });

    return allEvents;
  }, [tickets]);

  // Filter tickets for issues sidebar
  const filteredIssues = useMemo(() => {
    return tickets.filter((ticket) => {
      const matchesSearch = searchQuery === "" || 
        ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        ticket.project?.identifier.toLowerCase().includes(searchQuery.toLowerCase());
      const matchesProject = selectedProject === "" || 
        ticket.project_id?.toString() === selectedProject;
      const matchesAssignee = selectedAssignee === "" || 
        ticket.assignee_id?.toString() === selectedAssignee ||
        ticket.assignee_user?.id.toString() === selectedAssignee;
      const matchesStatus = selectedStatus === "" || 
        ticket.status === selectedStatus;
      const matchesPlanned = selectedPlanned === "" || 
        (selectedPlanned === "yes" && (ticket.start_date || ticket.end_date)) ||
        (selectedPlanned === "no" && !ticket.start_date && !ticket.end_date);
      
      return matchesSearch && matchesProject && matchesAssignee && matchesStatus && matchesPlanned;
    });
  }, [tickets, searchQuery, selectedProject, selectedAssignee, selectedStatus, selectedPlanned]);

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    // Get days from previous month to fill the first week
    const prevMonthLastDay = new Date(year, month, 0).getDate();
    const prevMonthDays: number[] = [];
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
      prevMonthDays.push(prevMonthLastDay - i);
    }

    // Get days from next month to fill the last week
    const totalCells = Math.ceil((startingDayOfWeek + daysInMonth) / 7) * 7;
    const nextMonthDays = totalCells - (startingDayOfWeek + daysInMonth);
    const nextMonthDaysArray: number[] = [];
    for (let i = 1; i <= nextMonthDays; i++) {
      nextMonthDaysArray.push(i);
    }

    return { daysInMonth, startingDayOfWeek, prevMonthDays, nextMonthDays: nextMonthDaysArray };
  };

  const { daysInMonth, startingDayOfWeek, prevMonthDays, nextMonthDays } = getDaysInMonth(currentDate);

  const getEventsForDate = (dateStr: string) => {
    return events.filter((event) => event.date === dateStr);
  };

  const formatDateString = (year: number, month: number, day: number): string => {
    return `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  };

  const navigateMonth = (direction: "prev" | "next") => {
    setCurrentDate((prev) => {
      const newDate = new Date(prev);
      if (direction === "prev") {
        newDate.setMonth(prev.getMonth() - 1);
      } else {
        newDate.setMonth(prev.getMonth() + 1);
      }
      return newDate;
    });
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const isToday = (year: number, month: number, day: number): boolean => {
    const today = new Date();
    return (
      today.getFullYear() === year &&
      today.getMonth() === month &&
      today.getDate() === day
    );
  };

  const monthNames = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ];

  const dayNames = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];

  const viewOptions: DropdownOption[] = [
    { value: "month", label: "Month" },
    { value: "week", label: "Week" },
    { value: "day", label: "Day" },
  ];

  const projectOptions: DropdownOption[] = useMemo(() => {
    const options: DropdownOption[] = [{ value: "", label: "All Projects" }];
    projects.forEach((project) => {
      options.push({ value: project.id.toString(), label: project.name });
    });
    return options;
  }, [projects]);

  const assigneeOptions: DropdownOption[] = useMemo(() => {
    const options: DropdownOption[] = [{ value: "", label: "All Assignees" }];
    users.forEach((user) => {
      options.push({ value: user.id.toString(), label: user.name });
    });
    return options;
  }, [users]);

  const statusOptions: DropdownOption[] = [
    { value: "", label: "All Statuses" },
    { value: "open", label: "Open" },
    { value: "in_progress", label: "In Progress" },
    { value: "resolved", label: "Resolved" },
    { value: "closed", label: "Closed" },
  ];

  const plannedOptions: DropdownOption[] = [
    { value: "", label: "All" },
    { value: "yes", label: "Planned" },
    { value: "no", label: "Not Planned" },
  ];

  const getStatusDisplay = (status: TicketStatus): string => {
    const statusMap: Record<TicketStatus, string> = {
      open: "OPEN",
      in_progress: "IN PROGRESS",
      resolved: "RESOLVED",
      closed: "CLOSED",
    };
    return statusMap[status] || status.toUpperCase();
  };

  return (
    <div className="min-h-screen bg-white">
      <div className="flex h-screen">
        {/* Main Calendar Area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Top Navigation */}
          <div className="border-b border-slate-200 px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <h1 className="text-xl font-semibold text-slate-900">Planner</h1>
                <div className="flex items-center gap-4 text-sm text-slate-600">
                  <button className="hover:text-slate-900">Your work</button>
                  <button className="text-blue-600 font-medium">Projects</button>
                  <button className="hover:text-slate-900">Filters</button>
                  <button className="hover:text-slate-900">Dashboards</button>
                  <button className="hover:text-slate-900">Teams</button>
                  <button className="hover:text-slate-900">Plans</button>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Button className="bg-blue-600 text-white hover:bg-blue-700 rounded-md px-4 py-2 text-sm font-medium">
                  Create
                </Button>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  <Input
                    placeholder="Search"
                    className="pl-9 w-64 border-slate-200"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Sub Navigation */}
          <div className="border-b border-slate-200 px-6 py-3">
            <div className="flex items-center gap-6 text-sm">
              <button 
                onClick={() => router.push("/schedule")}
                className="text-slate-600 hover:text-slate-900"
              >
                Schedule
              </button>
              <button className="text-blue-600 font-medium border-b-2 border-blue-600 pb-1">
                Calendar
              </button>
              <button 
                onClick={() => router.push("/timeline")}
                className="text-slate-600 hover:text-slate-900"
              >
                Timeline
              </button>
            </div>
          </div>

          {/* Calendar Controls */}
          <div className="border-b border-slate-200 px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => navigateMonth("prev")}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <h2 className="text-lg font-semibold text-slate-900 min-w-[140px]">
                  {monthNames[currentDate.getMonth()]}, {currentDate.getFullYear()}
                </h2>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => navigateMonth("next")}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-600">
                <div className="flex items-center gap-1">
                  <div className="w-6 h-6 rounded-full bg-blue-500"></div>
                  <div className="w-6 h-6 rounded-full bg-green-500 -ml-2"></div>
                  <div className="w-6 h-6 rounded-full bg-purple-500 -ml-2"></div>
                </div>
                <span>TLDE LN +4</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={goToToday} className="border-slate-200 text-slate-700">
                Today
              </Button>
              <AttributeButton
                label="Month"
                value="month"
                options={viewOptions}
                onSelect={() => {}}
                placeholder="Mo..."
              />
              <Button variant="outline" size="sm" className="border-slate-200 text-slate-700">
                <Upload className="h-4 w-4 mr-2" />
                Export
              </Button>
              <Button variant="outline" size="sm" className="border-slate-200 text-slate-700">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </Button>
              <Button variant="outline" size="sm" className="border-slate-200 text-slate-700">
                <List className="h-4 w-4 mr-2" />
                Issues
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <Maximize2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Calendar Grid */}
          <div className="flex-1 overflow-auto p-6">
            <div className="grid grid-cols-7 gap-px bg-slate-200 border border-slate-200">
              {/* Day Headers */}
              {dayNames.map((day) => (
                <div
                  key={day}
                  className="bg-white p-2 text-center text-xs font-medium text-slate-600 uppercase"
                >
                  {day}
                </div>
              ))}

              {/* Calendar Cells */}
              {(() => {
                const year = currentDate.getFullYear();
                const month = currentDate.getMonth();
                const cells: JSX.Element[] = [];

                // Previous month days
                const prevYear = month === 0 ? year - 1 : year;
                const prevMonth = month === 0 ? 11 : month - 1;
                prevMonthDays.forEach((day) => {
                  const dateStr = formatDateString(prevYear, prevMonth, day);
                  const dayEvents = getEventsForDate(dateStr);
                  cells.push(
                    <CalendarCell
                      key={`prev-${day}`}
                      day={day}
                      dateStr={dateStr}
                      events={dayEvents}
                      isCurrentMonth={false}
                      isToday={isToday(prevYear, prevMonth, day)}
                      onClick={() => {}}
                      tickets={tickets}
                    />
                  );
                });

                // Current month days
                for (let day = 1; day <= daysInMonth; day++) {
                  const dateStr = formatDateString(year, month, day);
                  const dayEvents = getEventsForDate(dateStr);
                  cells.push(
                    <CalendarCell
                      key={day}
                      day={day}
                      dateStr={dateStr}
                      events={dayEvents}
                      isCurrentMonth={true}
                      isToday={isToday(year, month, day)}
                      onClick={() => {}}
                      tickets={tickets}
                    />
                  );
                }

                // Next month days
                const nextYear = month === 11 ? year + 1 : year;
                const nextMonth = month === 11 ? 0 : month + 1;
                nextMonthDays.forEach((day) => {
                  const dateStr = formatDateString(nextYear, nextMonth, day);
                  const dayEvents = getEventsForDate(dateStr);
                  cells.push(
                    <CalendarCell
                      key={`next-${day}`}
                      day={day}
                      dateStr={dateStr}
                      events={dayEvents}
                      isCurrentMonth={false}
                      isToday={isToday(nextYear, nextMonth, day)}
                      onClick={() => {}}
                      tickets={tickets}
                    />
                  );
                });

                return cells;
              })()}
            </div>
          </div>
        </div>

        {/* Right Sidebar - Issues */}
        <div className="w-80 border-l border-slate-200 bg-white flex flex-col">
          {/* Tabs */}
          <div className="border-b border-slate-200 flex">
            <button className="flex-1 px-4 py-3 text-sm font-medium text-slate-900 border-b-2 border-blue-600">
              Basic
            </button>
            <button className="flex-1 px-4 py-3 text-sm font-medium text-slate-600 hover:text-slate-900">
              JQL
            </button>
          </div>

          {/* Search and Filters */}
          <div className="p-4 border-b border-slate-200 space-y-3">
            <Input
              placeholder="Enter summary or issue key"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="border-slate-200"
            />
            <div className="space-y-2">
              <AttributeButton
                label="Project"
                value={selectedProject}
                options={projectOptions}
                onSelect={setSelectedProject}
                placeholder="Project"
              />
              <AttributeButton
                label="Assignee"
                value={selectedAssignee}
                options={assigneeOptions}
                onSelect={setSelectedAssignee}
                placeholder="Assignee"
              />
              <AttributeButton
                label="Status"
                value={selectedStatus}
                options={statusOptions}
                onSelect={setSelectedStatus}
                placeholder="Status"
              />
              <AttributeButton
                label="Planned?"
                value={selectedPlanned}
                options={plannedOptions}
                onSelect={setSelectedPlanned}
                placeholder="Planned?"
              />
            </div>
            <Button className="w-full bg-blue-600 text-white hover:bg-blue-700">
              Search
            </Button>
          </div>

          {/* Issues List */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4 border-b border-slate-200 text-sm text-slate-600">
              {filteredIssues.length}/{tickets.length}
            </div>
            <div className="divide-y divide-slate-200">
              {loading ? (
                <div className="p-4 text-sm text-slate-500 text-center">Loading...</div>
              ) : filteredIssues.length === 0 ? (
                <div className="p-4 text-sm text-slate-500 text-center">No tickets found</div>
              ) : (
                filteredIssues.map((ticket) => (
                  <div
                    key={ticket.id}
                    className="p-3 hover:bg-slate-50 cursor-pointer flex items-center gap-3"
                  >
                    <div 
                      className={`w-4 h-4 rounded flex-shrink-0 ${getEventColor(ticket).className}`}
                      style={getEventColor(ticket).style}
                    ></div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm text-slate-900 truncate">
                        {ticket.project?.identifier ? `${ticket.project.identifier}-${ticket.id}` : `TICKET-${ticket.id}`} {ticket.title}
                      </div>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge
                          variant="secondary"
                          className="text-xs bg-slate-100 text-slate-700 border-0"
                        >
                          {getStatusDisplay(ticket.status)}
                        </Badge>
                        {ticket.assignee_user && (
                          <UserAvatar user={ticket.assignee_user} size="sm" />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Calendar Cell Component
function CalendarCell({
  day,
  dateStr,
  events,
  isCurrentMonth,
  isToday,
  onClick,
  tickets,
}: {
  day: number;
  dateStr: string;
  events: CalendarEvent[];
  isCurrentMonth: boolean;
  isToday: boolean;
  onClick: () => void;
  tickets: Ticket[];
}) {
  const MAX_VISIBLE_EVENTS = 3;
  const [hoveredEvent, setHoveredEvent] = useState<CalendarEvent | null>(null);
  const [hoverPosition, setHoverPosition] = useState({ x: 0, y: 0 });

  const handleEventMouseEnter = (event: CalendarEvent, e: React.MouseEvent) => {
    setHoveredEvent(event);
    const rect = e.currentTarget.getBoundingClientRect();
    setHoverPosition({ x: rect.left, y: rect.top + rect.height });
  };

  const handleEventMouseLeave = () => {
    setHoveredEvent(null);
  };

  const getTicketForEvent = (event: CalendarEvent): Ticket | undefined => {
    return tickets.find(t => t.id === event.ticketId);
  };

  return (
    <>
      <div
        className={`bg-white min-h-[120px] p-1.5 relative ${
          !isCurrentMonth ? "bg-slate-50" : ""
        } ${isToday ? "bg-blue-50" : ""}`}
      >
        <div
          className={`text-sm font-medium mb-1 ${
            isCurrentMonth ? "text-slate-900" : "text-slate-400"
          } ${isToday ? "text-blue-600 font-bold" : ""}`}
        >
          {day}
        </div>
        <div className="space-y-1">
          {events.slice(0, MAX_VISIBLE_EVENTS).map((event) => {
            const ticket = getTicketForEvent(event);
            const colorInfo = ticket ? getEventColor(ticket) : { className: event.color };
            
            return (
              <div
                key={event.id}
                className={`${colorInfo.className} text-white text-xs px-1.5 py-0.5 rounded truncate cursor-pointer hover:opacity-90 relative`}
                style={colorInfo.style}
                onMouseEnter={(e) => handleEventMouseEnter(event, e)}
                onMouseLeave={handleEventMouseLeave}
              >
                {event.hours}h {event.title}
              </div>
            );
          })}
          {events.length > MAX_VISIBLE_EVENTS && (
            <div className="text-xs text-slate-500 px-1.5">
              +{events.length - MAX_VISIBLE_EVENTS} more
            </div>
          )}
        </div>
      </div>
      
      {/* Hover Preview Tooltip */}
      {hoveredEvent && (
        <EventPreview
          event={hoveredEvent}
          ticket={getTicketForEvent(hoveredEvent)}
          position={hoverPosition}
          onClose={() => setHoveredEvent(null)}
        />
      )}
    </>
  );
}

// Event Preview Tooltip Component
function EventPreview({
  event,
  ticket,
  position,
  onClose,
}: {
  event: CalendarEvent;
  ticket?: Ticket;
  position: { x: number; y: number };
  onClose: () => void;
}) {
  const getStatusDisplay = (status: TicketStatus): string => {
    const statusMap: Record<TicketStatus, string> = {
      open: "OPEN",
      in_progress: "IN PROGRESS",
      resolved: "RESOLVED",
      closed: "CLOSED",
    };
    return statusMap[status] || status.toUpperCase();
  };

  const getPriorityDisplay = (priority: Priority): string => {
    return priority.charAt(0).toUpperCase() + priority.slice(1);
  };

  return (
    <div
      className="fixed z-50 bg-white border border-slate-200 rounded-lg shadow-lg p-4 min-w-[280px] max-w-[320px]"
      style={{
        left: `${position.x}px`,
        top: `${position.y + 8}px`,
      }}
      onMouseLeave={onClose}
    >
      <div className="space-y-3">
        <div>
          <div className="flex items-start justify-between gap-2 mb-1">
            <h3 className="font-semibold text-sm text-slate-900 line-clamp-2">
              {ticket?.title || event.title}
            </h3>
            {ticket && (
              <div className={`w-3 h-3 rounded flex-shrink-0 ${getEventColor(ticket).className}`} style={getEventColor(ticket).style}></div>
            )}
          </div>
          {ticket?.project && (
            <div className="text-xs text-slate-500 mb-2">
              {ticket.project.identifier}-{ticket.id}
            </div>
          )}
        </div>

        {ticket && (
          <>
            <div className="flex items-center gap-4 text-xs">
              <div>
                <span className="text-slate-500">Status:</span>{" "}
                <span className="font-medium text-slate-900">
                  {getStatusDisplay(ticket.status)}
                </span>
              </div>
              <div>
                <span className="text-slate-500">Priority:</span>{" "}
                <span className="font-medium text-slate-900">
                  {getPriorityDisplay(ticket.priority)}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs">
              <div>
                <span className="text-slate-500">Hours:</span>{" "}
                <span className="font-medium text-slate-900">
                  {ticket.estimated_hours || 8}h
                </span>
              </div>
              {ticket.assignee_user && (
                <div className="flex items-center gap-2">
                  <span className="text-slate-500">Assignee:</span>
                  <UserAvatar user={ticket.assignee_user} size="sm" showName />
                </div>
              )}
            </div>

            {ticket.start_date && (
              <div className="text-xs">
                <span className="text-slate-500">Start:</span>{" "}
                <span className="font-medium text-slate-900">
                  {new Date(ticket.start_date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>
            )}

            {ticket.end_date && (
              <div className="text-xs">
                <span className="text-slate-500">End:</span>{" "}
                <span className="font-medium text-slate-900">
                  {new Date(ticket.end_date).toLocaleDateString("en-US", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </span>
              </div>
            )}

            {ticket.summary && (
              <div className="text-xs pt-2 border-t border-slate-200">
                <span className="text-slate-500">Summary:</span>
                <p className="text-slate-700 mt-1 line-clamp-3">{ticket.summary}</p>
              </div>
            )}

            {ticket.labels && ticket.labels.length > 0 && (
              <div className="flex flex-wrap gap-1 pt-2 border-t border-slate-200">
                {ticket.labels.map((label) => (
                  <span
                    key={label.id}
                    className="text-xs px-2 py-0.5 rounded-full text-white"
                    style={{ backgroundColor: label.color || "#6b7280" }}
                  >
                    {label.name}
                  </span>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
