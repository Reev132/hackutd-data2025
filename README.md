# Catalyst

An AI-powered PM productivity agent that transforms meeting notes into structured deliverables using NVIDIA Nemotron.

## Overview

Catalyst helps Product Managers save time by automatically converting raw meeting notes into professional documents like PRDs, user stories, action items, and summaries. It leverages NVIDIA's Llama 3.3 Nemotron Super 49B model for intelligent content generation and integrates seamlessly with Notion for export.

## Features

- **AI-Powered Processing**: Uses NVIDIA Nemotron (llama-3.3-nemotron-super-49b-v1.5) for intelligent content generation
- **Multiple Output Types**:
  - Product Requirements Documents (PRDs)
  - User Stories with acceptance criteria
  - Action Items with assignments and priorities
  - Meeting Summaries
- **Notion Integration**: Export processed content directly to Notion
- **Modern UI**: Clean, responsive interface built with Next.js 14 and shadcn/ui
- **Real-time Processing**: Fast API responses with streaming support

## Tech Stack

### Frontend
- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **shadcn/ui** components
- **Lucide Icons**

### Backend
- **FastAPI** (Python)
- **NVIDIA Nemotron API** (via OpenAI SDK)
- **Notion API**
- **Pydantic** for data validation
- **python-dotenv** for environment management

## Project Structure

```
catalyst/
├── frontend/              # Next.js application
│   ├── app/              # App router pages
│   ├── components/       # React components
│   │   ├── ui/          # shadcn/ui components
│   │   └── CatalystApp.tsx
│   ├── lib/             # Utility functions
│   └── public/          # Static assets
├── backend/              # FastAPI server
│   ├── app/
│   │   ├── models/      # Pydantic schemas
│   │   ├── routes/      # API endpoints
│   │   ├── services/    # Business logic
│   │   │   ├── nemotron_service.py
│   │   │   └── notion_service.py
│   │   └── main.py      # FastAPI app
│   └── requirements.txt
├── .env.example          # Environment template
└── README.md
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+
- NVIDIA API Key ([Get one here](https://build.nvidia.com/))
- Notion Integration Token ([Create integration](https://www.notion.so/my-integrations))

### Installation

#### 1. Clone the repository

```bash
git clone <your-repo-url>
cd catalyst
```

#### 2. Set up environment variables

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# NVIDIA API Configuration
NVIDIA_API_KEY=your_nvidia_api_key_here

# Notion API Configuration
NOTION_API_KEY=your_notion_integration_token_here
NOTION_PARENT_PAGE_ID=your_default_parent_page_id_here

# Backend Configuration
BACKEND_URL=http://localhost:8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. Set up the Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp ../.env .env
```

#### 4. Set up the Frontend

```bash
cd frontend

# Install dependencies
npm install

# The .env.local file is already created
```

### Running the Application

#### Start the Backend Server

```bash
cd backend
source venv/bin/activate  # Activate venv if not already active
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

#### Start the Frontend Development Server

In a new terminal:

```bash
cd frontend
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

### 1. Process Meeting Notes

1. Paste your raw meeting notes into the input area
2. Select the desired output type:
   - **Summary**: Concise meeting overview
   - **PRD**: Full Product Requirements Document
   - **User Stories**: Agile user stories with acceptance criteria
   - **Action Items**: Extracted tasks with assignments
3. Click "Generate" to process with NVIDIA Nemotron
4. View the AI-generated output in the right panel

### 2. Export to Notion

1. After processing, enter a title for your Notion page
2. Click "Export to Notion"
3. The content will be created in your Notion workspace
4. You'll receive a URL to view the page

## API Endpoints

### POST `/api/catalyst/process`

Process meeting notes and generate structured output.

**Request Body:**
```json
{
  "notes": "Your meeting notes here...",
  "output_type": "prd" | "user_story" | "action_items" | "summary"
}
```

**Response:**
```json
{
  "content": "Generated content...",
  "output_type": "prd"
}
```

### POST `/api/catalyst/export-notion`

Export content to Notion.

**Request Body:**
```json
{
  "content": "Content to export...",
  "page_title": "My PRD",
  "database_id": "optional-database-id"
}
```

**Response:**
```json
{
  "success": true,
  "notion_url": "https://notion.so/...",
  "message": "Successfully exported to Notion"
}
```

## Configuration

### NVIDIA API

1. Sign up at [NVIDIA Build](https://build.nvidia.com/)
2. Navigate to the Nemotron model page
3. Generate an API key
4. Add to your `.env` file

### Notion API

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Create a new integration
3. Copy the Internal Integration Token
4. Share a Notion page with your integration
5. Copy the page ID from the URL
6. Add both to your `.env` file

## Development

### Backend Development

The backend uses FastAPI with automatic API documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Development

The frontend uses Next.js 14 with:
- Hot reload on file changes
- TypeScript for type safety
- Tailwind CSS for styling
- shadcn/ui for components

## Deployment

### Backend Deployment

The FastAPI backend can be deployed to:
- **Railway**: One-click deployment
- **Render**: Free tier available
- **AWS Lambda**: Using Mangum adapter
- **DigitalOcean App Platform**

### Frontend Deployment

The Next.js frontend can be deployed to:
- **Vercel**: Recommended (creators of Next.js)
- **Netlify**
- **Cloudflare Pages**

## Troubleshooting

### Backend Issues

**Import errors:**
```bash
# Ensure you're in the backend directory with venv activated
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**NVIDIA API errors:**
- Check your API key is valid
- Ensure you have credits/quota remaining
- Verify the model name is correct

### Frontend Issues

**API connection errors:**
- Ensure backend is running on port 8000
- Check NEXT_PUBLIC_API_URL in .env.local
- Verify CORS settings in backend

**Build errors:**
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - feel free to use this project for your own purposes.

## Acknowledgments

- Built for HackUTD 2025
- Powered by NVIDIA Nemotron
- UI components by shadcn/ui
- Icons by Lucide

## Support

For issues and questions, please open an issue on GitHub.

---

**Built with love for Product Managers everywhere**
