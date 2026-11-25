import "./style.css";

import {
    createEditor,
    getEditor,
    changeLanguage,
    resetEditor,
    toggleTheme
} from "./editor.js";

// CONFIGURATION

const API_BASE_URL = "http://127.0.0.1:8000";

// INITIALIZE MONACO EDITOR

createEditor();

// HTML ELEMENTS

const languageSelector = document.getElementById("language");

const runButton = document.getElementById("run-button");
const resetButton = document.getElementById("reset-button");
const themeButton = document.getElementById("theme-button");

const saveButton = document.getElementById("save-button");
const updateButton = document.getElementById("update-button");

const snippetsButton = document.getElementById("snippets-button");
const snippetsDialog = document.getElementById("snippets-dialog");
const closeSnippetsButton = document.getElementById("close-snippets-button");

const snippetSaveForm = document.getElementById("snippet-save-form");
const snippetNameInput = document.getElementById("snippet-name");
const saveSnippetButton = document.getElementById("save-snippet-button");

const snippetsList = document.getElementById("snippets-list");
const snippetMessage = document.getElementById("snippet-message");

const refreshSnippetsButton = document.getElementById(
    "refresh-snippets-button"
);

const output = document.getElementById("output");
const terminal = document.getElementById("terminal");
const customInput = document.getElementById("custom-input");

const executionStatus = document.getElementById("execution-status");
const executionTime = document.getElementById("execution-time");
const memoryUsage = document.getElementById("memory-usage");

const editorLanguageLabel = document.getElementById(
    "editor-language-label"
);

// APPLICATION STATE

let currentLanguage = languageSelector.value;

// ID of the snippet currently loaded in the editor.
// null means that the current program is not linked to a saved snippet.
let activeSnippetId = null;

const languageNames = {
    cpp: "C++",
    c: "C",
    python: "Python",
    java: "Java",
    javascript: "JavaScript"
};

// TAB MANAGEMENT

const tabButtons = document.querySelectorAll(".panel-tab");
const panels = document.querySelectorAll(".panel-content");

function switchTab(panelId) {

    tabButtons.forEach((button) => {

        button.classList.toggle(
            "active",
            button.dataset.tab === panelId
        );

    });

    panels.forEach((panel) => {

        const isActive = panel.id === panelId;

        panel.hidden = !isActive;
        panel.classList.toggle("active", isActive);

    });

}

tabButtons.forEach((button) => {

    button.addEventListener("click", () => {

        switchTab(button.dataset.tab);

    });

});

// EXECUTION STATUS

function setStatus(message, type = "") {

    executionStatus.textContent = message;

    executionStatus.className = "status-badge";

    if (type) {
        executionStatus.classList.add(type);
    }

}

// TERMINAL LOGGING

function logToTerminal(message) {

    const timestamp = new Date().toLocaleTimeString();

    terminal.textContent += `\n[${timestamp}] ${message}`;

    terminal.scrollTop = terminal.scrollHeight;

}

// API HELPER

async function apiRequest(endpoint, options = {}) {

    const response = await fetch(
        `${API_BASE_URL}${endpoint}`,
        options
    );

    const result = await response.json().catch(() => ({}));

    if (!response.ok) {

        throw new Error(
            result.detail || `Server error: ${response.status}`
        );

    }

    return result;

}

// LANGUAGE SELECTOR

languageSelector.addEventListener("change", (event) => {

    currentLanguage = event.target.value;

    changeLanguage(currentLanguage);

    editorLanguageLabel.textContent =
        languageNames[currentLanguage];

    output.textContent =
        `Language changed to ${languageNames[currentLanguage]}.`;

    setStatus("Ready");

    logToTerminal(
        `Language changed to ${languageNames[currentLanguage]}.`
    );

});

// RESET EDITOR

resetButton.addEventListener("click", () => {

    resetEditor(currentLanguage);

    activeSnippetId = null;

    updateButton.hidden = true;

    snippetNameInput.value = "";

    output.textContent = "Editor has been reset.";

    executionTime.textContent = "—";

    memoryUsage.textContent = "—";

    setStatus("Ready");

    logToTerminal("Editor has been reset.");

});

// THEME SWITCHING

themeButton.addEventListener("click", () => {

    const theme = toggleTheme();

    themeButton.textContent =
        theme === "vs" ? "☾ Dark" : "☀ Light";

});

// RUN CODE

runButton.addEventListener("click", async () => {

    currentLanguage = languageSelector.value;

    const sourceCode = getEditor().getValue();

    if (!sourceCode.trim()) {

        output.textContent = "Please write some code first.";

        setStatus("No code", "error");

        switchTab("output-panel");

        return;

    }

    const startTime = performance.now();

    runButton.disabled = true;

    runButton.textContent = "Running...";

    output.textContent = "Executing your program...";

    executionTime.textContent = "Calculating...";

    memoryUsage.textContent = "Calculating...";

    setStatus("Running", "running");

    switchTab("output-panel");

    logToTerminal("--------------------------------");

    logToTerminal(
        `Running ${languageNames[currentLanguage]} program...`
    );

    logToTerminal("Sending code to execution server.");

    try {

        const response = await fetch(`${API_BASE_URL}/run`, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                code: sourceCode,

                language: currentLanguage,

                input: customInput.value

            })

        });

        if (!response.ok) {

            throw new Error(`Server error: ${response.status}`);

        }

        const result = await response.json();

        const endTime = performance.now();

        const requestTime = endTime - startTime;

        const backendTime = result.execution_time_ms;

        executionTime.textContent =
            backendTime !== undefined
                ? `${backendTime.toFixed(2)} ms`
                : "Unavailable";

        memoryUsage.textContent =
            result.memory_usage_mb !== null &&
            result.memory_usage_mb !== undefined
                ? `${result.memory_usage_mb} MB`
                : "Unavailable";

        output.textContent =
            result.output || "(No output produced.)";

        const status = result.status || "unknown";

        if (status === "success") {

            setStatus("Success", "success");

        } else {

            setStatus(status.replace("_", " "), "error");

        }

        logToTerminal(`Language: ${languageNames[currentLanguage]}`);

        logToTerminal(`Status: ${status}`);

        logToTerminal(
            `Backend execution time: ${backendTime ?? "Unavailable"} ms`
        );

        logToTerminal(
            `Browser request time: ${requestTime.toFixed(2)} ms`
        );

        logToTerminal(
            `Peak memory: ${result.memory_usage_mb ?? "Unavailable"} MB`
        );

        logToTerminal(`Exit code: ${result.return_code ?? "N/A"}`);

        logToTerminal("Execution completed.");

    } catch (error) {

        output.textContent =
            "Could not connect to the backend.\n\n" +
            error.message;

        setStatus("Connection error", "error");

        logToTerminal(`ERROR: ${error.message}`);

        console.error("Backend connection error:", error);

    } finally {

        runButton.disabled = false;

        runButton.textContent = "▶ Run Code";

    }

});

// OPEN SNIPPET MANAGER

snippetsButton.addEventListener("click", async () => {

    snippetMessage.textContent = "";

    snippetsDialog.showModal();

    await loadSnippets();

});


// Close dialog

closeSnippetsButton.addEventListener("click", () => {

    snippetsDialog.close();

});

// LOAD ALL SNIPPETS

async function loadSnippets() {

    snippetsList.innerHTML = `
        <p class="empty-snippets">Loading saved programs...</p>
    `;

    refreshSnippetsButton.disabled = true;

    try {

        const snippets = await apiRequest("/snippets");

        renderSnippets(snippets);

    } catch (error) {

        snippetsList.innerHTML = `
            <p class="empty-snippets">
                Could not load snippets: ${escapeHTML(error.message)}
            </p>
        `;

        console.error("Snippet loading error:", error);

    } finally {

        refreshSnippetsButton.disabled = false;

    }

}

// SAFE HTML TEXT

function escapeHTML(value) {

    return String(value).replace(/[&<>"']/g, (character) => {

        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];

    });

}

// DISPLAY SAVED SNIPPETS

function renderSnippets(snippets) {

    snippetsList.replaceChildren();

    if (!snippets.length) {

        const emptyMessage = document.createElement("p");

        emptyMessage.className = "empty-snippets";

        emptyMessage.textContent =
            "No saved programs yet. Save your first program!";

        snippetsList.appendChild(emptyMessage);

        return;

    }

    snippets.forEach((snippet) => {

        const card = document.createElement("article");

        card.className = "snippet-card";

        const header = document.createElement("div");

        header.className = "snippet-card-header";

        const information = document.createElement("div");

        const name = document.createElement("h4");

        name.textContent = snippet.name;

        const date = document.createElement("p");

        date.className = "snippet-date";

        date.textContent =
            `Updated: ${new Date(snippet.updated_at).toLocaleString()}`;

        information.appendChild(name);

        information.appendChild(date);

        const language = document.createElement("span");

        language.className = "snippet-language";

        language.textContent =
            languageNames[snippet.language] || snippet.language;

        header.appendChild(information);

        header.appendChild(language);


        // Load and Delete buttons

        const actions = document.createElement("div");

        actions.className = "snippet-card-actions";

        const loadButton = document.createElement("button");

        loadButton.className = "load-snippet-button";

        loadButton.textContent = "Load";

        loadButton.addEventListener("click", () => {

            loadSnippet(snippet.id);

        });


        const deleteButton = document.createElement("button");

        deleteButton.className = "delete-snippet-button";

        deleteButton.textContent = "Delete";

        deleteButton.addEventListener("click", () => {

            deleteSnippet(snippet.id, snippet.name);

        });


        actions.appendChild(loadButton);

        actions.appendChild(deleteButton);

        card.appendChild(header);

        card.appendChild(actions);

        snippetsList.appendChild(card);

    });

}

// SAVE NEW SNIPPET

saveButton.addEventListener("click", async () => {

    if (!getEditor().getValue().trim()) {

        setStatus("No code", "error");

        output.textContent = "Write some code before saving.";

        switchTab("output-panel");

        return;

    }

    snippetMessage.textContent = "";

    snippetSaveForm.reset();

    snippetsDialog.showModal();

    await loadSnippets();

    snippetNameInput.focus();

});


snippetSaveForm.addEventListener("submit", async (event) => {

    event.preventDefault();

    const name = snippetNameInput.value.trim();

    const code = getEditor().getValue();

    currentLanguage = languageSelector.value;

    if (!name) {

        snippetMessage.textContent = "Please enter a program name.";

        return;

    }

    if (!code.trim()) {

        snippetMessage.textContent = "There is no code to save.";

        return;

    }

    saveSnippetButton.disabled = true;

    saveSnippetButton.textContent = "Saving...";

    try {

        const result = await apiRequest("/snippets", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({

                name: name,

                language: currentLanguage,

                code: code

            })

        });

        activeSnippetId = result.id;

        updateButton.hidden = false;

        snippetMessage.textContent =
            `Successfully saved "${result.name}"!`;

        setStatus("Snippet saved", "success");

        logToTerminal(
            `Snippet saved: ${result.name} (ID: ${result.id})`
        );

        await loadSnippets();

    } catch (error) {

        snippetMessage.textContent =
            `Could not save snippet: ${error.message}`;

        console.error("Snippet saving error:", error);

    } finally {

        saveSnippetButton.disabled = false;

        saveSnippetButton.textContent = "Save Code";

    }

});

// LOAD ONE SNIPPET

async function loadSnippet(snippetId) {

    try {

        const snippet = await apiRequest(
            `/snippets/${snippetId}`
        );

        // Load saved code into Monaco Editor.

        getEditor().setValue(snippet.code);

        // Restore the saved programming language.

        currentLanguage = snippet.language;

        languageSelector.value = currentLanguage;

        changeLanguage(currentLanguage);

        editorLanguageLabel.textContent =
            languageNames[currentLanguage] || currentLanguage;

        // Remember which snippet is currently loaded.

        activeSnippetId = snippet.id;

        snippetNameInput.value = snippet.name;

        updateButton.hidden = false;

        output.textContent =
            `Loaded snippet: ${snippet.name}`;

        executionTime.textContent = "—";

        memoryUsage.textContent = "—";

        setStatus("Snippet loaded", "success");

        logToTerminal(
            `Loaded snippet: ${snippet.name} (ID: ${snippet.id})`
        );

        snippetsDialog.close();

        switchTab("input-panel");

    } catch (error) {

        snippetMessage.textContent =
            `Could not load snippet: ${error.message}`;

        console.error("Snippet loading error:", error);

    }

}

// UPDATE CURRENT SNIPPET

updateButton.addEventListener("click", async () => {

    if (activeSnippetId === null) {

        return;

    }

    const name = snippetNameInput.value.trim();

    const code = getEditor().getValue();

    currentLanguage = languageSelector.value;

    if (!name) {

        setStatus("Invalid name", "error");

        return;

    }

    if (!code.trim()) {

        setStatus("No code", "error");

        return;

    }

    updateButton.disabled = true;

    updateButton.textContent = "Updating...";

    try {

        const result = await apiRequest(
            `/snippets/${activeSnippetId}`,
            {

                method: "PUT",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    name: name,

                    language: currentLanguage,

                    code: code

                })

            }
        );

        snippetNameInput.value = result.name;

        setStatus("Snippet updated", "success");

        output.textContent =
            `Successfully updated "${result.name}".`;

        logToTerminal(
            `Snippet updated: ${result.name} (ID: ${result.id})`
        );

        if (snippetsDialog.open) {

            await loadSnippets();

            snippetMessage.textContent =
                `Successfully updated "${result.name}"!`;

        }

    } catch (error) {

        setStatus("Update failed", "error");

        console.error("Snippet update error:", error);

        alert(`Could not update snippet: ${error.message}`);

    } finally {

        updateButton.disabled = false;

        updateButton.textContent = "Update";

    }

});

// DELETE SNIPPET

async function deleteSnippet(snippetId, snippetName) {

    const confirmed = confirm(
        `Are you sure you want to delete "${snippetName}"?`
    );

    if (!confirmed) {

        return;

    }

    try {

        await apiRequest(`/snippets/${snippetId}`, {

            method: "DELETE"

        });

        if (activeSnippetId === snippetId) {

            activeSnippetId = null;

            updateButton.hidden = true;

            snippetNameInput.value = "";

        }

        snippetMessage.textContent =
            `"${snippetName}" deleted successfully.`;

        setStatus("Snippet deleted", "success");

        logToTerminal(
            `Deleted snippet: ${snippetName} (ID: ${snippetId})`
        );

        await loadSnippets();

        snippetMessage.textContent =
            `"${snippetName}" deleted successfully.`;

    } catch (error) {

        snippetMessage.textContent =
            `Could not delete snippet: ${error.message}`;

        console.error("Snippet deletion error:", error);

    }

}

// REFRESH SNIPPETS

refreshSnippetsButton.addEventListener("click", async () => {

    snippetMessage.textContent = "";

    await loadSnippets();

});

// APPLICATION INITIALIZED

console.log("MultiCode frontend initialized successfully!");
