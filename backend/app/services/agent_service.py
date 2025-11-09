"""
Agent service for AI-powered meeting analysis and ticket creation.

This service implements a 3-agent workflow:
1. Meeting Analyzer (Nemotron) - Extracts tickets from meeting transcript
2. Ticket Creator (Python Logic) - Creates tickets in Firestore
3. Diagram Generator (Nemotron) - Generates Mermaid diagram of tickets
"""

import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from firebase_admin import firestore
from difflib import SequenceMatcher

from app.services.nemotron_service import get_nemotron_client
from app.services.ticket_service import ticket_service
from app.services.user_service import user_service
from app.services.project_service import project_service
from app.services.label_service import label_service
from app.models.schemas import (
    TicketCreate,
    UserCreate,
    ProjectCreate,
    LabelCreate,
    Priority,
    TicketStatus
)


class AgentService:
    """Service for multi-agent meeting analysis workflow."""

    # ========================================================================
    # AGENT 1: MEETING TO TICKETS (NEMOTRON)
    # ========================================================================

    @staticmethod
    def analyze_meeting(transcript: str) -> Dict[str, Any]:
        """
        Agent 1: Analyze meeting transcript and extract ticket specifications.

        Args:
            transcript: The meeting transcript text

        Returns:
            Dict with 'success' and either 'data' (ticket specs) or 'error'
        """
        print("[Agent 1] Analyzing meeting transcript...")

        system_prompt = """You are an expert project manager analyzing meeting transcripts.
Extract actionable tickets from the meeting discussion.

Return ONLY a valid JSON object with this exact structure (no markdown, no explanations):
{
  "project_name": "string (project name or identifier from meeting)",
  "tickets": [
    {
      "title": "string (concise ticket title)",
      "description": "string (detailed description)",
      "priority": "urgent|high|medium|low|none",
      "estimated_hours": number (estimated hours, can be null),
      "assignee_name": "string (person's name, can be null)",
      "deadline": "YYYY-MM-DD (ISO date, can be null)",
      "labels": ["string (label names)"],
      "dependencies": ["ticket:0 (means depends on ticket at index 0, or null)"]
    }
  ]
}

Important rules:
- Extract real, actionable tasks only
- Use exact priority values: urgent, high, medium, low, or none
- Parse dates into YYYY-MM-DD format
- For dependencies, use "ticket:N" format where N is the index
- If no clear information, use null
- Return valid JSON only"""

        user_prompt = f"""Analyze this meeting transcript and extract actionable tickets:

{transcript}

Return the JSON object with project_name and tickets array."""

        try:
            # Call Nemotron using OpenAI SDK
            client = get_nemotron_client()

            response = client.chat.completions.create(
                model="meta/llama-3.1-70b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more structured output
                max_tokens=4096
            )

            content = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
                if content.startswith("json"):
                    content = content[4:].strip()

            ticket_specs = json.loads(content)

            # Validate structure
            if "project_name" not in ticket_specs or "tickets" not in ticket_specs:
                raise ValueError("Missing required fields: project_name or tickets")
            
            # Ensure tickets is a list
            if not isinstance(ticket_specs.get("tickets"), list):
                raise ValueError("tickets must be a list")

            ticket_count = len(ticket_specs['tickets'])
            print(f"[Agent 1] Extracted {ticket_count} tickets from meeting")
            
            if ticket_count == 0:
                print("[Agent 1] Warning: No tickets extracted from meeting transcript")

            return {
                "success": True,
                "data": ticket_specs
            }

        except json.JSONDecodeError as e:
            print(f"[Agent 1] JSON parse error: {str(e)}")
            print(f"[Agent 1] Raw content: {content[:500] if 'content' in locals() else 'N/A'}")
            return {
                "success": False,
                "error": f"Failed to parse AI response as JSON: {str(e)}"
            }
        except Exception as e:
            print(f"[Agent 1] Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error processing ticket specifications: {str(e)}"
            }

    # ========================================================================
    # AGENT 2: TICKET CREATOR (PYTHON LOGIC)
    # ========================================================================

    @staticmethod
    def _fuzzy_match_name(name: str, candidates: List[Dict]) -> Optional[Dict]:
        """Fuzzy match a name against a list of candidates."""
        if not name or not candidates:
            return None

        name_lower = name.lower().strip()
        best_match = None
        best_ratio = 0.0

        for candidate in candidates:
            candidate_name = candidate.get("name", "").lower().strip()
            ratio = SequenceMatcher(None, name_lower, candidate_name).ratio()

            if ratio > best_ratio:
                best_ratio = ratio
                best_match = candidate

        # Require at least 60% similarity
        return best_match if best_ratio >= 0.6 else None

    @staticmethod
    def _normalize_priority(priority_str: Optional[str]) -> Priority:
        """Normalize priority string to Priority enum."""
        if not priority_str:
            return Priority.medium

        priority_lower = priority_str.lower().strip()

        priority_map = {
            "urgent": Priority.urgent,
            "critical": Priority.urgent,
            "p0": Priority.urgent,
            "p1": Priority.urgent,
            "high": Priority.high,
            "p2": Priority.high,
            "important": Priority.high,
            "medium": Priority.medium,
            "p3": Priority.medium,
            "normal": Priority.medium,
            "low": Priority.low,
            "p4": Priority.low,
            "minor": Priority.low,
            "none": Priority.none,
            "": Priority.none,
        }

        return priority_map.get(priority_lower, Priority.medium)

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[str]:
        """Parse date string to ISO format (YYYY-MM-DD)."""
        if not date_str:
            return None

        try:
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    dt = datetime.strptime(date_str.strip(), fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
            return None
        except:
            return None

    @staticmethod
    def _generate_random_color() -> str:
        """Generate a random hex color."""
        return f"#{random.randint(0, 0xFFFFFF):06x}"

    @staticmethod
    def create_tickets_from_specs(
        db: firestore.Client,
        ticket_specs: Dict[str, Any],
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agent 2: Create tickets in Firestore from specifications.

        Args:
            db: Firestore client
            ticket_specs: Ticket specifications from Agent 1
            project_name: Override project name

        Returns:
            Dict with 'success' and either 'data' (created tickets) or 'error'
        """
        print("[Agent 2] Creating tickets from specifications...")

        try:
            # Use provided project name or extract from specs
            proj_name = project_name or ticket_specs.get("project_name")
            if not proj_name:
                proj_name = "General"

            # Get or create project
            project = project_service.get_project_by_name(db, proj_name)
            if not project:
                project = project_service.get_project_by_identifier(db, proj_name)

            if not project:
                print(f"[Agent 2] Creating new project: {proj_name}")
                project = project_service.create_project(db, ProjectCreate(
                    name=proj_name,
                    identifier=proj_name[:10].upper().replace(" ", ""),
                    description=f"Auto-created from meeting analysis"
                ))

            project_id = project["id"]
            print(f"[Agent 2] Using project: {proj_name} (ID: {project_id})")

            # Get all users for fuzzy matching
            all_users = user_service.get_all_users(db)

            # Get existing labels for this project
            existing_labels = label_service.get_all_labels(db, project_id=project_id)
            label_map = {label["name"].lower(): label for label in existing_labels}

            # Process each ticket spec
            created_tickets = []
            ticket_id_map = {}  # Map index to created ticket ID

            for idx, spec in enumerate(ticket_specs.get("tickets", [])):
                print(f"[Agent 2] Processing ticket {idx + 1}/{len(ticket_specs['tickets'])}: {spec.get('title', 'Untitled')}")

                # Handle assignee
                assignee_id = None
                assignee_name = spec.get("assignee_name")
                if assignee_name:
                    matched_user = AgentService._fuzzy_match_name(assignee_name, all_users)
                    if matched_user:
                        assignee_id = matched_user["id"]
                        print(f"[Agent 2]   Matched assignee: {assignee_name} -> {matched_user['name']}")
                    else:
                        print(f"[Agent 2]   Creating new user: {assignee_name}")
                        new_user = user_service.create_user(db, UserCreate(
                            name=assignee_name,
                            color=AgentService._generate_random_color()
                        ))
                        assignee_id = new_user["id"]
                        all_users.append(new_user)

                # Handle labels
                label_ids = []
                for label_name in spec.get("labels", []):
                    label_key = label_name.lower().strip()
                    if label_key in label_map:
                        label_ids.append(label_map[label_key]["id"])
                    else:
                        print(f"[Agent 2]   Creating new label: {label_name}")
                        new_label = label_service.create_label(db, LabelCreate(
                            name=label_name,
                            color=AgentService._generate_random_color(),
                            project_id=project_id
                        ))
                        label_ids.append(new_label["id"])
                        label_map[label_key] = new_label

                # Handle dependencies (parent ticket)
                parent_ticket_id = None
                dependencies = spec.get("dependencies", [])
                if dependencies:
                    for dep in dependencies:
                        if isinstance(dep, str) and dep.startswith("ticket:"):
                            try:
                                dep_idx = int(dep.split(":")[1])
                                if dep_idx in ticket_id_map:
                                    parent_ticket_id = ticket_id_map[dep_idx]
                                    print(f"[Agent 2]   Set parent: ticket at index {dep_idx}")
                                    break
                            except (ValueError, IndexError):
                                pass

                # Normalize priority
                priority = AgentService._normalize_priority(spec.get("priority"))

                # Parse deadline
                deadline = AgentService._parse_date(spec.get("deadline"))

                # Create ticket
                ticket_data = TicketCreate(
                    title=spec.get("title", "Untitled Task"),
                    summary=spec.get("description"),
                    priority=priority,
                    estimated_hours=spec.get("estimated_hours"),
                    assignee_id=assignee_id,
                    end_date=deadline,
                    project_id=project_id,
                    parent_ticket_id=parent_ticket_id,
                    label_ids=label_ids,
                    status=TicketStatus.open
                )

                created_ticket = ticket_service.create_ticket(db, ticket_data)
                created_tickets.append(created_ticket)
                ticket_id_map[idx] = created_ticket["id"]

                print(f"[Agent 2]   ✓ Created ticket: {created_ticket['id']}")

            print(f"[Agent 2] Successfully created {len(created_tickets)} tickets")

            return {
                "success": True,
                "data": {
                    "tickets": created_tickets,
                    "project": project,
                    "summary": f"Created {len(created_tickets)} ticket(s) in project '{proj_name}'"
                }
            }

        except ValueError as e:
            print(f"[Agent 2] Validation error: {str(e)}")
            return {
                "success": False,
                "error": f"Validation error: {str(e)}"
            }
        except Exception as e:
            print(f"[Agent 2] Error creating tickets: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error creating tickets: {str(e)}"
            }

    # ========================================================================
    # AGENT 3: DIAGRAM GENERATOR (NEMOTRON)
    # ========================================================================

    @staticmethod
    def generate_diagram(tickets: List[Dict[str, Any]], project_name: str) -> Dict[str, Any]:
        """
        Agent 3: Generate Mermaid diagram from created tickets.

        Args:
            tickets: List of created tickets
            project_name: Project name

        Returns:
            Dict with 'success' and either 'diagram' (Mermaid syntax) or 'error'
        """
        print(f"[Agent 3] Generating diagram for {len(tickets)} tickets...")

        # Prepare ticket summary
        ticket_summary = []
        for idx, ticket in enumerate(tickets):
            summary = {
                "id": ticket.get("id"),
                "index": idx,
                "title": ticket.get("title"),
                "priority": ticket.get("priority"),
                "assignee_id": ticket.get("assignee_id"),
                "parent_ticket_id": ticket.get("parent_ticket_id"),
                "estimated_hours": ticket.get("estimated_hours")
            }
            ticket_summary.append(summary)

        system_prompt = """You are an expert at creating Mermaid diagrams for project visualization.
Generate a Mermaid flowchart showing the tickets and their relationships.

Return ONLY the Mermaid diagram code (no markdown code blocks, no explanations).

Requirements:
- Use flowchart format (graph TD or graph LR)
- Show ticket dependencies (parent-child relationships)
- Color-code by priority: urgent=red, high=orange, medium=yellow, low=green, none=gray
- Include ticket titles (abbreviated if too long)
- Make it visually clear and readable

Example output format:
graph TD
    A[Ticket 1: Setup] --> B[Ticket 2: Implementation]
    B --> C[Ticket 3: Testing]
    style A fill:#ff6b6b
    style B fill:#ffd93d
    style C fill:#6bcf7f"""

        user_prompt = f"""Create a Mermaid diagram for project "{project_name}" with these tickets:

{json.dumps(ticket_summary, indent=2)}

Generate the Mermaid diagram code."""

        try:
            # Call Nemotron using OpenAI SDK
            client = get_nemotron_client()

            response = client.chat.completions.create(
                model="meta/llama-3.1-70b-instruct",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5,
                max_tokens=2048
            )

            diagram = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if diagram.startswith("```"):
                lines = diagram.split("\n")
                diagram = "\n".join(lines[1:-1]) if len(lines) > 2 else diagram
                if diagram.startswith("mermaid"):
                    diagram = diagram[7:].strip()

            print(f"[Agent 3] Generated diagram ({len(diagram)} characters)")

            return {
                "success": True,
                "diagram": diagram
            }

        except Exception as e:
            print(f"[Agent 3] Error generating diagram: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Error generating diagram: {str(e)}"
            }

    # ========================================================================
    # COMPLETE WORKFLOW
    # ========================================================================

    @staticmethod
    def process_meeting_transcript(
        db: firestore.Client,
        transcript: str,
        project_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete 3-agent workflow: Analyze meeting → Create tickets → Generate diagram.

        Args:
            db: Firestore client
            transcript: Meeting transcript text
            project_name: Optional override for project name

        Returns:
            Dict with 'success' and either complete results or 'error'
        """
        print(f"[AgentService] Starting complete workflow...")

        # Agent 1: Analyze meeting
        analysis_result = AgentService.analyze_meeting(transcript)
        if not analysis_result["success"]:
            return {
                "success": False,
                "error": f"Agent 1 failed: {analysis_result['error']}",
                "stage": "analysis"
            }

        ticket_specs = analysis_result["data"]

        # Agent 2: Create tickets
        creation_result = AgentService.create_tickets_from_specs(
            db, ticket_specs, project_name
        )
        if not creation_result["success"]:
            return {
                "success": False,
                "error": f"Agent 2 failed: {creation_result['error']}",
                "stage": "creation",
                "ticket_specs": ticket_specs
            }

        created_tickets = creation_result["data"]["tickets"]
        project = creation_result["data"]["project"]

        # Agent 3: Generate diagram
        diagram_result = AgentService.generate_diagram(
            created_tickets,
            project["name"]
        )

        # Diagram generation is optional - don't fail if it errors
        diagram = None
        if diagram_result["success"]:
            diagram = diagram_result["diagram"]
        else:
            print(f"[AgentService] Warning: Diagram generation failed: {diagram_result.get('error')}")

        print(f"[AgentService] ✓ Complete workflow finished successfully")

        return {
            "success": True,
            "data": {
                "tickets": created_tickets,
                "project": project,
                "diagram": diagram,
                "summary": creation_result["data"]["summary"],
                "ticket_count": len(created_tickets)
            }
        }


# Singleton instance
agent_service = AgentService()
