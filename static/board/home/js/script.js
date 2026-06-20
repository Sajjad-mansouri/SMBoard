    // Sample Data
    let userData = {};

    // Your own boards
    let yourBoards = [];
    let closedBoards = [];

    // Guest boards
    let guestBoards = [];

    // DOM Elements

    const yourBoardsContainer = document.getElementById('your-boards');
    const guestBoardsContainer = document.getElementById('guest-boards');
    const yourBoardsEmpty = document.getElementById('your-boards-empty');
    const guestBoardsEmpty = document.getElementById('guest-boards-empty');
    const createBoardModal = document.getElementById('create-board-modal');
    const createBoardBtn = document.getElementById('create-board-btn');
    const closeModalBtn = document.getElementById('close-modal');
    const cancelCreateBtn = document.getElementById('cancel-create');
    const confirmCreateBtn = document.getElementById('confirm-create');
    const boardNameInput = document.getElementById('board-name-input');
    const colorPicker = document.getElementById('color-picker');

    const closedModal = document.getElementById('closed-boards-modal');
    const closedBoardsBtn = document.getElementById('closed-boards-btn');
    const closeClosedModal = document.getElementById('close-closed-modal');
    const doneClosed = document.getElementById('done-closed-boards');
    const closeDeleteModal = document.getElementById('close-delete-modal');
    const cancelDelete = document.getElementById('cancel-delete');
    const confirmDeleteBtn = document.getElementById('confirm-delete');
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const closedBoardsList = document.getElementById('closed-boards-list');
    const noClosedMessage = document.getElementById('no-closed-boards-message');
    const deleteBoardNameSpan = document.getElementById('delete-board-name');
    let selectedColor = '#0079bf';


    // Color picker functionality
    colorPicker.addEventListener('click', (e) => {
        if (e.target.classList.contains('color-option')) {
            document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('selected'));
            e.target.classList.add('selected');
            selectedColor = e.target.getAttribute('data-color');
        }
    });

    // Render Board Card
    function renderBoardCard(board, isGuest = false) {
        const card = document.createElement('div');
        card.className = 'board-card';

        if (board.background_color) {
            card.style.background = board.background_color;

        } else if (board.background_image != null) {
            card.style.backgroundImage = `url(${board.background_image})`;
            card.style.backgroundSize = "cover";
            card.style.backgroundPosition = "center";
            card.style.backgroundRepeat = "no-repeat";

        }


        let metaInfo = `${board.cards} cards`;
        if (isGuest) {
            metaInfo = `Owner: ${board.owner.username} · ${board.cards} cards`;
        }

        card.innerHTML = `
                ${isGuest ? '<div class="guest-badge">👥 Guest</div>' : ''}
                <div class="board-card-title">${board.name}</div>
                <div class="board-card-meta">${metaInfo}</div>
            `;

        card.addEventListener('click', () => {
            window.location.href = `/board/${board.id}/`
        });

        return card;
    }

    function openBoard() {
        console.log("open board")
    }
    // Render All Boards
    function renderBoards() {
        // Your Boards
        yourBoardsContainer.innerHTML = '';
        if (yourBoards.length === 0) {
            yourBoardsEmpty.classList.remove('hidden');
        } else {
            yourBoardsEmpty.classList.add('hidden');
            yourBoards.forEach(board => {
                yourBoardsContainer.appendChild(renderBoardCard(board));

            });
            // Add Create New Board card
            const createCard = document.createElement('div');
            createCard.className = 'board-card create-new';
            createCard.innerHTML = `
                    <div class="create-new-content">
                        <div class="create-new-icon">+</div>
                        <div class="create-new-text">Create New Board</div>
                    </div>
                `;
            createCard.addEventListener('click', openCreateModal);
            yourBoardsContainer.appendChild(createCard);
        }

        // Guest Boards
        guestBoardsContainer.innerHTML = '';
        if (guestBoards.length === 0) {
            guestBoardsEmpty.classList.remove('hidden');
        } else {
            guestBoardsEmpty.classList.add('hidden');
            guestBoards.forEach(board => {
                guestBoardsContainer.appendChild(renderBoardCard(board, true));
            });
        }
    }

    // Modal Functions
    function openCreateModal() {
        createBoardModal.classList.add('active');
        boardNameInput.focus();
    }

    function closeCreateModal() {
        createBoardModal.classList.remove('active');
        boardNameInput.value = '';
        document.querySelector('.color-option[data-color="#0079bf"]').classList.add('selected');
        selectedColor = '#0079bf';
    }

    async function fetchCreateNewBoard(name) {

    }

    // Create New Board
    async function createNewBoard() {
        const name = boardNameInput.value.trim();

        if (!name) {
            alert('Please enter a board name.');
            return;
        }
        try {
            body = JSON.stringify({
                "name": name,
                "background_color": selectedColor,
            });
            const response = await auth.authenticatedRequest(`api/boards/`, body, "POST");
            const newBoard = await response.json()

            if (response.ok) {

                yourBoards.push(newBoard);
                renderBoards();
                closeCreateModal();

            } else {
                closeCreateModal();

            }
        } catch (error) {
            closeCreateModal();
            console.log(error)
        }


    }


    // Event Listeners
    createBoardBtn.addEventListener('click', openCreateModal);
    closeModalBtn.addEventListener('click', closeCreateModal);
    cancelCreateBtn.addEventListener('click', closeCreateModal);
    confirmCreateBtn.addEventListener('click', createNewBoard);

    createBoardModal.addEventListener('click', (e) => {
        if (e.target === createBoardModal) {
            closeCreateModal();
        }
    });

    boardNameInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            createNewBoard();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            if (createBoardModal.classList.contains('active')) {
                closeCreateModal();
            }
            if (profileDropdown.classList.contains('active')) {
                profileDropdown.classList.remove('active');
            }
            if (searchResults.classList.contains('active')) {
                searchResults.classList.remove('active');
            }
        }

        // Ctrl+K or Cmd+K to focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchInput.focus();
        }
    });



    async function getContentData() {
        // id: 1,
        // name: "Marketing Website",
        // color: "#0079bf",
        // cards: 12,
        try {
        console.log("******getContentData*****")
            const boardResponse = await auth.authenticatedRequest(`api/boards/`, null, "GET")
            const guestBoardResponse = await auth.authenticatedRequest(`api/guest-boards/`, null, "GET")



            let boardData = await boardResponse.json()
            let guestBoardData = await guestBoardResponse.json()


            boardData = [...boardData.filter(b => b.closed == false)]

            if (boardResponse.ok && guestBoardResponse.ok) {
                yourBoards = boardData;
                guestBoards = guestBoardData;
                renderBoards();
            }

        } catch (error) {
            console.log(error)
        }
    }
    // Initialize
    getContentData()

    console.log('SMBoards Page Loaded');
    console.log('Press Ctrl+K to focus search');

    document.getElementById("profile-logout-btn").addEventListener("click", () => {
        auth.logout()
    })



    // ---------- CLOSED BOARDS MODAL LOGIC ----------
    async function renderClosedBoardsList() {
        if (!closedBoardsList) return;
        const closed = await getClosedBoards();
        closedBoardsList.innerHTML = '';

        if (closed.length === 0) {
            noClosedMessage.classList.remove('hidden');
            closedBoardsList.classList.add('hidden');
        } else {
            noClosedMessage.classList.add('hidden');
            closedBoardsList.classList.remove('hidden');

            closed.forEach(board => {
                const li = document.createElement('li');
                li.className = 'closed-board-item';
                li.innerHTML = `
              <div class="closed-board-name">
                ${escapeHtml(board.name)}
                
              </div>
              <div class="closed-board-actions">
                <button class="btn btn-outline reopen-btn" data-id="${board.id}" style="padding:6px 12px; font-size:0.8rem;">🔄 Reopen</button>
                <button class="btn btn-outline delete-btn" data-id="${board.id}" style="padding:6px 12px; font-size:0.8rem; color:var(--danger-color); border-color:var(--danger-color);">🗑️ Delete</button>
              </div>
            `;
                closedBoardsList.appendChild(li);
            });

            // Attach event listeners to reopen & delete buttons
            document.querySelectorAll('#closed-boards-list .reopen-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const boardId = btn.getAttribute('data-id');
                    reopenBoard(boardId);
                });
            });

            document.querySelectorAll('#closed-boards-list .delete-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const boardId = btn.getAttribute('data-id');
                    openDeleteConfirmation(boardId);
                });
            });
        }
    }

    async function reopenBoard(boardId) {
        // Find board in your or guest
        body = JSON.stringify({
            "closed": false
        })
        const response = await auth.authenticatedRequest(`api/boards/${boardId}/`, body, "PATCH", {}, "application/json")
        const data = await response.json()

        getContentData()
        renderClosedBoardsList()
        // If closed modal is still open, re-render its list
        if (closedModal.classList.contains('active')) {
            renderClosedBoardsList();
        }

    }

    function openDeleteConfirmation(boardId) {

        const board = [...closedBoards].find(b => b.id === Number(boardId));

        if (!board) return;
        boardToDeleteId = boardId;
        deleteBoardNameSpan.textContent = board.title;
        deleteConfirmModal.classList.add('active');
    }

    async function deleteBoardPermanently(boardId) {
        // Remove from your or guest

        try {
            const response = await auth.authenticatedRequest(`api/boards/${boardId}/`, "", "DELETE")

            if (response.ok) {
                // Close delete modal & update closed list if needed
                deleteConfirmModal.classList.remove('active');
                if (closedModal.classList.contains('active')) {
                    renderClosedBoardsList()

                }

            } else {
                console.log("error happening")
            }
        } catch (error) {
            console.log(error)
        }


    }

    function openClosedModal() {
        renderClosedBoardsList();
        closedModal.classList.add('active');
    }

    function closeClosedModalFn() {
        closedModal.classList.remove('active');
    }

    function closeDeleteModalFn() {
        deleteConfirmModal.classList.remove('active');
        boardToDeleteId = null;
    }


    // Closed boards button
    closedBoardsBtn.addEventListener('click', openClosedModal);
    closeClosedModal.addEventListener('click', closeClosedModalFn);
    doneClosed.addEventListener('click', closeClosedModalFn);
    closedModal.addEventListener('click', (e) => {
        if (e.target === closedModal) closeClosedModalFn();
    });

    // Delete confirmation modal events
    closeDeleteModal.addEventListener('click', closeDeleteModalFn);
    cancelDelete.addEventListener('click', closeDeleteModalFn);
    deleteConfirmModal.addEventListener('click', (e) => {
        if (e.target === deleteConfirmModal) closeDeleteModalFn();
    });

    confirmDeleteBtn.addEventListener('click', () => {
        if (boardToDeleteId) {
            deleteBoardPermanently(boardToDeleteId);
        }
    });



    async function getClosedBoards() {
        try {
            const response = await auth.authenticatedRequest(`api/closed/`, null, "GET")
            const data = await response.json()


            if (response.ok) {
                closedBoards = data
                return data
            } else {
                console.log('not ok!')
            }
        } catch (error) {
            console.log(error)
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