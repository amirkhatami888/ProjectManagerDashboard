(function () {
  const launcher = document.getElementById('rcsAiLauncher');
  const drawer = document.getElementById('rcsAiDrawer');
  const close = document.getElementById('rcsAiClose');
  const newChat = document.getElementById('rcsAiNewChat');
  const backdrop = document.getElementById('rcsAiBackdrop');
  const form = document.getElementById('rcsAiForm');
  const input = document.getElementById('rcsAiInput');
  const messages = document.getElementById('rcsAiMessages');
  const sendButton = form ? form.querySelector('button[type="submit"]') : null;
  let conversationId = null;
  let requestGeneration = 0;
  if (!launcher || !drawer || !form) return;
  function openDrawer() {
    drawer.classList.add('open');
    if (backdrop) backdrop.classList.add('open');
    document.body.style.overflow = 'hidden';
    input.focus();
  }
  function closeDrawer() {
    drawer.classList.remove('open');
    if (backdrop) backdrop.classList.remove('open');
    document.body.style.overflow = '';
  }
  launcher.addEventListener('click', openDrawer);
  close.addEventListener('click', closeDrawer);
  if (backdrop) backdrop.addEventListener('click', closeDrawer);
  function resetConversation() {
    conversationId = null;
    requestGeneration += 1;
    messages.innerHTML =
      '<div class="rcs-ai-welcome">' +
      '<span class="rcs-ai-welcome-sparkle"><i class="bi bi-stars"></i></span>' +
      '<h5>گفتگوی جدید آماده است</h5>' +
      '<p>سؤال خود را درباره طرح، پروژه یا زیرپروژه بنویسید.</p>' +
      '</div>';
    input.value = '';
    input.disabled = false;
    input.focus();
  }
  if (newChat) newChat.addEventListener('click', resetConversation);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer.classList.contains('open')) closeDrawer();
  });
  function addMessage(text, type) {
    const node = document.createElement('div');
    node.className = 'rcs-ai-message ' + type;
    if (type.indexOf('assistant') !== -1 && window.renderAiMarkdown) {
      window.renderAiMarkdown(node, text);
    } else {
      node.textContent = text;
    }
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
    return node;
  }
  function addActionCard(action) {
    const card = document.createElement('div');
    card.className = 'rcs-ai-action-card';
    card.innerHTML =
      '<div class="rcs-ai-action-title"><i class="bi bi-pencil-square"></i> پیش‌نمایش تغییر</div>' +
      '<div class="rcs-ai-action-row"><span>فیلد</span><strong></strong></div>' +
      '<div class="rcs-ai-action-row"><span>مقدار فعلی</span><del></del></div>' +
      '<div class="rcs-ai-action-row"><span>مقدار جدید</span><b></b></div>' +
      '<button type="button" class="rcs-ai-confirm"><i class="bi bi-check2"></i> تأیید و ذخیره تغییر</button>' +
      '<small class="rcs-ai-action-expiry"><i class="bi bi-clock"></i> این پیش‌نمایش تا ۱۰ دقیقه معتبر است</small>';
    card.querySelector('strong').textContent = action.field_label || action.field;
    card.querySelector('del').textContent = action.old_value || 'خالی';
    card.querySelector('b').textContent = action.new_value || 'خالی';
    const button = card.querySelector('button');
    button.addEventListener('click', async () => {
      button.disabled = true;
      button.innerHTML = '<i class="bi bi-hourglass-split"></i> در حال ذخیره...';
      try {
        const response = await fetch('/ai-assistant/action/confirm/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
          body: JSON.stringify({action_id: action.action_id})
        });
        const data = await response.json();
        if (!data.ok) throw new Error(data.error || 'خطا در ذخیره تغییر');
        button.className = 'rcs-ai-confirm done';
        button.innerHTML = '<i class="bi bi-check-circle-fill"></i> تغییر با موفقیت ذخیره شد';
        addMessage(data.message, 'assistant');
      } catch (error) {
        button.disabled = false;
        button.innerHTML = '<i class="bi bi-arrow-repeat"></i> تلاش دوباره';
        addMessage(error.message, 'error');
      }
    });
    messages.appendChild(card);
    messages.scrollTop = messages.scrollHeight;
  }
  function addOptions(options) {
    if (!Array.isArray(options) || !options.length) return;
    const wrap = document.createElement('div');
    wrap.className = 'rcs-ai-answer-options';
    options.forEach((label) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.addEventListener('click', () => {
        input.value = label;
        form.requestSubmit();
      });
      wrap.appendChild(button);
    });
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }
  function csrf() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
  }
  document.querySelectorAll('[data-ai-prompt]').forEach((button) => {
    button.addEventListener('click', () => {
      input.value = button.getAttribute('data-ai-prompt') || '';
      input.focus();
      form.requestSubmit();
    });
  });
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    const generation = requestGeneration;
    addMessage(text, 'user'); input.value = ''; input.disabled = true;
    const originalButtonHtml = sendButton ? sendButton.innerHTML : '';
    if (sendButton) {
      sendButton.disabled = true;
      sendButton.setAttribute('aria-busy', 'true');
      sendButton.innerHTML = '<i class="bi bi-hourglass-split"></i>';
    }
    const loading = addMessage('در حال بررسی اطلاعات سامانه...', 'assistant rcs-ai-loading');
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 180000);
    try {
      const response = await fetch('/ai-assistant/chat/', {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrf()},
        signal: controller.signal,
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          context_type: window.location.pathname.slice(0, 30),
          use_web: Boolean(document.getElementById('rcsAiWeb')?.checked)
        })
      });
      const responseText = await response.text();
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        throw new Error(`خطای سرویس (HTTP ${response.status})`);
      }
      loading.remove();
      if (generation !== requestGeneration) return;
      if (!response.ok) {
        addMessage(data.error || `خطای سرویس (HTTP ${response.status})`, 'error');
        return;
      }
      addMessage(data.ok ? data.answer : (data.error || 'خطای نامشخص'), data.ok ? 'assistant' : 'error');
      if (data.ok) {
        conversationId = data.conversation_id || conversationId;
        addOptions(data.options);
        if (data.action) addActionCard(data.action);
      }
    } catch (error) {
      loading.remove();
      if (error.name === 'AbortError') {
        addMessage('پاسخ‌گویی بیش از زمان مجاز طول کشید. لطفاً دوباره تلاش کنید.', 'error');
      } else if (error.message && error.message.startsWith('خطای سرویس')) {
        addMessage(error.message, 'error');
      } else {
        addMessage('ارتباط با دستیار برقرار نشد. تنظیمات سرویس هوش مصنوعی را بررسی کنید.', 'error');
      }
    } finally {
      window.clearTimeout(timeout);
      input.disabled = false;
      if (sendButton) {
        sendButton.disabled = false;
        sendButton.removeAttribute('aria-busy');
        sendButton.innerHTML = originalButtonHtml;
      }
      input.focus();
    }
  });
})();
