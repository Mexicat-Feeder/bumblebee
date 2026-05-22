<script lang="ts">
  import { createEventDispatcher, onMount, tick } from 'svelte';

  export let slug: string;
  export let disabled: boolean = false;

  const dispatch = createEventDispatcher<{
    finished: { summary: string };
  }>();

  interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: string;
  }

  let messages: Message[] = [];
  let input = '';
  let loading = false;
  let finishing = false;
  let hasSummary = false;
  let summaryText = '';
  let error = '';
  let chatContainer: HTMLElement;

  onMount(() => {
    loadHistory();
  });

  async function loadHistory() {
    try {
      const resp = await fetch(`/api/projects/${slug}/qa/history`);
      if (resp.ok) {
        const data = await resp.json();
        messages = data.messages || [];
        hasSummary = data.has_summary || false;
        summaryText = data.summary || '';
        await tick();
        scrollToBottom();
      }
    } catch {
      // Will start with empty history
    }
  }

  async function sendMessage() {
    if (!input.trim() || loading || disabled) return;

    const userMessage = input.trim();
    input = '';
    error = '';

    // Add user message optimistically
    messages = [...messages, { role: 'user', content: userMessage }];
    await tick();
    scrollToBottom();

    loading = true;
    try {
      const resp = await fetch(`/api/projects/${slug}/qa/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      messages = [...messages, { role: 'assistant', content: data.response }];
      await tick();
      scrollToBottom();
    } catch (e: any) {
      error = e.message || 'Failed to send message';
      // Remove the optimistically added user message
      messages = messages.slice(0, -1);
    }
    loading = false;
  }

  async function finishQA() {
    if (finishing) return;
    finishing = true;
    error = '';

    try {
      const resp = await fetch(`/api/projects/${slug}/qa/finish`, {
        method: 'POST',
      });

      if (!resp.ok) {
        const data = await resp.json().catch(() => ({ detail: resp.statusText }));
        throw new Error(data.detail || `HTTP ${resp.status}`);
      }

      const data = await resp.json();
      hasSummary = true;
      summaryText = data.summary;
      dispatch('finished', { summary: data.summary });
    } catch (e: any) {
      error = e.message || 'Failed to generate summary';
    }
    finishing = false;
  }

  function onKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function scrollToBottom() {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }
</script>

<section class="qa-chat-section">
  <div class="chat-header">
    <h2 class="section-header">PRD REVIEW</h2>
    <span class="chat-hint">
      {#if messages.length === 0}
        Send a message to start the Q&A. The AI will read your PRD and ask clarifying questions.
      {:else if hasSummary}
        Q&A complete — summary generated.
      {:else}
        {messages.length} message{messages.length !== 1 ? 's' : ''} · Click "Finish Q&A" when done
      {/if}
    </span>
  </div>

  <!-- Chat messages -->
  <div class="chat-messages" bind:this={chatContainer}>
    {#if messages.length === 0 && !loading}
      <div class="empty-state">
        <p>👋 Start by describing your project or asking a question.</p>
        <p class="empty-hint">If you uploaded a PRD, the AI will read it automatically.</p>
      </div>
    {/if}

    {#each messages as msg}
      <div class="message" class:user={msg.role === 'user'} class:assistant={msg.role === 'assistant'}>
        <div class="message-label">{msg.role === 'user' ? 'You' : 'AI Architect'}</div>
        <div class="message-content">{msg.content}</div>
      </div>
    {/each}

    {#if loading}
      <div class="message assistant">
        <div class="message-label">AI Architect</div>
        <div class="message-content typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>
    {/if}
  </div>

  <!-- Error banner -->
  {#if error}
    <div class="chat-error">
      <span>⚠ {error}</span>
      <button class="dismiss-btn" on:click={() => error = ''}>✕</button>
    </div>
  {/if}

  <!-- Summary panel -->
  {#if hasSummary && summaryText}
    <div class="summary-panel">
      <h3 class="summary-header">Q&A SUMMARY</h3>
      <div class="summary-content">{summaryText}</div>
    </div>
  {/if}

  <!-- Input area -->
  {#if !hasSummary}
    <div class="chat-input-area">
      <textarea
        class="chat-input"
        bind:value={input}
        on:keydown={onKeydown}
        placeholder="Type your message..."
        rows="2"
        disabled={disabled || loading || finishing}
      ></textarea>
      <div class="chat-actions">
        <button
          class="btn-send"
          on:click={sendMessage}
          disabled={!input.trim() || loading || disabled}
        >
          {loading ? '...' : 'Send'}
        </button>
        {#if messages.length >= 2}
          <button
            class="btn-finish"
            on:click={finishQA}
            disabled={finishing || disabled}
          >
            {finishing ? 'Generating summary...' : 'Finish Q&A'}
          </button>
        {/if}
      </div>
    </div>
  {/if}
</section>

<style>
  .qa-chat-section {
    background: var(--bg-card, #16202E);
    border: 1px solid rgba(58, 190, 255, 0.12);
    border-radius: 12px;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .chat-header {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .section-header {
    font-family: var(--font-ui);
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--color-text-primary, #E6EDF3);
    margin: 0;
  }

  .chat-hint {
    font-size: 0.75rem;
    color: var(--color-text-muted, #6B7A8D);
  }

  /* Messages container */
  .chat-messages {
    max-height: 400px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    padding: 12px;
    background: rgba(0, 0, 0, 0.15);
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.04);
  }

  .empty-state {
    text-align: center;
    padding: 30px 20px;
    color: var(--color-text-muted, #6B7A8D);
    font-size: 0.85rem;
  }

  .empty-state p { margin: 4px 0; }
  .empty-hint { font-size: 0.75rem; }

  /* Messages */
  .message {
    display: flex;
    flex-direction: column;
    gap: 4px;
    max-width: 85%;
  }

  .message.user {
    align-self: flex-end;
  }

  .message.assistant {
    align-self: flex-start;
  }

  .message-label {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-text-muted, #6B7A8D);
  }

  .message.user .message-label {
    text-align: right;
  }

  .message-content {
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 0.85rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message.user .message-content {
    background: rgba(58, 190, 255, 0.15);
    border: 1px solid rgba(58, 190, 255, 0.25);
    color: var(--color-text-primary, #E6EDF3);
  }

  .message.assistant .message-content {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: var(--color-text-primary, #E6EDF3);
  }

  /* Typing indicator */
  .typing {
    display: flex;
    gap: 4px;
    padding: 12px 16px;
  }

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--color-text-muted, #6B7A8D);
    animation: typing-bounce 1.2s ease-in-out infinite;
  }

  .dot:nth-child(2) { animation-delay: 0.15s; }
  .dot:nth-child(3) { animation-delay: 0.3s; }

  @keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); }
    30% { transform: translateY(-4px); }
  }

  /* Error */
  .chat-error {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: rgba(255, 80, 80, 0.1);
    border: 1px solid rgba(255, 80, 80, 0.3);
    border-radius: 6px;
    font-size: 0.8rem;
    color: #FF6B6B;
  }

  .dismiss-btn {
    background: none;
    border: none;
    color: #FF6B6B;
    cursor: pointer;
    padding: 0 4px;
    font-size: 0.85rem;
  }

  /* Summary panel */
  .summary-panel {
    padding: 16px;
    background: rgba(58, 190, 85, 0.08);
    border: 1px solid rgba(58, 190, 85, 0.2);
    border-radius: 8px;
  }

  .summary-header {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #3ABE55;
    margin: 0 0 10px 0;
  }

  .summary-content {
    font-size: 0.83rem;
    line-height: 1.6;
    color: var(--color-text-primary, #E6EDF3);
    white-space: pre-wrap;
  }

  /* Input area */
  .chat-input-area {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .chat-input {
    background: #1E2D42;
    border: 1px solid rgba(58, 190, 255, 0.20);
    border-radius: 8px;
    padding: 10px 14px;
    color: var(--color-text-primary, #E6EDF3);
    font-family: var(--font-ui);
    font-size: 0.85rem;
    resize: vertical;
    min-height: 44px;
    max-height: 120px;
    width: 100%;
    box-sizing: border-box;
    transition: border-color 150ms;
  }

  .chat-input:focus {
    border-color: rgba(58, 190, 255, 0.65);
    outline: none;
  }

  .chat-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .chat-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }

  .btn-send {
    background: var(--color-accent-primary, #3ABEFF);
    color: #0B1220;
    border: none;
    border-radius: 6px;
    padding: 8px 20px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms;
  }

  .btn-send:hover:not(:disabled) {
    background: #5BCEFF;
  }

  .btn-send:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-finish {
    background: transparent;
    color: #3ABE55;
    border: 1px solid rgba(58, 190, 85, 0.4);
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 150ms, border-color 150ms;
  }

  .btn-finish:hover:not(:disabled) {
    background: rgba(58, 190, 85, 0.1);
    border-color: rgba(58, 190, 85, 0.6);
  }

  .btn-finish:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
