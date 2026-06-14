        (function() {
            // ============================================
            // CONFIGURATION
            // ============================================
            const auth = new Auth()

            const CONFIG = {

            };

            async function prepareConfig() {
                const url = origin + '/api/setting-config/'
                const response = await auth.authenticatedRequest(url, null, "GET");
                const data = await response.json();
                console.log(response, data)
                CONFIG["IS_PYTHONANYWHERE"] = data.host_async_ability
                CONFIG["NOTIFICATION"] = data.notification_setting

            }

            console.log(CONFIG)

            // Mock existing usernames for validation
            const existingUsernames = ['johndoe', 'admin', 'test', 'user', 'trello'];

            // ============================================
            // TOAST NOTIFICATION SYSTEM
            // ============================================
            function showToast(message, type = 'info', duration = 3000) {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = `toast ${type}`;

                const icons = {
                    success: '✅',
                    error: '❌',
                    warning: '⚠️',
                    info: 'ℹ️'
                };

                toast.innerHTML = `
                    <span class="toast-icon">${icons[type] || icons.info}</span>
                    <span class="toast-message">${message}</span>
                    <button class="toast-close" onclick="this.parentElement.remove()">×</button>
                `;

                container.appendChild(toast);

                setTimeout(() => {
                    if (toast.parentElement) {
                        toast.classList.add('removing');
                        setTimeout(() => {
                            if (toast.parentElement) {
                                toast.remove();
                            }
                        }, 300);
                    }
                }, duration);
            }

            // ============================================
            // MODAL SYSTEM
            // ============================================
            function showModal({
                title,
                message,
                icon,
                confirmText,
                confirmClass,
                onConfirm
            }) {
                const container = document.getElementById('modal-container');

                const overlay = document.createElement('div');
                overlay.className = 'modal-overlay';

                overlay.innerHTML = `
                    <div class="modal">
                        <div class="modal-header">
                            <span class="modal-icon">${icon || '⚠️'}</span>
                            <span class="modal-title">${title}</span>
                        </div>
                        <div class="modal-body">${message}</div>
                        <div class="modal-footer">
                            <button class="btn-modal-cancel" id="modal-cancel">Cancel</button>
                            <button class="btn-modal-confirm ${confirmClass || ''}" id="modal-confirm">${confirmText || 'Confirm'}</button>
                        </div>
                    </div>
                `;

                container.appendChild(overlay);

                const closeModal = () => {
                    overlay.classList.add('fade-out');
                    setTimeout(() => overlay.remove(), 200);
                };

                overlay.querySelector('#modal-cancel').addEventListener('click', closeModal);

                overlay.querySelector('#modal-confirm').addEventListener('click', () => {
                    if (onConfirm) onConfirm();
                    closeModal();
                });

                overlay.addEventListener('click', (e) => {
                    if (e.target === overlay) closeModal();
                });

                return {
                    close: closeModal
                };
            }

            // ============================================
            // APPLY CONFIGURATION
            // ============================================
            async function applyConfiguration() {
                await prepareConfig()
                const pythonanywhereBanner = document.getElementById('pythonanywhere-banner');
                const localDevBanner = document.getElementById('local-dev-banner');
                const frequencyCard = document.getElementById('notification-frequency-card');
                const typesCard = document.getElementById('notification-types-card');
                const frequencySelect = document.getElementById('notification-frequency');
                const selectAllCheckbox = document.getElementById('select-all-notifications');
                const notificationCheckboxes = document.querySelectorAll('.notification-checkbox');
                const saveSettingsBtn = document.getElementById('save-settings-btn');

                if (CONFIG.IS_PYTHONANYWHERE) {
                    pythonanywhereBanner.style.display = 'flex';
                    localDevBanner.style.display = 'none';
                    frequencyCard.classList.add('disabled-card');
                    typesCard.classList.add('disabled-card');
                    frequencySelect.disabled = true;
                    selectAllCheckbox.disabled = true;
                    notificationCheckboxes.forEach(cb => cb.disabled = true);
                    saveSettingsBtn.disabled = true;
                } else {
                    pythonanywhereBanner.style.display = 'none';
                    localDevBanner.style.display = 'flex';
                    frequencyCard.classList.remove('disabled-card');
                    typesCard.classList.remove('disabled-card');
                    frequencySelect.disabled = false;
                    selectAllCheckbox.disabled = false;
                    notificationCheckboxes.forEach(cb => cb.disabled = false);
                    saveSettingsBtn.disabled = false;
                }
            }

            // ---------- STATE ----------
            let cardsData = [{
                id: 'c1',
                title: 'Design new landing page',
                list: 'In Progress',
                label: 'High Priority',
                labelColor: '#eb5a46',
                due: '2024-12-15',
                board: 'Marketing Website',
                archived: false
            }, {
                id: 'c2',
                title: 'Fix login bug',
                list: 'To Do',
                label: 'Bug',
                labelColor: '#f2d600',
                due: '2024-12-10',
                board: 'App Development',
                archived: false
            }, {
                id: 'c3',
                title: 'Update API documentation',
                list: 'Done',
                label: 'Documentation',
                labelColor: '#61bd4f',
                due: '2024-12-05',
                board: 'Backend Services',
                archived: false
            }, {
                id: 'c4',
                title: 'User research interviews',
                list: 'In Progress',
                label: 'Research',
                labelColor: '#0079bf',
                due: '2024-12-20',
                board: 'Design System',
                archived: false
            }, {
                id: 'c5',
                title: 'Old marketing campaign',
                list: 'Archived',
                label: 'Marketing',
                labelColor: '#ff9f1a',
                due: '2024-10-01',
                board: 'Marketing Website',
                archived: true
            }, {
                id: 'c6',
                title: 'Legacy code cleanup',
                list: 'Archived',
                label: 'Tech Debt',
                labelColor: '#eb5a46',
                due: '2024-09-15',
                board: 'App Development',
                archived: true
            }];

            let boardsData = [{
                id: 'b1',
                name: 'Marketing Website',
                color: 'linear-gradient(135deg, #667eea, #764ba2)',
                closed: false
            }, {
                id: 'b2',
                name: 'App Development',
                color: 'linear-gradient(135deg, #4facfe, #00f2fe)',
                closed: false
            }, {
                id: 'b3',
                name: 'Backend Services',
                color: '#eb5a46',
                closed: false
            }, {
                id: 'b4',
                name: 'Design System',
                color: '#61bd4f',
                closed: false
            }];

            const CARDS_PER_PAGE = 3;
            let currentCardsPage = 1;
            let showArchivedCards = false;

            // ---------- DOM ELEMENTS ----------
            const navItems = document.querySelectorAll('.sidebar-nav-item');
            const panels = document.querySelectorAll('.content-panel');
            const cardsTbody = document.getElementById('cards-table-body');
            const prevPageBtn = document.getElementById('prev-page');
            const nextPageBtn = document.getElementById('next-page');
            const pageIndicator = document.getElementById('page-indicator');
            const showActiveBtn = document.getElementById('show-active-cards');
            const showArchivedBtn = document.getElementById('show-archived-cards');
            const boardsListDiv = document.getElementById('boards-list');
            const newBoardInput = document.getElementById('new-board-name');
            const createBoardBtn = document.getElementById('create-board-btn');
            const backToHomeBtn = document.getElementById('back-to-home-btn');
            let nextCardsPage = "";
            let prevCardsPage = "";

            async function fetchDelete(url, body) {
                try {
                    const bodyJSON = JSON.stringify(body)


                    const response = await auth.authenticatedRequest(url, bodyJSON, "DELETE", {})

                    if (response.ok) {

                        return true
                    } else {
                        return false
                    }

                } catch (error) {
                    console.log(error)
                    return false
                }
            }

            function escapeHtml(text) {
                return String(text).replace(/[&<>"]/g, function(m) {
                    if (m === '&') return '&amp;';
                    if (m === '<') return '&lt;';
                    if (m === '>') return '&gt;';
                    if (m === '"') return '&quot;';
                    return m;
                });
            }

            async function getCards(next = false, previous = false) {

                try {
                    let url;
                    if (next) {
                        url = nextCardsPage
                    } else if (previous) {
                        url = prevCardsPage
                    } else {

                        url = origin + `/api/card-list/?archived=${showArchivedCards}`;
                    }
                    const response = await auth.authenticatedRequest(url, null, "GET");
                    const data = await response.json();
                    if (response.ok) {
                        nextCardsPage = data.next
                        prevCardsPage = data.previous

                        return data
                    }
                } catch (error) {
                    console.log(error)
                }

            }

            async function renderCards(next = false, previous = false) {
                const data = await getCards(next, previous)

                const totalPages = data.total_pages;
                const paginatedCards = data.results

                cardsTbody.innerHTML = '';

                if (paginatedCards.length === 0) {
                    cardsTbody.innerHTML = `<tr><td colspan="6" style="text-align:center;padding:24px;color:var(--text-secondary);">No cards found.</td></tr>`;
                } else {
                    paginatedCards.forEach(card => {
                        const tr = document.createElement('tr');
                        const labelElementsList = []
                        card.card_labels.forEach(label => {
                            labelElementsList.push(`<span style="background:${label.color};color:white;padding:2px 8px;border-radius:10px;font-size:0.75rem;">${escapeHtml(label.name)}</span>`)
                        })
                        const labelElements = labelElementsList.join(" ")
                        tr.innerHTML = `
                            <td><strong>${escapeHtml(card.name)}</strong></td>
                            <td>${escapeHtml(card.board_list_name)}</td>
                            <td>${labelElements}</td>
                            <td>${escapeHtml(card.due_date?card.due_date:"")}</td>
                            <td>${escapeHtml(card.board)}</td>
                            <td>
                                <div class="flex-row">
                                    ${!card.archived 
                                        ? `<button class="btn btn-sm btn-outline archive-card-btn" data-id="${card.id}">📦 Archive</button>` 
                                        : `<button class="btn btn-sm btn-outline unarchive-card-btn" data-id="${card.id}">📤 Restore</button><button class="btn btn-sm btn-danger delete-card-btn" data-id="${card.id}" data-title="${card.name}">🗑️ Delete</button>`
                                    }
                                    
                                </div>
                            </td>
                        `;
                        cardsTbody.appendChild(tr);
                    });
                }

                pageIndicator.textContent = `Page ${data.page} of ${data.total_pages}`;
                prevPageBtn.disabled = data.previous == null;
                nextPageBtn.disabled = data.next == null;

                attachCardEvents();
            }

            async function getBoards() {
                try {
                    const url = origin + `/api/boards/`;
                    const response = await auth.authenticatedRequest(url, null, "GET");
                    const data = await response.json();
                    if (response.ok) {
                        return data
                    }
                } catch (error) {
                    console.log(error)
                }
            }

            async function renderBoards() {
                boardsListDiv.innerHTML = '';
                const boardsData = await getBoards()
                console.log("boardsData", boardsData)

                boardsData.forEach(board => {
                    const boardDiv = document.createElement('div');
                    boardDiv.className = 'board-card';
                    boardDiv.style.background = board.background_color;
                    boardDiv.innerHTML = `
                        <span class="board-card-title">
                            ${escapeHtml(board.name)}
                            ${board.closed ? '<span class="archived-badge">Closed</span>' : ''}
                        </span>
                        <div class="board-actions">
                            ${!board.closed 
                                ? `<button class="close-board-btn" data-id="${board.id}">🔒 Close</button>` 
                                : `<button class="reopen-board-btn" data-id="${board.id}">🔓 Reopen</button>`
                            }
                            <button class="remove-board-btn" data-id="${board.id}" data-name="${board.name}">🗑️ Remove</button>
                        </div>
                    `;
                    boardsListDiv.appendChild(boardDiv);
                });


                attachBoardEvents();
            }

            async function update(url, body) {
                try {
                    const bodyJSON = JSON.stringify(body)
                    const response = await auth.authenticatedRequest(url, bodyJSON, "PATCH", {}, "application/json")
                    const data = response.json()
                    if (response.ok) {
                        return data
                    } else {
                        return false
                    }
                } catch (error) {
                    console.log(error)
                    return false
                }
            }

            function attachCardEvents() {
                document.querySelectorAll('.archive-card-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const url = origin + `/api/card/update-archived/${id}/`
                        const body = {
                            "archived": true
                        }
                        const result = await update(url, body)

                        if (result) {
                            showToast(`Card "<strong>${result.name}</strong>" has been archived.`, 'success');

                            renderCards();
                        }
                    });
                });

                document.querySelectorAll('.unarchive-card-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const url = origin + `/api/card/update-archived/${id}/`
                        const body = {
                            "archived": false
                        }
                        const result = await update(url, body)
                        if (result) {

                            showToast(`Card "<strong>${result.name}</strong>" has been restored.`, 'success');

                            renderCards();
                        }
                    });
                });

                document.querySelectorAll('.delete-card-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const title = btn.getAttribute('data-title');



                        showModal({
                            title: 'Delete Card',
                            message: `Are you sure you want to permanently delete <strong>"${title}"</strong>? This action cannot be undone.`,
                            icon: '🗑️',
                            confirmText: 'Delete Permanently',
                            confirmClass: '',
                            onConfirm: async () => {
                                const url = origin + `/api/cards/${id}/`
                                const result = await fetchDelete(url, {})
                                if (result) {
                                    renderCards();
                                    showToast(`Card deleted successfully.`, 'success');

                                }
                            }
                        });

                    });
                });
            }

            function attachBoardEvents() {
                document.querySelectorAll('.close-board-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const url = origin + `/api/boards/${id}/`
                        const body = {
                            "closed": true
                        }
                        const result = await update(url, body)
                        if (result) {

                            renderBoards();
                            showToast(`Board "<strong>${result.name}</strong>" has been closed.`, 'warning');
                        }
                    });
                });

                document.querySelectorAll('.reopen-board-btn').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const url = origin + `/api/boards/${id}/`
                        const body = {
                            "closed": false
                        }
                        const result = await update(url, body)
                        if (result) {

                            renderBoards();
                            showToast(`Board "<strong>${result.name}</strong>" has been reopened.`, 'success');
                        }
                    });
                });

                document.querySelectorAll('.remove-board-btn').forEach(btn => {
                    btn.addEventListener('click', (e) => {
                        e.stopPropagation();
                        const id = btn.getAttribute('data-id');
                        const boardName = btn.getAttribute('data-name');



                        showModal({
                            title: 'Remove Board',
                            message: `Are you sure you want to remove <strong>"${boardName}"</strong>? This will permanently delete the board and all its data. This action cannot be undone.`,
                            icon: '🗑️',
                            confirmText: 'Remove Board',
                            confirmClass: '',
                            onConfirm: async () => {
                                const url = origin + `/api/boards/${id}/`
                                const result = await fetchDelete(url, {})
                                if (result) {
                                    renderBoards();
                                    showToast(`Board "<strong>${boardName}</strong>" has been removed.`, 'success');

                                }
                            }
                        });

                    });
                });

                const createNewCard = document.getElementById('create-new-board-card');
                if (createNewCard) {
                    createNewCard.addEventListener('click', () => {
                        const boardsNavItem = document.querySelector('.sidebar-nav-item[data-panel="boards"]');
                        if (boardsNavItem) boardsNavItem.click();
                        newBoardInput.focus();
                    });
                }
            }

            // ---------- NAVIGATION ----------
            navItems.forEach(item => {
                item.addEventListener('click', () => {
                    navItems.forEach(nav => nav.classList.remove('active'));
                    item.classList.add('active');
                    const panelId = item.getAttribute('data-panel');
                    panels.forEach(panel => panel.classList.remove('active'));
                    const activePanel = document.getElementById(`${panelId}-panel`);
                    if (activePanel) activePanel.classList.add('active');
                    if (panelId === 'cards') renderCards();
                    else if (panelId === 'boards') renderBoards();
                });
            });

            backToHomeBtn.addEventListener('click', () => {
                window.location.href = '/';
            });

            // ---------- PAGINATION ----------
            prevPageBtn.addEventListener('click', () => {
                renderCards(false, true);
            });
            nextPageBtn.addEventListener('click', () => {
                renderCards(true);

            });

            // ---------- FILTER TOGGLES ----------
            showActiveBtn.addEventListener('click', () => {
                showArchivedCards = false;
                currentCardsPage = 1;
                renderCards();
                showActiveBtn.style.background = 'var(--accent-color)';
                showActiveBtn.style.color = 'white';
                showActiveBtn.style.border = 'none';
                showArchivedBtn.style.background = 'transparent';
                showArchivedBtn.style.color = 'var(--text-color)';
                showArchivedBtn.style.border = '1px solid var(--border-color)';
            });

            showArchivedBtn.addEventListener('click', () => {
                showArchivedCards = true;
                currentCardsPage = 1;
                renderCards();
                showArchivedBtn.style.background = 'var(--accent-color)';
                showArchivedBtn.style.color = 'white';
                showArchivedBtn.style.border = 'none';
                showActiveBtn.style.background = 'transparent';
                showActiveBtn.style.color = 'var(--text-color)';
                showActiveBtn.style.border = '1px solid var(--border-color)';
            });

            showActiveBtn.style.background = 'var(--accent-color)';
            showActiveBtn.style.color = 'white';
            showActiveBtn.style.border = 'none';

            // ---------- CREATE BOARD ----------
            createBoardBtn.addEventListener('click', async () => {
                const name = newBoardInput.value.trim();
                if (name) {
                    const bodyJSON = JSON.stringify({
                        "name": name
                    })
                    const url = origin + `/api/boards/`
                    try {
                        const response = await auth.authenticatedRequest(url, bodyJSON, "POST")
                        const data = await response.json()

                        if (response.ok) {
                            renderBoards();
                            showToast(`Board "<strong>${data.names}</strong>" created successfully!`, 'success');

                        }
                    } catch (error) {
                        showToast('Temporary issue. Please try again.', 'error');

                    }

                } else {
                    showToast('Please enter a board name.', 'error');
                }
            });

            // ---------- PROFILE IMAGE UPLOAD ----------
            const profileImageInput = document.getElementById('profile-image-input');
            const profileImageDisplay = document.getElementById('profile-image-display');
            const profileInitials = document.getElementById('profile-initials');

            document.querySelector('.profile-image-upload').addEventListener('click', (e) => {
                if (e.target.tagName !== 'INPUT') profileImageInput.click();
            });

            function populateProfileImage(imgSrc, username = "") {
                if (imgSrc) {

                    profileInitials.style.display = 'none';
                    const existingImg = profileImageDisplay.querySelector('img');
                    if (existingImg) existingImg.remove();
                    const img = document.createElement('img');
                    img.src = imgSrc;
                    profileImageDisplay.appendChild(img);
                } else {
                    profileInitials.innerText = username[0]
                }
            }
            async function getUserProfileInfo() {
                const url = origin + `/api/user/`
                try {
                    const response = await auth.authenticatedRequest(url, null, "GET")
                    const data = await response.json()
                    if (response.ok) {
                        populateProfileImage(data.profile_image, data.username)
                        document.getElementById('profile-firstname').value = data.first_name;
                        document.getElementById('profile-lastname').value = data.last_name;
                        document.getElementById('profile-username').value = data.username;
                        document.getElementById('profile-bio').value = data.profile.bio;
                        document.getElementById('profile-email').value = data.email;

                    }
                } catch (error) {
                    console.log(data)
                }


            }
            getUserProfileInfo()
            profileImageInput.addEventListener('change', async (e) => {
                const file = e.target.files[0];
                if (file) {
                    try {
                        const url = origin + `/api/update-profile/`
                        const body = new FormData()
                        body.append("profile_image", file)
                        const response = await auth.authenticatedRequest(url, body, "PATCH", {}, "multipart/form-data");
                        const data = await response.json()
                        if (response.ok) {
                            populateProfileImage(data.profile_image)
                        }
                    } catch (error) {
                        console.log(error)
                    }

                }
            });

            // ---------- SAVE PROFILE WITH USERNAME VALIDATION ----------
            document.getElementById('save-profile-btn').addEventListener('click', async () => {
                const firstName = document.getElementById('profile-firstname').value.trim();
                const lastName = document.getElementById('profile-lastname').value.trim();
                const username = document.getElementById('profile-username').value.trim();
                const bio = document.getElementById('profile-bio').value.trim();
                const email = document.getElementById('profile-email').value.trim();



                try {
                    const url = origin + `/api/update-user/`
                    const bodyJSON = JSON.stringify({
                        "first_name": firstName,
                        "last_name": lastName,
                        "username": username,
                        "email": email,

                        "profile": {
                            "bio": bio
                        }
                    })
                    const response = await auth.authenticatedRequest(url, bodyJSON, "PATCH", {}, "application/json")
                    const data = await response.json()
                    if (response.ok) {

                        showToast('Profile saved successfully!', 'success');
                    } else {
                        Object.entries(data).forEach(([key, value]) => {
                            showToast(value, 'error');

                        })
                    }
                } catch (error) {

                    showToast('Temporary issue. Please try again.', 'error');
                }
                // Simulate successful save


            });
            document.getElementById('delete-account-btn').addEventListener('click', () => {
                showModal({
                    title: 'Delete Account',
                    message: `
                        <p style="margin-bottom:12px;">Are you absolutely sure you want to delete your account?</p>
                        <p style="margin-bottom:12px;"><strong>This action cannot be undone.</strong> All of your data will be permanently removed including:</p>
                        <ul style="margin-left:20px;margin-bottom:12px;">
                            <li>Your profile and personal information</li>
                            <li>All boards you own</li>
                            <li>All cards assigned to you</li>
                            <li>Comments and activity history</li>
                        </ul>
                        <p>Please type <strong>DELETE</strong> to confirm:</p>
                        <input type="text" id="delete-confirm-input" class="form-input" style="margin-top:8px;" placeholder="Type DELETE to confirm">
                    `,
                    icon: '⚠️',
                    confirmText: 'Delete My Account',
                    confirmClass: '',
                    onConfirm: async () => {
                        const confirmInput = document.getElementById('delete-confirm-input');
                        if (confirmInput && confirmInput.value === 'DELETE') {
                            const url = origin + `/api/delete-account/`
                            const result = await fetchDelete(url, {})
                            if (result) {
                                showToast('Your account has been scheduled for deletion. You will be logged out.', 'warning', 5000);
                                console.log('Account deletion confirmed');
                                window.location.href = "/"

                            }
                        } else {
                            showToast('Please type DELETE to confirm account deletion.', 'error');
                        }
                    }
                });
            });
            // ---------- NOTIFICATION SETTINGS ----------
            const selectAllCheckbox = document.getElementById('select-all-notifications');
            const notificationCheckboxes = document.querySelectorAll('.notification-checkbox');

            async function getAndPopulateCheckBoxes() {
                const url = origin + `/api/notification-settings/${CONFIG["NOTIFICATION"]}/`
                try {
                    const response = await auth.authenticatedRequest(url, null, "GET");
                    const data = await response.json();

                    if (response.ok) {
                        Object.entries(data).forEach(([key, value]) => {
                            const notif = document.querySelector(`.notification-checkbox[name="${key}"]`)
                            if (notif) {

                                notif.checked = value

                            }
                        })
                        selectAllCheckbox.addEventListener('change', () => {
                            if (!CONFIG.IS_PYTHONANYWHERE) {
                                notificationCheckboxes.forEach(checkbox => {
                                    checkbox.checked = selectAllCheckbox.checked;
                                });
                            }
                        });

                        notificationCheckboxes.forEach(checkbox => {
                            checkbox.addEventListener('change', () => {
                                if (!CONFIG.IS_PYTHONANYWHERE) {
                                    const allChecked = Array.from(notificationCheckboxes).every(cb => cb.checked);
                                    selectAllCheckbox.checked = allChecked;
                                }
                            });
                        });
                    }
                } catch (error) {
                    console.log(error)
                }

            }



            document.getElementById('save-settings-btn').addEventListener('click', async () => {
                if (CONFIG.IS_PYTHONANYWHERE) {
                    showToast(`Notification settings are not available on ${origin}.`, 'warning');
                    return;
                }

                const notifications = {};
                const frequency = document.getElementById('notification-frequency').value;
                notifications["email_frequency"] = frequency
                notificationCheckboxes.forEach(cb => {
                    if (cb.checked) {
                        notifications[cb.getAttribute("name")] = true;
                    } else {

                        notifications[cb.getAttribute("name")] = false;
                    }

                });


                const url = origin + `/api/notification-settings/${CONFIG["NOTIFICATION"]}/`
                const body = notifications
                const result = await update(url, body)

                if (result) {
                    showToast('Notification settings saved successfully!', 'success');

                }

            });

            // ---------- INITIAL SETUP ----------

            async function runSequentially() {
                await applyConfiguration();
                getAndPopulateCheckBoxes()
            }
            runSequentially()

            console.log('✅ Trello Settings Page Loaded Successfully');
            console.log('🔧 Mode:', CONFIG.IS_PYTHONANYWHERE ? 'PythonAnywhere' : 'Local Development');
        })();