# Research Paper RAG Frontend

A modern Next.js frontend for the Research Paper RAG system. This application provides a beautiful, responsive interface for querying research papers using RAG (Retrieval-Augmented Generation) technology.

## Features

- 🔍 **Query Interface** - Ask questions about your research papers with AI-powered answers
- 📚 **Paper Library** - Browse and manage uploaded research papers
- 📤 **Upload Papers** - Drag & drop interface for uploading PDF research papers
- 📊 **Query History** - View past queries and their responses
- 🌓 **Dark Mode** - Automatic dark mode support
- 📱 **Responsive Design** - Works beautifully on desktop, tablet, and mobile

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API requests
- **Lucide React** - Beautiful icon library
- **React Dropzone** - File upload with drag & drop
- **date-fns** - Date formatting utilities

## Getting Started

### Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000` (default)

### Installation

1. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

2. Install dependencies:

   ```bash
   npm install
   ```

3. Create a `.env.local` file (already created with default values):

   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. Run the development server:

   ```bash
   npm run dev
   ```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with metadata
│   ├── page.tsx            # Main page with tab navigation
│   └── globals.css         # Global styles with Tailwind
├── components/
│   ├── QueryInterface.tsx  # Query papers component
│   ├── PaperLibrary.tsx    # Browse papers component
│   ├── UploadPaper.tsx     # Upload papers component
│   └── QueryHistoryView.tsx # Query history component
├── lib/
│   └── api.ts              # API client and types
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
└── next.config.js
```

## API Integration

The frontend connects to the following backend API endpoints:

- `POST /api/upload` - Upload a research paper
- `GET /api/papers` - List all papers
- `GET /api/papers/{id}` - Get paper details
- `DELETE /api/papers/{id}` - Delete a paper
- `GET /api/papers/{id}/stats` - Get paper statistics
- `POST /api/query` - Query papers with a question
- `GET /api/queries/history` - Get query history
- `GET /health` - Health check

All API configuration is in `lib/api.ts`.

## Configuration

### Environment Variables

- `NEXT_PUBLIC_API_URL` - Backend API URL (default: `http://localhost:8000`)

### Customization

- **Colors**: Edit `tailwind.config.ts` to customize the color scheme
- **Styles**: Modify `app/globals.css` for global style changes
- **API Client**: Update `lib/api.ts` to modify API configuration

## Features Overview

### 1. Query Interface

- Ask natural language questions about research papers
- Adjust the number of sources (top K) with a slider
- View AI-generated answers with citations
- See response time and confidence scores

### 2. Paper Library

- View all uploaded papers in a card layout
- Click to view detailed information
- Delete papers you no longer need
- See paper metadata, sections, and chunks

### 3. Upload Papers

- Drag & drop PDF files
- Automatic processing and indexing
- View detailed upload results
- See detected sections and metadata

### 4. Query History

- Browse past queries chronologically
- View full query details and answers
- See which papers were referenced
- Track response times

## Development

### Type Safety

The project uses TypeScript for type safety. API types are defined in `lib/api.ts`:

- `Paper` - Research paper metadata
- `QueryResult` - Query response with citations
- `QueryHistory` - Historical query record

### Styling

Tailwind CSS is used for styling with:

- Dark mode support via `dark:` classes
- Responsive design with `sm:`, `md:`, `lg:` breakpoints
- Custom color gradients and shadows
- Smooth transitions and animations

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### Cannot connect to backend

Make sure:

1. Backend is running on `http://localhost:8000`
2. `.env.local` has the correct `NEXT_PUBLIC_API_URL`
3. CORS is enabled on the backend

### TypeScript errors during development

The TypeScript errors you see during file creation are expected and will be resolved once you run `npm install` to install all dependencies.

### Build errors

Run `npm install` to ensure all dependencies are installed before building.

## License

This project is part of the Research Paper RAG Assessment.
