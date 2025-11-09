"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  Search,
  Filter,
  X,
  Trash2,
  Calendar,
  User as UserIcon,
  Tag,
  Circle,
  Clock,
  Grid,
  Link2,
  Sparkles,
  Folder,
  Copy,
  ChevronDown,
} from "lucide-react";
import { AttributeButton } from "@/components/ui/attribute-button";
import { DateAttributeButton } from "@/components/ui/date-attribute-button";
import { MultiSelectLabels } from "@/components/ui/multi-select-labels";
import { DropdownOption } from "@/components/ui/dropdown";
import { UserAvatar, User } from "@/components/ui/user-avatar";

// Backend types
type TicketStatus = "open" | "in_progress" | "resolved" | "closed";
type Priority = "urgent" | "high" | "medium" | "low" | "none";

interface Project {
  id: number;
  name: string;
  identifier: string;
  description?: string;
}

interface Label {
  id: number;
  name: string;
  color?: string;
  project_id: number;
}

interface Cycle {
  id: number;
  name: string;
  project_id: number;
  start_date: string;
  end_date: string;
  status: string;
}

interface Module {
  id: number;
  name: string;
  project_id: number;
  description?: string;
  lead_id?: string;
}

interface Ticket {
  id: number;
  title: string;
  summary: string | null;
  start_date: string | null;
  end_date: string | null;
  assignee: string | null; // Keep for backward compatibility
  assignee_id?: number | null;
  status: TicketStatus;
  priority: Priority;
  estimated_hours?: number | null;
  project_id?: number | null;
  cycle_id?: number | null;
  module_id?: number | null;
  parent_ticket_id?: number | null;
  created_at: string;
  updated_at: string;
  // Nested relationships
  project?: { id: number; name: string; identifier: string };
  cycle?: { id: number; name: string; start_date: string; end_date: string };
  module?: { id: number; name: string };
  parent?: { id: number; title: string; status: TicketStatus };
  labels?: Array<{ id: number; name: string; color?: string }>;
  subtasks?: Array<{ id: number; title: string; status: TicketStatus }>;
  assignee_user?: User | null;
}

interface TicketFormData {
  title: string;
  summary?: string;
  start_date?: string | null;
  end_date?: string | null;
  assignee?: string | null; // Keep for backward compatibility
  assignee_id?: number | null;
  status?: TicketStatus;
  priority?: Priority;
  estimated_hours?: number | null;
  project_id?: number | null;
  cycle_id?: number | null;
  module_id?: number | null;
  parent_ticket_id?: number | null;
  label_ids?: number[];
}

export default function TicketsPage() {
  // State for tickets
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus | "all">(
    "all"
  );

  // State for reference data
  const [projects, setProjects] = useState<Project[]>([]);
  const [labels, setLabels] = useState<Label[]>([]);
  const [cycles, setCycles] = useState<Cycle[]>([]);
  const [modules, setModules] = useState<Module[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);
  const [createMore, setCreateMore] = useState(false);

  // Form state
  const [formData, setFormData] = useState<TicketFormData>({
    title: "",
    summary: "",
    assignee: "",
    assignee_id: null,
    start_date: null,
    end_date: null,
    status: "open",
    priority: "none",
    estimated_hours: null,
    project_id: null,
    cycle_id: null,
    module_id: null,
    parent_ticket_id: null,
    label_ids: [],
  });

  // Track the display status (Backlog, Todo, etc.) separately from backend status
  const [displayStatus, setDisplayStatus] = useState<string>("backlog");

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch all data on mount
  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchProjects(),
        fetchLabels(),
        fetchCycles(),
        fetchModules(),
        fetchUsers(),
        fetchTickets(),
      ]);
    } catch (error) {
      console.error("Error fetching data:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch(`${API_URL}/projects/`);
      if (!response.ok) throw new Error("Failed to fetch projects");
      const data = await response.json();
      setProjects(data.projects || []);
      // Set the first project as selected by default
      if (data.projects && data.projects.length > 0 && !selectedProject) {
        setSelectedProject(data.projects[0]);
        setFormData((prev) => ({ ...prev, project_id: data.projects[0].id }));
      }
    } catch (error) {
      console.error("Error fetching projects:", error);
    }
  };

  const fetchLabels = async () => {
    try {
      const response = await fetch(`${API_URL}/labels/`);
      if (!response.ok) throw new Error("Failed to fetch labels");
      const data = await response.json();
      setLabels(data.labels || []);
    } catch (error) {
      console.error("Error fetching labels:", error);
    }
  };

  const fetchCycles = async () => {
    try {
      const response = await fetch(`${API_URL}/cycles/`);
      if (!response.ok) throw new Error("Failed to fetch cycles");
      const data = await response.json();
      setCycles(data.cycles || []);
    } catch (error) {
      console.error("Error fetching cycles:", error);
    }
  };

  const fetchModules = async () => {
    try {
      const response = await fetch(`${API_URL}/modules/`);
      if (!response.ok) throw new Error("Failed to fetch modules");
      const data = await response.json();
      setModules(data.modules || []);
    } catch (error) {
      console.error("Error fetching modules:", error);
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

  const fetchTickets = async () => {
    try {
      const response = await fetch(`${API_URL}/tickets/`);
      if (!response.ok) throw new Error("Failed to fetch tickets");
      const data = await response.json();
      setTickets(data.tickets);
    } catch (error) {
      console.error("Error fetching tickets:", error);
      alert("Failed to load tickets. Please check your backend connection.");
    }
  };

  const createTicket = async () => {
    try {
      const payload: any = {
        title: formData.title.trim(),
        status: formData.status || "open",
        priority: formData.priority || "none",
        project_id: formData.project_id,
      };

      // Only include optional fields if they have values
      if (formData.summary && formData.summary.trim()) {
        payload.summary = formData.summary.trim();
      }
      if (formData.assignee_id) {
        payload.assignee_id = formData.assignee_id;
      } else if (formData.assignee && formData.assignee.trim()) {
        // Fallback for backward compatibility
        payload.assignee = formData.assignee.trim();
      }
      if (formData.start_date) {
        payload.start_date = formData.start_date;
      }
      if (formData.end_date) {
        payload.end_date = formData.end_date;
      }
      if (formData.cycle_id) {
        payload.cycle_id = formData.cycle_id;
      }
      if (formData.module_id) {
        payload.module_id = formData.module_id;
      }
      if (formData.parent_ticket_id) {
        payload.parent_ticket_id = formData.parent_ticket_id;
      }
      if (formData.estimated_hours) {
        payload.estimated_hours = formData.estimated_hours;
      }
      // Always include label_ids, even if empty array (to clear labels)
      payload.label_ids = formData.label_ids || [];

      const response = await fetch(`${API_URL}/tickets/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Create error:", errorData);
        throw new Error("Failed to create ticket");
      }

      await fetchTickets();

      if (createMore) {
        // Keep modal open and reset form except project
        const currentProjectId = formData.project_id;
        resetForm();
        setFormData((prev) => ({ ...prev, project_id: currentProjectId }));
      } else {
        setShowCreateModal(false);
        resetForm();
      }
      alert("Ticket created successfully!");
    } catch (error) {
      console.error("Error creating ticket:", error);
      alert("Failed to create ticket");
    }
  };

  const updateTicket = async () => {
    if (!editingTicket) return;

    try {
      const payload: any = {
        title: formData.title.trim(),
        status: formData.status,
        priority: formData.priority,
      };

      // Only include optional fields if they have values
      if (formData.summary && formData.summary.trim()) {
        payload.summary = formData.summary.trim();
      }
      // Always include assignee_id to allow clearing it (send null if not set)
      if (formData.assignee_id) {
        payload.assignee_id = formData.assignee_id;
      } else if (formData.assignee && formData.assignee.trim()) {
        // Fallback for backward compatibility
        payload.assignee = formData.assignee.trim();
      } else {
        // Explicitly clear assignee if not set
        payload.assignee_id = null;
        payload.assignee = null;
      }
      if (formData.start_date) {
        payload.start_date = formData.start_date;
      }
      if (formData.end_date) {
        payload.end_date = formData.end_date;
      }
      if (formData.project_id) {
        payload.project_id = formData.project_id;
      }
      if (formData.cycle_id) {
        payload.cycle_id = formData.cycle_id;
      }
      if (formData.module_id) {
        payload.module_id = formData.module_id;
      }
      if (formData.parent_ticket_id) {
        payload.parent_ticket_id = formData.parent_ticket_id;
      }
      if (formData.estimated_hours) {
        payload.estimated_hours = formData.estimated_hours;
      }
      // Always include label_ids, even if empty array (to clear labels)
      payload.label_ids = formData.label_ids || [];

      const response = await fetch(`${API_URL}/tickets/${editingTicket.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Update error:", errorData);
        throw new Error("Failed to update ticket");
      }

      await fetchTickets();
      setShowEditModal(false);
      setEditingTicket(null);
      resetForm();
      alert("Ticket updated successfully!");
    } catch (error) {
      console.error("Error updating ticket:", error);
      alert("Failed to update ticket");
    }
  };

  const deleteTicket = async (ticketId: number) => {
    if (!confirm("Are you sure you want to delete this ticket?")) return;

    try {
      const response = await fetch(`${API_URL}/tickets/${ticketId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete ticket");

      await fetchTickets();
      alert("Ticket deleted successfully!");
    } catch (error) {
      console.error("Error deleting ticket:", error);
      alert("Failed to delete ticket");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      summary: "",
      assignee: "",
      assignee_id: null,
      start_date: null,
      end_date: null,
      status: "open",
      priority: "none",
      estimated_hours: null,
      project_id: selectedProject?.id || null,
      cycle_id: null,
      module_id: null,
      parent_ticket_id: null,
      label_ids: [],
    });
    setDisplayStatus("backlog");
    setCreateMore(false);
  };

  const openEditModal = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setFormData({
      title: ticket.title,
      summary: ticket.summary || "",
      assignee: ticket.assignee || "",
      assignee_id: ticket.assignee_id || ticket.assignee_user?.id || null,
      start_date: ticket.start_date,
      end_date: ticket.end_date,
      status: ticket.status,
      priority: ticket.priority,
      estimated_hours: ticket.estimated_hours || null,
      project_id: ticket.project_id || null,
      cycle_id: ticket.cycle_id || null,
      module_id: ticket.module_id || null,
      parent_ticket_id: ticket.parent_ticket_id || null,
      label_ids: ticket.labels?.map((l) => l.id) || [],
    });
    // Map backend status to display status
    const statusToDisplay: Record<TicketStatus, string> = {
      open: "backlog",
      in_progress: "todo",
      resolved: "in_progress",
      closed: "done",
    };
    setDisplayStatus(statusToDisplay[ticket.status] || "backlog");
    setShowEditModal(true);
  };

  const statusColors: Record<TicketStatus, string> = {
    open: "bg-blue-500 text-white",
    in_progress: "bg-yellow-500 text-white",
    resolved: "bg-green-500 text-white",
    closed: "bg-gray-500 text-white",
  };

  const priorityColors: Record<Priority, string> = {
    urgent: "bg-red-600 text-white",
    high: "bg-orange-500 text-white",
    medium: "bg-blue-500 text-white",
    low: "bg-gray-400 text-white",
    none: "bg-gray-300 text-gray-700",
  };

  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ticket.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ??
        false);
    const matchesStatus =
      selectedStatus === "all" || ticket.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  // Map backend status to display column
  // We map each backend status to a unique display column:
  // - "open" -> "backlog"
  // - "in_progress" -> "todo" (tickets ready to work on)
  // - "resolved" -> "in_progress" (tickets being worked on)
  // - "closed" -> "done" (completed tickets)
  const getDisplayColumn = (ticket: Ticket): string => {
    switch (ticket.status) {
      case "open":
        return "backlog";
      case "in_progress":
        return "todo";
      case "resolved":
        return "in_progress";
      case "closed":
        return "done";
      default:
        return "backlog";
    }
  };

  // Group tickets by display column
  const ticketsByColumn = {
    backlog: filteredTickets.filter((t) => getDisplayColumn(t) === "backlog"),
    todo: filteredTickets.filter((t) => getDisplayColumn(t) === "todo"),
    in_progress: filteredTickets.filter((t) => getDisplayColumn(t) === "in_progress"),
    done: filteredTickets.filter((t) => getDisplayColumn(t) === "done"),
  };

  // Get ticket icon and color based on priority/type
  const getTicketIcon = (ticket: Ticket): { icon: string; bgColor: string; iconColor: string } => {
    // Map priority to icon colors
    switch (ticket.priority) {
      case "urgent":
        return { icon: "campaign", bgColor: "bg-orange-100", iconColor: "text-orange-600" };
      case "high":
        return { icon: "description", bgColor: "bg-green-100", iconColor: "text-green-600" };
      case "medium":
        return { icon: "edit_note", bgColor: "bg-cyan-100", iconColor: "text-cyan-600" };
      case "low":
        return { icon: "palette", bgColor: "bg-purple-100", iconColor: "text-purple-600" };
      default:
        return { icon: "edit_note", bgColor: "bg-cyan-100", iconColor: "text-cyan-600" };
    }
  };

  // Get ticket identifier
  const getTicketId = (ticket: Ticket): string => {
    if (ticket.project?.identifier) {
      return `${ticket.project.identifier} ${ticket.id}`;
    }
    return `TICKET-${ticket.id}`;
  };

  // Format date
  const formatDate = (dateString: string | null): string => {
    if (!dateString) return "";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", { day: "numeric", month: "short", year: "numeric" });
  };

  // Get status icon
  const getStatusIcon = (column: string): string => {
    switch (column) {
      case "backlog":
        return "pending";
      case "todo":
        return "radio_button_unchecked";
      case "in_progress":
        return "progress_activity";
      case "done":
        return "check_circle";
      default:
        return "pending";
    }
  };

  // Get status icon color
  const getStatusIconColor = (column: string): string => {
    switch (column) {
      case "backlog":
        return "text-gray-500";
      case "todo":
        return "text-gray-500";
      case "in_progress":
        return "text-yellow-500";
      case "done":
        return "text-green-500";
      default:
        return "text-gray-500";
    }
  };

  const statuses: Array<{ value: TicketStatus | "all"; label: string }> = [
    { value: "all", label: "All" },
    { value: "open", label: "Open" },
    { value: "in_progress", label: "In Progress" },
    { value: "resolved", label: "Resolved" },
    { value: "closed", label: "Closed" },
  ];

  // Status options for dropdown (matching Plane.so status colors)
  const statusOptions: DropdownOption[] = [
    {
      value: "backlog",
      label: "Backlog",
      icon: Circle,
      description: "Backlog",
    },
    { value: "todo", label: "Todo", icon: Circle, description: "Todo" },
    {
      value: "in_progress",
      label: "In Progress",
      icon: Circle,
      description: "In Progress",
    },
    { value: "done", label: "Done", icon: Circle, description: "Done" },
  ];

  // Priority options
  const priorityOptions: DropdownOption[] = [
    { value: "urgent", label: "Urgent", icon: Circle },
    { value: "high", label: "High", icon: Circle },
    { value: "medium", label: "Medium", icon: Circle },
    { value: "low", label: "Low", icon: Circle },
    { value: "none", label: "None", icon: Circle },
  ];

  // Convert backend data to dropdown options
  const assigneeOptions: DropdownOption[] = [
    { value: "", label: "None", icon: UserIcon, description: "Unassigned" },
    ...users.map((user) => ({
      value: user.id.toString(),
      label: user.name,
      icon: UserIcon,
      description: user.email || "",
    })),
  ];

  // Filter labels, cycles, and modules by selected project
  const filteredLabels = formData.project_id
    ? labels.filter((label) => label.project_id === formData.project_id)
    : labels;

  const filteredCycles = formData.project_id
    ? cycles.filter((cycle) => cycle.project_id === formData.project_id)
    : cycles;

  const filteredModules = formData.project_id
    ? modules.filter((module) => module.project_id === formData.project_id)
    : modules;

  const projectOptions: DropdownOption[] = projects.map((project) => ({
    value: project.id.toString(),
    label: project.name,
    icon: Folder,
    description: project.identifier,
  }));

  const cycleOptions: DropdownOption[] = [
    { value: "", label: "None", icon: Clock },
    ...filteredCycles.map((cycle) => ({
      value: cycle.id.toString(),
      label: cycle.name,
      icon: Clock,
      description: cycle.name,
    })),
  ];

  const moduleOptions: DropdownOption[] = [
    { value: "", label: "None", icon: Grid },
    ...filteredModules.map((module) => ({
      value: module.id.toString(),
      label: module.name,
      icon: Grid,
      description: module.name,
    })),
  ];

  const parentTicketOptions: DropdownOption[] = [
    { value: "", label: "None", icon: Link2 },
    ...tickets
      .filter((t) => t.id !== editingTicket?.id) // Don't allow self-referencing
      .map((ticket) => ({
        value: ticket.id.toString(),
        label: ticket.title,
        icon: Link2,
        description: ticket.title,
      })),
  ];

  const columns = [
    { key: "backlog", label: "Backlog" },
    { key: "todo", label: "Todo" },
    { key: "in_progress", label: "In progress" },
    { key: "done", label: "Done" },
  ];

  return (
    <div className="flex flex-col h-screen bg-white overflow-hidden">
      {/* Header */}
      <header className="flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-gray-200">
        <div className="flex items-center text-sm text-gray-500">
          {selectedProject && (
            <>
              <span className="text-base mr-2">🚀</span>
              <span>{selectedProject.name}</span>
              <span className="material-symbols-outlined text-lg mx-1">chevron_right</span>
            </>
          )}
          <span>Work Items</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center border border-gray-300 rounded">
            <button className="p-2 border-r border-gray-300 text-gray-600 hover:bg-gray-100">
              <span className="material-symbols-outlined text-lg">view_kanban</span>
            </button>
            <button className="p-2 text-gray-600 hover:bg-gray-100">
              <span className="material-symbols-outlined text-lg">list</span>
            </button>
          </div>
          <button className="flex items-center px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-100">
            Filters <span className="material-symbols-outlined text-lg ml-1">expand_more</span>
          </button>
          <button className="flex items-center px-3 py-1.5 border border-gray-300 rounded text-sm text-gray-700 hover:bg-gray-100">
            Display <span className="material-symbols-outlined text-lg ml-1">expand_more</span>
          </button>
          <button className="px-4 py-1.5 bg-[#4361EE] text-white rounded text-sm font-medium hover:bg-blue-700" onClick={() => setShowCreateModal(true)}>
            Add work item
          </button>
        </div>
      </header>

      {/* Kanban Board */}
      <div className="flex-1 p-6 overflow-x-auto bg-white">
        {loading ? (
          <div className="text-center py-12">
            <p className="text-gray-500">Loading tickets...</p>
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-6 min-w-max">
            {columns.map((column) => {
              const columnTickets = ticketsByColumn[column.key as keyof typeof ticketsByColumn] || [];
              const statusIcon = getStatusIcon(column.key);
              const statusIconColor = getStatusIconColor(column.key);

              return (
                <div key={column.key} className="space-y-4 min-w-[280px]">
                  {/* Column Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <span className={`material-symbols-outlined text-lg mr-2 ${statusIconColor}`}>
                        {statusIcon}
                      </span>
                      <h2 className="font-medium text-gray-800">
                        {column.label}
                      </h2>
                      <span className="ml-2 text-sm text-gray-500">
                        {columnTickets.length}
                      </span>
                    </div>
                    <div className="flex items-center space-x-1 text-gray-500">
                      <button className="hover:text-gray-800">
                        <span className="material-symbols-outlined text-lg">more_horiz</span>
                      </button>
                      <button className="hover:text-gray-800">
                        <span className="material-symbols-outlined text-lg">add</span>
                      </button>
                    </div>
                  </div>

                  {/* Tickets */}
                  <div className="space-y-4">
                    {columnTickets.map((ticket) => {
                      const ticketIcon = getTicketIcon(ticket);
                      const ticketId = getTicketId(ticket);
                      const displayDate = ticket.end_date || ticket.start_date || ticket.created_at;

                      return (
                        <div
                          key={ticket.id}
                          className="p-4 bg-white border border-gray-200 rounded-lg shadow-sm cursor-pointer hover:shadow-md transition-shadow relative group"
                          onClick={() => openEditModal(ticket)}
                        >
                          {/* Delete Button */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteTicket(ticket.id);
                            }}
                            className="absolute top-2 right-2 p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                            title="Delete ticket"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>

                          {/* Ticket Header */}
                          <div className="flex items-start mb-2">
                            <div className={`w-5 h-5 rounded-sm ${ticketIcon.bgColor} flex items-center justify-center mr-2`}>
                              <span className={`material-symbols-outlined text-sm ${ticketIcon.iconColor}`}>
                                {ticketIcon.icon}
                              </span>
                            </div>
                            <span className="text-xs text-gray-500">{ticketId}</span>
                          </div>

                          {/* Ticket Title */}
                          <p className="text-sm text-gray-900 mb-4 line-clamp-2">
                            {ticket.title}
                          </p>

                          {/* Ticket Metadata */}
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center space-x-2">
                              <span className="material-symbols-outlined text-sm">signal_cellular_alt</span>
                              <span className="flex items-center">
                                <span className={`material-symbols-outlined text-sm mr-1 ${statusIconColor}`}>
                                  {statusIcon}
                                </span>
                                {column.label}
                              </span>
                              {displayDate && (
                                <span className="flex items-center">
                                  <span className="material-symbols-outlined text-sm mr-1">calendar_today</span>
                                  {formatDate(displayDate)}
                                </span>
                              )}
                            </div>
                            {ticket.assignee_user && (
                              <div className="flex -space-x-2">
                                {ticket.assignee_user.avatar_url ? (
                                  <img
                                    alt={ticket.assignee_user.name}
                                    className="w-5 h-5 rounded-full border-2 border-white"
                                    src={ticket.assignee_user.avatar_url}
                                  />
                                ) : (
                                  <div
                                    className="w-5 h-5 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-medium"
                                    style={{
                                      backgroundColor: ticket.assignee_user.color || "#3b82f6",
                                    }}
                                  >
                                    {(ticket.assignee_user.initials || ticket.assignee_user.name.substring(0, 2)).toUpperCase()}
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Add New Item Button */}
                  <button
                    className="flex items-center text-sm text-gray-500 w-full px-2 py-1 rounded hover:bg-gray-100"
                    onClick={() => {
                      const statusMap: Record<string, TicketStatus> = {
                        backlog: "open",
                        todo: "in_progress",
                        in_progress: "resolved",
                        done: "closed",
                      };
                      setDisplayStatus(column.key);
                      setFormData((prev) => ({
                        ...prev,
                        status: statusMap[column.key] || "open",
                      }));
                      setShowCreateModal(true);
                    }}
                  >
                    <span className="material-symbols-outlined text-lg mr-1">add</span>
                    New work item
                  </button>
                </div>
              );
            })}
          </div>
        )}

        {!loading && filteredTickets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No tickets found</p>
          </div>
        )}
      </div>

      {/* Create Ticket Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4 bg-black/10">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-200">
                <h2 className="text-xl font-semibold text-slate-900">
                  Create new work item
                </h2>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => {
                    setShowCreateModal(false);
                    resetForm();
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Project Selector */}
                <div>
                  <AttributeButton
                    label="Project"
                    value={formData.project_id?.toString() || ""}
                    options={projectOptions}
                    onSelect={(value) => {
                      const projectId = value ? parseInt(value) : null;
                      const project = projects.find((p) => p.id === projectId);
                      setSelectedProject(project || null);
                      setFormData({
                        ...formData,
                        project_id: projectId,
                        cycle_id: null, // Reset cycle when project changes
                        module_id: null, // Reset module when project changes
                        label_ids: [], // Reset labels when project changes
                      });
                    }}
                    icon={Folder}
                    placeholder="Select Project"
                  />
                </div>

                {/* Title Input */}
                <div>
                  <Input
                    placeholder="Title"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="border-slate-200 text-slate-900 placeholder:text-slate-400 text-base focus-visible:ring-blue-500"
                  />
                </div>

                {/* Description Textarea */}
                <div className="relative">
                  <Textarea
                    placeholder="Click to add description"
                    value={formData.summary || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, summary: e.target.value })
                    }
                    className="min-h-[120px] border-slate-200 text-slate-900 placeholder:text-slate-400 resize-none focus-visible:ring-blue-500"
                  />
                  <div className="absolute bottom-3 right-3">
                    <div className="flex items-center gap-1 px-2 py-1 rounded bg-purple-100 text-xs text-purple-700 border border-purple-200">
                      <Sparkles className="h-3 w-3" />
                      <span>AI</span>
                    </div>
                  </div>
                </div>

                {/* Attribute Buttons Row */}
                <div className="flex flex-wrap gap-2">
                  <AttributeButton
                    label="Backlog"
                    value={displayStatus}
                    options={statusOptions}
                    onSelect={(value) => {
                      const statusMap: Record<string, TicketStatus> = {
                        backlog: "open",
                        todo: "in_progress",
                        in_progress: "resolved",
                        done: "closed",
                      };
                      setDisplayStatus(value);
                      setFormData({
                        ...formData,
                        status: statusMap[value] || "open",
                      });
                    }}
                    icon={Circle}
                    placeholder="Backlog"
                  />
                  <AttributeButton
                    label="Priority"
                    value={formData.priority || "none"}
                    options={priorityOptions}
                    onSelect={(value) =>
                      setFormData({ ...formData, priority: value as Priority })
                    }
                    icon={Circle}
                    placeholder="None"
                  />
                  <AttributeButton
                    label="Assignees"
                    value={formData.assignee_id?.toString() || ""}
                    options={assigneeOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        assignee_id: value ? parseInt(value) : null,
                        assignee: null, // Clear old assignee string
                      })
                    }
                    icon={UserIcon}
                    placeholder="None"
                  />
                  <div className="w-full">
                    <MultiSelectLabels
                      selectedLabelIds={formData.label_ids || []}
                      availableLabels={filteredLabels}
                      onSelect={(labelId) => {
                        if (!formData.label_ids?.includes(labelId)) {
                          setFormData({
                            ...formData,
                            label_ids: [...(formData.label_ids || []), labelId],
                          });
                        }
                      }}
                      onRemove={(labelId) => {
                        setFormData({
                          ...formData,
                          label_ids: (formData.label_ids || []).filter(
                            (id) => id !== labelId
                          ),
                        });
                      }}
                      placeholder="Labels"
                    />
                  </div>
                  <DateAttributeButton
                    label="Start date"
                    value={formData.start_date}
                    onChange={(value) =>
                      setFormData({ ...formData, start_date: value })
                    }
                    placeholder="Start date"
                  />
                  <DateAttributeButton
                    label="Due date"
                    value={formData.end_date}
                    onChange={(value) =>
                      setFormData({ ...formData, end_date: value })
                    }
                    placeholder="Due date"
                  />
                  <AttributeButton
                    label="Cycle"
                    value={formData.cycle_id?.toString() || ""}
                    options={cycleOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        cycle_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Clock}
                    placeholder="Cycle"
                  />
                  <AttributeButton
                    label="Modules"
                    value={formData.module_id?.toString() || ""}
                    options={moduleOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        module_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Grid}
                    placeholder="Modules"
                  />
                  <AttributeButton
                    label="Add parent"
                    value={formData.parent_ticket_id?.toString() || ""}
                    options={parentTicketOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        parent_ticket_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Link2}
                    placeholder="Add parent"
                  />
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="create-more"
                      checked={createMore}
                      onChange={(e) => setCreateMore(e.target.checked)}
                      className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                    />
                    <label
                      htmlFor="create-more"
                      className="text-sm text-slate-700 cursor-pointer"
                    >
                      Create more
                    </label>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setShowCreateModal(false);
                        resetForm();
                      }}
                      className="text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    >
                      Discard
                    </Button>
                    <Button
                      onClick={createTicket}
                      disabled={!formData.title.trim()}
                      className="bg-blue-600 text-white hover:bg-blue-700 rounded-md font-medium px-4 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      Save
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Edit Ticket Modal */}
        {showEditModal && editingTicket && (
          <div className="fixed inset-0 flex items-center justify-center z-50 p-4 bg-black/10">
            <div className="w-full max-w-2xl bg-white rounded-lg shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-200">
                <h2 className="text-xl font-semibold text-slate-900">
                  Edit Ticket #{editingTicket.id}
                </h2>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingTicket(null);
                    resetForm();
                  }}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Modal Content */}
              <div className="p-6 space-y-6">
                {/* Project Selector */}
                <div>
                  <AttributeButton
                    label="Project"
                    value={formData.project_id?.toString() || ""}
                    options={projectOptions}
                    onSelect={(value) => {
                      const projectId = value ? parseInt(value) : null;
                      const project = projects.find((p) => p.id === projectId);
                      setSelectedProject(project || null);
                      setFormData({
                        ...formData,
                        project_id: projectId,
                        cycle_id: null, // Reset cycle when project changes
                        module_id: null, // Reset module when project changes
                        label_ids: [], // Reset labels when project changes
                      });
                    }}
                    icon={Folder}
                    placeholder="Select Project"
                  />
                </div>

                {/* Title Input */}
                <div>
                  <Input
                    placeholder="Title"
                    value={formData.title}
                    onChange={(e) =>
                      setFormData({ ...formData, title: e.target.value })
                    }
                    className="border-slate-200 text-slate-900 placeholder:text-slate-400 text-base focus-visible:ring-blue-500"
                  />
                </div>

                {/* Description Textarea */}
                <div className="relative">
                  <Textarea
                    placeholder="Click to add description"
                    value={formData.summary || ""}
                    onChange={(e) =>
                      setFormData({ ...formData, summary: e.target.value })
                    }
                    className="min-h-[120px] border-slate-200 text-slate-900 placeholder:text-slate-400 resize-none focus-visible:ring-blue-500"
                  />
                </div>

                {/* Attribute Buttons Row */}
                <div className="flex flex-wrap gap-2">
                  <AttributeButton
                    label="Status"
                    value={displayStatus}
                    options={statusOptions}
                    onSelect={(value) => {
                      const statusMap: Record<string, TicketStatus> = {
                        backlog: "open",
                        todo: "in_progress",
                        in_progress: "resolved",
                        done: "closed",
                      };
                      setDisplayStatus(value);
                      setFormData({
                        ...formData,
                        status: statusMap[value] || "open",
                      });
                    }}
                    icon={Circle}
                    placeholder="Backlog"
                  />
                  <AttributeButton
                    label="Priority"
                    value={formData.priority || "none"}
                    options={priorityOptions}
                    onSelect={(value) =>
                      setFormData({ ...formData, priority: value as Priority })
                    }
                    icon={Circle}
                    placeholder="None"
                  />
                  <AttributeButton
                    label="Assignees"
                    value={formData.assignee_id?.toString() || ""}
                    options={assigneeOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        assignee_id: value ? parseInt(value) : null,
                        assignee: null, // Clear old assignee string
                      })
                    }
                    icon={UserIcon}
                    placeholder="None"
                  />
                  <div className="w-full">
                    <MultiSelectLabels
                      selectedLabelIds={formData.label_ids || []}
                      availableLabels={filteredLabels}
                      onSelect={(labelId) => {
                        if (!formData.label_ids?.includes(labelId)) {
                          setFormData({
                            ...formData,
                            label_ids: [...(formData.label_ids || []), labelId],
                          });
                        }
                      }}
                      onRemove={(labelId) => {
                        setFormData({
                          ...formData,
                          label_ids: (formData.label_ids || []).filter(
                            (id) => id !== labelId
                          ),
                        });
                      }}
                      placeholder="Labels"
                    />
                  </div>
                  <DateAttributeButton
                    label="Start date"
                    value={formData.start_date}
                    onChange={(value) =>
                      setFormData({ ...formData, start_date: value })
                    }
                    placeholder="Start date"
                  />
                  <DateAttributeButton
                    label="Due date"
                    value={formData.end_date}
                    onChange={(value) =>
                      setFormData({ ...formData, end_date: value })
                    }
                    placeholder="Due date"
                  />
                  <AttributeButton
                    label="Cycle"
                    value={formData.cycle_id?.toString() || ""}
                    options={cycleOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        cycle_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Clock}
                    placeholder="Cycle"
                  />
                  <AttributeButton
                    label="Modules"
                    value={formData.module_id?.toString() || ""}
                    options={moduleOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        module_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Grid}
                    placeholder="Modules"
                  />
                  <AttributeButton
                    label="Add parent"
                    value={formData.parent_ticket_id?.toString() || ""}
                    options={parentTicketOptions}
                    onSelect={(value) =>
                      setFormData({
                        ...formData,
                        parent_ticket_id: value ? parseInt(value) : null,
                      })
                    }
                    icon={Link2}
                    placeholder="Add parent"
                  />
                </div>

                {/* Bottom Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-200">
                  <Button
                    variant="outline"
                    className="flex-1 border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingTicket(null);
                      resetForm();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1 bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    onClick={updateTicket}
                    disabled={!formData.title.trim()}
                  >
                    Update Ticket
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
