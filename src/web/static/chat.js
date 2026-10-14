// RAGQuery Chat Frontend

const chatMessages = document.getElementById('chatMessages');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const chatForm = document.getElementById('chatForm');

// Auto-resize textarea
questionInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
});

// Enter to send (Shift+Enter for new line)
questionInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

function askExample(btn) {
    questionInput.value = btn.textContent;
    questionInput.focus();
    chatForm.dispatchEvent(new Event('submit'));
}

async function sendMessage(event) {
    event.preventDefault();

    const question = questionInput.value.trim();
    if (!question) return;

    // Add user message
    addMessage(question, 'user');
    questionInput.value = '';
    questionInput.style.height = 'auto';

    // Show loading
    const loadingId = addLoading();
    sendBtn.disabled = true;

    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();
        removeLoading(loadingId);

        if (data.error) {
            addMessage(data.error, 'bot', { error: true });
        } else {
            const meta = [];
            if (data.intent) meta.push(`intent: ${data.intent}`);
            if (data.source) meta.push(`source: ${data.source}`);
            if (data.elapsed_ms) meta.push(`${data.elapsed_ms}ms`);

            addMessage(data.answer, 'bot', { meta: meta.join(' | ') });
        }
    } catch (err) {
        removeLoading(loadingId);
        addMessage(`Erro de conexão: ${err.message}`, 'bot', { error: true });
    }

    sendBtn.disabled = false;
    questionInput.focus();
}

function addMessage(text, role, opts = {}) {
    const div = document.createElement('div');
    div.className = `message ${role}`;

    const content = document.createElement('div');
    content.className = 'message-content';

    if (role === 'bot') {
        content.innerHTML = renderMarkdown(text);
    } else {
        content.textContent = text;
    }

    div.appendChild(content);

    if (opts.meta) {
        const meta = document.createElement('div');
        meta.className = 'message-meta';
        meta.textContent = opts.meta;
        div.appendChild(meta);
    }

    chatMessages.appendChild(div);
    scrollToBottom();
}

function addLoading() {
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = id;
    div.innerHTML = `
        <div class="message-content">
            <div class="loading-dots">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(div);
    scrollToBottom();
    return id;
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Simple markdown renderer
function renderMarkdown(text) {
    if (!text) return '';

    let html = escapeHtml(text);

    // Code blocks (```...```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(m, lang, code) {
        return `<pre><code>${code.trim()}</code></pre>`;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Tables
    html = renderTables(html);

    // Headers
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');

    // Lists
    html = html.replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>');
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/^  - (.+)$/gm, '<li style="margin-left:20px">$1</li>');

    // Paragraphs (double newline)
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraph if not already wrapped
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }

    return html;
}

function renderTables(text) {
    const lines = text.split('\n');
    let result = [];
    let inTable = false;
    let tableLines = [];

    for (const line of lines) {
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
            if (!inTable) inTable = true;
            tableLines.push(line);
        } else {
            if (inTable) {
                result.push(buildTable(tableLines));
                tableLines = [];
                inTable = false;
            }
            result.push(line);
        }
    }
    if (inTable) {
        result.push(buildTable(tableLines));
    }
    return result.join('\n');
}

function buildTable(lines) {
    if (lines.length < 2) return lines.join('\n');

    let html = '<table>';

    // Header
    const headerCells = lines[0].split('|').filter(c => c.trim());
    html += '<thead><tr>';
    for (const cell of headerCells) {
        html += `<th>${cell.trim()}</th>`;
    }
    html += '</tr></thead>';

    // Body (skip separator line)
    html += '<tbody>';
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (line.match(/^\|[\s\-:|]+\|$/)) continue; // separator
        const cells = line.split('|').filter(c => c.trim() !== '' || c.includes(' '));
        if (cells.length === 0) continue;
        html += '<tr>';
        for (const cell of cells) {
            if (cell.trim() === '' && cells.indexOf(cell) === 0) continue;
            html += `<td>${cell.trim()}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody></table>';
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// LLM Download
async function downloadLLM() {
    const btn = document.getElementById('llmDownloadBtn');
    const progress = document.getElementById('llmProgress');
    const progressFill = document.getElementById('llmProgressFill');
    const progressText = document.getElementById('llmProgressText');

    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Iniciando download...';
    progress.style.display = 'block';

    try {
        const resp = await fetch('/api/llm/download', { method: 'POST' });
        const data = await resp.json();

        if (data.status === 'exists') {
            btn.textContent = 'Modelo pronto!';
            await activateLLM();
            return;
        }

        // Poll progress
        const interval = setInterval(async () => {
            try {
                const pResp = await fetch('/api/llm/download/progress');
                const pData = await pResp.json();

                progressFill.style.width = pData.progress + '%';
                progressText.textContent = pData.progress + '%';
                btn.textContent = `Baixando... ${pData.progress}%`;

                if (pData.error) {
                    clearInterval(interval);
                    btn.textContent = 'Erro: ' + pData.error;
                    btn.disabled = false;
                }

                if (pData.done) {
                    clearInterval(interval);
                    btn.textContent = 'Ativando LLM...';
                    progressFill.style.width = '100%';
                    progressText.textContent = '100%';
                    await activateLLM();
                }
            } catch (e) {
                // ignore polling errors
            }
        }, 2000);
    } catch (err) {
        btn.textContent = 'Erro: ' + err.message;
        btn.disabled = false;
    }
}

async function activateLLM() {
    const btn = document.getElementById('llmDownloadBtn');
    const statusItem = document.getElementById('llmStatus');
    const statusText = document.getElementById('llmStatusText');
    const panel = document.getElementById('llmDownloadPanel');

    try {
        const resp = await fetch('/api/llm/activate', { method: 'POST' });
        const data = await resp.json();

        if (data.status === 'ok') {
            if (statusItem) {
                statusItem.className = 'status-item ok';
            }
            if (statusText) {
                statusText.textContent = 'LLM: Ativo';
            }
            if (panel) {
                panel.style.display = 'none';
            }
            addMessage('LLM ativado com sucesso! As respostas agora podem usar IA para classificar perguntas complexas.', 'bot');
        } else {
            if (btn) {
                btn.textContent = 'LLM: ' + data.message;
            }
        }
    } catch (e) {
        if (btn) {
            btn.textContent = 'Erro ao ativar: ' + e.message;
        }
    }
}
