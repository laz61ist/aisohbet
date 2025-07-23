document.addEventListener('DOMContentLoaded', () => {
    const chatList = document.getElementById('chatList');
    const messageContainer = document.getElementById('messageContainer');
    const userInput = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');
    const newChatBtn = document.getElementById('newChatBtn');

    let currentChatId = null;

    // Merkezi API çağrı fonksiyonu
    const apiCall = async (action, body = {}) => {
        const params = new URLSearchParams({ action });
        try {
            const response = await fetch(`api.php?${params}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(body),
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`API Hatası: ${response.status} ${response.statusText} - ${errorText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API Çağrısı Başarısız:', error);
            alert(`Bir hata oluştu: ${error.message}`);
            return null;
        }
    };

    // Sohbet listesini render eder
    const renderChats = async () => {
        const chats = await apiCall('getChats');
        chatList.innerHTML = '';
        if (chats && chats.length > 0) {
            chats.forEach(chat => {
                const li = document.createElement('li');
                li.textContent = chat.title;
                li.dataset.chatId = chat.id;
                if (chat.id === currentChatId) {
                    li.classList.add('active');
                }
                li.addEventListener('click', () => selectChat(chat.id));
                chatList.appendChild(li);
            });
        }
    };

    // Mesajları render eder
    const renderMessages = (messages) => {
        messageContainer.innerHTML = '';
        if (!messages) return;

        messages.forEach(message => {
            const messageEl = document.createElement('div');
            messageEl.classList.add('message', message.role);

            let contentHTML = '';
            if (message.role === 'user') {
                contentHTML = `<span class="sender">Siz</span><p>${message.content}</p>`;
            } else { // AI
                try {
                    const aiContent = JSON.parse(message.content);
                    contentHTML = `<span class="sender">AI Danışmanlar Kurulu</span>`;

                    if (aiContent.summary) { // Moderatör Cevabı
                        contentHTML += `<div class="summary"><strong>Özet:</strong> ${aiContent.summary}</div>`;
                        contentHTML += `<div class="details">`;
                        if(aiContent.details) {
                            for (const [expert, analysis] of Object.entries(aiContent.details)) {
                                contentHTML += `<h4>${expert.charAt(0).toUpperCase() + expert.slice(1)} Analizi:</h4><p>${analysis}</p>`;
                            }
                        }
                        contentHTML += `</div>`;
                    } else if (aiContent.direct_response) { // Uzman Cevabı
                        contentHTML += `<p>${aiContent.direct_response}</p>`;
                    } else if (aiContent.error) {
                        contentHTML += `<p><strong>Hata:</strong> ${aiContent.error}</p>`;
                    }
                     else {
                        contentHTML += `<p>${message.content}</p>`; // Düz metin fallback
                    }
                } catch (e) {
                    // JSON parse edilemezse, düz metin olarak göster
                    contentHTML = `<span class="sender">AI</span><p>${message.content}</p>`;
                }
            }
            messageEl.innerHTML = contentHTML;
            messageContainer.appendChild(messageEl);
        });
        messageContainer.scrollTop = messageContainer.scrollHeight; // En alta kaydır
    };

    // Belirli bir sohbeti seçer ve mesajları yükler
    const selectChat = async (chatId) => {
        if (!chatId) {
            messageContainer.innerHTML = '<div class="message ai"><p>Başlamak için bir sohbet seçin veya yeni bir tane oluşturun.</p></div>';
            return;
        }
        currentChatId = chatId;
        const messages = await apiCall('getMessages', { chatId });
        renderMessages(messages);
        await renderChats(); // Aktif sohbeti işaretlemek için listeyi yeniden render et
    };

    // Mesaj gönderme işlemi
    const sendMessage = async () => {
        const messageText = userInput.value.trim();
        if (!messageText || !currentChatId) return;

        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Kullanıcı mesajını anında ekle (iyimser güncelleme)
        const tempMessages = await apiCall('getMessages', { chatId: currentChatId }) || [];
        tempMessages.push({ role: 'user', content: messageText });
        renderMessages(tempMessages);

        const response = await apiCall('sendMessage', {
            chatId: currentChatId,
            message: messageText,
        });

        if (response) {
            await selectChat(currentChatId); // Tüm sohbeti yeniden yükle
        } else {
             // Hata durumunda eski mesajları geri yükle
            await selectChat(currentChatId);
        }

        userInput.disabled = false;
        sendBtn.disabled = false;
        userInput.focus();
    };

    // Yeni sohbet oluşturma
    const createNewChat = async () => {
        const chatTitle = prompt("Yeni sohbet başlığı girin:", "Yeni Analiz");
        if (chatTitle) {
            const result = await apiCall('createChat', { title: chatTitle });
            if (result && result.chatId) {
                currentChatId = result.chatId;
                await renderChats();
                await selectChat(currentChatId);
            }
        }
    };

    // Başlangıç fonksiyonu
    const initialize = async () => {
        await renderChats();
        const firstChat = chatList.querySelector('li');
        if (firstChat) {
            selectChat(firstChat.dataset.chatId);
        } else {
            selectChat(null);
        }
    };

    // Olay dinleyicileri
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    newChatBtn.addEventListener('click', createNewChat);

    initialize();
});
