// MeloFlow Client Application Logic
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const tabDirect = document.getElementById('tab-direct');
    const tabSpotify = document.getElementById('tab-spotify');
    const panelDirect = document.getElementById('panel-direct');
    const panelSpotify = document.getElementById('panel-spotify');
    
    const settingsToggleBtn = document.getElementById('settings-toggle-btn');
    const settingsCloseBtn = document.getElementById('settings-close-btn');
    const alertSettingsBtn = document.getElementById('alert-settings-btn');
    const settingsPanel = document.getElementById('settings-panel');
    const backdrop = document.getElementById('backdrop');
    const settingsForm = document.getElementById('settings-form');
    const settingsTestStatus = document.getElementById('settings-test-status');
    const spotifyStatusBadge = document.getElementById('spotify-status-badge');
    const spotifyUnconfiguredAlert = document.getElementById('spotify-unconfigured-alert');
    
    const directDownloadForm = document.getElementById('direct-download-form');
    const directUrlInput = document.getElementById('direct-url-input');
    const directPasteBtn = document.getElementById('direct-paste-btn');
    
    const spotifyDownloadForm = document.getElementById('spotify-download-form');
    const spotifyUrlInput = document.getElementById('spotify-url-input');
    const spotifyPasteBtn = document.getElementById('spotify-paste-btn');
    
    const statusPanel = document.getElementById('status-panel');
    const statusBadge = document.getElementById('status-badge');
    const statusPlaceholder = document.getElementById('status-placeholder');
    const downloadProgress = document.getElementById('download-progress');
    const progressPhase = document.getElementById('progress-phase');
    const downloadSuccessArea = document.getElementById('download-success-area');
    const successSongTitle = document.getElementById('success-song-title');
    const directDownloadAnchor = document.getElementById('direct-download-anchor');

    // 1. Navigation Tab Toggles
    tabDirect.addEventListener('click', () => {
        switchTab('direct');
    });

    tabSpotify.addEventListener('click', () => {
        switchTab('spotify');
    });

    function switchTab(tab) {
        if (tab === 'direct') {
            tabDirect.classList.add('active');
            tabDirect.setAttribute('aria-selected', 'true');
            tabSpotify.classList.remove('active');
            tabSpotify.setAttribute('aria-selected', 'false');
            panelDirect.classList.add('active');
            panelSpotify.classList.remove('active');
        } else {
            tabSpotify.classList.add('active');
            tabSpotify.setAttribute('aria-selected', 'true');
            tabDirect.classList.remove('active');
            tabDirect.setAttribute('aria-selected', 'false');
            panelSpotify.classList.add('active');
            panelDirect.classList.remove('active');
        }
    }

    // 2. Settings Slide Drawer Toggle
    function openSettings() {
        settingsPanel.classList.add('open');
        backdrop.classList.add('open');
    }

    function closeSettings() {
        settingsPanel.classList.remove('open');
        backdrop.classList.remove('open');
        settingsTestStatus.className = 'settings-test-result hidden';
        settingsTestStatus.innerHTML = '';
    }

    settingsToggleBtn.addEventListener('click', openSettings);
    alertSettingsBtn.addEventListener('click', openSettings);
    settingsCloseBtn.addEventListener('click', closeSettings);
    backdrop.addEventListener('click', closeSettings);

    // 3. Paste Helper Buttons (System clipboard API integration)
    async function pasteFromClipboard(inputElement) {
        try {
            const text = await navigator.clipboard.readText();
            inputElement.value = text;
            // Trigger input events so styling/validation reacts properly
            inputElement.dispatchEvent(new Event('input'));
        } catch (err) {
            console.error('Failed to read clipboard contents: ', err);
            alert('Unable to access clipboard. Please paste manually.');
        }
    }

    directPasteBtn.addEventListener('click', () => pasteFromClipboard(directUrlInput));
    spotifyPasteBtn.addEventListener('click', () => pasteFromClipboard(spotifyUrlInput));

    // 4. Initial Server Configuration Checks
    async function checkServerStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();
            
            // Hide settings controls if locked in production
            if (data.settings_locked) {
                settingsToggleBtn.classList.add('hidden');
                if (alertSettingsBtn) alertSettingsBtn.classList.add('hidden');
            } else {
                settingsToggleBtn.classList.remove('hidden');
                if (alertSettingsBtn) alertSettingsBtn.classList.remove('hidden');
            }
            
            if (data.spotify_connected) {
                // Spotify is configured properly
                spotifyStatusBadge.className = 'status-indicator active';
                spotifyUnconfiguredAlert.classList.add('hidden');
                document.getElementById('spotify-client-id').value = '••••••••••••••••••••••••••••••••';
                document.getElementById('spotify-client-secret').value = '••••••••••••••••••••••••••••••••';
            } else {
                // Spotify credentials are missing or failing validation
                spotifyStatusBadge.className = 'status-indicator inactive';
                spotifyUnconfiguredAlert.classList.remove('hidden');
                
                const alertText = spotifyUnconfiguredAlert.querySelector('p');
                if (data.settings_locked) {
                    if (alertText) alertText.textContent = 'Spotify integration is currently not configured on the server. Please contact the administrator to set the environment keys.';
                } else {
                    if (alertText) alertText.textContent = 'To pull data from Spotify, please configure your client credentials. Click the gear icon or button below.';
                }
            }
        } catch (err) {
            console.error('Failed to check server configuration: ', err);
        }
    }

    // Run configuration check on startup
    checkServerStatus();

    // 5. Save Credentials Settings Submission
    settingsForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const clientId = document.getElementById('spotify-client-id').value.trim();
        const clientSecret = document.getElementById('spotify-client-secret').value.trim();
        
        // Display loading state in drawer
        settingsTestStatus.className = 'settings-test-result success';
        settingsTestStatus.innerHTML = 'Testing credentials & establishing connection...';
        settingsTestStatus.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                settingsTestStatus.className = 'settings-test-result success';
                settingsTestStatus.innerHTML = `<strong>Success!</strong> ${data.message}`;
                // Refresh client status indicators
                await checkServerStatus();
                // Close after a brief 1.5s delay to let user see success state
                setTimeout(closeSettings, 1500);
            } else {
                settingsTestStatus.className = 'settings-test-result error';
                settingsTestStatus.innerHTML = `<strong>Connection Failed:</strong> ${data.error}`;
                spotifyStatusBadge.className = 'status-indicator inactive';
            }
        } catch (err) {
            settingsTestStatus.className = 'settings-test-result error';
            settingsTestStatus.innerHTML = `<strong>Network Error:</strong> Could not connect to API server.`;
            spotifyStatusBadge.className = 'status-indicator inactive';
        }
    });

    // 6. Direct Link Download Handling
    directDownloadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const urlVal = directUrlInput.value.trim();
        if (!urlVal) return;

        showLoadingState('Extracting audio stream from direct link...');
        statusBadge.textContent = 'EXTRACTING';
        statusBadge.style.color = 'var(--secondary)';
        
        try {
            const response = await fetch('/api/download/direct', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: urlVal })
            });

            await handleDownloadResponse(response);
        } catch (err) {
            showErrorState(`Network error during download: ${err.message}`);
        }
    });

    // 7. Spotify Track Download Handling
    spotifyDownloadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const urlVal = spotifyUrlInput.value.trim();
        if (!urlVal) return;

        showLoadingState('Fetching metadata & matching track streams...');
        statusBadge.textContent = 'CONVERTING';
        statusBadge.style.color = 'var(--primary)';

        try {
            const response = await fetch('/api/download/spotify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: urlVal })
            });

            await handleDownloadResponse(response);
        } catch (err) {
            showErrorState(`Network error during conversion: ${err.message}`);
        }
    });

    // Helper: Update UI to downloading state
    function showLoadingState(message) {
        statusPanel.className = 'status-panel active';
        statusPlaceholder.classList.add('hidden');
        downloadSuccessArea.classList.add('hidden');
        
        progressPhase.textContent = message;
        downloadProgress.classList.remove('hidden');
    }

    // Helper: Update UI to success state
    function showSuccessState(songName, downloadUrl) {
        statusPanel.className = 'status-panel success-state';
        statusBadge.textContent = 'COMPLETE';
        statusBadge.style.color = 'var(--success)';
        
        downloadProgress.classList.add('hidden');
        statusPlaceholder.classList.add('hidden');
        
        successSongTitle.textContent = songName;
        directDownloadAnchor.href = downloadUrl;
        directDownloadAnchor.download = songName;
        downloadSuccessArea.classList.remove('hidden');
    }

    // Helper: Update UI to error state
    function showErrorState(errorMsg) {
        statusPanel.className = 'status-panel error-state';
        statusBadge.textContent = 'ERROR';
        statusBadge.style.color = 'var(--error)';
        
        downloadProgress.classList.add('hidden');
        downloadSuccessArea.classList.add('hidden');
        
        statusPlaceholder.textContent = errorMsg;
        statusPlaceholder.classList.remove('hidden');
    }

    // Common response handler for processing binary/stream downloads
    async function handleDownloadResponse(response) {
        if (!response.ok) {
            // Read the error message payload from JSON response
            let errorText = 'Internal Server Error';
            try {
                const errData = await response.json();
                errorText = errData.error || errorText;
            } catch (_) {
                // If response is not JSON, fallback to status code
                errorText = `Status Code: ${response.status} (${response.statusText})`;
            }
            showErrorState(errorText);
            return;
        }

        // Parse filename from Content-Disposition response header
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'downloaded_song.mp3';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
            if (filenameMatch && filenameMatch[1]) {
                filename = filenameMatch[1].replace(/['"]/g, '');
            }
        }

        // Update status state to final compilation
        progressPhase.textContent = 'Building high-fidelity MP3 stream container...';
        
        // Read response content as a binary blob
        const fileBlob = await response.blob();
        
        // Create browser trigger object URL
        const downloadUrl = URL.createObjectURL(fileBlob);
        
        // Update UI to success and display triggering anchors
        showSuccessState(filename, downloadUrl);
        
        // Programmatically trigger browser download automatically
        const autoLink = document.createElement('a');
        autoLink.href = downloadUrl;
        autoLink.download = filename;
        document.body.appendChild(autoLink);
        autoLink.click();
        document.body.removeChild(autoLink);
    }
});
