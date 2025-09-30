// Track application state
let indexedFiles = [];
let backendConnected = false;
let currentFolderPath = null;
let allIndexedFolders = [];
let searchMode = 'current'; // 'current' or 'all'

// Get Electron IPC
const { ipcRenderer } = require('electron');

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkBackendConnection();
    loadIndexedFolders();
});

// Check if Python backend is running
async function checkBackendConnection() {
    try {
        const response = await fetch('http://localhost:8000/health');
        if (response.ok) {
            backendConnected = true;
            showStatus('Backend connected', 'success');
        } else {
            showStatus('Backend not running. Start Python server first.', 'error');
        }
    } catch (error) {
        showStatus('Backend not running. Start Python server first.', 'error');
    }
}

// Load all indexed folders from backend
async function loadIndexedFolders() {
    if (!backendConnected) return;
    
    try {
        const response = await fetch('http://localhost:8000/folders');
        const data = await response.json();
        
        if (data.status === 'success') {
            allIndexedFolders = data.folders;
            updateSearchDisplay();
        }
    } catch (error) {
        console.error('Error loading folders:', error);
    }
}

// Update search mode display
function updateSearchMode() {
    const currentRadio = document.getElementById('currentFolderOnly');
    const allRadio = document.getElementById('allFolders');
    
    searchMode = currentRadio.checked ? 'current' : 'all';
    updateSearchDisplay();
}

// Update the display of which folders are being searched
function updateSearchDisplay() {
    const foldersSearching = document.getElementById('foldersSearching');
    const foldersList = document.getElementById('foldersList');
    
    if (searchMode === 'all' && allIndexedFolders.length > 0) {
        // Show all indexed folders
        foldersSearching.style.display = 'block';
        foldersList.innerHTML = allIndexedFolders.map(folder => {
            const folderName = folder.split('/').pop() || folder;
            return `<div class="folder-path-item">📁 ${folderName}</div>`;
        }).join('');
    } else if (searchMode === 'current' && currentFolderPath) {
        // Show only current folder
        foldersSearching.style.display = 'block';
        const folderName = currentFolderPath.split('/').pop() || currentFolderPath;
        foldersList.innerHTML = `<div class="folder-path-item">📁 ${folderName}</div>`;
    } else {
        foldersSearching.style.display = 'none';
    }
}

// Display status messages to user
function showStatus(message, type = 'info') {
    const statusBox = document.getElementById('statusBox');
    statusBox.style.display = 'block';
    statusBox.className = 'status-box ' + type;
    statusBox.textContent = message;
}

// Clear the database
async function clearDatabase() {
    if (!backendConnected) {
        showStatus('Backend not connected', 'error');
        return;
    }
    
    if (!confirm('This will delete all indexed files. Continue?')) {
        return;
    }
    
    try {
        showStatus('Clearing database...', 'loading');
        const response = await fetch('http://localhost:8000/clear', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Clear UI
            indexedFiles = [];
            allIndexedFolders = [];
            currentFolderPath = null;
            updateFileList([]);
            updateFileCount(0);
            document.getElementById('selectedPath').textContent = '';
            document.getElementById('questionInput').disabled = true;
            document.getElementById('sendButton').disabled = true;
            document.getElementById('chatArea').innerHTML = '';
            document.getElementById('searchModeSection').style.display = 'none';
            document.getElementById('foldersSearching').style.display = 'none';
            
            // Reset search mode to current folder
            document.getElementById('currentFolderOnly').checked = true;
            searchMode = 'current';
            
            showStatus('Database cleared successfully', 'success');
        } else {
            showStatus('Error clearing database', 'error');
        }
    } catch (error) {
        showStatus('Error: ' + error.message, 'error');
    }
}

// Handle folder selection
async function selectFolder() {
    // Ask Electron to show folder picker
    const folderPath = await ipcRenderer.invoke('select-folder');
    if (folderPath) {
        // Display selected path
        document.getElementById('selectedPath').textContent = folderPath;
        currentFolderPath = folderPath;
        
        // Index folder if backend is connected
        if (backendConnected) {
            indexFolder(folderPath);
        } else {
            mockIndexFolder();
        }
    }
}

// Send folder to backend for indexing PDFs and Word documents
async function indexFolder(folderPath) {
    showStatus('Indexing files...', 'loading');
    
    try {
        // Call backend API to index files
        const response = await fetch('http://localhost:8000/index', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ folder_path: folderPath })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Update UI with indexed files
            indexedFiles = data.indexed_files;
            updateFileList(indexedFiles);
            updateFileCount(data.total_files);
            
            const pdfText = data.pdf_count ? `${data.pdf_count} PDF${data.pdf_count > 1 ? 's' : ''}` : '';
            const wordText = data.word_count ? `${data.word_count} Word doc${data.word_count > 1 ? 's' : ''}` : '';
            const filesText = [pdfText, wordText].filter(t => t).join(' and ');
            
            showStatus(`Successfully indexed ${filesText}`, 'success');
            
            // Reload all indexed folders and show search mode section
            await loadIndexedFolders();
            
            // Ensure search mode section is visible
            document.getElementById('searchModeSection').style.display = 'block';
            
            // Update display immediately after loading folders
            updateSearchDisplay();
            
            // Enable chat functionality
            document.getElementById('questionInput').disabled = false;
            document.getElementById('sendButton').disabled = false;
        } else {
            showStatus(data.message || 'No files found', 'error');
        }
    } catch (error) {
        showStatus('Error indexing files: ' + error.message, 'error');
    }
}

// Mock indexing for testing without backend
function mockIndexFolder() {
    const mockFiles = ['Document1.pdf', 'Document2.pdf', 'Document3.docx'];
    updateFileList(mockFiles);
    updateFileCount(mockFiles.length);
    showStatus(`Indexed ${mockFiles.length} files (mock mode)`, 'success');
}

// Update file list display in sidebar
function updateFileList(files) {
    const fileListElement = document.getElementById('fileList');
    fileListElement.innerHTML = files.map(file => {
        const icon = file.endsWith('.docx') || file.endsWith('.doc') ? '📄' : '📕';
        return `<div class="file-item">${icon} ${file}</div>`;
    }).join('');
}

// Update file counter display
function updateFileCount(count) {
    document.getElementById('fileCount').textContent = count;
}

// Send chat message to backend
async function sendMessage() {
    const input = document.getElementById('questionInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const chatArea = document.getElementById('chatArea');
    
    // Display user's message
    chatArea.innerHTML += `
        <div class="message">
            <strong>You</strong>
            <div class="message-content">${message}</div>
        </div>
    `;
    
    // Clear input field
    input.value = '';
    
    if (backendConnected) {
        try {
            // Determine which folder to search in based on search mode
            const folderPathToSearch = searchMode === 'current' ? currentFolderPath : null;
            
            // Send question to backend with folder filter
            const response = await fetch('http://localhost:8000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    question: message,
                    folder_path: folderPathToSearch
                })
            });
            
            const data = await response.json();
            
            // Log response for debugging
            console.log('Chat response:', data);
            
            // Check if we got a valid response
            if (!data || !data.answer) {
                console.error('Invalid response from backend:', data);
                chatArea.innerHTML += `
                    <div class="message">
                        <strong>Error</strong>
                        <div class="message-content">Failed to get response from AI. Please check the browser console and backend logs for details.</div>
                    </div>
                `;
            } else {
                // Display AI response with sources
                chatArea.innerHTML += `
                    <div class="message">
                        <strong>FileChat</strong>
                        <div class="message-content">${data.answer}</div>
                        ${data.sources && data.sources.length > 0 ? 
                            `<div style="margin-top: 8px; font-size: 11px; color: rgba(255,255,255,0.4)">
                                Sources: ${data.sources.join(', ')}
                            </div>` : ''
                        }
                    </div>
                `;
            }
        } catch (error) {
            // Display error message
            chatArea.innerHTML += `
                <div class="message">
                    <strong>Error</strong>
                    <div class="message-content">Failed to get response: ${error.message}</div>
                </div>
            `;
        }
    } else {
        // Mock response when backend not connected
        chatArea.innerHTML += `
            <div class="message">
                <strong>FileChat</strong>
                <div class="message-content">Backend not connected. Start the Python server to enable chat.</div>
            </div>
        `;
    }
    
    // Scroll to bottom of chat
    chatArea.scrollTop = chatArea.scrollHeight;
}

// Handle Enter key in input field
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('questionInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.target.disabled) {
            sendMessage();
        }
    });
});