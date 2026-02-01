/**
 * Common functions shared between review interfaces
 *
 * Required interface from parent page:
 * - getTotalGroups(): return total number of groups
 * - getDecisions(): return decisions object
 * - saveProgressImpl(): implementation of save logic
 * - displayCurrentGroup(): refresh current group display
 * - currentGroupIndex: current group index variable
 *
 * Optional interface:
 * - onGroupChange(newIndex): callback invoked before displayCurrentGroup()
 */

/* global currentGroupIndex:writable, getTotalGroups, getDecisions, saveProgressImpl, displayCurrentGroup, onGroupChange, prompt */

/* exported previousGroup, nextGroup, jumpToGroup, saveProgress, quitReview, showAlert, showFullImage */

function previousGroup() {
    if (currentGroupIndex > 0) {
        currentGroupIndex--;
        // Optional hook for page-specific logic (e.g., reset video seek positions)
        if (typeof onGroupChange === 'function') {
            onGroupChange(currentGroupIndex);
        }
        displayCurrentGroup();
    }
}

function nextGroup() {
    const total = getTotalGroups();
    if (currentGroupIndex < total - 1) {
        currentGroupIndex++;
        // Optional hook for page-specific logic (e.g., reset video seek positions)
        if (typeof onGroupChange === 'function') {
            onGroupChange(currentGroupIndex);
        }
        displayCurrentGroup();
    }
}

function jumpToGroup() {
    const total = getTotalGroups();
    const input = prompt(`Jump to group number (1-${total}):`);
    if (input) {
        const groupNum = parseInt(input);
        if (groupNum >= 1 && groupNum <= total) {
            currentGroupIndex = groupNum - 1;
            // Optional hook for page-specific logic (e.g., reset video seek positions)
            if (typeof onGroupChange === 'function') {
                onGroupChange(currentGroupIndex);
            }
            displayCurrentGroup();
        } else {
            showAlert('Invalid group number', 'warning');
        }
    }
}

async function saveProgress() {
    const decisions = getDecisions();
    if (Object.keys(decisions).length === 0) {
        showAlert('No decisions to save yet', 'warning');
        return;
    }

    try {
        await saveProgressImpl();
    } catch (error) {
        showAlert('Failed to save: ' + error.message, 'error');
    }
}

async function quitReview() {
    const decisions = getDecisions();
    if (Object.keys(decisions).length > 0) {
        if (confirm('You have unsaved decisions. Save before quitting?')) {
            await saveProgress();
        }
    }

    if (confirm('Close the review interface and shutdown server?')) {
        try {
            // Shutdown the backend server
            await fetch('/api/shutdown', { method: 'POST' });
        } catch (_error) {
            console.log('Server shutdown initiated');
        }
        // Close the browser window
        window.close();
    }
}

function showAlert(message, type = 'info', persist = false) {
    const container = document.getElementById('alert-container');
    if (!container) {
        console.warn('Alert container not found, using console:', message);
        return;
    }

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    container.appendChild(alert);

    if (!persist) {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
}

/**
 * Show full resolution image in lightbox
 */
function showFullImage(photoId, filename) {
    // Create lightbox if it doesn't exist
    let lightbox = document.getElementById('photo-lightbox');
    if (!lightbox) {
        lightbox = document.createElement('div');
        lightbox.id = 'photo-lightbox';
        lightbox.style.cssText = `
            display: none;
            position: fixed;
            z-index: 10000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
            cursor: pointer;
        `;

        const img = document.createElement('img');
        img.id = 'lightbox-image';
        img.style.cssText = `
            display: block;
            margin: auto;
            max-width: 95%;
            max-height: 95%;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        `;

        const caption = document.createElement('div');
        caption.id = 'lightbox-caption';
        caption.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            color: white;
            background: rgba(0,0,0,0.7);
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 14px;
        `;

        lightbox.appendChild(img);
        lightbox.appendChild(caption);
        document.body.appendChild(lightbox);

        // Close on click
        lightbox.onclick = () => {
            lightbox.style.display = 'none';
        };

        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && lightbox.style.display === 'block') {
                lightbox.style.display = 'none';
            }
        });
    }

    // Update and show lightbox
    const img = document.getElementById('lightbox-image');
    const caption = document.getElementById('lightbox-caption');

    img.src = `/api/review/thumbnail/${photoId}?size=2000`;
    caption.textContent = filename;
    lightbox.style.display = 'block';
}
