document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Elements ---
    const findUserStage = document.getElementById('find-user-stage');
    const removeAccessForm = document.getElementById('remove-access-form');
    const usernameInput = document.getElementById('username');
    const findServersBtn = document.getElementById('find-servers-btn');
    const serverListHeading = document.getElementById('server-list-heading');
    const displayUsernameSpan = document.getElementById('display-username');
    const ipListUl = document.getElementById('ip-list');
    const selectAllCheckbox = document.getElementById('select-all-ips');
    const submitRemovalBtn = document.getElementById('submit-removal-btn');
    const ipSearchInput = document.getElementById('ip-search-input'); // <-- Get the search input

    const feedbackDiv = document.getElementById('form-feedback');
    const resultsDetailsDiv = document.getElementById('results-details');
    const resultsListUl = document.getElementById('results-list');

    const findSpinner = findServersBtn.querySelector('.spinner');
    const removeSpinner = submitRemovalBtn.querySelector('.spinner');

    // --- Helper Functions (reuse or adapt from giveaccess.js) ---
    const showFeedback = (message, type = 'info') => {
        feedbackDiv.textContent = message;
        feedbackDiv.className = `form-feedback ${type}`;
        feedbackDiv.style.display = 'block';
        // Ensure results area is hidden when general feedback is shown
        resultsDetailsDiv.style.display = 'none';
    };

    const clearFeedback = () => {
        feedbackDiv.textContent = '';
        feedbackDiv.style.display = 'none';
        feedbackDiv.className = 'form-feedback';
    };

    const toggleLoading = (buttonSpinner, isLoading) => {
        const button = buttonSpinner.closest('button');
        if (isLoading) {
            button.disabled = true;
            buttonSpinner.style.display = 'inline-block';
        } else {
            button.disabled = false;
            buttonSpinner.style.display = 'none';
        }
    };

    const resetToInitialState = () => {
        findUserStage.style.display = 'block';
        removeAccessForm.style.display = 'none';
        resultsDetailsDiv.style.display = 'none';
        ipListUl.innerHTML = ''; // Clear IP list
        usernameInput.value = ''; // Clear username input maybe? Optional.
        selectAllCheckbox.checked = false;
        ipSearchInput.value = ''; 
        clearFeedback();
    };

    // --- Event Listener: Find Servers Button ---
    findServersBtn.addEventListener('click', async () => {
        const username = usernameInput.value.trim();
        clearFeedback();
        ipSearchInput.value = ''; 
        ipListUl.innerHTML = ''; // Clear previous list if any
        removeAccessForm.style.display = 'none'; // Hide form while fetching
        resultsDetailsDiv.style.display = 'none'; // Hide results

        if (!username) {
            showFeedback('Please enter a username.', 'error');
            return;
        }

        toggleLoading(findSpinner, true);

        try {
            const response = await fetch(`/api/get-user-ips/${encodeURIComponent(username)}`);
            const data = await response.json();

            if (response.ok) {
                displayUsernameSpan.textContent = username; // Display the username in the heading
                ipListUl.innerHTML = ''; // Ensure list is clear

                if (data.ips && data.ips.length > 0) {
                    data.ips.forEach(ip => {
                        const li = document.createElement('li');
                        const checkboxId = `ip-${ip.replace(/\./g, '-')}`; // Create valid ID
                        li.innerHTML = `
                            <input type="checkbox" id="${checkboxId}" value="${ip}" name="selected_ips">
                            <label for="${checkboxId}">${ip}</label>
                        `;
                        ipListUl.appendChild(li);
                    });
                    removeAccessForm.style.display = 'block'; // Show the form with IPs
                    selectAllCheckbox.checked = false; // Ensure select-all is unchecked initially
                    filterIpList();
                } else {
                    // This case should ideally be caught by 404 below, but handle just in case
                     showFeedback(`No active servers found for username "${username}".`, 'info');
                }
            } else {
                // Handle specific errors from API (400, 404, 500)
                 showFeedback(data.error || data.message || `Error ${response.status}: Could not fetch server list.`, 'error');
            }

        } catch (error) {
            console.error('Fetch Error (Find Servers):', error);
            showFeedback(`Network error fetching server list: ${error.message}`, 'error');
        } finally {
            toggleLoading(findSpinner, false);
        }
    });

    const filterIpList = () => {
        const searchTerm = ipSearchInput.value.toLowerCase().trim();
        const ipListItems = ipListUl.querySelectorAll('li');

        let visibleCount = 0;
        ipListItems.forEach(item => {
            const label = item.querySelector('label');
            const ipAddress = label ? label.textContent.toLowerCase() : '';

            const isMatch = ipAddress.includes(searchTerm); // Simple substring match

            if (isMatch) {
                item.classList.remove('hidden-by-search');
                visibleCount++;
            } else {
                item.classList.add('hidden-by-search');
            }
        });

        if (ipListItems.length > 0 && visibleCount === 0 && searchTerm !== '') {
            showFeedback(`No IP addresses match "${searchTerm}".`, 'info');
        }
    };

    ipSearchInput.addEventListener('input', filterIpList);

    // --- Event Listener: Select/Deselect All Checkbox ---
    selectAllCheckbox.addEventListener('change', () => {
        const checkboxes = ipListUl.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAllCheckbox.checked;
        });
    });

     // --- Event Listener: Individual checkbox changes (to uncheck 'Select All') ---
     ipListUl.addEventListener('change', (event) => {
         if (event.target.type === 'checkbox') {
             const allCheckboxes = ipListUl.querySelectorAll('input[type="checkbox"]');
             const allChecked = Array.from(allCheckboxes).every(cb => cb.checked);
             const noneChecked = Array.from(allCheckboxes).every(cb => !cb.checked); // Optional: Check if needed

             selectAllCheckbox.checked = allChecked;
             // Optional: Handle indeterminate state if needed
             selectAllCheckbox.indeterminate = !allChecked && !noneChecked;

         }
     });


    // --- Event Listener: Form Submission (Remove Access) ---
    removeAccessForm.addEventListener('submit', async (event) => {
        event.preventDefault(); 
        clearFeedback();
        resultsDetailsDiv.style.display = 'none';
        resultsListUl.innerHTML = ''; // Clear previous results

        const username = usernameInput.value.trim(); // Get username again
        const selectedIpCheckboxes = ipListUl.querySelectorAll('input[type="checkbox"]:checked');
        const ipsToRemove = Array.from(selectedIpCheckboxes).map(cb => cb.value);

        if (!username) { 
             showFeedback('Username is missing.', 'error');
             return;
        }
        if (ipsToRemove.length === 0) {
            showFeedback('Please select at least one IP address to remove access from.', 'error');
            return;
        }

        toggleLoading(removeSpinner, true);

        const payload = {
            username: username,
            ips: ipsToRemove
        };

        try {
            const response = await fetch(removeAccessForm.action || '/accesspoint/removeaccess', { // Use form action or default
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // 'X-CSRFToken': window.csrf_token // Add if using CSRF
                },
                body: JSON.stringify(payload),
            });

            const result = await response.json(); // Assume JSON response

            if (response.ok) { // Handles 200 and 207
                 showFeedback(result.message || 'Removal request processed.', result.all_success ? 'success' : 'info');

                // Display detailed results (reuse logic from giveaccess.js)
                if (result.results && typeof result.results === 'object') {
                    resultsListUl.innerHTML = ''; // Clear just before populating
                    resultsDetailsDiv.style.display = 'block';
                    Object.entries(result.results).forEach(([ip, res]) => {
                        const li = document.createElement('li');
                        const statusClass = res.success ? 'status-success' : 'status-failure';
                        const messageText = res.message || (res.success ? 'Success' : 'Failure');
                        li.innerHTML = `
                            <span class="ip-address">${ip}:</span>
                            <span class="${statusClass}"></span>
                            <span class="message">${messageText}</span>
                        `;
                        resultsListUl.appendChild(li);
                    });
                }

                 // Optionally reset form fields or hide the IP list after successful submission
                 // resetToInitialState(); // Call this to go back to step 1
                 removeAccessForm.style.display = 'none'; // Or just hide the IP list part


            } else {
                 showFeedback(`Error: ${result.error || response.statusText || 'Unknown error'}`, 'error');
                 resultsDetailsDiv.style.display = 'none';
            }

        } catch (error) {
            console.error('Fetch Error (Remove Access):', error);
            showFeedback(`Network or client-side error during removal: ${error.message}`, 'error');
            resultsDetailsDiv.style.display = 'none';
        } finally {
            toggleLoading(removeSpinner, false);
        }
    });

}); // End DOMContentLoaded