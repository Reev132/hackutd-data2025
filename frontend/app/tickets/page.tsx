"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Plus, Search, Filter, X, Trash2, Calendar } from "lucide-react";

// Match backend TicketStatus enum
type TicketStatus = "open" | "in_progress" | "resolved" | "closed";

// Match backend TicketOut schema
interface Ticket {
  id: number;
  title: string;
  summary: string | null;
  start_date: string | null;
  end_date: string | null;
  assignee: string | null;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
}

// Match backend TicketCreate schema
interface TicketCreate {
  title: string;
  summary?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  assignee?: string | null;
  status?: TicketStatus;
}

// Match backend TicketUpdate schema
interface TicketUpdate {
  title?: string;
  summary?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  assignee?: string | null;
  status?: TicketStatus;
}

export default function TicketsPage() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState<TicketStatus | "all">("all");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTicket, setEditingTicket] = useState<Ticket | null>(null);

  // Form state for create/edit
  const [formData, setFormData] = useState<TicketCreate>({
    title: "",
    summary: "",
    assignee: "",
    start_date: null,
    end_date: null,
    status: "open",
  });

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  // Fetch tickets on mount
  useEffect(() => {
    fetchTickets();
  }, []);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/tickets/`);
      if (!response.ok) throw new Error("Failed to fetch tickets");
      const data = await response.json();
      setTickets(data.tickets);
    } catch (error) {
      console.error("Error fetching tickets:", error);
      alert("Failed to load tickets. Please check your backend connection.");
    } finally {
      setLoading(false);
    }
  };

  const createTicket = async () => {
    try {
      const payload: any = {
        title: formData.title.trim(),
        status: formData.status || "open",
      };

      // Only include optional fields if they have values
      if (formData.summary && formData.summary.trim()) {
        payload.summary = formData.summary.trim();
      }
      if (formData.assignee && formData.assignee.trim()) {
        payload.assignee = formData.assignee.trim();
      }
      if (formData.start_date) {
        payload.start_date = formData.start_date;
      }
      if (formData.end_date) {
        payload.end_date = formData.end_date;
      }

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
      setShowCreateModal(false);
      resetForm();
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
      };

      // Only include optional fields if they have values
      if (formData.summary && formData.summary.trim()) {
        payload.summary = formData.summary.trim();
      }
      if (formData.assignee && formData.assignee.trim()) {
        payload.assignee = formData.assignee.trim();
      }
      if (formData.start_date) {
        payload.start_date = formData.start_date;
      }
      if (formData.end_date) {
        payload.end_date = formData.end_date;
      }

      const response = await fetch(`${API_URL}/tickets/${editingTicket.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Update error:", errorData);
        console.error("Validation details:", JSON.stringify(errorData.detail, null, 2));
        alert(`Update failed: ${JSON.stringify(errorData.detail)}`);
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
      start_date: null,
      end_date: null,
      status: "open",
    });
  };

  const openEditModal = (ticket: Ticket) => {
    setEditingTicket(ticket);
    setFormData({
      title: ticket.title,
      summary: ticket.summary || "",
      assignee: ticket.assignee || "",
      start_date: ticket.start_date,
      end_date: ticket.end_date,
      status: ticket.status,
    });
    setShowEditModal(true);
  };

  const statusColors: Record<TicketStatus, string> = {
    open: "bg-blue-500 text-white",
    in_progress: "bg-yellow-500 text-white",
    resolved: "bg-green-500 text-white",
    closed: "bg-gray-500 text-white",
  };

  const filteredTickets = tickets.filter((ticket) => {
    const matchesSearch =
      ticket.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (ticket.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
    const matchesStatus = selectedStatus === "all" || ticket.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const statuses: Array<{ value: TicketStatus | "all"; label: string }> = [
    { value: "all", label: "All" },
    { value: "open", label: "Open" },
    { value: "in_progress", label: "In Progress" },
    { value: "resolved", label: "Resolved" },
    { value: "closed", label: "Closed" },
  ];

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground">Tickets</h1>
            <p className="text-muted-foreground">
              Manage your product tickets and issues
            </p>
          </div>
          <Button className="gap-2" onClick={() => setShowCreateModal(true)}>
            <Plus className="h-4 w-4" />
            New Ticket
          </Button>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="p-4">
            <div className="flex flex-col gap-4 md:flex-row md:items-center">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search tickets..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <div className="flex gap-2">
                  {statuses.map((status) => (
                    <Button
                      key={status.value}
                      variant={selectedStatus === status.value ? "default" : "outline"}
                      size="sm"
                      onClick={() => setSelectedStatus(status.value)}
                    >
                      {status.label}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading tickets...</p>
          </div>
        )}

        {/* Tickets Grid */}
        {!loading && (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filteredTickets.map((ticket) => (
              <Card key={ticket.id} className="transition-shadow hover:shadow-md">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base font-semibold line-clamp-1">
                      {ticket.title}
                    </CardTitle>
                    <Badge className={statusColors[ticket.status]}>
                      {ticket.status.replace("_", " ")}
                    </Badge>
                  </div>
                  {ticket.summary && (
                    <CardDescription className="line-clamp-2">
                      {ticket.summary}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent className="space-y-3">
                  {ticket.assignee && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Assignee:</span>
                      <span className="font-medium">{ticket.assignee}</span>
                    </div>
                  )}
                  {ticket.start_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Start:</span>
                      <span>{new Date(ticket.start_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {ticket.end_date && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Due:</span>
                      <span>{new Date(ticket.end_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Created:</span>
                    <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1"
                      onClick={() => openEditModal(ticket)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="text-red-600 hover:text-red-700"
                      onClick={() => deleteTicket(ticket.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {!loading && filteredTickets.length === 0 && (
          <div className="text-center py-12">
            <p className="text-muted-foreground">No tickets found</p>
          </div>
        )}

        {/* Create Ticket Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Create New Ticket</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      setShowCreateModal(false);
                      resetForm();
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Title *</label>
                  <Input
                    placeholder="Enter ticket title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Summary</label>
                  <Textarea
                    placeholder="Enter ticket summary"
                    value={formData.summary || ""}
                    onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                    className="min-h-[100px]"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Assignee</label>
                  <Input
                    placeholder="Enter assignee name"
                    value={formData.assignee || ""}
                    onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Start Date</label>
                    <Input
                      type="date"
                      value={formData.start_date || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, start_date: e.target.value || null })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Date</label>
                    <Input
                      type="date"
                      value={formData.end_date || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, end_date: e.target.value || null })
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <div className="grid grid-cols-2 gap-2">
                    {statuses.slice(1).map((status) => (
                      <Button
                        key={status.value}
                        variant={formData.status === status.value ? "default" : "outline"}
                        onClick={() =>
                          setFormData({ ...formData, status: status.value as TicketStatus })
                        }
                      >
                        {status.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    className="flex-1"
                    onClick={createTicket}
                    disabled={!formData.title.trim()}
                  >
                    Create Ticket
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setShowCreateModal(false);
                      resetForm();
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Edit Ticket Modal */}
        {showEditModal && editingTicket && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>Edit Ticket #{editingTicket.id}</CardTitle>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingTicket(null);
                      resetForm();
                    }}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Title *</label>
                  <Input
                    placeholder="Enter ticket title"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Summary</label>
                  <Textarea
                    placeholder="Enter ticket summary"
                    value={formData.summary || ""}
                    onChange={(e) => setFormData({ ...formData, summary: e.target.value })}
                    className="min-h-[100px]"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Assignee</label>
                  <Input
                    placeholder="Enter assignee name"
                    value={formData.assignee || ""}
                    onChange={(e) => setFormData({ ...formData, assignee: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Start Date</label>
                    <Input
                      type="date"
                      value={formData.start_date || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, start_date: e.target.value || null })
                      }
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">End Date</label>
                    <Input
                      type="date"
                      value={formData.end_date || ""}
                      onChange={(e) =>
                        setFormData({ ...formData, end_date: e.target.value || null })
                      }
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Status</label>
                  <div className="grid grid-cols-2 gap-2">
                    {statuses.slice(1).map((status) => (
                      <Button
                        key={status.value}
                        variant={formData.status === status.value ? "default" : "outline"}
                        onClick={() =>
                          setFormData({ ...formData, status: status.value as TicketStatus })
                        }
                      >
                        {status.label}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="flex gap-2 pt-4">
                  <Button
                    className="flex-1"
                    onClick={updateTicket}
                    disabled={!formData.title.trim()}
                  >
                    Update Ticket
                  </Button>
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setShowEditModal(false);
                      setEditingTicket(null);
                      resetForm();
                    }}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
