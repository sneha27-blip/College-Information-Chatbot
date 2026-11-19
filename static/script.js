/**
 * College Information Chatbot - Client Interaction Script
 */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const chatForm = document.getElementById("chatForm");
    const messageInput = document.getElementById("messageInput");
    const sendBtn = document.getElementById("sendBtn");
    const chatMessages = document.getElementById("chatMessages");
    const typingIndicator = document.getElementById("typingIndicator");
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
    const clearChatBtn = document.getElementById("clearChatBtn");
    const clearModalOverlay = document.getElementById("clearModalOverlay");
    const cancelClearBtn = document.getElementById("cancelClearBtn");
    const confirmClearBtn = document.getElementById("confirmClearBtn");
    const categoryModalOverlay = document.getElementById("categoryModalOverlay");
    const closeCategoryModalBtn = document.getElementById("closeCategoryModalBtn");
    const categoryModalTitle = document.getElementById("categoryModalTitle");
    const categoryQuestionsList = document.getElementById("categoryQuestionsList");

    // Scroll chat to bottom
    function scrollToBottom(smooth = true) {
        if (!chatMessages) return;
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: smooth ? "smooth" : "auto"
        });
    }

    // Auto-scroll on initial load if history exists
    scrollToBottom(false);

    // Auto-resize textarea
    function autoResizeInput() {
        messageInput.style.height = "auto";
        const newHeight = Math.min(messageInput.scrollHeight, 120);
        messageInput.style.height = newHeight + "px";
    }

    if (messageInput) {
        messageInput.addEventListener("input", autoResizeInput);
        
        // Enter to send, Shift+Enter for newline
        messageInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    }

    // Format plain text or basic markdown (bold, bullet points, linebreaks)
    function formatMessageText(text) {
        if (!text) return "";
        let formatted = text
            // Escape basic HTML entities
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Convert bold **text** -> <strong>text</strong>
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Convert bullets: lines starting with • or -
        const lines = formatted.split("\n");
        let inList = false;
        let resultLines = [];

        for (let line of lines) {
            let trimmed = line.trim();
            if (trimmed.startsWith("•") || trimmed.startsWith("-")) {
                if (!inList) {
                    resultLines.push("<ul>");
                    inList = true;
                }
                const bulletContent = trimmed.substring(1).trim();
                resultLines.push(`<li>${bulletContent}</li>`);
            } else {
                if (inList) {
                    resultLines.push("</ul>");
                    inList = false;
                }
                if (trimmed.length > 0) {
                    resultLines.push(`<p>${trimmed}</p>`);
                }
            }
        }
        if (inList) {
            resultLines.push("</ul>");
        }

        return resultLines.join("");
    }

    // Append User Message to UI
    function appendUserMessage(text, timestamp) {
        const timeStr = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const initial = window.CURRENT_USER && window.CURRENT_USER.fullName ? window.CURRENT_USER.fullName[0].toUpperCase() : 'S';
        
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper message-user";
        wrapper.innerHTML = `
            <div class="message-bubble">
                <div class="message-text">${text}</div>
                <div class="message-meta">
                    <span class="meta-time">${timeStr}</span>
                    <i class="fa-solid fa-check-double"></i>
                </div>
            </div>
            <div class="avatar-user" title="${window.CURRENT_USER ? window.CURRENT_USER.fullName : 'Student'}">
                <span>${initial}</span>
            </div>
        `;

        // Insert before typing indicator
        chatMessages.insertBefore(wrapper, typingIndicator);
        scrollToBottom();
    }

    // Append Bot Message to UI
    function appendBotMessage(text, category, timestamp) {
        const timeStr = timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper message-bot";
        
        let categoryHtml = "";
        if (category && category !== "Small Talk" && category !== "Unknown") {
            categoryHtml = `<div class="bot-category-badge"><i class="fa-solid fa-tag"></i> ${category}</div>`;
        }

        wrapper.innerHTML = `
            <div class="avatar-bot" title="College Bot">
                <i class="fa-solid fa-robot"></i>
            </div>
            <div class="message-bubble">
                ${categoryHtml}
                <div class="message-text">${formatMessageText(text)}</div>
                <div class="message-meta">
                    <span class="meta-time">${timeStr}</span>
                    <button class="btn-copy-msg" onclick="copyMessage(this)" title="Copy message">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>
            </div>
        `;

        chatMessages.insertBefore(wrapper, typingIndicator);
        scrollToBottom();
    }

    // Show / Hide Typing Indicator
    function showTypingIndicator() {
        typingIndicator.style.display = "flex";
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.style.display = "none";
    }

    // Handle Form Submit
    if (chatForm) {
        chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const message = messageInput.value.trim();
            if (!message) return;

            // Clear input and reset height
            messageInput.value = "";
            autoResizeInput();
            messageInput.focus();

            // Disable send button while sending
            sendBtn.disabled = true;

            // Display user message in chat
            appendUserMessage(message);

            // Show typing indicator
            showTypingIndicator();

            try {
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ message: message })
                });

                hideTypingIndicator();

                if (!response.ok) {
                    if (response.status === 401) {
                        window.location.href = "/login";
                        return;
                    }
                    throw new Error("Server error " + response.status);
                }

                const data = await response.json();
                if (data.status === "success") {
                    appendBotMessage(data.reply, data.category, data.timestamp);
                } else {
                    appendBotMessage("An error occurred while retrieving information. Please try again.", "Error");
                }
            } catch (err) {
                hideTypingIndicator();
                appendBotMessage(
                    "Connection issue encountered. Please make sure the Flask server is running and try again.",
                    "Network Alert"
                );
            } finally {
                sendBtn.disabled = false;
            }
        });
    }

    // Click suggestion chips (in welcome banner and above input)
    document.addEventListener("click", (e) => {
        const chip = e.target.closest(".suggestion-chip, .quick-chip");
        if (chip) {
            const question = chip.getAttribute("data-question") || chip.textContent.trim();
            if (question) {
                messageInput.value = question;
                autoResizeInput();
                chatForm.dispatchEvent(new Event("submit"));
            }
        }
    });

    // Category Filter / Explorer Modal in Sidebar
    const categoryButtons = document.querySelectorAll(".category-chip");
    categoryButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const categoryName = btn.getAttribute("data-category");
            showCategoryQuestions(categoryName);
        });
    });

    function showCategoryQuestions(categoryName) {
        if (!categoryModalTitle || !categoryQuestionsList) return;
        categoryModalTitle.textContent = `${categoryName} - Related Questions`;
        categoryQuestionsList.innerHTML = "";

        const suggestions = window.SUGGESTIONS_DATA || {};
        const questions = suggestions[categoryName] || [];

        if (questions.length === 0) {
            // General query fallback
            questions.push(
                `Tell me about ${categoryName}`,
                `What are the guidelines for ${categoryName}?`
            );
        }

        questions.forEach(q => {
            const qBtn = document.createElement("button");
            qBtn.className = "category-q-btn";
            qBtn.innerHTML = `<i class="fa-solid fa-arrow-right" style="color: #2563eb; margin-right: 8px;"></i> ${q}`;
            qBtn.addEventListener("click", () => {
                categoryModalOverlay.classList.remove("active");
                messageInput.value = q;
                autoResizeInput();
                chatForm.dispatchEvent(new Event("submit"));
                if (window.innerWidth <= 900) {
                    sidebar.classList.remove("open");
                }
            });
            categoryQuestionsList.appendChild(qBtn);
        });

        categoryModalOverlay.classList.add("active");
    }

    if (closeCategoryModalBtn) {
        closeCategoryModalBtn.addEventListener("click", () => {
            categoryModalOverlay.classList.remove("active");
        });
    }

    if (categoryModalOverlay) {
        categoryModalOverlay.addEventListener("click", (e) => {
            if (e.target === categoryModalOverlay) {
                categoryModalOverlay.classList.remove("active");
            }
        });
    }

    // Clear Chat History Modal
    if (clearChatBtn) {
        clearChatBtn.addEventListener("click", () => {
            clearModalOverlay.classList.add("active");
        });
    }

    if (cancelClearBtn) {
        cancelClearBtn.addEventListener("click", () => {
            clearModalOverlay.classList.remove("active");
        });
    }

    if (clearModalOverlay) {
        clearModalOverlay.addEventListener("click", (e) => {
            if (e.target === clearModalOverlay) {
                clearModalOverlay.classList.remove("active");
            }
        });
    }

    if (confirmClearBtn) {
        confirmClearBtn.addEventListener("click", async () => {
            try {
                confirmClearBtn.disabled = true;
                confirmClearBtn.textContent = "Clearing...";

                const res = await fetch("/api/history/clear", { method: "POST" });
                if (res.ok) {
                    // Remove all message-wrappers except welcome-banner & typing-indicator
                    const messages = chatMessages.querySelectorAll(".message-wrapper");
                    messages.forEach(m => m.remove());
                    clearModalOverlay.classList.remove("active");

                    // Show temporary toast or notice
                    appendBotMessage(
                        "Chat history has been cleared successfully. How can I assist you now?",
                        "System"
                    );
                }
            } catch (err) {
                alert("Failed to clear chat history. Please try again.");
            } finally {
                confirmClearBtn.disabled = false;
                confirmClearBtn.innerHTML = `<i class="fa-solid fa-trash-can"></i> Yes, Clear History`;
            }
        });
    }

    // Mobile Sidebar Toggle
    if (sidebarToggleBtn && sidebar) {
        sidebarToggleBtn.addEventListener("click", () => {
            sidebar.classList.toggle("open");
        });
    }

    if (sidebarCloseBtn && sidebar) {
        sidebarCloseBtn.addEventListener("click", () => {
            sidebar.classList.remove("open");
        });
    }
});

// Global copy message utility
window.copyMessage = function(btn) {
    const bubble = btn.closest(".message-bubble");
    if (!bubble) return;
    const textElement = bubble.querySelector(".message-text");
    if (!textElement) return;

    const textToCopy = textElement.innerText;
    navigator.clipboard.writeText(textToCopy).then(() => {
        const icon = btn.querySelector("i");
        const originalClass = icon.className;
        icon.className = "fa-solid fa-check";
        btn.style.color = "#10b981";
        setTimeout(() => {
            icon.className = originalClass;
            btn.style.color = "";
        }, 1800);
    }).catch(err => {
        console.error("Failed to copy message:", err);
    });
};
