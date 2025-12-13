# DS-Star Frontend

Modern React + TypeScript web interface for the DS-Star Multi-Agent System.

## Features

- 🎨 **Modern UI**: Clean, dark-themed interface with smooth animations
- 💬 **Real-time Chat**: WebSocket-based streaming of agent reasoning
- 📊 **Interactive Charts**: Plotly.js integration for data visualizations
- 🤖 **Agent Routing**: Visual display of which specialists are handling queries
- 📱 **Responsive Design**: Works on desktop and tablet devices
- ⚡ **Fast**: Built with Vite for instant hot module replacement

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Plotly.js** - Interactive charts
- **React Markdown** - Markdown rendering
- **Lucide React** - Icon library
- **WebSocket** - Real-time communication

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API server running on port 8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── Header.tsx       # Top navigation bar
│   │   ├── Sidebar.tsx      # Specialist list and examples
│   │   ├── ChatInterface.tsx # Main chat container
│   │   ├── MessageList.tsx  # Message display
│   │   ├── MessageBubble.tsx # Individual message
│   │   ├── StreamingIndicator.tsx # Real-time events
│   │   └── ChartDisplay.tsx # Chart visualization
│   ├── types.ts             # TypeScript interfaces
│   ├── App.tsx              # Main app component
│   ├── App.css              # App styles
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles
├── index.html               # HTML template
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript config
├── vite.config.ts           # Vite config
└── README.md                # This file
```

## API Integration

The frontend connects to the backend API at `http://localhost:8000`:

- **REST API**: `/api/status`, `/api/query`, `/api/history`
- **WebSocket**: `/ws/query` for real-time streaming

The Vite dev server proxies these requests automatically.

## Environment Variables

No environment variables are required for development. The API URL is configured in `vite.config.ts`.

## Customization

### Colors

The color scheme is defined in CSS custom properties. Main colors:

- Background: `#0f172a` (dark blue)
- Surface: `#1e293b` (lighter blue)
- Primary: `#3b82f6` (blue)
- Text: `#e2e8f0` (light gray)

### Components

All components are modular and can be customized independently. Each component has its own CSS file for styling.

## Troubleshooting

**"Failed to connect to DS-Star system"**
- Ensure the backend server is running on port 8000
- Check that CORS is properly configured in the backend

**WebSocket connection fails**
- Verify the WebSocket endpoint is accessible
- Check browser console for connection errors

**Charts not displaying**
- Ensure Plotly.js is properly installed
- Check that chart data includes `plotly_json` field

## License

[Add license information]
