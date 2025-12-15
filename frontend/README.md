# DS-STAR Workbench Frontend

A modern React-based UI for the DS-Star multi-agent data science system. Features an iterative workflow with real-time streaming, code display, interactive visualizations, and verification steps.

## Features

- **Analysis Timeline**: Step-by-step view of the iterative analysis workflow
- **Code Display**: Syntax-highlighted Python code with copy functionality
- **Interactive Charts**: Plotly.js visualizations with zoom, pan, and export
- **Verifier Assessment**: Approve or decline analysis results with feedback
- **Real-time Updates**: WebSocket-based streaming for live progress

## Tech Stack

- React 18 + TypeScript
- Tailwind CSS v4 for styling
- Radix UI for accessible components
- Framer Motion for animations
- Plotly.js for interactive charts
- react-syntax-highlighter for code display

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Backend server running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Opens at http://localhost:3000

### Build

```bash
npm run build
```

Output in `dist/` folder.

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── content/       # CodeDisplay, ChartDisplay, etc.
│   │   ├── layout/        # AppShell, Header
│   │   ├── sidebar/       # ActiveDatasetPanel, ResearchGoalPanel
│   │   └── timeline/      # AnalysisTimeline, StepCard, IterationCard
│   ├── hooks/             # useAnalysis, useWebSocket
│   ├── services/          # API and WebSocket services
│   ├── types/             # TypeScript definitions
│   ├── App.tsx
│   └── index.css          # Tailwind + custom styles
├── tailwind.config.js
├── vite.config.ts
└── package.json
```

## API Integration

The frontend connects to the backend via:

- `GET /api/status` - System status and dataset info
- `POST /api/analyze` - Start new analysis
- `WS /ws/stream` - Real-time analysis events

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
