(function() {
    const auth = new Auth()
    const STORAGE_KEY = 'SM_board_data';

    const defaultData = {

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
        const allFiles = [...cardData.cardfile_set, ...cardData.cardimage_set, ...cardData.linkattachment_set]
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

    function cardDataExtract(cardData) {
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
        card["activities"] = cardData.activities

        return card
    }

    function prepareCard(data) {
        const cards = {}
        const labels = []
        let card
        data.board_lists.forEach(list => {
            list.list_cards.forEach(cardData => {
                card = cardDataExtract(cardData)

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

        renderLists();

    }



    function renderLists() {
        const board = getActiveBoard(),
            wrapper = document.getElementById('lists-wrapper');
        wrapper.innerHTML = '';
        board.lists.forEach(list => {
            wrapper.appendChild(createListElement(list));
        });



    }

    function createListElement(list) {
        const board = getActiveBoard();
        const div = document.createElement('div');
        div.className = 'list';
        div.dataset.listId = list.id;
        div.innerHTML =
            `<div class="list-header"><input type="text" class="list-title" disabled value="${escapeHtml(list.title)}" data-list-id="${list.id}" /></div><div class="list-cards" data-list-id="${list.id}"></div>`;
        const cardsContainer = div.querySelector('.list-cards');
        list.cardIds.forEach(cid => {

            if (board.cards[cid]) {
                if (!showArchived && board.cards[cid].archived)
                    return;
                cardsContainer.appendChild(renderCardElement(board.cards[cid]));
            }
        });

        cardsContainer.addEventListener('click', (e) => {
            const cardEl = e.target.closest('.card');
            if (cardEl)
                openCardModal(cardEl.dataset.cardId);
        });

        // List menu button - three dots

        return div;
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


    function openCardModal(id) {
        currentCardId = id;
        editingCommentIndex = null;
        const c = getActiveBoard().cards[id];
        if (!c) return;

        document.getElementById('modal-card-title').value = c.title;
        document.getElementById('modal-card-title').disabled = true
        document.getElementById('modal-card-title').classList.toggle('completed', c.completed);

        document.getElementById('modal-description').value = c.description;
        document.getElementById('modal-description').disabled = true
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


        renderModalLabelsDisplay();
        renderModalDatesDisplay();

        renderModalChecklists();
        renderModalAttachments();



        document.getElementById('card-modal-overlay').classList.remove('hidden');
    }

    function closeCardModal() {
        if (currentCardId) {
            const c = getActiveBoard().cards[currentCardId];
            c.title = document.getElementById('modal-card-title').value.trim() || 'Untitled';
            c.description = document.getElementById('modal-description').value;


            renderBoard();
        }
        currentCardId = null;
        editingCommentIndex = null;

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


                container.appendChild(span);
            }
        });

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

            container.appendChild(badge);
        }
        if (card.dueDate) {
            const badge = document.createElement('span');
            const overdue = isOverdue(card.dueDate);
            badge.className = 'date-badge' + (overdue ? ' overdue' : '') + (card.completed ? ' complete-date' : '');
            badge.textContent = 'Due: ' + new Date(card.dueDate).toLocaleString();

            container.appendChild(badge);
        }
        if (!card.startDate && !card.dueDate) {
            const addBtn = document
                .createElement('button');
            addBtn.className = 'btn-secondary small';
            addBtn.textContent = '+ Add dates';

            container.appendChild(addBtn);
        }
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
            block.innerHTML = `<div class="checklist-block-header"><input type="text" class="checklist-block-title-input" value="${escapeHtml(checklist.name)}" data-clindex="${clIndex}" placeholder="Checklist name" /><span class="progress-text">${progress}%</span></div><div class="checklist-progress-bar"><div class="checklist-progress-fill" style="width:${progress}%"></div></div><div class="checklist-items-container" data-clindex="${clIndex}"></div><div class="inline-add-item-area" data-clindex="${clIndex}"><div class="inline-add-item-form hidden" data-clindex="${clIndex}"><input type="text" class="inline-item-input" placeholder="Item text..." data-clindex="${clIndex}" /><button class="btn-primary small save-inline-item-btn" data-clindex="${clIndex}">Add</button><button class="btn-secondary small cancel-inline-item-btn" data-clindex="${clIndex}">✕</button></div></div>`;
            block.querySelector("input").disabled = true
            const itemsContainer = block.querySelector('.checklist-items-container');
            checklist.items.forEach((item, index) => {
                const i = item.id
                const itemDiv = document.createElement('div');
                itemDiv.className = 'checklist-item';
                itemDiv.innerHTML =
                    `<input type="checkbox" ${item.completed?'checked':''} data-clindex="${clIndex}" data-itemindex="${i}"><input type="text" disabled class="checklist-item-text ${item.completed?'completed':''}" value="${escapeHtml(item.text)}" data-clindex="${clIndex}" data-itemindex="${i}" />`;

                itemDiv.querySelector("input").disabled = true
                itemsContainer.appendChild(itemDiv);

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
            const downloadLink = att.type === "link" ? "" : `<div class="dropdown-item att-download" data-attindex="${i}">Download</div>`
            const dropDownMenu = `<div class="dropdown-menu right-align hidden attachment-dropdown" style="position:absolute;right:0;top:100%;min-width:160px;">${downloadLink}
                    </div>`
            const attachmentAction = att.type === "link" ? "" : `<div class="attachment-actions"><button class="attachment-dot-btn" data-attindex="${i}">⋯</button>
                    ${dropDownMenu}
                </div>`
            div.innerHTML = `<div class="attachment-thumb">${thumbContent}</div>
                <div class="attachment-info">
                    <div class="attachment-name">${escapeHtml(att.name)}</div>
                    <div class="attachment-meta">${uploader?uploader.name:'Unknown'} · ${time}</div>
                </div>${attachmentAction}`
            container.appendChild(div);
            if (att.type != "link") {

                const dotBtn = div.querySelector('.attachment-dot-btn');
                const dropdown = div.querySelector('.attachment-dropdown');
                dotBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    document.querySelectorAll('.attachment-dropdown').forEach(d => d.classList.add('hidden'));
                    dropdown.classList.toggle('hidden');
                });

                div.querySelector('.att-download')?.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const link = document.createElement('a');
                    link.href = att.data;
                    link.download = att.name; // Optional: custom filename
                    link.click();
                });
            }

        });

    }


    function addEventListeners() {


        document.getElementById('close-modal-btn').onclick = closeCardModal;
        document.getElementById('card-modal-overlay').addEventListener('click', e => {
            if (e.target === e
                .currentTarget) closeCardModal();
        });



        document.querySelectorAll('.popover-close-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const targetId = this.dataset.close;
                if (targetId) document.getElementById(targetId)
                    .classList.add('hidden');
            });
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



    loadData();


})();