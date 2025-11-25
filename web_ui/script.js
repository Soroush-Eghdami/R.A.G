// Smart RAG Web UI - Alpine.js Application
function ragApp() {
    return {
        // State
        currentSection: 'chat',
        chatHistory: [],
        currentQuestion: '',
        includeSources: true,
        topK: 3,
        apiUrl: 'http://localhost:8000',
        isLoading: false,
        loadingText: 'Processing...',
        connectionStatus: 'disconnected',
        connectionStatusText: 'Disconnected',
        isDragging: false,
        toasts: [],
        darkMode: false,

        // Initialize
        init() {
            this.loadSettings();
            this.checkConnection();
            this.setupTheme();
            setInterval(() => this.checkConnection(), 30000); // Check every 30 seconds
        },

        // Theme Management
        setupTheme() {
            const saved = localStorage.getItem('darkMode');
            if (saved === 'true' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                document.documentElement.classList.add('dark');
                this.darkMode = true;
            }
        },

        toggleTheme() {
            this.darkMode = !this.darkMode;
            if (this.darkMode) {
                document.documentElement.classList.add('dark');
                localStorage.setItem('darkMode', 'true');
            } else {
                document.documentElement.classList.remove('dark');
                localStorage.setItem('darkMode', 'false');
            }
        },

        // Connection Management
        async checkConnection() {
            try {
                const response = await fetch(`${this.apiUrl}/health`);
                const data = await response.json();
                
                if (response.ok && data.status === 'healthy') {
                    this.connectionStatus = 'connected';
                    this.connectionStatusText = 'Connected';
                } else if (data.status === 'degraded') {
                    this.connectionStatus = 'degraded';
                    this.connectionStatusText = 'Degraded';
                } else {
                    this.connectionStatus = 'disconnected';
                    this.connectionStatusText = 'Disconnected';
                }
            } catch (error) {
                this.connectionStatus = 'disconnected';
                this.connectionStatusText = 'Disconnected';
            }
        },

        // Chat Functions
        async sendMessage() {
            if (!this.currentQuestion.trim() || this.isLoading) return;

            const question = this.currentQuestion.trim();
            this.currentQuestion = '';

            // Add user message
            this.chatHistory.push({
                sender: 'user',
                content: question,
                time: new Date().toLocaleTimeString(),
                sources: null
            });

            this.isLoading = true;
            this.loadingText = 'Generating response...';

            try {
                const response = await fetch(`${this.apiUrl}/query`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question: question,
                        top_k: parseInt(this.topK),
                        include_sources: this.includeSources
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    this.chatHistory.push({
                        sender: 'assistant',
                        content: data.answer,
                        time: new Date().toLocaleTimeString(),
                        sources: data.sources || []
                    });
                } else {
                    this.showToast(`Error: ${data.detail || 'Unknown error occurred'}`, 'error');
                }
            } catch (error) {
                this.showToast(`Connection error: ${error.message}`, 'error');
            } finally {
                this.isLoading = false;
                // Scroll to bottom
                setTimeout(() => {
                    const chatContainer = document.querySelector('[x-show="currentSection === \'chat\'"] .overflow-y-auto');
                    if (chatContainer) {
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    }
                }, 100);
            }
        },

        formatMessage(content) {
            // Simple markdown-like formatting
            return content
                .replace(/\n/g, '<br>')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>');
        },

        // File Upload
        handleFileSelect(event) {
            const files = Array.from(event.target.files);
            this.uploadFiles(files);
        },

        handleFileDrop(event) {
            this.isDragging = false;
            const files = Array.from(event.dataTransfer.files);
            this.uploadFiles(files);
        },

        async uploadFiles(files) {
            if (files.length === 0) return;

            this.isLoading = true;
            this.loadingText = 'Uploading and processing files...';

            for (const file of files) {
                try {
                    const formData = new FormData();
                    formData.append('file', file);

                    // Note: This is a simplified upload. In production, you'd need to handle file uploads properly
                    // For now, we'll show a toast that file upload needs to be implemented via API
                    this.showToast(`File upload for ${file.name} - Please use CLI for now`, 'info');
                } catch (error) {
                    this.showToast(`Error uploading ${file.name}: ${error.message}`, 'error');
                }
            }

            this.isLoading = false;
        },

        // Settings
        saveSettings() {
            localStorage.setItem('ragSettings', JSON.stringify({
                apiUrl: this.apiUrl,
                includeSources: this.includeSources,
                topK: this.topK
            }));
            this.showToast('Settings saved successfully!', 'success');
            this.checkConnection();
        },

        loadSettings() {
            const saved = localStorage.getItem('ragSettings');
            if (saved) {
                const settings = JSON.parse(saved);
                this.apiUrl = settings.apiUrl || this.apiUrl;
                this.includeSources = settings.includeSources !== undefined ? settings.includeSources : true;
                this.topK = settings.topK || 3;
            }
        },

        async testConnection() {
            this.isLoading = true;
            this.loadingText = 'Testing connection...';
            await this.checkConnection();
            this.isLoading = false;

            if (this.connectionStatus === 'connected') {
                this.showToast('Connection successful!', 'success');
            } else {
                this.showToast('Connection failed. Check your API URL.', 'error');
            }
        },

        // Toast Notifications
        showToast(message, type = 'info') {
            const toast = { message, type, id: Date.now() };
            this.toasts.push(toast);
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== toast.id);
            }, 5000);
        }
    }
}
