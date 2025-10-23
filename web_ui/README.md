# Smart RAG Web UI

A beautiful, modern web interface for the Smart RAG system designed specifically for law students.

## 🚀 Quick Start

### Option 1: Using Python Server (Recommended)

1. **Start your RAG API** (in one terminal):
   ```bash
   python -m app.api
   ```

2. **Start the Web UI** (in another terminal):
   ```bash
   # Windows
   cd web_ui
   python server.py
   
   # Or double-click: start_web_ui.bat
   ```

3. **Open your browser** to `http://localhost:8080`

### Option 2: Using Any Web Server

1. **Start your RAG API**:
   ```bash
   python -m app.api
   ```

2. **Serve the files** using any web server:
   ```bash
   # Using Python's built-in server
   cd web_ui
   python -m http.server 8080
   
   # Using Node.js (if you have it)
   npx serve .
   
   # Using any other web server
   # Just serve the web_ui directory
   ```

3. **Open your browser** to `http://localhost:8080`

## ✨ Features

### 💬 Interactive Chat
- Real-time conversation with your RAG system
- Message history with timestamps
- Source citations for academic integrity
- Quick action buttons for legal topics

### 📁 Document Upload
- Drag & drop file upload
- Support for TXT, PDF, DOCX files
- Progress tracking and status updates
- File preview with icons

### 🔍 Topic Search
- Search specific legal topics
- Relevance scoring
- Popular topic suggestions
- Real-time search results

### ⚙️ Settings
- API configuration
- Chunk size and overlap settings
- Temperature control
- Connection testing

## 🎨 Design Features

- **Modern UI** with gradient backgrounds
- **Responsive design** for all devices
- **Smooth animations** and transitions
- **Professional styling** suitable for academic use
- **Mobile-friendly** interface
- **Accessibility** features

## 🔧 Configuration

The web UI automatically connects to your RAG API at `http://localhost:8000`. You can change this in the Settings section.

## 📱 Mobile Support

The interface is fully responsive and works great on:
- Desktop computers
- Tablets
- Mobile phones
- All modern browsers

## 🛠️ Troubleshooting

### Connection Issues
1. Make sure your RAG API is running on port 8000
2. Check the API URL in Settings
3. Use the "Test Connection" button

### File Upload Issues
1. Ensure your RAG API supports file upload
2. Check file format (TXT, PDF, DOCX only)
3. Verify file size (not too large)

### Browser Compatibility
- Chrome/Chromium (recommended)
- Firefox
- Safari
- Edge

## 📂 File Structure

```
web_ui/
├── index.html          # Main HTML file
├── styles.css          # CSS styling
├── script.js           # JavaScript functionality
├── server.py           # Python web server
├── start_web_ui.bat    # Windows startup script
├── start_web_ui.sh     # Linux/Mac startup script
└── README.md           # This file
```

## 🎯 Perfect for Law Students

This web UI is specifically designed for law students with:
- **Academic-friendly** interface
- **Source citations** for research
- **Legal topic** quick actions
- **Professional** appearance
- **Easy navigation** for studying

Enjoy your Smart RAG system! 📚⚖️
