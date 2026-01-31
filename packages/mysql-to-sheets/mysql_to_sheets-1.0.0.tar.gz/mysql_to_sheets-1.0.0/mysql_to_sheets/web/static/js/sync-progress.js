/**
 * Real-time sync progress tracking via Server-Sent Events.
 *
 * Usage:
 *   const progress = new SyncProgress({
 *     onProgress: (data) => console.log('Progress:', data),
 *     onLog: (data) => console.log('Log:', data),
 *     onComplete: (data) => console.log('Complete:', data),
 *   });
 *   progress.connect();
 *   // Later: progress.disconnect();
 */

class SyncProgress {
    constructor(options = {}) {
        this.options = {
            endpoint: '/api/sync/progress/stream',
            syncId: null,  // Filter to specific sync
            reconnectDelay: 3000,
            maxReconnectAttempts: 5,
            onProgress: null,
            onLog: null,
            onComplete: null,
            onConnect: null,
            onDisconnect: null,
            onError: null,
            ...options
        };

        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        this.clientId = null;
    }

    /**
     * Connect to the SSE endpoint.
     */
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        let url = this.options.endpoint;
        if (this.options.syncId) {
            url += `?sync_id=${encodeURIComponent(this.options.syncId)}`;
        }

        try {
            this.eventSource = new EventSource(url);

            this.eventSource.addEventListener('connected', (e) => {
                const data = JSON.parse(e.data);
                this.clientId = data.client_id;
                this.isConnected = true;
                this.reconnectAttempts = 0;
                console.debug('[SyncProgress] Connected:', this.clientId);
                if (this.options.onConnect) {
                    this.options.onConnect(data);
                }
            });

            this.eventSource.addEventListener('progress', (e) => {
                const data = JSON.parse(e.data);
                if (this.options.onProgress) {
                    this.options.onProgress(data);
                }
            });

            this.eventSource.addEventListener('log', (e) => {
                const data = JSON.parse(e.data);
                if (this.options.onLog) {
                    this.options.onLog(data);
                }
            });

            this.eventSource.addEventListener('complete', (e) => {
                const data = JSON.parse(e.data);
                if (this.options.onComplete) {
                    this.options.onComplete(data);
                }
                // Auto-disconnect after completion if filtering by sync_id
                if (this.options.syncId) {
                    this.disconnect();
                }
            });

            this.eventSource.onerror = (e) => {
                console.warn('[SyncProgress] Connection error');
                this.isConnected = false;
                if (this.options.onError) {
                    this.options.onError(e);
                }
                this._handleReconnect();
            };

        } catch (error) {
            console.error('[SyncProgress] Failed to connect:', error);
            if (this.options.onError) {
                this.options.onError(error);
            }
        }
    }

    /**
     * Disconnect from the SSE endpoint.
     */
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        this.isConnected = false;
        if (this.options.onDisconnect) {
            this.options.onDisconnect();
        }
        console.debug('[SyncProgress] Disconnected');
    }

    /**
     * Handle reconnection after error.
     */
    _handleReconnect() {
        if (this.reconnectAttempts >= this.options.maxReconnectAttempts) {
            console.error('[SyncProgress] Max reconnect attempts reached');
            this.disconnect();
            return;
        }

        this.reconnectAttempts++;
        const delay = this.options.reconnectDelay * this.reconnectAttempts;
        console.debug(`[SyncProgress] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (!this.isConnected) {
                this.connect();
            }
        }, delay);
    }
}

/**
 * Progress bar component that integrates with SyncProgress.
 */
class SyncProgressBar {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error(`Container #${containerId} not found`);
            return;
        }

        this.options = {
            showPhase: true,
            showEta: true,
            showLogs: true,
            maxLogs: 50,
            ...options
        };

        this.syncProgress = null;
        this._render();
    }

    /**
     * Render the progress bar HTML.
     */
    _render() {
        this.container.innerHTML = `
            <div class="sync-progress-container hidden">
                <div class="sync-progress-header">
                    <span class="sync-phase">Ready</span>
                    <span class="sync-eta"></span>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar progress-bar-striped progress-bar-animated bg-primary"
                         role="progressbar"
                         style="width: 0%"
                         aria-valuenow="0"
                         aria-valuemin="0"
                         aria-valuemax="100">
                    </div>
                </div>
                <div class="sync-progress-stats">
                    <span class="sync-rows"></span>
                    <span class="sync-percent">0%</span>
                </div>
                <div class="sync-logs-container" style="display: none;">
                    <div class="sync-logs-header">
                        <span>Logs</span>
                        <button class="btn btn-sm btn-outline-secondary sync-logs-toggle">
                            <i class="bi bi-chevron-down"></i>
                        </button>
                    </div>
                    <div class="sync-logs" style="max-height: 200px; overflow-y: auto;"></div>
                </div>
            </div>
        `;

        // Get references to elements
        this.progressContainer = this.container.querySelector('.sync-progress-container');
        this.progressBar = this.container.querySelector('.progress-bar');
        this.phaseEl = this.container.querySelector('.sync-phase');
        this.etaEl = this.container.querySelector('.sync-eta');
        this.rowsEl = this.container.querySelector('.sync-rows');
        this.percentEl = this.container.querySelector('.sync-percent');
        this.logsContainer = this.container.querySelector('.sync-logs-container');
        this.logsEl = this.container.querySelector('.sync-logs');
        this.logsToggle = this.container.querySelector('.sync-logs-toggle');

        // Toggle logs visibility
        if (this.logsToggle) {
            this.logsToggle.addEventListener('click', () => {
                this.logsEl.style.display = this.logsEl.style.display === 'none' ? 'block' : 'none';
                const icon = this.logsToggle.querySelector('i');
                if (icon) {
                    icon.className = this.logsEl.style.display === 'none'
                        ? 'bi bi-chevron-down'
                        : 'bi bi-chevron-up';
                }
            });
        }
    }

    /**
     * Start tracking progress for a sync.
     * @param {string} syncId - Optional sync ID to filter
     */
    start(syncId = null) {
        this.progressContainer.classList.remove('hidden');
        this.logsEl.innerHTML = '';

        this.syncProgress = new SyncProgress({
            syncId: syncId,
            onProgress: (data) => this._updateProgress(data),
            onLog: (data) => this._addLog(data),
            onComplete: (data) => this._handleComplete(data),
        });
        this.syncProgress.connect();
    }

    /**
     * Stop tracking progress.
     */
    stop() {
        if (this.syncProgress) {
            this.syncProgress.disconnect();
            this.syncProgress = null;
        }
    }

    /**
     * Update progress display.
     */
    _updateProgress(data) {
        const percent = data.percent || 0;

        // Update progress bar
        this.progressBar.style.width = `${percent}%`;
        this.progressBar.setAttribute('aria-valuenow', percent);
        this.percentEl.textContent = `${percent}%`;

        // Update phase
        if (this.options.showPhase && data.phase) {
            const phaseLabels = {
                connecting: 'Connecting to database...',
                fetching: 'Fetching data...',
                cleaning: 'Processing data...',
                pushing: 'Pushing to Google Sheets...',
                complete: 'Sync complete!',
                failed: 'Sync failed',
            };
            this.phaseEl.textContent = phaseLabels[data.phase] || data.phase;
        }

        // Update message if different from phase
        if (data.message && data.message !== this.phaseEl.textContent) {
            this.phaseEl.textContent = data.message;
        }

        // Update ETA
        if (this.options.showEta && data.eta_seconds != null) {
            const mins = Math.floor(data.eta_seconds / 60);
            const secs = Math.round(data.eta_seconds % 60);
            this.etaEl.textContent = mins > 0
                ? `ETA: ${mins}m ${secs}s`
                : `ETA: ${secs}s`;
        } else {
            this.etaEl.textContent = '';
        }

        // Update rows stats
        if (data.rows_pushed > 0 || data.total_rows > 0) {
            if (data.chunk_total > 0) {
                this.rowsEl.textContent = `Chunk ${data.chunk_current}/${data.chunk_total} | ${data.rows_pushed.toLocaleString()} rows`;
            } else {
                this.rowsEl.textContent = `${data.rows_pushed.toLocaleString()} rows`;
            }
        } else if (data.rows_fetched > 0) {
            this.rowsEl.textContent = `Fetched: ${data.rows_fetched.toLocaleString()} rows`;
        }

        // Update progress bar color based on phase
        this.progressBar.classList.remove('bg-primary', 'bg-success', 'bg-danger', 'bg-warning');
        if (data.phase === 'complete') {
            this.progressBar.classList.add('bg-success');
            this.progressBar.classList.remove('progress-bar-animated');
        } else if (data.phase === 'failed') {
            this.progressBar.classList.add('bg-danger');
            this.progressBar.classList.remove('progress-bar-animated');
        } else {
            this.progressBar.classList.add('bg-primary');
        }
    }

    /**
     * Add a log entry.
     */
    _addLog(data) {
        if (!this.options.showLogs) return;

        this.logsContainer.style.display = 'block';

        const levelColors = {
            info: 'text-info',
            warning: 'text-warning',
            error: 'text-danger',
            debug: 'text-muted',
        };

        const time = new Date(data.timestamp).toLocaleTimeString();
        const color = levelColors[data.level] || 'text-secondary';

        const logEntry = document.createElement('div');
        logEntry.className = `sync-log-entry ${color}`;
        logEntry.innerHTML = `<span class="sync-log-time">${time}</span> ${this._escapeHtml(data.message)}`;
        this.logsEl.appendChild(logEntry);

        // Limit log entries
        while (this.logsEl.children.length > this.options.maxLogs) {
            this.logsEl.removeChild(this.logsEl.firstChild);
        }

        // Auto-scroll to bottom
        this.logsEl.scrollTop = this.logsEl.scrollHeight;
    }

    /**
     * Handle sync completion.
     */
    _handleComplete(data) {
        if (data.success) {
            this.phaseEl.textContent = `Synced ${data.rows_synced.toLocaleString()} rows in ${data.duration_seconds.toFixed(1)}s`;
            this.progressBar.classList.remove('bg-primary');
            this.progressBar.classList.add('bg-success');
        } else {
            this.phaseEl.textContent = data.error_message || 'Sync failed';
            this.progressBar.classList.remove('bg-primary');
            this.progressBar.classList.add('bg-danger');
        }
        this.progressBar.classList.remove('progress-bar-animated');
        this.etaEl.textContent = '';
    }

    /**
     * Reset the progress bar to initial state.
     */
    reset() {
        this.stop();
        this.progressContainer.classList.add('hidden');
        this.progressBar.style.width = '0%';
        this.progressBar.classList.remove('bg-success', 'bg-danger');
        this.progressBar.classList.add('bg-primary', 'progress-bar-animated');
        this.phaseEl.textContent = 'Ready';
        this.etaEl.textContent = '';
        this.rowsEl.textContent = '';
        this.percentEl.textContent = '0%';
        this.logsContainer.style.display = 'none';
        this.logsEl.innerHTML = '';
    }

    /**
     * Escape HTML for safe display.
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SyncProgress, SyncProgressBar };
}
