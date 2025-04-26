document.addEventListener('DOMContentLoaded', () => {
    // --- Get DOM Elements ---
    const form = document.getElementById('give-access-form');
    const feedbackDiv = document.getElementById('form-feedback');
    const resultsDetailsDiv = document.getElementById('results-details');
    const resultsListUl = document.getElementById('results-list');
    const submitBtn = document.getElementById('submit-btn');
    const spinner = submitBtn.querySelector('.spinner');

    // Group Input Elements
    const groupTagContainer = document.getElementById('group-tag-container');
    const groupInputField = document.getElementById('group-input-field');
    const groupTagsDisplay = document.getElementById('group-tags-display');
    const groupHiddenInput = document.getElementById('groups-hidden-input');
    const groupSuggestionsList = document.getElementById('group-suggestions');
    const availableGroups = window.availableGroups || []; // Get groups from global scope
    let selectedGroups = new Set(); // Use a Set for uniqueness

    // IP Input Elements
    const ipTagContainer = document.getElementById('ip-tag-container');
    const ipInputField = document.getElementById('ip-input-field');
    const ipTagsDisplay = document.getElementById('ip-tags-display');
    const ipHiddenInput = document.getElementById('ips-hidden-input');
    let selectedIPs = new Set();

    // --- Helper Functions ---
    const showFeedback = (message, type = 'info') => {
        feedbackDiv.textContent = message;
        feedbackDiv.className = `form-feedback ${type}`; // Reset classes and add type
        feedbackDiv.style.display = 'block';
        resultsDetailsDiv.style.display = 'none'; // Hide detailed results when new feedback shows
    };

    const clearFeedback = () => {
        feedbackDiv.textContent = '';
        feedbackDiv.style.display = 'none';
        feedbackDiv.className = 'form-feedback';
    };

    const toggleLoading = (isLoading) => {
        if (isLoading) {
            submitBtn.disabled = true;
            spinner.style.display = 'inline-block';
        } else {
            submitBtn.disabled = false;
            spinner.style.display = 'none';
        }
    };

    // --- Tag Creation/Deletion ---
    const createTagElement = (text, displayList, valueSet, hiddenInput) => {
        const tag = document.createElement('li');
        tag.classList.add('tag');
        tag.textContent = text;

        const removeBtn = document.createElement('span');
        removeBtn.classList.add('tag-remove');
        removeBtn.textContent = '×'; // Multiplication sign (x)
        removeBtn.onclick = () => {
            valueSet.delete(text);
            tag.remove();
            updateHiddenInput(hiddenInput, valueSet);
        };

        tag.appendChild(removeBtn);
        displayList.appendChild(tag);
    };

    const updateHiddenInput = (inputElement, valueSet) => {
        inputElement.value = Array.from(valueSet).join(',');
    };

    // --- Group Input Logic ---
    const filterAndShowSuggestions = (query) => {
        const lowerQuery = query.toLowerCase();
        groupSuggestionsList.innerHTML = ''; // Clear previous suggestions

        if (!query && !selectedGroups.size) { // Don't show if empty and nothing selected
             hideSuggestions();
             return;
        }

        const filtered = availableGroups.filter(group =>
            !selectedGroups.has(group) && // Don't suggest already selected groups
            group.toLowerCase().includes(lowerQuery)
        );

        if (filtered.length > 0) {
            filtered.forEach(group => {
                const li = document.createElement('li');
                li.classList.add('suggestion-item');
                li.textContent = group;
                li.addEventListener('mousedown', (e) => { // Use mousedown to fire before blur
                    e.preventDefault(); // Prevent input blur
                    addGroupTag(group);
                });
                groupSuggestionsList.appendChild(li);
            });
            groupSuggestionsList.style.display = 'block';
        } else {
            hideSuggestions();
        }
    };

    const hideSuggestions = () => {
        // Delay hiding slightly to allow click events on suggestions
        setTimeout(() => {
            if (document.activeElement !== groupInputField) {
                 groupSuggestionsList.style.display = 'none';
            }
        }, 150);
    };

     const addGroupTag = (group) => {
        if (group && !selectedGroups.has(group)) {
            selectedGroups.add(group);
            createTagElement(group, groupTagsDisplay, selectedGroups, groupHiddenInput);
            updateHiddenInput(groupHiddenInput, selectedGroups);
        }
        groupInputField.value = ''; // Clear input field
        hideSuggestions();
        groupInputField.focus(); // Keep focus
    };


    groupInputField.addEventListener('input', () => filterAndShowSuggestions(groupInputField.value));
    groupInputField.addEventListener('focus', () => filterAndShowSuggestions(groupInputField.value)); // Show suggestions on focus
    groupInputField.addEventListener('blur', hideSuggestions); // Hide when focus is lost

    // Add click listener to container to focus input field
    groupTagContainer.addEventListener('click', (e) => {
        // Only focus if the click wasn't on the input itself or a remove button
        if (e.target === groupTagContainer || e.target === groupTagsDisplay) {
             groupInputField.focus();
        }
    });


    // --- IP Input Logic ---
    const addIpTag = (ip) => {
        // Basic IP format check (optional, backend validates thoroughly)
        // const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
        // if (!ip || !ipRegex.test(ip)) {
        //     showFeedback('Invalid IP address format.', 'error');
        //     setTimeout(clearFeedback, 3000);
        //     return;
        // }
        if (ip && !selectedIPs.has(ip)) {
             selectedIPs.add(ip.trim());
             createTagElement(ip.trim(), ipTagsDisplay, selectedIPs, ipHiddenInput);
             updateHiddenInput(ipHiddenInput, selectedIPs);
        }
        ipInputField.value = ''; // Clear input
    };

    ipInputField.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission
            addIpTag(ipInputField.value);
        }
    });
     // Add click listener to container to focus input field
    ipTagContainer.addEventListener('click', (e) => {
        if (e.target === ipTagContainer || e.target === ipTagsDisplay) {
             ipInputField.focus();
        }
    });

    // --- Form Submission Logic ---
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Stop default form submission
        clearFeedback();
        resultsDetailsDiv.style.display = 'none';
        resultsListUl.innerHTML = ''; // Clear previous results
        toggleLoading(true);

        // Collect data
        const formData = new FormData(form);
        const data = {
            username: formData.get('username'),
            groups: groupHiddenInput.value, // Get from hidden input
            ips: ipHiddenInput.value,       // Get from hidden input
            pub_key: formData.get('pub_key'),
            add_to_sudoers: formData.get('add_to_sudoers') === 'true' // Checkbox value
        };

        // Basic Frontend Validation (Optional - supplements backend)
        if (!data.username || !data.pub_key || (!data.groups && !data.ips)) {
             showFeedback('Please fill in Username, Public Key, and at least one Group or IP.', 'error');
             toggleLoading(false);
             return;
        }


        try {
            const response = await fetch(form.action, { // Use form's action attribute
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    // Add CSRF token header if using Flask-WTF/CSRFProtect
                    // 'X-CSRFToken': window.csrf_token
                },
                body: JSON.stringify(data),
            });

            const result = await response.json(); // Assume backend always returns JSON

            if (response.ok) { // Covers 200 and 207 status codes
                // Show the main feedback message (success or info based on overall status)
                showFeedback(result.message || 'Request processed successfully.', result.all_success ? 'success' : 'info');

                // *** Display detailed results if available ***
                if (result.results && typeof result.results === 'object' && Object.keys(result.results).length > 0) {
                    resultsListUl.innerHTML = ''; // Clear any previous results first
                    resultsDetailsDiv.style.display = 'block'; // Show the container

                    // Loop through the results object (IP is key, res is value object)
                    Object.entries(result.results).forEach(([ip, res]) => {
                        const li = document.createElement('li'); // Create a list item for each IP

                        // Determine CSS class based on success status
                        const statusClass = res.success ? 'status-success' : 'status-failure';

                        // Get the message, provide a default if empty
                        const messageText = res.message || (res.success ? 'Operation successful' : 'Operation failed');

                        // Construct the HTML for the list item using defined CSS classes
                        li.innerHTML = `
                            <span class="ip-address">${ip}:</span>
                            <span class="${statusClass}"></span>
                            <span class="message">${messageText}</span>
                        `; // Uses spans for specific styling

                        resultsListUl.appendChild(li); // Add the new list item to the UL
                    });
                } else {
                     resultsDetailsDiv.style.display = 'none'; // Hide if no results data
                }

                // Optional: Clear form only on *full* success (if desired)
                // if(result.all_success){
                //     form.reset();
                //     // Clear tags etc.
                // }

            } else {
                // Handle HTTP errors (4xx, 5xx)
                showFeedback(`Error: ${result.error || response.statusText || 'Unknown error'}`, 'error');
                 resultsDetailsDiv.style.display = 'none'; // Ensure results are hidden on error
            }

        } catch (error) {
            // Handle fetch/network errors
            console.error('Fetch Error:', error);
            showFeedback(`Network or client-side error: ${error.message}`, 'error');
             resultsDetailsDiv.style.display = 'none'; // Ensure results are hidden on error
        } finally {
            toggleLoading(false);
        }
    }); // End form submit listener

}); // End DOMContentLoaded