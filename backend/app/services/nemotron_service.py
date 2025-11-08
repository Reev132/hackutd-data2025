import os
from openai import OpenAI

class NemotronService:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=os.getenv("NVIDIA_API_KEY")
        )
        self.model = "nvidia/llama-3.3-nemotron-super-49b-v1.5"

    def generate_prd(self, notes: str) -> str:
        """Generate a Product Requirements Document from meeting notes."""
        prompt = f"""You are an expert Product Manager. Convert the following meeting notes into a comprehensive Product Requirements Document (PRD).

Meeting Notes:
{notes}

Generate a well-structured PRD with the following sections:
1. Executive Summary
2. Problem Statement
3. Goals and Objectives
4. User Stories
5. Functional Requirements
6. Non-Functional Requirements
7. Success Metrics
8. Timeline and Milestones

Format the output in clear markdown with proper headings and bullet points."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )

        return response.choices[0].message.content

    def generate_user_stories(self, notes: str) -> str:
        """Generate user stories from meeting notes."""
        prompt = f"""You are an expert Product Manager. Convert the following meeting notes into well-structured user stories.

Meeting Notes:
{notes}

Generate user stories in the format:
- Title: [Brief title]
- As a [user type]
- I want [goal]
- So that [benefit]
- Acceptance Criteria:
  - [criterion 1]
  - [criterion 2]
  - [criterion 3]

Create multiple user stories covering all features and requirements mentioned in the notes. Format in markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2048
        )

        return response.choices[0].message.content

    def generate_action_items(self, notes: str) -> str:
        """Extract and organize action items from meeting notes."""
        prompt = f"""You are an expert Project Manager. Extract all action items from the following meeting notes.

Meeting Notes:
{notes}

Generate a list of action items with the following format:
- Task: [Clear description of the task]
- Assignee: [Person responsible, if mentioned]
- Deadline: [Due date, if mentioned]
- Priority: [High/Medium/Low based on context]

Format the output in markdown with clear sections. If information is not available, mark as "TBD"."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1024
        )

        return response.choices[0].message.content

    def generate_summary(self, notes: str) -> str:
        """Generate a concise summary of meeting notes."""
        prompt = f"""You are an expert at summarizing meetings. Create a concise, well-organized summary of the following meeting notes.

Meeting Notes:
{notes}

Generate a summary with:
1. Key Points Discussed
2. Decisions Made
3. Next Steps
4. Open Questions

Keep it concise but comprehensive. Format in markdown."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1024
        )

        return response.choices[0].message.content
