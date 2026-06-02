(function() {
    const auth = new Auth()
    const STORAGE_KEY = 'SM_board_data';

    const defaultData = {
        activeBoardId: 'board1',
        boards: [{
            id: 'board1',
            title: 'My Board',
            background: '#f0f2f5',
            boardMembers: ['user1', 'user2'],
            memberRoles: {
                'user1': 'admin',
                'user2': 'member'
            },
            boardVisibility: 'public',
            joinRequests: [],
            boardWatched: false,
            boardClosed: false,
            archivedLists: [],
            lists: [{
                id: 'list1',
                title: 'To Do',
                cardIds: ['card1']
            }, {
                id: 'list2',
                title: 'In Progress',
                cardIds: ['card2']
            }, {
                id: 'list3',
                title: 'Done',
                cardIds: []
            }],
            cards: {

            }
        }],
        users: [],
        labels: []
    };
    let appState = JSON.parse(JSON.stringify(defaultData));
    let showArchived = false;
    let CURRENT_USER_ID;
    let currentActivityFilter = 'all';
    async function fetchPostWithFormData(url, body, fetchType) {

        try {


            const response = await auth.authenticatedRequest(url, body, fetchType, {}, "multipart/form-data")
            if (response.ok) {

                const data = await response.json()

                return data
            } else {
                return false
            }


        } catch (error) {
            console.log(error)
            return false
        }
    }

    function checkAttachmentClass(type) {
        const image_types = ["image", "png", "jpeg"];
        const file_types = ["text", "plain", "csv", "zip", "rar", "file"];

        const typeList = type.split("/");
        const imageType = image_types.some(item => typeList.includes(item));
        const fileType = file_types.some(item => typeList.includes(item));
        return [imageType, fileType]
    }
    async function fetchUpdate(url, body) {



        try {
            const bodyJSON = JSON.stringify(body)
            console.log("bodyjson", bodyJSON, url)
            const response = await auth.authenticatedRequest(url, bodyJSON, "PATCH", {}, "application/json")
            if (response.ok) {

                const data = await response.json()
                return data
            } else {
                return false
            }



        } catch (error) {
            console.log(error)
            return false
        }

    }

    async function fetchPost(url, body) {
        try {
            const bodyJSON = JSON.stringify(body)

            console.log(url, bodyJSON)
            const response = await auth.authenticatedRequest(url, bodyJSON, "POST")
            const data = await response.json()
            if (response.ok) {

                console.log("fetch post data", data)
                return data

            } else {
                console.log(data)
                return false
            }



        } catch (error) {
            console.log(error)
            return false
        }
    }

    async function fetchDelete(url, body) {
        try {
            const bodyJSON = JSON.stringify(body)


            const response = await auth.authenticatedRequest(url, bodyJSON, "DELETE", {})
            console.log(response)
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

    async function saveData(func = null, model = null, body = null, objId = null, useFormData = false) {
        // localStorage.setItem(STORAGE_KEY, JSON.stringify(appState));


        let path = "";
        let result;
        if (model == "Card") {
            path = `card/${objId}/`
            const url = origin + "/api/" + path

            if (useFormData) {
                result = await fetchPostWithFormData(url, body, "PATCH")

            } else {
                result = await fetchUpdate(url, body)
            }


        } else if (model == "Checklist") {
            if (func == "create") {
                path = "checklists/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `checklists/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `checklists/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }

        } else if (model == "ChecklistItem") {
            if (func == "create") {
                path = "checklist-items/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `checklist-items/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `checklist-items/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "Comment") {
            if (func == "create") {
                path = "comments/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `comments/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `comments/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "CardImage") {
            if (func == "create") {
                path = "card-images/"
                const url = origin + "/api/" + path
                console.log(url, body)
                result = await fetchPostWithFormData(url, body)



            } else if (func == "delete") {
                path = `card-images/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `card-images/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "CardFile") {
            if (func == "create") {
                path = "card-files/"
                const url = origin + "/api/" + path
                result = await fetchPostWithFormData(url, body)



            } else if (func == "delete") {
                path = `card-files/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `card-files/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "CardLabel") {
            if (func == "create") {
                path = "card-labels/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `card-labels/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `card-labels/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "BoardList") {
            if (func == "create") {
                path = "board-lists/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `board-lists/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `board-lists/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "BoardListOrder") {
            if (func == "update") {
                path = `board-list-order/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "CardOrder") {
            if (func == "update") {
                path = `card-order/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        } else if (model == "CardMember") {
            if (func == "create") {
                path = `card-members/`
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)
            } else if (func == "delete") {
                path = `card-members/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            }
        } else if (model == "BoardMember") {
            if (func == "create") {
                path = "board-members/"
                const url = origin + "/api/" + path
                result = await fetchPost(url, body)



            } else if (func == "delete") {
                path = `board-members/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchDelete(url, body)


            } else if (func == "update") {
                path = `board-members/${objId}/`
                const url = origin + "/api/" + path
                result = await fetchUpdate(url, body)
            }
        }
        return result
    }

    function migrateData(data) {
        data.boards.forEach(board => {
            if (!board.boardMembers) board.boardMembers = [data.users?.[0]?.id || 'user1'];
            if (!board.memberRoles) board.memberRoles = {};
            if (!board.boardVisibility) board.boardVisibility = 'private';
            if (!board.joinRequests) board.joinRequests = [];
            if (board.boardWatched === undefined) board.boardWatched = false;
            if (board.boardClosed === undefined) board.boardClosed = false;
            if (!board.archivedLists) board.archivedLists = [];
            Object.values(board.cards).forEach(card => {
                if (!card.checklists && card.checklist) {
                    if (Array.isArray(card.checklist) && card.checklist.length > 0 && typeof card
                        .checklist[0] === 'object' && !card.checklist[0].items) {
                        card.checklists = [{
                            id: generateId(),
                            name: 'Checklist',
                            items: card.checklist
                        }];
                    } else if (card.checklist && Array.isArray(card.checklist) && card.checklist
                        .length > 0 && card.checklist[0].items) {
                        card.checklists = card.checklist;
                    } else {
                        card.checklists = [];
                    }
                    delete card.checklist;
                }
                if (!card.checklists) card.checklists = [];
                card.checklists.forEach(cl => {
                    if (!cl.id) cl.id = generateId();
                    if (!cl.name) cl
                        .name = 'Checklist';
                    if (!cl.items) cl.items = [];
                });
            });
        });
        return data;
    }



    function prepareBoardObject(data) {
        const boardObj = {}
        boardObj["id"] = data.id
        boardObj["title"] = data.name
        boardObj["background"] = data.background_color ? data.background_color : `url(${data.background_image}) center / cover no - repeat`

        boardObj["boardVisibility"] = data.status
        boardObj["boardWatched"] = data.board_watched
        boardObj["boardClosed"] = data.closed
        boardObj["cards"] = {}



        return boardObj

    }

    function prepareListArray(data) {
        const listObjs = []
        const archivedList = []
        data.board_lists.forEach(list => {

            const cardIds = list.list_cards.map(item => item.id);
            const newList = {
                "id": list.id,
                "title": list.name,
                "cardIds": cardIds
            }
            if (list.archived == false) listObjs.push(newList)
            if (list.archived == true) archivedList.push(newList)
        })

        return [listObjs, archivedList]
    }

    function prepareMembershipArrays(data) {
        const boardMembers = []
        const boardMembership = {}
        const memberRoles = {}
        const joinRequests = []
        const users = []
        data.board_memberships.forEach(member => {
            boardMembership[member.user.id] = {
                "id": member.id
            }
            if (member.accepted) {
                boardMembers.push(member.user.id)
                memberRoles[`${member.user.id}`] = member.member_type
            }
            users.push({
                id: member.user.id,
                name: member.user.fullname ? member.user.fullname : member.user.username,
                color: "#0079bf",
                email: member.user.email,
                username: member.user.username,
                profileImage: member.user.profile_image
            })
            if (!member.accepted) joinRequests.push(member.user.id)


        })

        return [boardMembers, memberRoles, joinRequests, users, boardMembership]
    }

    function prepareComments(cardData) {
        const comments = []
        cardData.card_comments.forEach(commentData => {
            const comment = {}
            comment["userId"] = commentData["user"]
            comment["text"] = commentData["content"]
            comment["timestamp"] = commentData["timestamp"]
            comment["edited"] = commentData["edited"]
            comment["id"] = commentData["id"]
            comment["reply"] = commentData["reply"]


            comments.push(comment)
        })
        return comments
    }

    function prepareChecklistItems(checklistData) {
        const items = []
        checklistData.checklist_items.forEach(itemData => {
            const item = {}
            item["id"] = itemData["id"]
            item["text"] = itemData["name"]
            item["completed"] = itemData["is_completed"]

            items.push(item)
        })
        return items
    }

    function prepareCheckLists(cardData) {
        const checklists = []
        cardData.card_checklists.forEach(checklistData => {
            const checklist = {}
            const checklistItems = prepareChecklistItems(checklistData)
            checklist["id"] = checklistData["id"]
            checklist["name"] = checklistData["name"]
            checklist["items"] = checklistItems
            checklists.push(checklist)
        })
        return checklists
    }

    function prepareAttachments(cardData) {
        const attachments = []
        const allFiles = [...cardData.cardfile_set, ...cardData.cardimage_set]
        allFiles.forEach(fileData => {
            const attachment = {}
            attachment["id"] = fileData["id"]

            attachment["name"] = fileData["display_name"]
            attachment["type"] = fileData["file_type"]
            attachment["data"] = fileData["file"]
            attachment["uploadedAt"] = fileData["upload_at"]
            attachment["uploadedBy"] = fileData["user"]

            attachments.push(attachment)
        })
        return attachments
    }

    function prepareCard(data) {
        const cards = {}
        const labels = []
        data.board_lists.forEach(list => {
            list.list_cards.forEach(cardData => {

                const comments = prepareComments(cardData)
                const checklists = prepareCheckLists(cardData)
                const attachments = prepareAttachments(cardData)


                const card = {}

                card["id"] = cardData["id"]
                card["title"] = cardData["name"]
                card["description"] = cardData["description"]
                card["labels"] = cardData["labels"]
                card["startDate"] = cardData["start_date"]
                card["dueDate"] = cardData["due_date"]

                card["assignedUsers"] = cardData["card_memberships"]
                card["coverColor"] = cardData["cover_color"]
                card["coverImage"] = cardData["cover_img"]
                card["watched"] = cardData["watched"]
                card["archived"] = cardData["archived"]
                card["completed"] = cardData["completed"]
                card["checklists"] = checklists
                card["comments"] = comments
                card["attachments"] = attachments
                card["activities"] = []

                labels.push(...cardData["card_labels"])

                cards[`${cardData["id"]}`] = card

            })

        })

        return [cards, labels]
    }


    async function fetchData() {
        try {
            const boardId = document.getElementById("board-title").dataset.board;
            const url = origin + `/api/board/${boardId}`
            const response = await auth.authenticatedRequest(url, null, "GET")
            const data = await response.json()

            const userUrl = origin + `/api/current-user/`
            const userResponse = await auth.authenticatedRequest(userUrl, null, "GET")
            const currentUserData = await userResponse.json()
            CURRENT_USER_ID = currentUserData.user



            const boardObj = prepareBoardObject(data)
            const [listObjs, archivedList] = prepareListArray(data)
            const [boardMembers, memberRoles, joinRequests, users, boardMembership] = prepareMembershipArrays(data)
            const [cards, labels] = prepareCard(data)



            boardObj["archivedLists"] = archivedList
            boardObj["lists"] = listObjs
            boardObj["joinRequests"] = joinRequests
            boardObj["boardMembers"] = boardMembers
            boardObj["memberRoles"] = memberRoles
            appState["activeBoardId"] = data.id
            boardObj["cards"] = cards
            appState["boards"] = [boardObj]
            appState["users"] = users
            appState["labels"] = labels
            appState["boardMembership"] = boardMembership



        } catch (error) {
            console.log(error)
        }
    }

    async function loadData() {
        await fetchData()
        const stored = localStorage.getItem(STORAGE_KEY);

        if (stored) {
            try {
                appState = JSON.parse(stored);
                appState = migrateData(appState);
            } catch (e) {
                console.log(e)
            }
        }
        const oldStored = localStorage.getItem('kanban_board_data_v4');
        if (oldStored && !stored) {
            try {
                appState = JSON.parse(oldStored);
                appState = migrateData(appState);
                saveData();
            } catch (e) {
                console.log(e)
            }

        }


        renderBoard();
        addEventListeners();

    }

    function getActiveBoard() {

        return appState.boards.find(b => b.id === appState.activeBoardId) || appState
            .boards[0];
    }

    function generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    function getUserById(id) {
        console.log("appState.users", appState.users)
        return appState.users.find(u => u.id === id);
    }

    function getLabelById(id) {
        return appState.labels.find(l => l.id === id);
    }

    function escapeHtml(t) {
        const d = document.createElement('div');
        d.textContent = t;
        return d.innerHTML;
    }

    function isOverdue(d) {
        if (!d) return false;
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        return new Date(d) < today;
    }

    function getChecklistProgress(checklists) {
        if (!checklists || !checklists.length) return 0;
        let total = 0,
            done = 0;
        checklists.forEach(cl => {
            if (cl.items && cl.items.length) {
                total += cl.items.length;
                done += cl.items.filter(i => i.completed).length;
            }
        });
        return total === 0 ? 0 : Math.round((
            done / total) * 100);
    }

    function getSingleChecklistProgress(cl) {
        if (!cl.items || !cl.items.length) return 0;
        return Math.round((cl
            .items.filter(i => i.completed).length / cl.items.length) * 100);
    }

    function addActivity(card, text, userId) {
        card.activities.push({
            timestamp: Date.now(),
            text,
            user: userId ||
                null
        });
    }

    function linkify(comment) {


        if (comment.reply) {


            return `<a href="" data-reply-id="${comment.reply.id}" data-reply-type="${comment.reply.type}">${comment.reply.name}</a> ${comment.text}`
        } else {
            return comment.text
        }
        const urlRegex = /(\[([^\]]+)\]\(([^)]+)\))|(https?:\/\/[^\s]+)/g;
        return text.replace(
            urlRegex, (match, md, mdText, mdUrl, rawUrl) => {
                if (md)
                    return ` <a href="${escapeHtml(mdUrl)}" target="_blank" rel="noopener" >${escapeHtml(mdText)}</a>`;
                return `<a href="${escapeHtml(rawUrl)}" target="_blank" rel="noopener">${escapeHtml(rawUrl)}</a>`;
            });
    }

    let draggedList = null,
        listPlaceholder = null,
        draggedCard = null,
        cardPlaceholder = null,
        currentCardId = null,
        editingCommentIndex = null;

    function renderBoard() {
        const board = getActiveBoard();
        document.body.style.background = board.background;
        document.getElementById('board-title').innerText = board.title;
        document.getElementById('board-title').textContent = board.title;
        renderBoardMenuBar();
        renderLists();
        updateNotificationBadge();
        updateBoardWatchStatus();
    }

    function updateBoardWatchStatus() {
        const board = getActiveBoard();
        const statusEl = document.getElementById('board-watch-status');
        if (board.boardWatched) {
            statusEl.textContent = 'Watching';
        } else {
            statusEl.textContent = 'Not watching';
        }
    }

    function renderBoardMenuBar() {
        const board = getActiveBoard();
        const avatarsContainer = document.getElementById('board-member-avatars');
        const visibilityBtn = document.getElementById('visibility-badge-btn');
        avatarsContainer.innerHTML = '';
        const displayMembers = board.boardMembers.slice(0, 4);
        displayMembers.forEach(uid => {
            const u = getUserById(uid);
            if (u) {
                const avatar = document.createElement('span');
                const profileImage = u.profileImage ? `<img src="${u.profileImage}" alt="${u.name}">` : `${u.name[0]}`
                avatar.className = 'board-member-avatar-small';
                avatar.style.backgroundColor = u.color;
                avatar.innerHTML = profileImage;
                avatar.title = u.name + (board.memberRoles[uid] === 'admin' ? ' (Admin)' : '');
                avatarsContainer.appendChild(avatar);
            }
        });
        if (board.boardMembers.length > 4) {
            const more = document.createElement('span');
            more.className = 'board-member-avatar-small more';
            more.textContent = '+' + (board.boardMembers.length - 4);
            more.title = board.boardMembers.length - 4 + ' more members';
            avatarsContainer.appendChild(more);
        }
        const visLabels = {
            'private': '🔒 Private',
            'workspace': '🏢 Workspace',
            'public': '🌐 Public'
        };
        visibilityBtn.textContent = visLabels[board.boardVisibility] || '🌐 Public';
        document.getElementById('board-title').textContent = board.title;
    }

    function renderLists() {
        const board = getActiveBoard(),
            wrapper = document.getElementById('lists-wrapper');
        wrapper.innerHTML = '';
        board.lists.forEach(list => {
            wrapper.appendChild(createListElement(list));
        });
        attachListDragEvents();
        attachCardDragEvents();

    }

    function createListElement(list) {
        const board = getActiveBoard();
        const div = document.createElement('div');
        div.className = 'list';
        div.dataset.listId = list.id;
        div.innerHTML =
            `<div class="list-header"><span class="drag-handle" draggable="true">⋮⋮</span><input type="text" class="list-title" value="${escapeHtml(list.title)}" data-list-id="${list.id}" /><div class="list-header-actions"><div style="position:relative;"><button class="icon-btn list-menu-btn" data-list-id="${list.id}" title="List actions">⋯</button><div class="list-menu-dropdown hidden" data-list-id="${list.id}"><div class="list-menu-dropdown-item" data-action="archive-list">📦 Archive List</div></div></div></div></div><div class="list-cards" data-list-id="${list.id}"></div><div class="list-actions"><button class="add-card-btn" data-list-id="${list.id}">+ Add Card</button></div>`;
        const cardsContainer = div.querySelector('.list-cards');
        list.cardIds.forEach(cid => {

            if (board.cards[cid]) {
                if (!showArchived && board.cards[cid].archived)
                    return;
                cardsContainer.appendChild(renderCardElement(board.cards[cid]));
            }
        });
        div.querySelector('.list-title').addEventListener('change', () => {
            const title = div.querySelector(
                '.list-title').value.trim() || 'Untitled';
            list.title = title

            saveData();
            renderBoard();
        });
        div.querySelector('.add-card-btn').addEventListener('click', () => {
            const t = prompt('Card title:');
            if (
                t && t.trim()) addCardToList(list.id, t.trim());
        });
        cardsContainer.addEventListener('click', (e) => {
            const cardEl = e.target.closest('.card');
            if (cardEl)
                openCardModal(cardEl.dataset.cardId);
        });

        // List menu button - three dots
        const menuBtn = div.querySelector('.list-menu-btn');
        const menuDropdown = div.querySelector('.list-menu-dropdown');
        menuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllPopovers();
            document.querySelectorAll('.list-menu-dropdown').forEach(d => {
                if (d !== menuDropdown) d.classList.add('hidden');
            });

            menuDropdown.classList.toggle('hidden');


            if (!menuDropdown.classList.contains('hidden')) {
                const rect = menuBtn.getBoundingClientRect();
                menuDropdown.style.position = 'absolute';
                menuDropdown.style.top = '100%';
                menuDropdown.style.right = '0';
                menuDropdown.style.left = 'auto';
            }
        });
        menuDropdown.querySelector('[data-action="archive-list"]').addEventListener('click', async () => {
            menuDropdown.classList.add('hidden');
            if (confirm(`Archive list "${list.title}"? All cards in this list will also be archived.`)) {
                const body = {
                    archived: true
                }

                const result = await saveData("update", "BoardList", body, list.id);
                if (result) {

                    archiveList(list.id);
                }
            }
        });

        return div;
    }

    function archiveList(listId) {
        const board = getActiveBoard();
        const listIndex = board.lists.findIndex(l => l.id === listId);
        if (listIndex === -1) return;
        const archivedList = board.lists[listIndex];
        if (!board.archivedLists) board.archivedLists = [];

        board.archivedLists.push(JSON.parse(JSON.stringify(archivedList)));
        archivedList.cardIds.forEach(cardId => {
            if (board.cards[cardId]) {
                board.cards[cardId].archived = true;
                addActivity(board.cards[cardId], `archived card as part of list "${archivedList.title}"`, CURRENT_USER_ID);
            }
        });
        board.lists.splice(listIndex, 1);

        renderBoard();
    }

    function unarchiveList(listId, listData) {
        const board = getActiveBoard();
        if (board.archivedLists) {
            board.archivedLists = board.archivedLists.filter(l => l.id !== listId);
        }
        const newList = JSON.parse(JSON.stringify(listData));
        newList.cardIds = [];
        board.lists.push(newList);
        listData.cardIds.forEach(cardId => {
            if (board.cards[cardId]) {
                board.cards[cardId].archived = false;
                newList.cardIds.push(cardId);
                addActivity(board.cards[cardId], `restored from archive`, CURRENT_USER_ID);
            }
        });

        renderBoard();
        renderArchivedModal();
    }

    function permanentlyDeleteList(listId) {
        const board = getActiveBoard();
        if (board.archivedLists) {
            board.archivedLists = board.archivedLists.filter(l => l.id !== listId);
        }

        renderArchivedModal();
    }

    function unarchiveCard(cardId) {
        const board = getActiveBoard();
        if (board.cards[cardId]) {
            board.cards[cardId].archived = false;
            const originalList = board.lists.find(l => l.cardIds.includes(cardId));
            if (!originalList) {
                const firstList = board.lists[0];
                if (firstList) firstList.cardIds.push(cardId);
            }
            addActivity(board.cards[cardId], `restored from archive`, CURRENT_USER_ID);
            saveData();
            renderBoard();
            renderArchivedModal();
        }
    }

    function permanentlyDeleteCard(cardId) {
        const board = getActiveBoard();
        delete board.cards[cardId];
        if (board.archivedLists) {
            board.archivedLists.forEach(l => {
                l.cardIds = l.cardIds.filter(id => id !== cardId);
            });
        }
        saveData();
        renderArchivedModal();
        renderBoard();
    }

    function renderCardElement(card) {
        const div = document.createElement('div');
        div.className = 'card' + (card.completed ? ' completed-card' : '');
        div.draggable = true;
        div.dataset.cardId = card.id;
        const progress = getChecklistProgress(card.checklists),
            overdue = card.dueDate && isOverdue(card.dueDate);
        const labelsHTML = card.labels.map(lid => {
            const l = getLabelById(lid);
            return l ?
                `<span class="card-label" style="background:${l.color}" title="${l.name}"></span>` : '';
        }).join(
            '');

        const usersHTML = card.assignedUsers.map(member => {
            const u = getUserById(member.user);
            return u ?
                `<span class="card-user-avatar" style="background:${u.color}" title="${u.name}">${u.name[0]}</span>` :
                '';
        }).join('');

        const coverStyle = card.coverImage ? `background-image:url(${card.coverImage});background-size:cover;` : (card
            .coverColor ? `background-color:${card.coverColor};` : '');
        let checklistMiniHTML = '';
        if (card.checklists && card.checklists.length > 0) {
            checklistMiniHTML = card.checklists.map(cl => {
                    const
                        clProgress = getSingleChecklistProgress(cl);
                    return `<div class="card-checklist-mini"><span>${escapeHtml(cl.name)}</span><span class="mini-bar"><span class="mini-fill" style="width:${clProgress}%"></span></span><span>${clProgress}%</span></div>`;
                })
                .join('');
        }
        div.innerHTML =
            `${(card.coverColor||card.coverImage)?`<div class="card-cover" style="${coverStyle}"></div>`:''}<div class="card-title">${escapeHtml(card.title)} ${card.archived?'<span class="archive-badge">ARCHIVED</span>':''} ${card.watched?'👀':''} ${card.completed?'✅':''}</div><div class="card-meta">${labelsHTML?`<div class="card-badges">${labelsHTML}</div>`:''}${card.dueDate?`<span class="due-date ${overdue?'overdue':''}">📅 ${new Date(card.dueDate).toLocaleDateString()}</span>`:''}<div class="card-users">${usersHTML}</div></div>${checklistMiniHTML}${card.checklists&&card.checklists.length>0?`<div class="checklist-progress"><div class="checklist-progress-fill" style="width:${progress}%"></div></div><small style="font-size:0.7rem">${progress}%</small>`:''}`;
        return div;
    }

    function addCardToList(listId, title) {
        const b = getActiveBoard();
        const id = generateId();
        b.cards[id] = {
            id,
            title,
            description: '',
            labels: [],
            startDate: '',
            dueDate: '',
            assignedUsers: [],
            coverColor: '',
            coverImage: '',
            watched: false,
            archived: false,
            completed: false,
            checklists: [],
            comments: [],
            attachments: [],
            activities: []
        };
        addActivity(b.cards[id], 'Card created', CURRENT_USER_ID);
        b.lists.find(l => l.id === listId).cardIds.push(id);
        saveData();
        renderBoard();
    }

    function deleteCard(cid) {
        const b = getActiveBoard();
        b.lists.forEach(l => l.cardIds = l.cardIds.filter(id => id !== cid));
        delete b.cards[cid];
        saveData();
        renderBoard();
    }

    async function moveCard(cardId, targetListId, targetIndex) {
        const b = getActiveBoard();
        const oldList = b.lists.find(l => l.cardIds.includes(cardId));
        b.lists.forEach(l => l.cardIds = l.cardIds.filter(id => id != cardId));
        const tl = b.lists.find(l => l.id == targetListId);
        const cardIdList = [...tl.cardIds]
        if (tl) {
            if (targetIndex != undefined) cardIdList.splice(targetIndex, 0,
                cardId);
            else cardIdList.push(cardId);
        }
        if (oldList && tl && oldList.id != tl.id) addActivity(b
            .cards[cardId], `moved from ${oldList.title} to ${tl.title}`, null);


        const body = []
        cardIdList.forEach((cardId, index) => {
            body.push({
                "id": cardId,
                "order": index
            })
        })

        const result = await saveData("update", "CardOrder", body);
        if (result) {
            tl.cardIds = cardIdList
            renderBoard();
        }
    }

    function copyCard(cardId) {
        const b = getActiveBoard();
        const original = b.cards[cardId];
        if (!original)
            return;
        const newId = generateId();
        const newCard = JSON.parse(JSON.stringify(original));
        newCard.id = newId;
        newCard.activities = [];
        addActivity(newCard, 'Card copied', CURRENT_USER_ID);
        b.cards[newId] = newCard;
        const list = b.lists.find(l => l.cardIds.includes(cardId));
        if (list) list
            .cardIds.push(newId);
        saveData();
        renderBoard();
    }

    function toggleWatch(cardId) {
        const card = getActiveBoard().cards[cardId];
        if (!card) return;
        card.watched = !card.watched;
        addActivity(card, card.watched ? 'started watching' : 'stopped watching', CURRENT_USER_ID);
        saveData();
        renderBoard();
    }

    function toggleArchive(cardId) {
        const card = getActiveBoard().cards[cardId];
        if (!card) return;
        card.archived = !card.archived;
        addActivity(card, card.archived ? 'archived card' : 'unarchived card', CURRENT_USER_ID);
        const body = {
            "archived": card.archived ? true : false
        }
        saveData("update", "Card", body, card.id);
        renderBoard();
    }

    function attachListDragEvents() {
        if (listPlaceholder) listPlaceholder.remove();
        listPlaceholder = document.createElement('div');
        listPlaceholder.className = 'list-drop-placeholder';
        document.querySelectorAll('.drag-handle').forEach(handle => {
            handle.setAttribute('draggable', 'true');
            handle.removeEventListener('dragstart', onListDragStart);
            handle.addEventListener('dragstart', onListDragStart);
            handle.removeEventListener('dragend', onListDragEnd);
            handle.addEventListener('dragend', onListDragEnd);


        });
        const wrapper = document.getElementById('lists-wrapper');
        wrapper.removeEventListener('dragover', onWrapperDragOver);
        wrapper.addEventListener('dragover', onWrapperDragOver);
        wrapper.removeEventListener('drop', onWrapperDrop);
        wrapper.addEventListener('drop', onWrapperDrop);
    }

    function onListDragStart(e) {

        const handle = e.target.closest('.drag-handle');
        if (!handle) return;
        const listEl = handle.closest('.list');
        if (!listEl) return;
        draggedList = listEl;
        e.dataTransfer.setData('text/plain', listEl.dataset.listId);
        e.dataTransfer.effectAllowed = 'move';
        listEl.style.opacity = '0.4';
        if (cardPlaceholder) cardPlaceholder.remove();
        if (listPlaceholder
            .parentNode) listPlaceholder.remove();
    }

    function onListDragEnd(e) {

        if (draggedList) draggedList.style.opacity = '1';
        if (listPlaceholder.parentNode) listPlaceholder.remove();
        draggedList = null;
    }



    function onWrapperDragOver(e) {

        if (!draggedList) return;
        e.preventDefault();
        const targetList = e.target.closest('.list');
        if (!targetList || targetList === draggedList) {

            if (listPlaceholder.parentNode) listPlaceholder.remove();
            return;
        }
        const wrapper = document.getElementById('lists-wrapper');
        const rect = targetList.getBoundingClientRect();
        const middle = rect.left + rect.width / 2;

        if (e.clientX < middle) {
            wrapper.insertBefore(listPlaceholder, targetList);

        } else {
            wrapper.insertBefore(listPlaceholder, targetList.nextSibling);
        }
    }

    async function onWrapperDrop(e) {

        e.preventDefault();
        if (!draggedList || !listPlaceholder.parentNode) return;

        const wrapper = document.getElementById('lists-wrapper');
        const placeholderIdx = Array.from(wrapper.children).indexOf(listPlaceholder);
        if (placeholderIdx === -1) return;
        const children = Array.from(wrapper.children);
        let targetIndex = 0;
        let prevList = null,
            nextList = null;
        for (let i = placeholderIdx - 1; i >= 0; i--) {
            if (children[i].classList && children[i].classList.contains('list')) {
                prevList = children[i];
                break;
            }
        }
        for (let i = placeholderIdx +
                1; i < children.length; i++) {
            if (children[i].classList && children[i].classList.contains('list')) {
                nextList = children[i];
                break;
            }
        }


        const board = getActiveBoard();
        const fromId = draggedList.dataset.listId;

        const fromIndex = board.lists.findIndex(l => l.id == fromId);

        if (fromIndex === -1) return;
        if (prevList) {
            const prevId = prevList.dataset.listId;
            targetIndex = board.lists.findIndex(l => l.id == prevId) + 1;
        } else if (nextList) {
            const nextId = nextList.dataset.listId;
            targetIndex = board.lists.findIndex(l => l.id == nextId);
        } else {
            targetIndex = board.lists.length;
        }
        const boardList = [...board.lists]
        const [moved] = boardList.splice(fromIndex, 1);

        boardList.splice(targetIndex, 0, moved);
        boardList.forEach((list, index) => {
            list.order = index;
        });
        const body = boardList.map(list => ({
            id: list.id,
            order: list.order
        }))

        const result = await saveData("update", "BoardListOrder", body);
        if (result) {
            board.lists = boardList
            if (listPlaceholder.parentNode) listPlaceholder.remove();


            if (draggedList) draggedList.style.opacity = '1';
            draggedList = null;
            renderBoard();
        }
    }


    function attachCardDragEvents() {
        if (cardPlaceholder) cardPlaceholder.remove();
        cardPlaceholder = document.createElement('div');
        cardPlaceholder.className = 'card-drop-placeholder';
        document.querySelectorAll('.card').forEach(card => {
            card.removeEventListener('dragstart',
                onCardDragStart);
            card.addEventListener('dragstart', onCardDragStart);
            card.removeEventListener('dragend', onCardDragEnd);
            card.addEventListener('dragend', onCardDragEnd);
        });
        document.querySelectorAll('.list-cards').forEach(container => {
            container.removeEventListener('dragover',
                onCardDragOver);
            container.addEventListener('dragover', onCardDragOver);
            container.removeEventListener('drop', onCardDrop);
            container.addEventListener('drop', onCardDrop);
        });
    }

    function onCardDragStart(e) {
        draggedCard = this;
        e.dataTransfer.setData('text/plain', this.dataset.cardId);
        this.classList.add('dragging');
        if (cardPlaceholder.parentNode) cardPlaceholder.remove();
    }

    function onCardDragEnd(e) {
        this.classList.remove('dragging');
        if (cardPlaceholder.parentNode) cardPlaceholder
            .remove();
        draggedCard = null;
    }

    function onCardDragOver(e) {
        e.preventDefault();
        const container = e.target.closest('.list-cards');
        if (!container) return;
        const afterEl = getDragAfterElement(container, e.clientY);

        if (afterEl) {
            container.insertBefore(cardPlaceholder, afterEl);
        } else {

            container.appendChild(cardPlaceholder)
        };
    }

    function onCardDrop(e) {
        e.preventDefault();
        if (cardPlaceholder.parentNode) cardPlaceholder.remove();
        const cardId = e.dataTransfer.getData('text/plain');
        const targetList = e.target.closest('.list-cards');
        if (!targetList) return;
        const listId = targetList.dataset.listId;
        const afterElement = getDragAfterElement(targetList, e.clientY);
        let index = undefined;

        if (afterElement) {
            const cards = [
                ...targetList.querySelectorAll('.card:not(.dragging)')
            ];
            index = cards.indexOf(afterElement);

        }
        moveCard(cardId, listId, index);
    }

    function getDragAfterElement(container, y) {
        const els = [...container.querySelectorAll(
            '.card:not(.dragging)')];
        return els.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            if (offset < 0 && offset > closest.offset) return {
                offset,
                element: child
            };
            return closest;
        }, {
            offset: Number.NEGATIVE_INFINITY
        }).element;
    }

    function updateNotificationBadge() {
        const b = getActiveBoard()
    }



    function closeAllPopovers() {
        document.getElementById('cover-popover').classList.add('hidden');
        document.getElementById('labels-popover').classList.add('hidden');
        document.getElementById('dates-popover').classList.add('hidden');
        document.getElementById('members-popover').classList.add('hidden');
        document.getElementById('attach-popover').classList.add('hidden');
        document.getElementById('three-dot-dropdown').classList.add('hidden');
        document.getElementById('add-dropdown').classList.add('hidden');
        document.getElementById('visibility-dropdown').classList.add('hidden');
        document.getElementById('profile-dropdown').classList.add('hidden');
        document.getElementById('board-menu-dropdown').classList.add('hidden');
        document.querySelectorAll('.list-menu-dropdown').forEach(d => d.classList.add('hidden'));
        document.querySelectorAll('.role-dropdown').forEach(d => d.remove());
    }

    function positionPopover(popoverEl, anchorEl, offsetX = 0, offsetY = 4) {
        const rect = anchorEl
            .getBoundingClientRect();
        let left = rect.left + offsetX;
        let top = rect.bottom + offsetY;
        const pw =
            popoverEl.offsetWidth || 300;
        const ph = popoverEl.offsetHeight || 200;
        if (left + pw > window
            .innerWidth - 10) left = window.innerWidth - pw - 10;
        if (left < 5) left = 5;
        if (top + ph > window
            .innerHeight - 10) top = rect.top - ph - offsetY;
        if (top < 5) top = 5;
        popoverEl.style.left = Math.round(left) + 'px';
        popoverEl.style.top = Math.round(top) + 'px';
    }

    function updateWatchIndicator() {
        const card = currentCardId ? getActiveBoard().cards[currentCardId] :
            null;
        const indicator = document.getElementById('watch-indicator-modal');
        if (card && card.watched)
            indicator.classList.remove('hidden');
        else indicator.classList.add('hidden');
    }

    function openCardModal(id) {
        currentCardId = id;
        editingCommentIndex = null;
        const c = getActiveBoard().cards[id];
        if (!c) return;

        document.getElementById('modal-card-title').value = c.title;
        document.getElementById('modal-card-title').classList.toggle('completed', c.completed);
        document.getElementById('modal-completion').value = c.completed ? 'complete' : 'incomplete';
        document.getElementById('modal-description').value = c.description;
        document.getElementById('modal-start-date').value = c.startDate || '';
        document.getElementById('modal-due-datetime').value = c.dueDate || '';
        const coverDiv = document.getElementById('modal-cover');

        if (c.coverImage) {
            coverDiv.style.backgroundImage =
                `url(${c.coverImage})`;
            coverDiv.style.backgroundSize = 'cover';
            coverDiv.style.backgroundPosition = 'center';
            coverDiv.style.backgroundColor = 'transparent';
            coverDiv.classList.add('visible');
        } else if (c.coverColor) {
            coverDiv.style.backgroundImage = '';
            coverDiv.style.backgroundColor = c.coverColor;
            coverDiv.classList.add('visible');
        } else {
            coverDiv.style.backgroundImage = '';
            coverDiv.style.backgroundColor = 'transparent';
            coverDiv.classList.remove('visible');
        }
        document.getElementById('watch-dropdown-item').textContent = c.watched ? '👀 Unwatch' : '👀 Watch';
        document.getElementById('archive-dropdown-item').textContent = c.archived ? '📤 Unarchive' : '📦 Archive';
        updateWatchIndicator();
        renderModalLabelsDisplay();
        renderModalDatesDisplay();
        renderModalMembersDisplay();
        renderModalChecklists();
        renderModalAttachments();
        renderModalCommentsActivity();
        updateCommentUserSelect();
        closeAllPopovers();
        document.getElementById('card-modal-overlay').classList.remove('hidden');
    }

    function closeCardModal() {
        if (currentCardId) {
            const c = getActiveBoard().cards[currentCardId];
            c.title = document.getElementById('modal-card-title').value.trim() || 'Untitled';
            c.description = document.getElementById('modal-description').value;
            c.completed = document.getElementById('modal-completion').value === 'complete';
            saveData();
            renderBoard();
        }
        currentCardId = null;
        editingCommentIndex = null;
        closeAllPopovers();
        document.getElementById('card-modal-overlay').classList.add('hidden');
    }

    function renderModalLabelsDisplay() {
        const container = document.getElementById('modal-labels-display');
        const
            card = getActiveBoard().cards[currentCardId];
        container.innerHTML = '';

        card.labels.forEach(lid => {

            const l = getLabelById(lid);
            if (l) {
                const span = document.createElement(
                    'span');
                span.className = 'label-tag';
                span.style.backgroundColor = l.color;
                span.textContent = l.name;
                span.title = 'Click to remove';
                span.addEventListener('click', async () => {
                    const result = await saveData("delete", "CardLabel", {}, lid);
                    if (result) {
                        card.labels = card.labels.filter(id => id !== lid);
                        addActivity(card, `removed label "${l.name}"`, CURRENT_USER_ID);
                        renderModalLabelsDisplay();
                        renderBoard();

                    }
                });
                container.appendChild(span);
            }
        });
        const addBtn = document.createElement('button');
        addBtn.className = 'add-label-inline';
        addBtn.textContent = '+';
        addBtn.title = 'Add label';
        addBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeAllPopovers();
            openLabelsPopover(e.target);
        });
        container.appendChild(addBtn);
    }

    function renderModalDatesDisplay() {
        const container = document.getElementById('modal-dates-display');
        const
            card = getActiveBoard().cards[currentCardId];
        container.innerHTML = '';
        if (card.startDate) {
            const badge = document.createElement('span');
            badge.className = 'date-badge';
            badge.textContent = 'Start: ' + new Date(card.startDate).toLocaleDateString();
            badge.addEventListener('click', (e) => {
                closeAllPopovers();
                openDatesPopover(e.target);
            });
            container.appendChild(badge);
        }
        if (card.dueDate) {
            const badge = document.createElement('span');
            const overdue = isOverdue(card.dueDate);
            badge.className = 'date-badge' + (overdue ? ' overdue' : '') + (card.completed ? ' complete-date' : '');
            badge.textContent = 'Due: ' + new Date(card.dueDate).toLocaleString();
            badge.addEventListener('click', (e) => {
                closeAllPopovers();
                openDatesPopover(e.target);
            });
            container.appendChild(badge);
        }
        if (!card.startDate && !card.dueDate) {
            const addBtn = document
                .createElement('button');
            addBtn.className = 'btn-secondary small';
            addBtn.textContent = '+ Add dates';
            addBtn.addEventListener('click', (e) => {
                closeAllPopovers();
                openDatesPopover(e.target);
            });
            container.appendChild(addBtn);
        }
    }

    function renderModalMembersDisplay() {
        const container = document.getElementById('modal-members-display');
        const card = getActiveBoard().cards[currentCardId];
        container.innerHTML = '';
        card.assignedUsers.forEach(member => {
            const u = getUserById(member.user);
            if (u) {
                const avatar = document.createElement(
                    'span');
                avatar.className = 'member-avatar';
                avatar.style.backgroundColor = u.color;
                avatar.textContent = u.name[0];
                avatar.title = u.name + ' (click to remove)';
                avatar.addEventListener('click', async () => {
                    card.assignedUsers = card.assignedUsers.filter(m => m.user !== member.user);

                    const result = await saveData("delete", "CardMember", {}, member.id);
                    if (result) {

                        addActivity(card, `removed user ${u.name}`, CURRENT_USER_ID);
                        renderModalMembersDisplay();
                        renderBoard();
                    }
                });
                container.appendChild(avatar);
            }
        });
        const addBtn = document.createElement('button');
        addBtn.className = 'add-member-inline';
        addBtn.textContent = '+';
        addBtn.title = 'Add member';
        addBtn.addEventListener('click', (e) => {
            closeAllPopovers();
            openMembersPopover(e.target);
        });
        container.appendChild(addBtn);
    }

    function renderModalChecklists() {
        const container = document.getElementById('modal-checklists');
        const card =
            getActiveBoard().cards[currentCardId];
        container.innerHTML = '';
        if (!card.checklists || card.checklists.length === 0) {
            container.innerHTML =
                '<p style="color:var(--text-secondary);font-size:0.85rem;">No checklists yet.</p>';
            return;
        }

        card.checklists.forEach((checklist, Index) => {

            const clIndex = checklist.id
            const progress = getSingleChecklistProgress(
                checklist);
            const block = document.createElement('div');
            block.className = 'checklist-block';
            block.dataset.clIndex = clIndex;
            block.innerHTML = `<div class="checklist-block-header"><input type="text" class="checklist-block-title-input" value="${escapeHtml(checklist.name)}" data-clindex="${clIndex}" placeholder="Checklist name" /><span class="progress-text">${progress}%</span><button class="icon-btn small delete-checklist-block-btn" data-clindex="${clIndex}" title="Delete checklist">🗑</button></div><div class="checklist-progress-bar"><div class="checklist-progress-fill" style="width:${progress}%"></div></div><div class="checklist-items-container" data-clindex="${clIndex}"></div><div class="inline-add-item-area" data-clindex="${clIndex}"><button class="btn-secondary small show-add-item-form-btn" data-clindex="${clIndex}">+ Add item</button><div class="inline-add-item-form hidden" data-clindex="${clIndex}"><input type="text" class="inline-item-input" placeholder="Item text..." data-clindex="${clIndex}" /><button class="btn-primary small save-inline-item-btn" data-clindex="${clIndex}">Add</button><button class="btn-secondary small cancel-inline-item-btn" data-clindex="${clIndex}">✕</button></div></div>`;
            const itemsContainer = block.querySelector('.checklist-items-container');
            checklist.items.forEach((item, index) => {
                const i = item.id
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checklist-item';
                itemDiv.innerHTML =
                    `<input type="checkbox" ${item.completed?'checked':''} data-clindex="${clIndex}" data-itemindex="${i}"><input type="text" class="checklist-item-text ${item.completed?'completed':''}" value="${escapeHtml(item.text)}" data-clindex="${clIndex}" data-itemindex="${i}" /><button class="icon-btn small delete-checklist-item" data-clindex="${clIndex}" data-itemindex="${i}">🗑</button>`;
                itemsContainer.appendChild(itemDiv);
                itemDiv.querySelector('input[type="checkbox"]').addEventListener('change', async function() {
                    checklist.items[index].completed = this.checked;
                    const body = {
                        "is_completed": this.checked
                    }
                    const result = await saveData("update", "ChecklistItem", body, i);
                    if (result) {

                        addActivity(card,
                            `${checklist.items[index].completed?'completed':'uncompleted'} "${checklist.items[index].text}" in "${checklist.name}"`,
                            CURRENT_USER_ID);
                        renderModalChecklists();
                        renderBoard();
                    }
                });
                itemDiv.querySelector('.checklist-item-text').addEventListener('input', async function() {
                    const name = this.value.trim()
                    const body = {
                        "name": name,
                        "checklist": checklist.id
                    }
                    const result = await saveData("update", "ChecklistItem", body, i);
                    if (result) {

                        checklist.items[index].text = result.name;
                    }
                });
                itemDiv.querySelector('.delete-checklist-item').addEventListener('click', async () => {
                    const deletedText = checklist.items[index].text;
                    const result = await saveData("delete", "ChecklistItem", {}, i);

                    if (result) {
                        checklist.items.splice(index, 1);
                        addActivity(card,
                            `deleted checklist item "${deletedText}" from "${checklist.name}"`,
                            CURRENT_USER_ID);
                        renderModalChecklists();
                        renderBoard();

                    }
                });
            });
            block.querySelector('.checklist-block-title-input').addEventListener('input', function() {
                const name = this.value.trim() || 'Checklist';
                checklist.name = name;
                const body = {
                    "name": name
                }
                saveData("update", "Checklist", body, clIndex);
                renderBoard();
            });
            block.querySelector('.delete-checklist-block-btn').addEventListener('click', async () => {
                if (confirm(
                        `Delete entire checklist "${checklist.name}"?`)) {
                    card.checklists.splice(Index,
                        1);

                    await saveData("delete", "Checklist", {}, clIndex);
                    addActivity(card, `deleted checklist "${checklist.name}"`, CURRENT_USER_ID);
                    renderModalChecklists();
                    renderBoard();
                }
            });
            const showBtn = block.querySelector('.show-add-item-form-btn');
            const inlineForm = block.querySelector('.inline-add-item-form');
            const inlineInput = block
                .querySelector('.inline-item-input');
            const saveBtn = block.querySelector(
                '.save-inline-item-btn');
            const cancelBtn = block.querySelector(
                '.cancel-inline-item-btn');
            showBtn.addEventListener('click', () => {
                showBtn.classList.add('hidden');
                inlineForm.classList.remove('hidden');
                inlineInput.focus();
            });
            cancelBtn.addEventListener('click', () => {
                inlineForm.classList.add('hidden');
                showBtn.classList.remove('hidden');
                inlineInput.value = '';
            });
            const addItemFn = async () => {
                const txt = inlineInput.value
                    .trim();
                if (txt) {
                    const body = {
                        "name": txt,
                        "checklist": checklist.id
                    }
                    const result = await saveData("create", "ChecklistItem", body, checklist.id);
                    if (result) {
                        checklist.items.push({
                            id: result.id,
                            text: result.name,
                            completed: false
                        });
                        addActivity(card, `added checklist item "${txt}" to "${checklist.name}"`,
                            CURRENT_USER_ID);

                        renderModalChecklists();
                        renderBoard();
                    }

                }
                inlineForm.classList.add('hidden');
                showBtn.classList.remove('hidden');
                inlineInput.value = '';
            };
            saveBtn.addEventListener('click', addItemFn);
            inlineInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e
                        .preventDefault();
                    addItemFn();
                }
                if (e.key === 'Escape') {
                    inlineForm.classList.add('hidden');
                    showBtn.classList.remove('hidden');
                    inlineInput.value = '';
                }
            });
            container.appendChild(block);
        });
    }

    function extractMainText(text) {
        // ^ means start of string
        return text.replace(/^\[.*?\]\s*/, '');
    }

    function renderModalAttachments() {
        const container = document.getElementById('modal-attachments');
        const card =
            getActiveBoard().cards[currentCardId];
        container.innerHTML = '';
        if (card.attachments.length === 0) {
            container.innerHTML =
                '<p style="color:var(--text-secondary);font-size:0.85rem;">No attachments yet.</p>';
            return;
        }
        card.attachments.forEach((att, index) => {
            const div = document.createElement('div');
            div.className = 'attachment-card';

            const i = att.id
            div.setAttribute("data-attid", att.id)
            div.setAttribute("data-type", att.type)

            const isImage = att.type && att.type.startsWith('image/');
            const
                thumbContent = isImage ? `<img src="${att.data}" alt="${escapeHtml(att.name)}" />` : (att.type ===
                    'link' ? '🔗' : '📄');
            const uploader = getUserById(att.uploadedBy);
            const time = att
                .uploadedAt ? new Date(att.uploadedAt).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                }) : '';
            div.innerHTML =
                `<div class="attachment-thumb">${thumbContent}</div><div class="attachment-info"><div class="attachment-name">${escapeHtml(att.name)}</div><div class="attachment-meta">${uploader?uploader.name:'Unknown'} · ${time}</div></div><div class="attachment-actions"><button class="attachment-dot-btn" data-attindex="${i}">⋯</button><div class="dropdown-menu right-align hidden attachment-dropdown" style="position:absolute;right:0;top:100%;min-width:160px;"><div class="dropdown-item att-download" data-attindex="${i}">Download</div><div class="dropdown-item att-comment" data-attindex="${i}">💬 Comment</div>${isImage?`<div class="dropdown-item att-set-cover" data-attindex="${i}">🖼️ Set as Cover</div>`:''}<div class="dropdown-item att-remove-cover" data-attindex="${i}" style="${card.coverImage===att.data?'':'display:none;'}">❌ Remove Cover</div><div class="dropdown-divider"></div><div class="dropdown-item danger att-remove" data-attindex="${i}">🗑 Remove</div></div></div>`;
            container.appendChild(div);
            const dotBtn = div.querySelector('.attachment-dot-btn');
            const dropdown =
                div.querySelector('.attachment-dropdown');
            dotBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                document.querySelectorAll('.attachment-dropdown').forEach(d => d.classList.add('hidden'));
                dropdown.classList.toggle('hidden');
            });
            div.querySelector('.att-edit')?.addEventListener('click', async (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                const newName = prompt('Edit attachment name:', att.name);
                if (newName?.trim()) {
                    const fileId = div.dataset.attid
                    const type = div.dataset.type
                    const [imageType, fileType] = checkAttachmentClass(type)

                    let result;
                    const body = {
                        "name": newName.trim()
                    }
                    if (imageType) {
                        result = await saveData("update", "CardImage", body, fileId);

                    } else if (fileType) {
                        result = await saveData("update", "CardFile", body, fileId);

                    }
                    console.log(result)
                    if (result) {
                        att.name = result.display_name;
                        renderModalAttachments();
                    }

                }
            });
            div.querySelector('.att-download')?.addEventListener('click', (e) => {
                e.stopPropagation();
                const link = document.createElement('a');
                link.href = att.data;
                link.download = att.name; // Optional: custom filename
                link.click();
            });
            div.querySelector('.att-comment')?.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                const linkText = att.type === 'link' ? att.data : att.name;

                const newCommentText = document.getElementById('new-comment-text')
                newCommentText.value = `[${att.name}]`
                newCommentText.setAttribute("data-reply-type", att.type)
                newCommentText.setAttribute("data-reply-id", att.id)

                // document.getElementById('new-comment-text').value = `[${att.name}](${linkText})`;
                document.getElementById('new-comment-text').focus();
                document.getElementById('comment-sidebar').scrollIntoView({
                    behavior: 'smooth'
                });
            });
            div.querySelector('.att-set-cover')?.addEventListener('click', async (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                console.log(att)
                body = {
                    "cover_image_fk": att.id,
                    "cover_color": "",
                    "cover_image": null
                }
                const result = await saveData("update", "Card", body, currentCardId);
                if (result) {
                    card.coverImage = att.cover_img;
                    card.coverColor = '';
                    addActivity(card, `set cover from attachment "${att.name}"`, CURRENT_USER_ID);

                    openCardModal(currentCardId);

                }


            });
            div.querySelector('.att-remove-cover')?.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                if (card.coverImage === att.data) {
                    card.coverImage =
                        '';
                    addActivity(card, 'removed cover', CURRENT_USER_ID);
                    saveData();
                    openCardModal(currentCardId);
                }
            });
            div.querySelector('.att-remove')?.addEventListener('click', async (e) => {
                e.stopPropagation();
                dropdown.classList.add('hidden');
                if (confirm('Remove this attachment?')) {
                    const fileId = div.dataset.attid
                    const type = div.dataset.type
                    const [imageType, fileType] = checkAttachmentClass(type)
                    let result;
                    if (imageType) {
                        result = await saveData("delete", "CardImage", {}, fileId);

                    } else if (fileType) {
                        result = await saveData("delete", "CardFile", {}, fileId);

                    }
                    if (result) {
                        const deleted = card.attachments[index];
                        card.attachments.splice(index, 1);
                        addActivity(card, `removed attachment "${deleted.name}"`, CURRENT_USER_ID);
                        renderModalAttachments();
                        renderModalCommentsActivity();

                    }
                }
            });
        });

    }

    function renderModalCommentsActivity() {
        const container = document.getElementById(
            'modal-comments-activity');
        const card = getActiveBoard().cards[currentCardId];
        container.innerHTML = '';
        const allItems = [];

        card.comments.forEach((c, i) => {

            allItems.push({
                type: 'comment',
                data: c,
                index: i,
                timestamp: c.timestamp
            });

        });

        card.activities.forEach(a => {
            allItems.push({
                type: 'activity',
                data: a,
                timestamp: a
                    .timestamp
            });
        });
        allItems.sort((a, b) => b.timestamp - a.timestamp);
        allItems.forEach(item => {
            if (item.type === 'comment') {
                const c = item.data;
                const u = getUserById(c.userId);
                const div = document.createElement('div');
                div.className = 'comment-item';

                const canEdit = c.userId === CURRENT_USER_ID;

                div.innerHTML = `<div class="comment-avatar" style="background:${u?.color||'#ccc'}">${u?.name?.[0]||'?'}</div><div class="comment-body"><div class="comment-header"><span class="comment-author">${u?.name||'Unknown'}</span><span class="comment-time">${new Date(c.timestamp*1000).toLocaleString()}${c.edited?' <span class="comment-edited">(edited)</span>':''}</span></div><div class="comment-content">${linkify(c)}</div>${canEdit?`<div class="comment-actions"><button class="edit-comment-btn" data-commentindex="${item.index}">✏️ Edit</button><button class="delete-comment-btn" data-commentindex="${c.id}">🗑 Delete</button></div>`:''}</div>`;
                div.querySelector("a")?.addEventListener("click", () => {
                    event.preventDefault()
                    const attId = event.target.dataset.replyId
                    const type = event.target.dataset.replyType


                    const element = document.querySelector(`[data-attid="${attId}"][data-type="${type}"]`);

                    if (element) {
                        element.scrollIntoView({
                            behavior: 'smooth',
                            block: 'center'
                        });

                        // Store original styles
                        const originalBg = element.style.backgroundColor;
                        const originalBorder = element.style.border;

                        // Apply beautiful highlight
                        element.style.transition = 'all 0.3s ease';
                        element.style.backgroundColor = '#fff3cd'; // Soft yellow
                        element.style.border = '1px solid #ffc107'; // Gold border
                        element.style.boxShadow = '0 0 5px rgba(0,0,0,0.1)';

                        setTimeout(() => {
                            element.style.backgroundColor = originalBg;
                            element.style.border = originalBorder;
                            element.style.boxShadow = '';
                        }, 5000);
                    }
                })
                container.appendChild(div);
                div.querySelector('.edit-comment-btn')?.addEventListener('click', () => {

                    editingCommentIndex = item.index;
                    document.getElementById('new-comment-text').value = c.text;
                    document.getElementById('new-comment-text').focus();
                    document.getElementById('add-comment-btn').textContent = 'Save Changes';
                    const discardBtn = document.createElement('button');
                    discardBtn.className = 'btn-secondary small';
                    discardBtn.textContent = 'Discard';
                    discardBtn.id = 'discard-edit-btn';
                    const actionsDiv = document.querySelector('.comment-input-actions');
                    const existingDiscard = document.getElementById('discard-edit-btn');
                    if (existingDiscard) existingDiscard.remove();
                    actionsDiv.appendChild(discardBtn);
                    discardBtn.addEventListener('click', cancelEditComment);
                    document.getElementById('comment-sidebar').scrollIntoView({
                        behavior: 'smooth'
                    });
                });
                div.querySelector('.delete-comment-btn')?.addEventListener('click', async () => {
                    if (confirm(
                            'Delete this comment?')) {
                        const commentId = div.querySelector('.delete-comment-btn').dataset.commentindex
                        const result = await saveData("delete", "Comment", {}, commentId);
                        if (result) {
                            card.comments.splice(item.index, 1);
                            addActivity(card, 'deleted a comment', CURRENT_USER_ID);
                            renderModalCommentsActivity();

                        }
                    }
                });
            } else {
                const a = item.data;
                const u =
                    getUserById(a.user);
                const div = document.createElement('div');
                div.className = 'activity-item-inline';
                div.innerHTML =
                    `<span class="activity-dot"></span><span>${escapeHtml(a.text)} ${u?`by <strong>${escapeHtml(u.name)}</strong>`:''} · ${new Date(a.timestamp).toLocaleString()}</span>`;
                container.appendChild(div);
            }
        });
        if (allItems.length === 0) {
            container.innerHTML =
                '<p style="color:var(--text-secondary);font-size:0.8rem;">No activity yet.</p>';
        }
    }

    function cancelEditComment() {
        editingCommentIndex = null;
        document.getElementById('new-comment-text').value = '';
        document.getElementById('add-comment-btn').textContent = 'Post Comment';
        const discardBtn = document
            .getElementById('discard-edit-btn');
        if (discardBtn) discardBtn.remove();
    }

    function updateCommentUserSelect() {
        const sel = document.getElementById('comment-user-select');
        sel.innerHTML = '<option value="">Post as...</option>';
        appState.users.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u.id;
            opt.textContent = u.name;
            sel.appendChild(opt);
        });
        sel.value = CURRENT_USER_ID;
    }

    function openCoverPopover(anchorEl) {
        closeAllPopovers();
        const popover = document.getElementById(
            'cover-popover');
        const colorGrid = document.getElementById('cover-color-grid');
        const coverColors = [
            '#0079bf', '#d29034', '#519839', '#b04632', '#89609e', '#cd5a91', '#4bbf6b', '#00aECC', '#838c91',
            '#172b4d', '#c377e0', '#ff7452', '#00c2e0', '#6d7a85', '#5aac44', '#ff9f1a'
        ];
        colorGrid.innerHTML = '';
        coverColors.forEach(color => {
            const swatch = document.createElement('div');
            swatch.className = 'cover-color-swatch';
            swatch.style.backgroundColor = color;
            swatch.addEventListener('click', async () => {
                const card = getActiveBoard().cards[currentCardId];
                card.coverColor = color;
                card.coverImage = '';
                addActivity(card, 'changed cover color', CURRENT_USER_ID);
                const body = {
                    "cover_color": color,
                    "cover_image": null,
                    "cover_image_fk": null
                }
                const result = await saveData("update", "Card", body, currentCardId);
                if (result) {
                    openCardModal(currentCardId);
                    popover.classList.add('hidden');

                }
            });
            colorGrid.appendChild(swatch);
        });
        document.getElementById('cover-custom-color').oninput = function() {
            const card = getActiveBoard()
                .cards[currentCardId];
            card.coverColor = this.value;
            card.coverImage = '';
            addActivity(card, 'changed cover color', CURRENT_USER_ID);
            saveData();
            openCardModal(currentCardId);
        };
        document.getElementById('cover-upload-area').onclick = () => document.getElementById('cover-image-input')
            .click();
        document.getElementById('cover-image-input').onchange = async function(e) {
            const file = e.target.files[0];
            if (file) {
                const formData = new FormData()
                formData.append("cover_image", file)
                formData.append("cover_color", "")


                const result = await saveData("update", "Card", formData, currentCardId, true);
                console.log(result)
                if (result) {

                    const card = getActiveBoard().cards[currentCardId];
                    card.coverImage = result.cover_img;
                    card.coverColor = '';
                    addActivity(card, 'uploaded cover image', CURRENT_USER_ID);

                    openCardModal(currentCardId);
                    popover.classList.add('hidden');
                }

            }
            this.value = '';
        };
        document.getElementById('remove-cover-btn-popover').onclick = () => {
            const card = getActiveBoard()
                .cards[currentCardId];
            card.coverColor = '';
            card.coverImage = '';
            addActivity(card, 'removed cover', CURRENT_USER_ID);
            saveData();
            openCardModal(currentCardId);
            popover.classList.add('hidden');
        };
        popover.classList.remove('hidden');
        positionPopover(popover, anchorEl, -100, 8);
    }

    function openLabelsPopover(anchorEl) {
        closeAllPopovers();
        const popover = document.getElementById(
            'labels-popover');
        const card = getActiveBoard().cards[currentCardId];
        const searchInput = document
            .getElementById('labels-search-input');
        const optionsList = document.getElementById(
            'labels-options-list');
        searchInput.value = '';

        function renderLabelOptions(filter = '') {
            optionsList.innerHTML = '';
            const filtered = appState.labels.filter(l => l.name.toLowerCase().includes(filter.toLowerCase()));
            filtered.forEach(l => {
                const div = document.createElement('div');
                div.className = 'label-option';
                const isSelected = card.labels.includes(l.id);
                div.innerHTML =
                    `<span class="label-color-dot" style="background:${l.color};"></span><span class="label-option-name">${escapeHtml(l.name)}</span>${isSelected?'<span class="label-option-check">✓</span>':''}`;
                div.addEventListener('click', async (event) => {
                    const result = await saveData("delete", "CardLabel", {}, l.id);
                    if (result) {
                        addActivity(card, `removed label "${l.name}"`, CURRENT_USER_ID);

                        card.labels = card.labels.filter(id => id !== l.id);
                        console.log("appState.labels", appState.labels, l.id)
                        appState.labels = appState.labels.filter(label => label.id !== l.id)

                        renderModalLabelsDisplay();
                        renderBoard();
                        renderLabelOptions(searchInput.value);

                    }

                });
                optionsList.appendChild(div);
            });
            if (filtered.length === 0 && filter) {
                optionsList
                    .innerHTML =
                    '<p style="color:var(--text-secondary);padding:8px;">No labels found.</p>';
            }
        }
        renderLabelOptions();
        searchInput.addEventListener('input', () => renderLabelOptions(searchInput.value));
        document.getElementById('new-label-name-popover').value = '';
        document.getElementById('create-label-popover-btn').onclick = async () => {
            const name = document.getElementById('new-label-name-popover').value.trim();
            const color = document.getElementById('new-label-color-popover').value;
            if (name) {
                const body = {
                    name: name,
                    color: color,
                    card: currentCardId
                }
                const result = await saveData("create", "CardLabel", body, currentCardId);
                if (result) {

                    const newLabel = {
                        id: result.id,
                        name: result.name,
                        color: result.color
                    };
                    appState.labels.push(newLabel);
                    card.labels.push(newLabel.id);
                    addActivity(card, `created and added label "${name}"`, CURRENT_USER_ID);
                    renderModalLabelsDisplay();
                    renderBoard();
                    updateFilterDropdowns();
                    renderLabelOptions(searchInput.value);
                }
                document.getElementById('new-label-name-popover').value = '';
            }
        };
        popover.classList.remove('hidden');
        positionPopover(popover, anchorEl, -50, 8);
    }

    function updateFilterDropdowns() {}

    function openDatesPopover(anchorEl) {
        closeAllPopovers();
        const popover = document.getElementById(
            'dates-popover');
        const card = getActiveBoard().cards[currentCardId];
        document.getElementById('modal-start-date').value = card.startDate || '';
        document.getElementById('modal-due-datetime').value = card.dueDate || '';
        document.getElementById('save-dates-btn').onclick = () => {
            const startDateVal = document.getElementById('modal-start-date').value;
            card.startDate = startDateVal
            const dueDateVal = document.getElementById('modal-due-datetime').value;
            card.dueDate = document.getElementById('modal-due-datetime').value;
            addActivity(card, `set dates: ${card.startDate||'none'} → ${card.dueDate||'none'}`, CURRENT_USER_ID);
            const body = {
                "start_date": startDateVal,
                "due_date": dueDateVal
            }
            saveData("update", "Card", body, card.id);
            renderModalDatesDisplay();
            renderBoard();
            popover.classList.add('hidden');
        };
        document.getElementById('clear-dates-btn').onclick = () => {
            card.startDate = '';
            card.dueDate = '';
            document.getElementById('modal-start-date').value = '';
            document.getElementById('modal-due-datetime').value = '';
            addActivity(card, 'cleared dates', CURRENT_USER_ID);
            saveData();
            renderModalDatesDisplay();
            renderBoard();
            popover.classList.add('hidden');
        };
        popover.classList.remove('hidden');
        positionPopover(popover, anchorEl, -40, 8);
    }

    function openMembersPopover(anchorEl) {
        closeAllPopovers();
        const popover = document.getElementById(
            'members-popover');
        const card = getActiveBoard().cards[currentCardId];
        const searchInput = document
            .getElementById('members-search-input');
        const optionsList = document.getElementById(
            'members-options-list');
        searchInput.value = '';

        function renderMemberOptions(filter = '') {
            optionsList.innerHTML = '';
            console.log(appState)
            const filtered = appState.users
                .filter(u => u.name.toLowerCase().includes(filter.toLowerCase()) && appState.boards[0].boardMembers.includes(u.id));
            filtered.forEach(u => {
                const div = document.createElement('div');
                div.className = 'member-option';

                const assignedMember = card.assignedUsers.find(member => member.user == u.id);
                if (assignedMember) div.setAttribute("data-member-id", assignedMember.id)

                div.innerHTML =
                    `<span class="member-option-avatar" style="background:${u.color};">${u.name[0]}</span><span>${escapeHtml(u.name)}</span>${assignedMember?' <span style="color:var(--success-color);">✓</span>':''}`;
                div.addEventListener('click', async () => {
                    let result;
                    if (assignedMember) {
                        result = await saveData("delete", "CardMember", {}, assignedMember.id)
                        if (result) {
                            card.assignedUsers = card.assignedUsers.filter(member => member.user !== u.id);
                            addActivity(card, `removed user ${u.name}`, CURRENT_USER_ID);

                        }
                    } else {
                        const body = {
                            "card": card.id,
                            "user": u.id
                        }
                        result = await saveData("create", "CardMember", body)
                        if (result) {
                            card.assignedUsers.push(result);
                            addActivity(card, `added user ${u.name}`, CURRENT_USER_ID);

                        }

                    }
                    console.log("result", result)
                    if (result) {

                        renderModalMembersDisplay();
                        renderBoard();
                        renderMemberOptions(searchInput.value);
                    }
                });
                optionsList.appendChild(div);
            });
        }
        renderMemberOptions();
        searchInput.addEventListener('input', () => renderMemberOptions(searchInput.value));
        popover.classList.remove('hidden');
        positionPopover(popover, anchorEl, -40, 8);
    }

    function openAttachPopover(anchorEl) {
        closeAllPopovers();
        const popover = document.getElementById('attach-popover');
        document.getElementById('attachment-file-input').value = '';
        document.getElementById('link-attachment-input-popover').value = '';
        document.getElementById('attachment-file-input').onchange = function(e) {
            const files = e.target.files;
            const card = getActiveBoard().cards[currentCardId];
            Array.from(files).forEach(async (f) => {
                console.log(f.name)
                console.log(f.type)

                const formData = new FormData()
                formData.append("file", f)
                formData.append("card", currentCardId)
                const [imageType, fileType] = checkAttachmentClass(f.type)

                let result;
                console.log(imageType, fileType, f.type)
                if (imageType) {
                    result = await saveData("create", "CardImage", formData, currentCardId, true);
                } else if (fileType) {
                    result = await saveData("create", "CardFile", formData, currentCardId, true);

                }
                console.log(result)
                if (result) {
                    card.attachments.push({
                        id: result.id,
                        name: result.name,
                        type: result.file_type,
                        data: result.file,
                        uploadedAt: result.upload_at,
                        uploadedBy: CURRENT_USER_ID
                    });
                    addActivity(card, `attached file "${f.name}"`, CURRENT_USER_ID);
                    saveData();
                    renderModalAttachments();
                    renderModalCommentsActivity();
                }

            });
            this.value = '';
            popover.classList.add('hidden');
        };
        document.getElementById('add-link-attachment-btn-popover').onclick = () => {
            const url = document
                .getElementById('link-attachment-input-popover').value.trim();
            if (url) {
                const card =
                    getActiveBoard().cards[currentCardId];
                card.attachments.push({
                    name: url,
                    type: 'link',
                    data: url,
                    uploadedAt: Date.now(),
                    uploadedBy: CURRENT_USER_ID
                });
                addActivity(card, `attached link: ${url}`, CURRENT_USER_ID);
                saveData();
                renderModalAttachments();
                renderModalCommentsActivity();
                document.getElementById('link-attachment-input-popover').value = '';
                popover.classList.add('hidden');
            }
        };
        popover.classList.remove('hidden');
        positionPopover(popover, anchorEl, -60, 8);
    }

    function openBackgroundModal() {
        const modal = document.getElementById('bg-modal-overlay-new');
        modal.classList.remove('hidden');
        renderBackgroundModalContent();
    }

    function renderBackgroundModalContent() {
        const photosGrid = document.getElementById('bg-photos-grid-modal');
        const photoUrls = [
            'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=200&fit=crop',
            'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=300&h=200&fit=crop',
            'https://images.unsplash.com/photo-1501785888041-af3ef285b470?w=300&h=200&fit=crop',
            'https://images.unsplash.com/photo-1519681393784-d120267933ba?w=300&h=200&fit=crop'
        ];
        photosGrid.innerHTML = photoUrls.map(url =>
            `<div class="bg-photo-thumb" style="background-image:url(${url})" data-bg-image="${url}"></div>`
        ).join('');

        photosGrid.querySelectorAll('.bg-photo-thumb').forEach(thumb => {
            thumb.addEventListener('click', () => {
                const board = getActiveBoard();
                board.background = `url(${thumb.dataset.bgImage}) center/cover no-repeat`;
                document.body.style.background = board.background;
                document.body.style.backgroundSize = 'cover';
                saveData();
            });
        });

        const colorsGrid = document.getElementById('bg-colors-grid-modal');
        const bgColors = ['#f0f2f5', '#e4f0f6', '#fce4ec', '#1a1a2e', '#2d3e50', '#6c5ce7', '#00b894', '#e17055'];
        colorsGrid.innerHTML = bgColors.map(c =>
            `<div class="bg-color-dot" style="background:${c}" data-bg-color="${c}"></div>`
        ).join('');

        colorsGrid.querySelectorAll('.bg-color-dot').forEach(dot => {
            dot.addEventListener('click', () => {
                const board = getActiveBoard();
                board.background = dot.dataset.bgColor;
                document.body.style.background = board.background;
                document.body.style.backgroundSize = '';
                saveData();
            });
        });

        document.getElementById('board-bg-custom-color-modal').oninput = function() {
            const board = getActiveBoard();
            board.background = this.value;
            document.body.style.background = this.value;
            document.body.style.backgroundSize = '';
            saveData();
        };
    }

    function openActivityModal() {
        const modal = document.getElementById('activity-modal-overlay');
        modal.classList.remove('hidden');
        renderActivityModalContent(currentActivityFilter);
    }

    function renderActivityModalContent(filter = 'all') {
        const board = getActiveBoard();
        const allActivities = [];

        Object.values(board.cards).forEach(card => {
            if (filter === 'comments') {
                card.comments.forEach(c => {
                    allActivities.push({
                        type: 'comment',
                        cardId: card.id,
                        cardTitle: card.title,
                        text: c.text,
                        timestamp: c.timestamp,
                        user: c.userId
                    });
                });
            } else {
                card.activities.forEach(act => {
                    allActivities.push({
                        type: 'activity',
                        cardId: card.id,
                        cardTitle: card.title,
                        ...act
                    });
                });
                card.comments.forEach(c => {
                    allActivities.push({
                        type: 'comment',
                        cardId: card.id,
                        cardTitle: card.title,
                        text: 'Commented: ' + c.text,
                        timestamp: c.timestamp,
                        user: c.userId
                    });
                });
            }
        });

        allActivities.sort((a, b) => b.timestamp - a.timestamp);

        const container = document.getElementById('board-activity-list-modal');
        container.innerHTML = '';

        if (allActivities.length === 0) {
            container.innerHTML = '<p style="color:var(--text-secondary);padding:8px;">No activity yet.</p>';
            return;
        }

        allActivities.slice(0, 50).forEach(act => {
            const user = getUserById(act.user);
            const time = new Date(act.timestamp).toLocaleString();
            const div = document.createElement('div');
            div.className = 'activity-item-inline';
            div.style.padding = '6px 0';
            div.innerHTML = `
                        <span class="activity-dot"></span>
                        <span><strong>${escapeHtml(act.cardTitle)}</strong> – ${escapeHtml(act.text)} ${user ? `by ${user.name}` : ''} · ${time}</span>
                    `;
            container.appendChild(div);
        });
    }

    function closeBackgroundModal() {
        document.getElementById('bg-modal-overlay-new').classList.add('hidden');
    }

    function closeActivityModal() {
        document.getElementById('activity-modal-overlay').classList.add('hidden');
    }

    function closeBoardMenuDropdown() {
        document.getElementById('board-menu-dropdown').classList.add('hidden');
    }

    function openShareModal() {
        document.getElementById('share-modal-overlay').classList.remove('hidden');
        renderShareModalContent();
    }

    function closeShareModal() {
        document.getElementById('share-modal-overlay').classList.add('hidden');
    }

    function renderShareModalContent() {
        console.log(appState)
        const board = getActiveBoard();
        document.getElementById('board-members-count').textContent = board.boardMembers.length;
        document.getElementById('join-requests-count').textContent = board.joinRequests.length;
        const membersContent = document.getElementById('board-members-content');
        membersContent.innerHTML = '';
        console.log("befor loop", board.boardMembers)
        board.boardMembers.forEach(uid => {
            const u = getUserById(uid);
            console.log("u", u)
            if (!u) return;
            const role = board.memberRoles[uid] || 'member';
            const row = document.createElement('div');
            row.className = 'share-member-row';
            const profileImage = u.profileImage ? `<img src="${u.profileImage}" alt="${u.name}">` : `${u.name[0]}`

            row.innerHTML = `
                    <div class="member-avatar-sm" style="background:${u.color};">${profileImage}</div>
                    <div class="member-details">
                        <div class="member-name">${escapeHtml(u.name)} ${role==='admin'?'👑':''}</div>
                        <div class="member-username">${u.username||''}</div>
                    </div>
                    <div class="member-role-badge" data-uid="${uid}">${role==='admin'?'Admin':role==='member'?'Member':role==='observer'?'Observer':'Member'} ▾</div>`;
            const roleBadge = row.querySelector('.member-role-badge');
            roleBadge.addEventListener('click', (e) => {
                e.stopPropagation();
                document.querySelectorAll('.role-dropdown').forEach(d => d.remove());
                const dropdown = document.createElement('div');
                dropdown.className = 'role-dropdown';
                dropdown.innerHTML = `
                            <div class="dropdown-item" data-role="admin">👑 Admin</div>
                            <div class="dropdown-item" data-role="member">👤 Member</div>
                            <div class="dropdown-item" data-role="observer">👁️ Observer</div>
                            <div class="dropdown-divider"></div>
                            <div class="dropdown-item danger" data-role="remove">🗑 Remove from board</div>`;
                roleBadge.appendChild(dropdown);
                dropdown.querySelectorAll('.dropdown-item').forEach(item => {
                    item.addEventListener('click', async () => {
                        const r = item.dataset.role;
                        let result;
                        const membershipId = appState["boardMembership"][uid].id
                        if (r === 'remove') {
                            board.boardMembers = board.boardMembers.filter(
                                id => id !== uid);
                            result = await saveData("delete", "BoardMember", {}, membershipId);
                            if (result) {
                                delete board.memberRoles[uid];
                                delete appState.boardMembership[uid];

                                Object.entries(getActiveBoard().cards).forEach(([key, card]) => {

                                    card.assignedUsers = card.assignedUsers.filter(member => member.user !== uid);
                                })

                                appState["users"] = appState["users"].filter(user => user.id != uid)


                            }
                        } else {
                            board.memberRoles[uid] = r;
                            const body = {
                                "member_type": r
                            }

                            result = await saveData("update", "BoardMember", body, membershipId);
                        }
                        if (result) {

                            renderShareModalContent();
                            renderBoardMenuBar();
                            dropdown.remove();

                        }
                    });
                });
            });
            membersContent.appendChild(row);
        });
        const joinContent = document.getElementById('join-requests-content');
        joinContent.innerHTML = '';
        if (board.joinRequests.length === 0) {
            joinContent.innerHTML =
                '<p style="color:var(--text-secondary);padding:8px;font-size:0.8rem;">No pending join requests.</p>';
        } else {
            board.joinRequests.forEach(uid => {
                const u = getUserById(uid);
                if (!u) return;
                const row = document.createElement('div');
                row.className = 'share-member-row';
                const profileImage = u.profileImage ? `<img src="${u.profileImage}" alt="${u.name}">` : ""

                row.innerHTML = `
                        <div class="member-avatar-sm" style="background:${u.color};">${profileImage}</div>
                        <div class="member-details"><div class="member-name">${escapeHtml(u.name)}</div><div class="member-username">${u.username||''}</div></div>
                        <button class="btn-primary small approve-join-btn" data-uid="${uid}">Approve</button>
                        <button class="btn-secondary small deny-join-btn" data-uid="${uid}">Deny</button>`;
                row.querySelector('.approve-join-btn').addEventListener('click', async () => {
                    const body = {
                        "accepted": true
                    }
                    const result = await saveData("update", "BoardMember", body, appState.boardMembership[uid].id);
                    if (result) {

                        board.boardMembers.push(uid);
                        board.memberRoles[uid] = 'member';
                        board.joinRequests = board.joinRequests.filter(id => id !== uid);
                        renderShareModalContent();
                        renderBoardMenuBar();
                    }
                });
                row.querySelector('.deny-join-btn').addEventListener('click', async () => {
                    const result = await saveData("delete", "BoardMember", {}, appState.boardMembership[uid].id);
                    if (result) {

                        board.joinRequests = board.joinRequests.filter(id => id !== uid);

                        renderShareModalContent();
                    }
                });
                joinContent.appendChild(row);
            });
        }
    }

    function openArchivedModal() {
        const modal = document.getElementById('archived-modal-overlay');
        modal.classList.remove('hidden');
        renderArchivedModal();
    }

    function renderArchivedModal() {
        const board = getActiveBoard();
        const archivedLists = board.archivedLists || [];
        const archivedListsContainer = document.getElementById('archived-lists-list');
        const archivedCardsContainer = document.getElementById('archived-cards-list');

        archivedListsContainer.innerHTML = '';
        if (archivedLists.length === 0) {
            archivedListsContainer.innerHTML = '<p style="color:var(--text-secondary);padding:8px;">No archived lists.</p>';
        } else {

            archivedLists.forEach(list => {
                const div = document.createElement('div');
                div.className = 'archived-item';
                div.innerHTML = `
                            <div class="archived-item-info">
                                <div class="archived-item-title">${escapeHtml(list.title)}</div>
                                <div class="archived-item-meta">${list.cardIds.length} cards</div>
                            </div>
                            <div class="archived-buttons">
                                <button class="btn-primary small unarchive-list-btn" data-list-id="${list.id}">↩️ Restore</button>
                                <button class="btn-danger small delete-list-permanent-btn" data-list-id="${list.id}">🗑 Delete</button>
                            </div>
                        `;
                div.querySelector('.unarchive-list-btn').addEventListener('click', async () => {
                    const body = {
                        archived: false
                    }
                    const result = await saveData("update", "BoardList", body, list.id);
                    if (result) {

                        unarchiveList(list.id, list);
                    }
                });
                div.querySelector('.delete-list-permanent-btn').addEventListener('click', async () => {
                    if (confirm(`Permanently delete list "${list.title}"? This cannot be undone.`)) {
                        const result = await saveData("delete", "BoardList", {}, list.id);
                        if (result) {

                            permanentlyDeleteList(list.id);
                        }
                    }
                });
                archivedListsContainer.appendChild(div);
            });
        }

        archivedCardsContainer.innerHTML = '';
        const archivedCards = Object.values(board.cards).filter(c => c.archived === true);
        if (archivedCards.length === 0) {
            archivedCardsContainer.innerHTML = '<p style="color:var(--text-secondary);padding:8px;">No archived cards.</p>';
        } else {
            archivedCards.forEach(card => {
                const div = document.createElement('div');
                div.className = 'archived-item';
                div.innerHTML = `
                            <div class="archived-item-info">
                                <div class="archived-item-title">${escapeHtml(card.title)}</div>
                                <div class="archived-item-meta">${card.labels.length} labels • ${card.assignedUsers.length} members</div>
                            </div>
                            <div class="archived-buttons">
                                <button class="btn-primary small unarchive-card-btn" data-card-id="${card.id}">↩️ Restore</button>
                                <button class="btn-danger small delete-card-permanent-btn" data-card-id="${card.id}">🗑 Delete</button>
                            </div>
                        `;
                div.querySelector('.unarchive-card-btn').addEventListener('click', () => {
                    unarchiveCard(card.id);
                });
                div.querySelector('.delete-card-permanent-btn').addEventListener('click', () => {
                    if (confirm(`Permanently delete card "${card.title}"? This cannot be undone.`)) {
                        permanentlyDeleteCard(card.id);
                    }
                });
                archivedCardsContainer.appendChild(div);
            });
        }
    }

    function closeArchivedModal() {
        document.getElementById('archived-modal-overlay').classList.add('hidden');
    }


    function addEventListeners() {
        // Profile avatar button



        document.getElementById('profile-logout-btn').onclick = () => {
            document.getElementById(
                'profile-dropdown').classList.add('hidden');
            alert('Logged out (demo)');
        };



        document.getElementById('add-list-btn').onclick = () => {
            document.getElementById('add-list-btn').classList.add('hidden');
            document.getElementById('add-list-form').classList.remove('hidden');
        };
        document.getElementById('cancel-list-btn').onclick = () => {
            document.getElementById('add-list-btn')
                .classList.remove('hidden');
            document.getElementById('add-list-form').classList.add('hidden');
        };
        document.getElementById('save-list-btn').onclick = async () => {
            const t = document.getElementById('new-list-title').value.trim();
            if (t) {
                const body = {
                    "name": t,
                    "board": appState.activeBoardId
                }
                const result = await saveData("create", "BoardList", body, appState.activeBoardId);
                if (result) {

                    getActiveBoard().lists.push({
                        id: result.id,
                        title: result.name,
                        cardIds: []
                    });
                    renderBoard();
                }
            }
            document.getElementById('new-list-title').value = '';
            document.getElementById('add-list-btn').classList.remove('hidden');
            document.getElementById('add-list-form').classList.add('hidden');
        };
        document.getElementById('edit-title-btn').onclick = () => {
            const el = document.getElementById(
                'board-title');
            el.contentEditable = 'true';
            el.focus();
        };
        document.getElementById('board-title').addEventListener('blur', () => {
            const el = document.getElementById(
                'board-title');
            el.contentEditable = 'false';
            getActiveBoard().title = el.innerText.trim() || 'Board';
            saveData();
            renderBoard();
        });
        document.getElementById('visibility-badge-btn').onclick = (e) => {
            e.stopPropagation();
            closeAllPopovers();
            const dd = document.getElementById('visibility-dropdown');
            dd.classList.toggle('hidden');
            if (!dd.classList.contains('hidden')) {
                const rect = document
                    .getElementById('visibility-badge-btn').getBoundingClientRect();
                dd.style.position = 'fixed';

                dd.style.left = rect.left + 'px';
            }
        };
        document.getElementById('visibility-dropdown').addEventListener('click', function(e) {
            const item = e
                .target.closest('.dropdown-item');
            if (!item) return;
            const vis = item.dataset.vis;
            if (vis) {
                getActiveBoard().boardVisibility = vis;
                saveData();
                renderBoardMenuBar();
                document.getElementById('visibility-dropdown').classList.add('hidden');
            }
        });
        document.getElementById('share-board-btn').onclick = openShareModal;
        document.getElementById('close-share-modal-btn').onclick = closeShareModal;
        document.getElementById('share-modal-overlay').addEventListener('click', e => {
            if (e.target === e
                .currentTarget) closeShareModal();
        });
        document.getElementById('share-invite-btn').onclick = async () => {
            const searchVal = document.getElementById(
                'share-search-input').value.trim().toLowerCase();
            if (searchVal) {
                const board = getActiveBoard();
                const body = {
                    "board": board.id,
                    "search": searchVal
                }
                const result = await saveData("create", "BoardMember", body);
                if (result) {
                    board.boardMembers.push(result.user.id);
                    board.memberRoles[result.user.id] = result.member_type;
                    appState["boardMembership"][result.user.id] = {
                        "id": result.id
                    }
                    appState["users"].push({
                        id: result.user.id,
                        name: result.user.fullname ? result.user.fullname : result.user.username,
                        color: "#0079bf",
                        email: result.user.email,
                        username: result.user.username,
                        profileImage: result.user.profile_image
                    })
                    renderShareModalContent();
                    renderBoardMenuBar();
                    document.getElementById('share-search-input').value = '';
                    alert(`${result.user.username} added to board!`);
                } else {
                    alert('User not found.');
                }
            }
        };
        document.getElementById('board-members-toggle').onclick = () => {
            const content = document.getElementById(
                'board-members-content');
            content.classList.toggle('hidden');
        };
        document.getElementById('join-requests-toggle').onclick = () => {
            const content = document.getElementById(
                'join-requests-content');
            content.classList.toggle('hidden');
        };

        // Board menu dots button
        document.getElementById('board-menu-dots-btn').onclick = (e) => {
            e.stopPropagation();
            closeAllPopovers();
            const dropdown = document.getElementById('board-menu-dropdown');
            dropdown.classList.toggle('hidden');
            updateBoardWatchStatus();
            if (!dropdown.classList.contains('hidden')) {
                const rect = e.target.getBoundingClientRect();
                dropdown.style.position = 'fixed';
                dropdown.style.top = rect.bottom + 4 + 'px';
                dropdown.style.right = (window.innerWidth - rect.right) + 'px';
                dropdown.style.left = 'auto';
            }
        };

        // Board menu dropdown items
        document.getElementById('board-menu-dropdown').addEventListener('click', function(e) {
            const item = e.target.closest('.board-menu-dropdown-item');
            if (!item) return;
            const action = item.dataset.action;
            if (action === 'share-users') {
                closeBoardMenuDropdown();
                openShareModal();
            } else if (action === 'change-bg') {
                closeBoardMenuDropdown();
                openBackgroundModal();
            } else if (action === 'activity') {
                closeBoardMenuDropdown();
                openActivityModal();
            } else if (action === 'watch') {
                const board = getActiveBoard();
                board.boardWatched = !board.boardWatched;
                saveData();
                updateBoardWatchStatus();
            } else if (action === 'archived-items') {
                closeBoardMenuDropdown();
                openArchivedModal();
            } else if (action === 'close-board') {
                if (confirm('Close this board? It will be archived.')) {
                    const board = getActiveBoard();
                    board.boardClosed = true;
                    saveData();
                    alert('Board closed (archived).');
                    closeBoardMenuDropdown();
                }
            }
        });

        // Archived modal close buttons
        document.getElementById('close-archived-modal').onclick = closeArchivedModal;
        document.getElementById('close-archived-modal-btn').onclick = closeArchivedModal;
        document.getElementById('archived-modal-overlay').addEventListener('click', e => {
            if (e.target === e.currentTarget) closeArchivedModal();
        });

        // Background modal close buttons
        document.getElementById('close-bg-modal-new').onclick = closeBackgroundModal;
        document.getElementById('close-bg-modal-new-btn').onclick = closeBackgroundModal;
        document.getElementById('bg-modal-overlay-new').addEventListener('click', e => {
            if (e.target === e.currentTarget) closeBackgroundModal();
        });

        // Activity modal close buttons
        document.getElementById('close-activity-modal').onclick = closeActivityModal;
        document.getElementById('close-activity-modal-btn').onclick = closeActivityModal;
        document.getElementById('activity-modal-overlay').addEventListener('click', e => {
            if (e.target === e.currentTarget) closeActivityModal();
        });

        // Activity filter tabs in modal
        document.querySelectorAll('.activity-filter-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const filter = tab.dataset.activityFilterModal;
                if (filter) {
                    currentActivityFilter = filter;
                    document.querySelectorAll('.activity-filter-tab').forEach(t =>
                        t.classList.remove('active')
                    );
                    tab.classList.add('active');
                    renderActivityModalContent(filter);
                }
            });
        });

        document.getElementById('close-modal-btn').onclick = closeCardModal;
        document.getElementById('card-modal-overlay').addEventListener('click', e => {
            if (e.target === e
                .currentTarget) closeCardModal();
        });
        document.getElementById('modal-card-title').addEventListener('input', function() {
            if (currentCardId) {
                const title = this.value.trim() || 'Untitled';
                getActiveBoard().cards[currentCardId].title = title;
                const body = {
                    "name": title
                }
                saveData("update", "Card", body, currentCardId);
            }
        });
        document.getElementById('modal-completion').addEventListener('change', function() {
            if (currentCardId) {
                const card = getActiveBoard().cards[currentCardId];
                card.completed = this.value === 'complete';
                document.getElementById('modal-card-title').classList.toggle('completed', card.completed);
                addActivity(card, card.completed ? 'marked complete' : 'marked incomplete', CURRENT_USER_ID);
                let val;
                if (this.value == "complete") {
                    val = true
                } else {
                    val = false
                }
                const body = {
                    "completed": val
                }
                saveData("update", "Card", body, card.id);
                renderModalDatesDisplay();
                renderBoard();
            }
        });
        document.getElementById('modal-description').addEventListener('input', function() {
            if (currentCardId) {
                getActiveBoard().cards[currentCardId].description = this.value;
                const body = {
                    "description": this.value
                }
                saveData("update", "Card", body, currentCardId);
            }
        });
        document.getElementById('modal-cover-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            openCoverPopover(this);
        });
        document.getElementById('three-dot-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            closeAllPopovers();
            const dd = document.getElementById('three-dot-dropdown');
            dd.classList.toggle('hidden');
            if (!dd.classList.contains('hidden')) {
                const rect = this
                    .getBoundingClientRect();
                dd.style.position = 'fixed';
                dd.style.top = rect.bottom + 4 + 'px';
                dd.style.right = (window.innerWidth - rect.right) + 'px';
                dd.style.left = 'auto';
            }
        });
        document.getElementById('three-dot-dropdown').addEventListener('click', function(e) {
            const item = e.target
                .closest('.dropdown-item');
            if (!item || !currentCardId) return;
            const action = item.dataset
                .action;
            const card = getActiveBoard().cards[currentCardId];
            if (action === 'move') {
                const lists =
                    getActiveBoard().lists;
                const listNames = lists.map((l, i) => `${i+1}. ${l.title}`).join(
                    '\n');
                const targetIdx = prompt(
                    `Move card to which list?\n\n${listNames}\n\nEnter list number (1-${lists.length}):`);
                if (
                    targetIdx) {
                    const idx = parseInt(targetIdx) - 1;
                    if (idx >= 0 && idx < lists.length) {
                        moveCard(currentCardId, lists[idx].id);
                        closeCardModal();
                    }
                }
            } else if (action === 'copy') {
                copyCard(currentCardId);
                closeCardModal();
            } else if (action === 'watch') {
                toggleWatch(currentCardId);
                updateWatchIndicator();
                renderBoard();
                document.getElementById('watch-dropdown-item').textContent = card.watched ? '👀 Unwatch' :
                    '👀 Watch';
            } else if (action === 'archive') {
                toggleArchive(currentCardId);
                closeCardModal();
            } else if (action === 'delete') {
                if (confirm('Delete card?')) {
                    deleteCard(
                        currentCardId);
                    closeCardModal();
                }
            }
            document.getElementById('three-dot-dropdown').classList.add('hidden');
        });
        document.getElementById('add-dropdown-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            closeAllPopovers();
            const dd = document.getElementById('add-dropdown');
            dd.classList.toggle('hidden');
            if (!dd.classList.contains('hidden')) {
                const rect = this
                    .getBoundingClientRect();
                dd.style.position = 'fixed';
                dd.style.top = rect.bottom + 4 + 'px';
                dd.style.left = rect.left + 'px';
                dd.style.right = 'auto';
            }
        });
        document.getElementById('add-dropdown').addEventListener('click', async function(e) {
            const item = e.target
                .closest('.dropdown-item');
            if (!item || !currentCardId) return;
            const addType = item.dataset
                .add;
            document.getElementById('add-dropdown').classList.add('hidden');
            if (addType === 'label')
                openLabelsPopover(document.getElementById('modal-labels-btn'));
            else if (addType === 'dates')
                openDatesPopover(document.getElementById('modal-dates-btn'));
            else if (addType === 'checklist') {
                const card = getActiveBoard().cards[currentCardId];
                const clName = 'Checklist ' + ((card
                    .checklists?.length || 0) + 1);

                const body = {
                    "name": clName,
                    "card": currentCardId
                }
                const result = await saveData("create", "Checklist", body, currentCardId);
                if (result) {

                    card.checklists.push({
                        id: result.id,
                        name: result.name,
                        items: []
                    });


                    addActivity(card, `added checklist "${clName}"`, CURRENT_USER_ID);

                    renderModalChecklists();
                    renderBoard();
                }

            } else if (addType === 'members') openMembersPopover(document.getElementById(
                'modal-members-display'));
            else if (addType === 'attachments') openAttachPopover(document
                .getElementById('attachments-section'));
        });
        document.getElementById('modal-labels-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            closeAllPopovers();
            openLabelsPopover(this);
        });
        document.getElementById('modal-dates-btn').addEventListener('click', function(e) {
            e.stopPropagation();
            closeAllPopovers();
            openDatesPopover(this);
        });
        document.getElementById('modal-checklist-btn').addEventListener('click', async function() {
            if (!currentCardId)
                return;
            const card = getActiveBoard().cards[currentCardId];
            const clName = 'Checklist ' + ((card
                .checklists?.length || 0) + 1);
            const body = {
                "name": clName,
                "card": currentCardId
            }
            const result = await saveData("create", "Checklist", body, currentCardId);
            if (result) {

                card.checklists.push({
                    id: result.id,
                    name: result.name,
                    items: []
                });

                addActivity(card, `added checklist "${clName}"`, CURRENT_USER_ID);

                renderModalChecklists();
                renderBoard();
            }
        });
        document.getElementById('modal-comment-btn').addEventListener('click', function() {
            document.getElementById(
                'new-comment-text').focus();
            document.getElementById('comment-sidebar').scrollIntoView({
                behavior: 'smooth'
            });
        });
        document.getElementById('add-comment-btn').addEventListener('click', async function() {
            if (!currentCardId)
                return;
            const newCommentText = document.getElementById('new-comment-text');
            const text = newCommentText.value.trim();
            if (!text) {

                return;
            }
            const card = getActiveBoard().cards[currentCardId];
            let result = false;


            if (editingCommentIndex !== null && card.comments[editingCommentIndex] && card
                .comments?.[editingCommentIndex]?.userId === CURRENT_USER_ID) {
                const body = {
                    "content": text,
                    "edited": true
                }
                result = await saveData("update", "Comment", body, card.comments[editingCommentIndex].id)
                if (result) {

                    card.comments[editingCommentIndex].text = text;
                    card.comments[editingCommentIndex].edited = true;
                    card.comments[editingCommentIndex].timestamp = result.timestamp;
                    addActivity(card, 'edited a comment', 'uid');
                    editingCommentIndex = null;
                    document.getElementById('add-comment-btn').textContent = 'Post Comment';
                    const discardBtn = document.getElementById('discard-edit-btn');
                    if (discardBtn) discardBtn.remove();
                }
            } else {
                const mainText = extractMainText(text);
                replyType = newCommentText.dataset.replyType
                replyId = newCommentText.dataset.replyId

                const body = {
                    "content": mainText,
                    "card": currentCardId,
                    "reply_type": replyType,
                    "reply_id": replyId
                }
                result = await saveData("create", "Comment", body, currentCardId);

                if (result) {
                    addActivity(card, 'commented', 'uid');
                    card.comments.push({
                        userId: result.user,
                        text: mainText,
                        timestamp: result.timestamp,
                        edited: false,
                        id: result.id,
                        reply: result.reply
                    });
                }
            }
            if (result) {

                renderModalCommentsActivity();
                document.getElementById('new-comment-text').value = '';
                document.getElementById('add-comment-btn').textContent = 'Post Comment';
                const discardBtn = document.getElementById('discard-edit-btn');
                if (discardBtn) discardBtn.remove();
                editingCommentIndex = null;
            }
            newCommentText.setAttribute("data-reply-type", "")
            newCommentText.setAttribute("data-reply-id", "")

        });

        document.getElementById('close-users-modal').onclick = () => document.getElementById('users-modal-overlay')
            .classList.add('hidden');
        document.getElementById('close-users-modal-top')?.addEventListener('click', () => document.getElementById(
            'users-modal-overlay').classList.add('hidden'));
        document.getElementById('add-user-btn').onclick = () => {
            const name = document.getElementById(
                'new-user-name').value.trim();
            const color = document.getElementById('new-user-color').value;
            if (
                name) {
                appState.users.push({
                    id: generateId(),
                    name,
                    color,
                    email: '',
                    username: '@' + name.toLowerCase().replace(/\s+/g, '')
                });
                saveData();
                renderUsersModal();
                updateFilterDropdowns();
            }
        };
        document.getElementById('close-labels-modal').onclick = () => document.getElementById('labels-modal-overlay')
            .classList.add('hidden');
        document.getElementById('close-labels-modal-top')?.addEventListener('click', () => document.getElementById(
            'labels-modal-overlay').classList.add('hidden'));
        document.getElementById('add-label-btn').onclick = () => {
            const name = document.getElementById(
                'new-label-name').value.trim();
            const color = document.getElementById('new-label-color').value;
            if (
                name) {
                appState.labels.push({
                    id: generateId(),
                    name,
                    color
                });
                saveData();
                renderLabelsModal();
                updateFilterDropdowns();
            }
        };

        document.getElementById('close-bg-modal').onclick = () => document.getElementById('bg-modal-overlay')
            .classList.add('hidden');
        document.getElementById('close-bg-modal-top')?.addEventListener('click', () => document.getElementById(
            'bg-modal-overlay').classList.add('hidden'));
        document.getElementById('apply-bg-btn').onclick = () => {
            const col = document.getElementById(
                'custom-bg-color').value;
            getActiveBoard().background = col;
            saveData();
            document.body.style.background = col;
            document.body.style.backgroundSize = '';
        };
        document.querySelectorAll('#bg-presets .bg-preset').forEach(p => {
            p.onclick = () => {
                const bg = p.dataset
                    .bg;
                getActiveBoard().background = bg;
                saveData();
                document.body.style.background = bg;
                document.body.style.backgroundSize = '';
            };
        });

        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);


        document.getElementById('close-board-activity-btn').onclick = () => document.getElementById(
            'board-activity-overlay').classList.add('hidden');
        document.getElementById('close-board-activity-btn-top')?.addEventListener('click', () => document
            .getElementById('board-activity-overlay').classList.add('hidden'));
        document.getElementById('board-activity-overlay').addEventListener('click', e => {
            if (e.target === e
                .currentTarget) document.getElementById('board-activity-overlay').classList.add('hidden');
        });



        document.getElementById('search-clear-btn').addEventListener('click', () => {
            document.getElementById(
                'search-input').value = '';

            document.getElementById('search-clear-btn').classList.add('hidden');
        });

        document.querySelectorAll('.popover-close-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const targetId = this.dataset.close;
                if (targetId) document.getElementById(targetId)
                    .classList.add('hidden');
            });
        });
        document.addEventListener('click', function(e) {

            if (!e.target.closest('#board-menu-dots-btn') && !e.target.closest('#board-menu-dropdown')) {
                document.getElementById('board-menu-dropdown').classList.add('hidden');
            }
            if (!e.target.closest('#visibility-badge-btn') && !e.target.closest('#visibility-dropdown')) {
                document.getElementById('visibility-dropdown').classList.add('hidden');
            }
            if (!e.target.closest('.list-menu-btn') && !e.target.closest('.list-menu-dropdown')) {
                document.querySelectorAll('.list-menu-dropdown').forEach(d => d.classList.add('hidden'));
            }
            if (!e.target.closest('#card-modal') && document.getElementById('card-modal-overlay').classList
                .contains('hidden')) {
                closeAllPopovers();
            }
            if (!e.target.closest('#three-dot-btn') && !e.target.closest('#three-dot-dropdown')) {
                document
                    .getElementById('three-dot-dropdown').classList.add('hidden');
            }
            if (!e.target.closest('#add-dropdown-btn') && !e.target.closest('#add-dropdown')) {
                document
                    .getElementById('add-dropdown').classList.add('hidden');
            }
            if (!e.target.closest('.attachment-dot-btn') && !e.target.closest('.attachment-dropdown')) {
                document
                    .querySelectorAll('.attachment-dropdown').forEach(d => d.classList.add('hidden'));
            }
            if (!e.target.closest('.member-role-badge') && !e.target.closest('.role-dropdown')) {
                document
                    .querySelectorAll('.role-dropdown').forEach(d => d.remove());
            }
        });
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                if (!document.getElementById(
                        'card-modal-overlay').classList.contains('hidden')) {
                    closeCardModal();
                }
                closeAllPopovers();
                document.getElementById('three-dot-dropdown').classList.add('hidden');
                document.getElementById('add-dropdown').classList.add('hidden');
                document.getElementById('visibility-dropdown').classList.add('hidden');
                document.getElementById('profile-dropdown').classList.add('hidden');
                document.getElementById('board-menu-dropdown').classList.add('hidden');
                document.querySelectorAll('.list-menu-dropdown').forEach(d => d.classList.add('hidden'));
                document.querySelectorAll('.role-dropdown').forEach(d => d.remove());
            }
        });
        document.querySelectorAll('.modal-overlay').forEach(overlay => {
            if (overlay.id === 'card-modal-overlay')
                return;
            overlay.addEventListener('click', function(e) {
                if (e.target === e.currentTarget) this.classList
                    .add('hidden');
            });
        });
    }

    function renderUsersModal() {
        const container = document.getElementById('users-list');
        container.innerHTML = '';
        appState.users.forEach(u => {
            const div = document.createElement('div');
            div.style.cssText =
                'display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding:4px;';
            div.innerHTML =
                `<span><span style="background:${u.color};width:22px;height:22px;display:inline-block;border-radius:50%;text-align:center;line-height:22px;color:white;font-weight:600;font-size:0.65rem;">${u.name[0]}</span> ${u.name}</span><button class="icon-btn small delete-user-btn" data-id="${u.id}">🗑</button>`;
            container.appendChild(div);
            div.querySelector('button').addEventListener('click', () => {
                appState.users = appState.users.filter(
                    usr => usr.id !== u.id);
                appState.boards.forEach(b => {
                    b.boardMembers = b.boardMembers.filter(uid => uid !== u.id);
                    delete b.memberRoles[u.id];
                    b.joinRequests = b.joinRequests.filter(uid => uid !== u.id);
                    Object.values(b.cards).forEach(c => c.assignedUsers = c.assignedUsers.filter(
                        member => member.user !== u.id));
                });
                saveData();
                renderUsersModal();
                updateFilterDropdowns();
                renderBoard();
            });
        });
    }

    function renderLabelsModal() {
        const container = document.getElementById('labels-list');
        container.innerHTML = '';
        appState.labels.forEach(l => {
            const div = document.createElement('div');
            div.style.cssText =
                'display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;padding:4px;';
            div.innerHTML =
                `<span><span style="background:${l.color};width:36px;height:14px;display:inline-block;border-radius:5px;"></span> ${l.name}</span><button class="icon-btn small delete-label-btn" data-id="${l.id}">🗑</button>`;
            container.appendChild(div);
            div.querySelector('button').addEventListener('click', () => {
                appState.labels = appState.labels.filter(
                    lbl => lbl.id !== l.id);
                appState.boards.forEach(b => Object.values(b.cards).forEach(c => c.labels = c.labels.filter(
                    lid => lid !== l.id)));
                saveData();
                renderLabelsModal();
                updateFilterDropdowns();
                renderBoard();
            });
        });
    }

    loadData();


})();