// Smart RAG Web UI JavaScript
class SmartRAG {
    constructor() {
        this.apiUrl = 'http://localhost:8000';
        this.isConnected = false;
        this.chatHistory = [];
        this.currentSection = 'chat';
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.checkConnection();
        this.loadSettings();
    }
    
    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const section = item.dataset.section;
                this.switchSection(section);
            });
        });
        
        // Chat functionality
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('questionInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        document.getElementById('clearChat').addEventListener('click', () => this.clearChat());
        
        // Quick action buttons
        document.querySelectorAll('.action-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const topic = btn.dataset.topic;
                this.askTopicQuestion(topic);
            });
        });
        
        // Upload functionality
        document.getElementById('uploadArea').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        document.getElementById('fileInput').addEventListener('change', (e) => this.handleFileUpload(e));
        document.getElementById('browseFiles').addEventListener('click', (e) => {
            e.preventDefault();
            document.getElementById('fileInput').click();
        });
        
        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileUpload(e);
        });
        
        // Search functionality
        document.getElementById('searchBtn').addEventListener('click', () => this.searchTopics());
        document.getElementById('topicSearch').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.searchTopics();
            }
        });
        
        // Settings
        document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
        document.getElementById('testConnection').addEventListener('click', () => this.testConnection());
        document.getElementById('temperature').addEventListener('input', (e) => {
            document.getElementById('temperatureValue').textContent = e.target.value;
        });
    }
    
    switchSection(section) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-section="${section}"]`).classList.add('active');
        
        // Update content
        document.querySelectorAll('.content-section').forEach(sec => {
            sec.classList.remove('active');
        });
        document.getElementById(`${section}-section`).classList.add('active');
        
        this.currentSection = section;
        
        // Load section-specific data
        if (section === 'search') {
            this.loadSearchResults();
        }
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            const data = await response.json();
            
            this.isConnected = response.ok;
            this.updateConnectionStatus(data);
        } catch (error) {
            this.isConnected = false;
            this.updateConnectionStatus({ status: 'error', error: error.message });
        }
    }
    
    updateConnectionStatus(data) {
        const statusIndicator = document.getElementById('modelStatus');
        const modelText = document.getElementById('modelText');
        
        if (data.status === 'healthy') {
            statusIndicator.className = 'status-indicator';
            modelText.textContent = 'Connected';
        } else if (data.status === 'degraded') {
            statusIndicator.className = 'status-indicator warning';
            modelText.textContent = 'Degraded';
        } else {
            statusIndicator.className = 'status-indicator error';
            modelText.textContent = 'Disconnected';
        }
    }
    
    async sendMessage() {
        const input = document.getElementById('questionInput');
        const question = input.value.trim();
        
        if (!question) return;
        
        // Add user message to chat
        this.addMessage('user', question);
        input.value = '';
        
        // Show loading
        this.showLoading('Generating response...');
        
        try {
            const response = await fetch(`${this.apiUrl}/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    top_k: parseInt(document.getElementById('topK').value),
                    include_sources: document.getElementById('includeSources').checked
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addMessage('assistant', data.answer, data.sources);
            } else {
                this.addMessage('assistant', `Error: ${data.detail || 'Unknown error occurred'}`);
            }
        } catch (error) {
            this.addMessage('assistant', `Connection error: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }
    
    addMessage(sender, content, sources = null) {
        const messagesContainer = document.getElementById('chatMessages');
        
        // Remove welcome message if it exists
        const welcomeMessage = messagesContainer.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;
        
        const time = new Date().toLocaleTimeString();
        
        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources">
                    <h4>Sources:</h4>
                    ${sources.map((source, index) => `
                        <div class="source-item">
                            <strong>Source ${index + 1}:</strong> ${source.substring(0, 200)}${source.length > 200 ? '...' : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        messageDiv.innerHTML = `
            <div class="message-content">${content}</div>
            <div class="message-time">${time}</div>
            ${sourcesHtml}
        `;
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Add to chat history
        this.chatHistory.push({ sender, content, time, sources });
    }
    
    clearChat() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-content">
                    <i class="fas fa-graduation-cap"></i>
                    <h3>Welcome to Smart RAG for Law Students!</h3>
                    <p>Ask any legal question and get comprehensive answers from your knowledge base.</p>
                    <div class="example-questions">
                        <h4>Try asking:</h4>
                        <ul>
                            <li>"What are the elements of negligence in tort law?"</li>
                            <li>"Explain the difference between civil and criminal law"</li>
                            <li>"What is the statute of limitations for contract disputes?"</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
        this.chatHistory = [];
    }
    
    askTopicQuestion(topic) {
        const topicQuestions = {
            'contract-law': 'What are the key elements of a valid contract?',
            'tort-law': 'What are the elements of negligence in tort law?',
            'criminal-law': 'What is the difference between misdemeanor and felony?',
            'constitutional-law': 'What are the fundamental rights protected by the constitution?'
        };
        
        const question = topicQuestions[topic];
        if (question) {
            document.getElementById('questionInput').value = question;
            this.switchSection('chat');
        }
    }
    
    async handleFileUpload(event) {
        const files = event.target.files || event.dataTransfer.files;
        if (!files.length) return;
        
        this.showLoading('Uploading and processing files...');
        
        for (let file of files) {
            await this.uploadFile(file);
        }
        
        this.hideLoading();
        this.showToast('Files uploaded successfully!', 'success');
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch(`${this.apiUrl}/ingest`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.addFileToList(file, 'success', data);
            } else {
                this.addFileToList(file, 'error', data);
            }
        } catch (error) {
            this.addFileToList(file, 'error', { error: error.message });
        }
    }
    
    addFileToList(file, status, data) {
        const container = document.getElementById('uploadedFiles');
        
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        const fileIcon = this.getFileIcon(file.type);
        
        fileItem.innerHTML = `
            <div class="file-info">
                <div class="file-icon">${fileIcon}</div>
                <div class="file-details">
                    <h4>${file.name}</h4>
                    <p>${this.formatFileSize(file.size)}</p>
                </div>
            </div>
            <div class="file-status ${status}">
                ${status === 'success' ? 'Processed' : 'Error'}
            </div>
        `;
        
        container.appendChild(fileItem);
    }
    
    getFileIcon(type) {
        if (type.includes('pdf')) return '<i class="fas fa-file-pdf"></i>';
        if (type.includes('word') || type.includes('document')) return '<i class="fas fa-file-word"></i>';
        return '<i class="fas fa-file-alt"></i>';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    async searchTopics() {
        const query = document.getElementById('topicSearch').value.trim();
        if (!query) return;
        
        this.showLoading('Searching topics...');
        
        try {
            const response = await fetch(`${this.apiUrl}/search/${encodeURIComponent(query)}`);
            const data = await response.json();
            
            this.displaySearchResults(data);
        } catch (error) {
            this.showToast(`Search error: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }
    
    displaySearchResults(results) {
        const container = document.getElementById('searchResults');
        container.innerHTML = '';
        
        if (results.documents && results.documents.length > 0) {
            results.documents.forEach((doc, index) => {
                const resultItem = document.createElement('div');
                resultItem.className = 'result-item';
                resultItem.innerHTML = `
                    <div class="result-title">Result ${index + 1}</div>
                    <div class="result-content">${doc.substring(0, 300)}${doc.length > 300 ? '...' : ''}</div>
                    <div class="result-meta">
                        <span>Topic: ${results.topic}</span>
                        <span class="result-score">Relevance: ${Math.round((1 - (index * 0.1)) * 100)}%</span>
                    </div>
                `;
                container.appendChild(resultItem);
            });
        } else {
            container.innerHTML = '<p>No results found for this topic.</p>';
        }
    }
    
    loadSearchResults() {
        // Load recent search results or popular topics
        const container = document.getElementById('searchResults');
        container.innerHTML = `
            <div class="result-item">
                <div class="result-title">Popular Legal Topics</div>
                <div class="result-content">
                    <p>Try searching for topics like:</p>
                    <ul>
                        <li>Contract Law</li>
                        <li>Tort Law</li>
                        <li>Criminal Law</li>
                        <li>Constitutional Law</li>
                        <li>Property Law</li>
                        <li>Family Law</li>
                    </ul>
                </div>
            </div>
        `;
    }
    
    saveSettings() {
        const settings = {
            apiUrl: document.getElementById('apiUrl').value,
            chunkSize: document.getElementById('chunkSize').value,
            chunkOverlap: document.getElementById('chunkOverlap').value,
            temperature: document.getElementById('temperature').value
        };
        
        localStorage.setItem('ragSettings', JSON.stringify(settings));
        this.apiUrl = settings.apiUrl;
        this.showToast('Settings saved successfully!', 'success');
        this.checkConnection();
    }
    
    loadSettings() {
        const saved = localStorage.getItem('ragSettings');
        if (saved) {
            const settings = JSON.parse(saved);
            document.getElementById('apiUrl').value = settings.apiUrl || this.apiUrl;
            document.getElementById('chunkSize').value = settings.chunkSize || 500;
            document.getElementById('chunkOverlap').value = settings.chunkOverlap || 50;
            document.getElementById('temperature').value = settings.temperature || 0.7;
            document.getElementById('temperatureValue').textContent = settings.temperature || 0.7;
            this.apiUrl = settings.apiUrl || this.apiUrl;
        }
    }
    
    async testConnection() {
        this.showLoading('Testing connection...');
        await this.checkConnection();
        this.hideLoading();
        
        if (this.isConnected) {
            this.showToast('Connection successful!', 'success');
        } else {
            this.showToast('Connection failed. Check your API URL.', 'error');
        }
    }
    
    showLoading(text = 'Loading...') {
        const overlay = document.getElementById('loadingOverlay');
        const loadingText = document.getElementById('loadingText');
        loadingText.textContent = text;
        overlay.classList.add('active');
    }
    
    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        overlay.classList.remove('active');
    }
    
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    new SmartRAG();
});
