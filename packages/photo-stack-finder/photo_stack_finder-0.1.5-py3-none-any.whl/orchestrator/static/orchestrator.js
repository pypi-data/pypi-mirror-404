// Photo Dedup Orchestrator Client-side Logic

// State
let currentBrowsePath = '';
let browseTargetInput = null;
let pipelineStages = [];  // Will be populated from /api/stages

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    setupEventListeners();
    await loadStages();  // Load stages first - MUST complete before checking status
    loadDefaults();
    await checkPipelineStatus();  // Check if pipeline is already running
});

/**
 * Load pipeline stages from server and render them dynamically
 */
async function loadStages() {
    try {
        console.log('loadStages: Starting to fetch pipeline stages...');
        const response = await fetch('/api/stages');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        pipelineStages = await response.json();
        console.log('Loaded pipeline stages:', pipelineStages);

        // Render stage elements
        const stageList = document.getElementById('stage-list');
        if (!stageList) {
            console.error('ERROR: Could not find stage-list element!');
            return;
        }
        console.log('Found stage-list element:', stageList);
        stageList.innerHTML = '';  // Clear existing content

        // Add pipeline stages
        pipelineStages.forEach((stage) => {
            console.log('Adding stage:', stage.stage_name);
            const stageDiv = document.createElement('div');
            stageDiv.className = 'stage pending';
            stageDiv.dataset.stage = stage.stage_id;
            stageDiv.dataset.stageName = stage.stage_name;
            if (stage.review_type) {
                stageDiv.dataset.reviewType = stage.review_type;
            }

            // Build review button HTML if stage produces reviewable data
            let reviewButtonHTML = '';
            if (stage.produces_review && stage.review_type) {
                reviewButtonHTML = `
                    <button class="stage-review-btn"
                            data-stage-id="${stage.stage_id}"
                            data-review-type="${stage.review_type}"
                            data-stage-name="${stage.stage_name}"
                            title="Review ${stage.stage_name} results"
                            disabled>
                        📊 Review
                    </button>
                `;
            }

            stageDiv.innerHTML = `
                <span class="stage-icon">⏳</span>
                <span class="stage-name">${stage.stage_name}</span>
                <span class="stage-status">Pending</span>
                ${reviewButtonHTML}
            `;

            stageList.appendChild(stageDiv);
        });

        console.log(`loadStages: Successfully rendered ${pipelineStages.length} stages`);
        console.log('Stage list children count:', stageList.children.length);

    } catch (error) {
        console.error('Failed to load pipeline stages:', error);
        alert('Failed to load pipeline stages. See console for details.');
    }
}

/**
 * Display an error in the error container and log to console
 */
function showError(errorMessage) {
    // Log to console for debugging (copyable)
    console.error('Pipeline Error:', errorMessage);

    // Show error container
    const errorContainer = document.getElementById('error-container');
    const errorText = document.getElementById('error-text');

    errorText.textContent = errorMessage;
    errorContainer.style.display = 'block';

    // Scroll error into view
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Hide the error container
 */
function hideError() {
    const errorContainer = document.getElementById('error-container');
    errorContainer.style.display = 'none';
}

function setupEventListeners() {
    // Copy error button
    const copyErrorBtn = document.getElementById('copy-error');
    copyErrorBtn.addEventListener('click', () => {
        const errorText = document.getElementById('error-text').textContent;
        navigator.clipboard.writeText(errorText).then(() => {
            copyErrorBtn.textContent = '✅ Copied!';
            setTimeout(() => {
                copyErrorBtn.textContent = '📋 Copy';
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy error:', err);
            alert('Failed to copy to clipboard. See console for error details.');
        });
    });
    // Form submission
    const form = document.getElementById('config-form');
    form.addEventListener('submit', handleFormSubmit);

    // Auto-fill work directory when source directory changes
    const sourceDirInput = document.getElementById('source-dir');
    sourceDirInput.addEventListener('blur', autoFillWorkDir);

    // Load defaults button
    const loadDefaultsBtn = document.getElementById('load-defaults');
    loadDefaultsBtn.addEventListener('click', loadDefaults);

    // Stop pipeline button
    const stopPipelineBtn = document.getElementById('stop-pipeline');
    stopPipelineBtn.addEventListener('click', handleStopPipeline);

    // Quit server button
    const quitServerBtn = document.getElementById('quit-server');
    quitServerBtn.addEventListener('click', handleQuitServer);

    // Browse buttons
    const browseSourceBtn = document.getElementById('browse-source');
    const browseWorkBtn = document.getElementById('browse-work');
    browseSourceBtn.addEventListener('click', () => openDirectoryBrowser('source-dir'));
    browseWorkBtn.addEventListener('click', () => openDirectoryBrowser('work-dir'));

    // Modal close buttons
    const closeModalBtn = document.getElementById('close-modal');
    const cancelBrowseBtn = document.getElementById('cancel-browse');
    const selectCurrentBtn = document.getElementById('select-current');

    closeModalBtn.addEventListener('click', closeDirectoryBrowser);
    cancelBrowseBtn.addEventListener('click', closeDirectoryBrowser);
    selectCurrentBtn.addEventListener('click', selectCurrentDirectory);

    // Review modal close button
    const closeReviewModalBtn = document.getElementById('close-review-modal');
    closeReviewModalBtn.addEventListener('click', closeReviewModal);

    // Event delegation for stage review buttons (will be created dynamically)
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('stage-review-btn')) {
            const stageId = parseInt(e.target.dataset.stageId);
            const reviewType = e.target.dataset.reviewType;
            const stageName = e.target.dataset.stageName;
            openReviewModal(stageId, reviewType, stageName);
        }
    });
}

/**
 * Get status display text and icon based on pipeline state
 * @param {Object} status - Pipeline status object
 * @returns {string} HTML string for status display
 */
function getStatusDisplayText(status) {
    if (!status) return '⏸️ Pipeline Idle';

    switch(status.stage) {
        case 'completed':
            // Show overall reduction statistics if available
            if (status.initial_photos && status.final_photos && status.reduction_pct !== undefined) {
                let text = `✅ ${status.initial_photos.toLocaleString()} → ${status.final_photos.toLocaleString()} photos (${status.reduction_pct.toFixed(1)}% reduction)`;
                if (status.final_sequences) {
                    text += `, ${status.final_sequences.toLocaleString()} sequences`;
                }
                // Add performance metrics if available
                if (status.total_elapsed_seconds !== undefined) {
                    const minutes = Math.floor(status.total_elapsed_seconds / 60);
                    const seconds = Math.floor(status.total_elapsed_seconds % 60);
                    const timeStr = minutes > 0 ? `${minutes}m ${seconds}s` : `${seconds}s`;
                    text += ` | ${timeStr}`;
                }
                if (status.average_throughput !== undefined) {
                    text += ` | ${status.average_throughput.toFixed(0)} items/sec`;
                }
                return text;
            }
            return '✅ Done';
        case 'stopped':
            return '⏹️ Pipeline Stopped';
        default:
            return '⏸️ Pipeline Idle';
    }
}

/**
 * Update pipeline control element (Stop button / Status display)
 * Transforms between interactive button and non-interactive status display
 * @param {Object} status - Pipeline status object with running flag and stage
 */
function updatePipelineControl(status) {
    const controlElement = document.getElementById('stop-pipeline');
    const startButton = document.getElementById('start-pipeline');

    if (status && status.running) {
        // Show as interactive Stop button
        startButton.style.display = 'none';
        controlElement.className = 'btn-danger';
        controlElement.innerHTML = '⏹️ Stop Pipeline';
        controlElement.disabled = false;
        controlElement.style.cursor = 'pointer';
        controlElement.style.display = 'inline-block';
    } else {
        // Show as non-interactive status display
        startButton.style.display = 'inline-block';
        controlElement.className = 'status-badge';
        controlElement.innerHTML = getStatusDisplayText(status);
        controlElement.disabled = true;
        controlElement.style.cursor = 'default';
        controlElement.style.display = 'inline-block';
    }
}

async function loadDefaults() {
    try {
        const sourceDir = document.getElementById('source-dir').value;
        const params = sourceDir ? `?source_dir=${encodeURIComponent(sourceDir)}` : '';

        const response = await fetch(`/api/config/defaults${params}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const defaults = await response.json();
        populateForm(defaults);

        console.log('Loaded defaults:', defaults);
    } catch (error) {
        console.error('Failed to load defaults:', error);
        alert('Failed to load default configuration. See console for details.');
    }
}

async function checkPipelineStatus() {
    try {
        const response = await fetch('/api/status');
        if (!response.ok) {
            console.log('No pipeline status available');
            return;
        }

        const status = await response.json();
        console.log('Initial pipeline status:', status);

        // If pipeline is running, reconnect to it
        if (status.running) {
            console.log('Pipeline is running, reconnecting...');

            // Show progress section
            document.getElementById('progress-section').style.display = 'block';

            // Update button/status display
            updatePipelineControl(status);

            // Display current status
            displayStatus(status);

            // Start WebSocket updates
            startWebSocketUpdates();
        } else if (status.completed) {
            // Pipeline completed, show final status
            console.log('Pipeline completed, showing results');
            document.getElementById('progress-section').style.display = 'block';
            displayStatus(status);

            // Try to load review data and enable buttons
            loadReviewData().then(success => {
                if (success) {
                    enableReviewButtons();
                }
            });
        }
    } catch (error) {
        console.error('Failed to check pipeline status:', error);
    }
}

function populateForm(config) {
    // Essential fields
    if (config.source_dir) {
        document.getElementById('source-dir').value = config.source_dir;
    }
    if (config.work_dir) {
        document.getElementById('work-dir').value = config.work_dir;
    }

    // Advanced options
    document.getElementById('max-workers').value = config.max_workers || '';
    document.getElementById('batch-size').value = config.batch_size || '';
    document.getElementById('debug-mode').checked = config.debug_mode || false;

    document.getElementById('comparison-method').value = config.comparison_method || 'SSIM';
    document.getElementById('ssim-threshold').value = config.gate_thresholds?.SSIM || 0.95;
    document.getElementById('aspect-ratio-threshold').value = config.gate_thresholds?.aspect_ratio || 0.85;

    document.getElementById('enable-benchmarks').checked = config.enable_benchmarks || false;
    document.getElementById('target-fpr').value = config.target_fpr || 0.00075;
}

async function autoFillWorkDir() {
    const sourceDir = document.getElementById('source-dir').value.trim();
    if (!sourceDir) return;

    try {
        const response = await fetch(`/api/config/defaults?source_dir=${encodeURIComponent(sourceDir)}`);
        if (!response.ok) return;

        const defaults = await response.json();
        if (defaults.work_dir) {
            document.getElementById('work-dir').value = defaults.work_dir;
        }
    } catch (error) {
        console.error('Failed to auto-fill work directory:', error);
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();

    // Check if form is valid - if not, open advanced options so user can see the error
    const form = event.target;
    if (!form.checkValidity()) {
        // Open advanced options if closed
        const advancedOptions = document.querySelector('.advanced-options');
        if (advancedOptions && !advancedOptions.open) {
            advancedOptions.open = true;
        }
        // Let browser show validation messages
        form.reportValidity();
        return;
    }

    // Collect form data
    const formData = new FormData(event.target);

    // Parse numeric fields - send actual values or null if empty
    // Backend will use null to keep CONFIG defaults
    const maxWorkers = formData.get('max_workers');
    const batchSize = formData.get('batch_size');

    const config = {
        source_dir: formData.get('source_dir'),
        work_dir: formData.get('work_dir'),
        max_workers: maxWorkers ? parseInt(maxWorkers) : null,
        batch_size: batchSize ? parseInt(batchSize) : null,
        debug_mode: formData.get('debug_mode') === 'on',
        comparison_method: formData.get('comparison_method'),
        gate_thresholds: {
            SSIM: parseFloat(formData.get('ssim_threshold')),
            aspect_ratio: parseFloat(formData.get('aspect_ratio_threshold')),
        },
        enable_benchmarks: formData.get('enable_benchmarks') === 'on',
        target_fpr: parseFloat(formData.get('target_fpr')),
    };

    // Validate
    if (!config.source_dir) {
        alert('Source directory is required');
        return;
    }

    try {
        // Start pipeline
        const response = await fetch('/api/pipeline/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        console.log('Pipeline started:', result);

        // Reload stages to reflect current pipeline configuration
        // (e.g., benchmark stage may be added/removed based on config)
        await loadStages();

        // Hide any previous errors
        hideError();

        // Show progress section
        document.getElementById('progress-section').style.display = 'block';

        // Update button/status display
        updatePipelineControl({running: true});

        // Scroll to progress
        document.getElementById('progress-section').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });

        // Start WebSocket updates
        startWebSocketUpdates();

    } catch (error) {
        console.error('Failed to start pipeline:', error);
        alert(`Failed to start pipeline: ${error.message}`);
    }
}

async function handleStopPipeline() {
    if (!confirm('Are you sure you want to stop the pipeline?')) {
        return;
    }

    try {
        const response = await fetch('/api/pipeline/stop', {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        console.log('Pipeline stopped');
        alert('Pipeline stopped successfully');

        // Stop WebSocket
        stopWebSocketUpdates();

        // Update button/status display
        updatePipelineControl({running: false, stage: 'stopped'});

    } catch (error) {
        console.error('Failed to stop pipeline:', error);
        alert(`Failed to stop pipeline: ${error.message}`);
    }
}

async function handleQuitServer() {
    if (!confirm('Are you sure you want to quit the server? This will close the web interface.')) {
        return;
    }

    try {
        // Send quit request
        await fetch('/api/shutdown', {
            method: 'POST'
        });

        // Show message to user
        document.body.innerHTML = '<div style="text-align: center; padding: 4rem; font-family: sans-serif;"><h1>Server Shutting Down</h1><p>You can close this browser window.</p></div>';

    } catch {
        // Server likely already shut down, which is fine
        console.log('Server quit initiated');
        document.body.innerHTML = '<div style="text-align: center; padding: 4rem; font-family: sans-serif;"><h1>Server Shutting Down</h1><p>You can close this browser window.</p></div>';
    }
}

let websocket = null;

function startWebSocketUpdates() {
    // Close existing connection if any
    if (websocket) {
        websocket.close();
    }

    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/progress`;

    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
        const status = JSON.parse(event.data);
        displayStatus(status);
    };

    websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
        console.log('WebSocket closed');
        websocket = null;
    };
}

function stopWebSocketUpdates() {
    if (websocket) {
        websocket.close();
        websocket = null;
    }
}

function displayStatus(status) {
    console.log('Status update:', status);

    // Update pipeline control element (button/status display) based on pipeline state
    updatePipelineControl(status);

    // Update stage indicators
    const stageElements = document.querySelectorAll('.stage');

    stageElements.forEach((element) => {
        // Use actual stage number from dataset, not loop index
        const stageNum = parseInt(element.dataset.stage);
        const iconElement = element.querySelector('.stage-icon');

        // Reset classes
        element.classList.remove('pending', 'running', 'completed', 'error');

        // Determine if we're currently actively running this stage
        const isCurrentlyRunning = status.stage_number === stageNum &&
                                   status.running;

        if (isCurrentlyRunning) {
            // Currently active stage
            element.classList.add('running');
            iconElement.textContent = '🔄';

            // Build detailed status message
            let statusText = status.message || 'Running...';

            // Add detailed progress if available
            if (status.total_count && status.current_count) {
                statusText = `${status.current_count}/${status.total_count}`;
                if (status.progress) {
                    statusText += ` (${status.progress.toFixed(1)}%)`;
                }
                if (status.rate) {
                    statusText += `, ${status.rate.toFixed(1)}/s`;
                }
                if (status.eta) {
                    statusText += `, finishes ${status.eta}`;
                }
            } else if (status.current_count) {
                // No total, just show count and rate
                statusText = `${status.current_count}`;
                if (status.rate) {
                    statusText += ` (${status.rate.toFixed(1)}/s)`;
                }
            }

            element.querySelector('.stage-status').textContent = statusText;
        } else if (status.stage_number && stageNum < status.stage_number) {
            // Stage has completed
            element.classList.add('completed');
            iconElement.textContent = '✅';

            // Display statistics if available, otherwise show "Complete"
            if (status.stages && Array.isArray(status.stages)) {
                const stageInfo = status.stages.find(s => s.position === stageNum);
                if (stageInfo && stageInfo.statistics) {
                    element.querySelector('.stage-status').textContent = stageInfo.statistics;
                } else {
                    // No statistics available - show "Complete" instead of preserving "Pending"
                    element.querySelector('.stage-status').textContent = 'Complete';
                }
            } else {
                // No stages array - show "Complete"
                element.querySelector('.stage-status').textContent = 'Complete';
            }

            // Check if review button should be enabled for this completed stage
            // Only check once per stage (avoid redundant API calls on every status update)
            if (!element.dataset.reviewChecked) {
                element.dataset.reviewChecked = 'true';
                checkAndEnableReviewButton(element);
            }
        } else {
            // Pending stages
            element.classList.add('pending');
            iconElement.textContent = '⏳';
            element.querySelector('.stage-status').textContent = 'Pending';
        }
    });

    // Handle errors
    if (status.error) {
        showError(status.error);
        stopWebSocketUpdates();
    }

    // Handle completion
    if (status.completed) {
        // Load review data automatically after pipeline completion
        // Then enable review buttons only if data loaded successfully
        loadReviewData().then(success => {
            if (success) {
                enableReviewButtons();
            } else {
                console.warn('Review data failed to load, buttons remain disabled');
            }
        });

        stopWebSocketUpdates();
    }
}

// Directory Browser Functions
async function openDirectoryBrowser(inputId) {
    browseTargetInput = inputId;
    const currentValue = document.getElementById(inputId).value;

    // Start from current value or home directory
    currentBrowsePath = currentValue || '';

    // Show modal
    document.getElementById('dir-browser-modal').style.display = 'flex';

    // Load directory contents
    await loadDirectory(currentBrowsePath);
}

function closeDirectoryBrowser() {
    document.getElementById('dir-browser-modal').style.display = 'none';
    browseTargetInput = null;
}

/**
 * Open the review modal with the specified review type
 * @param {number} stageId - Stage ID to load review data for
 * @param {string} reviewType - Type of review (e.g., 'photos', 'sequences')
 * @param {string} stageName - Display name of the stage
 */
async function openReviewModal(stageId, reviewType, stageName) {
    const modal = document.getElementById('review-modal');
    const iframe = document.getElementById('review-iframe');
    const title = document.getElementById('review-modal-title');

    // Load review data for this specific stage
    try {
        console.log(`Loading review data for stage ${stageId}...`);
        const success = await loadReviewData(stageId);

        if (!success) {
            alert('⚠️ Failed to load review data for this stage.');
            return;
        }
    } catch (error) {
        console.error(`Failed to load review data for stage ${stageId}:`, error);
        alert('⚠️ Failed to load review data: ' + error.message);
        return;
    }

    // Map review_type to the appropriate review page
    // Pass stage_id as query parameter so review page knows which data to load
    let reviewUrl;
    if (reviewType === 'photos') {
        reviewUrl = `/review_identical.html?stage_id=${stageId}`;
    } else {
        // All sequence-based reviews use the same interface
        // Backend filters by stage_id
        reviewUrl = `/review_sequences.html?stage_id=${stageId}`;
    }

    // Update title
    title.textContent = `📊 Review ${stageName} Results`;

    // Load review interface in iframe
    iframe.src = reviewUrl;

    // Show modal
    modal.style.display = 'flex';
}

/**
 * Close the review modal
 */
function closeReviewModal() {
    const modal = document.getElementById('review-modal');
    const iframe = document.getElementById('review-iframe');

    // Clear iframe src to stop any running processes
    iframe.src = 'about:blank';

    // Hide modal
    modal.style.display = 'none';
}

/**
 * Load review data from pipeline outputs
 * Called automatically after pipeline completion or when opening stage review
 * @param {number|null} stageId - Optional stage ID to load data for specific stage only
 * @returns {Promise<boolean>} True if data loaded successfully, false otherwise
 */
async function loadReviewData(stageId = null) {
    try {
        const stageParam = stageId !== null ? `?stage_id=${stageId}` : '';
        const logMsg = stageId !== null ? `for stage ${stageId}` : `for all stages`;
        console.log(`Loading review data ${logMsg}...`);

        const response = await fetch(`/api/review/load${stageParam}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        console.log('Review data loaded:', result);
        return true;

    } catch (error) {
        console.error('Failed to load review data:', error);
        return false;
    }
}

/**
 * Check and enable review button for a single completed stage
 * This allows incremental enabling as stages complete
 */
async function checkAndEnableReviewButton(stageElement) {
    const reviewBtn = stageElement.querySelector('.stage-review-btn');
    if (!reviewBtn) {
        return; // No review button for this stage
    }

    // Get stage ID from stage element data attribute
    const stageId = parseInt(stageElement.dataset.stage);
    if (isNaN(stageId)) {
        console.error('Stage element missing stage ID:', stageElement);
        return;
    }

    try {
        const response = await fetch('/api/review/availability');
        const data = await response.json();

        // Check if this specific stage has review data available
        // API returns: { stages: { stage_id: { available: bool, review_type: string } } }
        if (data.stages && data.stages[stageId] && data.stages[stageId].available) {
            reviewBtn.disabled = false;
            console.log(`Review button enabled for stage ${stageId} (${stageElement.dataset.stageName})`);
        }
    } catch (error) {
        console.error(`Failed to check review availability for stage ${stageId}:`, error);
    }
}

/**
 * Enable review buttons for completed stages that have reviewable data
 * This is called after full pipeline completion as a fallback
 */
async function enableReviewButtons() {
    // Check if review data is available
    try {
        const response = await fetch('/api/review/status');
        const status = await response.json();

        if (!status.loaded) {
            console.log('Review data not loaded, buttons remain disabled');
            return;
        }

        // Enable buttons for all completed stages with review data
        document.querySelectorAll('.stage-review-btn').forEach(btn => {
            const stageElement = btn.closest('.stage');
            if (stageElement && stageElement.classList.contains('completed')) {
                btn.disabled = false;
            }
        });

        console.log('Review buttons enabled');
    } catch (error) {
        console.error('Failed to check review status:', error);
    }
}

function selectCurrentDirectory() {
    if (browseTargetInput && currentBrowsePath) {
        document.getElementById(browseTargetInput).value = currentBrowsePath;

        // Trigger blur event to auto-fill work directory if source was selected
        if (browseTargetInput === 'source-dir') {
            document.getElementById('source-dir').dispatchEvent(new Event('blur'));
        }
    }
    closeDirectoryBrowser();
}

async function loadDirectory(path) {
    const directoryList = document.getElementById('directory-list');
    const breadcrumb = document.getElementById('breadcrumb');

    // Show loading
    directoryList.innerHTML = '<div class="loading">Loading...</div>';
    breadcrumb.textContent = path || 'Home';

    try {
        const response = await fetch(`/api/browse?path=${encodeURIComponent(path)}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        currentBrowsePath = data.current_path;

        // Update breadcrumb
        breadcrumb.textContent = currentBrowsePath;

        // Build directory list
        let html = '';

        // Add parent directory link if not at root
        if (data.parent_path) {
            html += `
                <div class="dir-item parent" data-path="${escapeHtml(data.parent_path)}">
                    <span>📁</span>
                    <span>..</span>
                </div>
            `;
        }

        // Add directories
        for (const dir of data.directories) {
            html += `
                <div class="dir-item" data-path="${escapeHtml(dir.path)}">
                    <span>📁</span>
                    <span>${escapeHtml(dir.name)}</span>
                </div>
            `;
        }

        if (data.directories.length === 0 && !data.parent_path) {
            html = '<div class="loading">No subdirectories found</div>';
        }

        directoryList.innerHTML = html;

        // Add click handlers to directory items
        directoryList.querySelectorAll('.dir-item').forEach(item => {
            item.addEventListener('click', () => {
                const dirPath = item.getAttribute('data-path');
                if (dirPath) {
                    loadDirectory(dirPath);
                }
            });
        });

    } catch (error) {
        console.error('Failed to load directory:', error);
        directoryList.innerHTML = `<div class="loading">Error: ${escapeHtml(error.message)}</div>`;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
