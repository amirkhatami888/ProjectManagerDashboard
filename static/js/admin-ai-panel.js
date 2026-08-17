(function () {
    const form = document.getElementById('adminAiForm');
    const input = document.getElementById('adminAiInput');
    const messages = document.getElementById('adminAiMessages');
    if (!form || !input || !messages) return;

    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
    const fullAssistant = document.getElementById('adminAiOpenFull');

    function addMessage(text, type) {
        const empty = messages.querySelector('.admin-ai-panel__empty');
        if (empty) empty.remove();
        const node = document.createElement('div');
        node.className = 'admin-ai-message admin-ai-message--' + type;
        node.textContent = text;
        messages.appendChild(node);
        messages.scrollTop = messages.scrollHeight;
        return node;
    }

    async function ask(question) {
        const text = question.trim();
        if (!text) return;
        addMessage(text, 'user');
        input.value = '';
        input.disabled = true;
        const send = form.querySelector('button');
        send.disabled = true;
        const loading = addMessage('در حال بررسی داده‌های مجاز سامانه…', 'assistant');

        try {
            const response = await fetch('/ai-assistant/chat/', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
                body: JSON.stringify({message: text})
            });
            const data = await response.json();
            loading.remove();
            addMessage(data.ok ? data.answer : (data.error || 'دستیار در حال حاضر نتوانست پاسخ دهد.'), data.ok ? 'assistant' : 'error');
        } catch (error) {
            loading.remove();
            addMessage('ارتباط با دستیار برقرار نشد. تنظیمات سرویس هوش مصنوعی را بررسی کنید.', 'error');
        } finally {
            input.disabled = false;
            send.disabled = false;
            input.focus();
        }
    }

    form.addEventListener('submit', function (event) {
        event.preventDefault();
        ask(input.value);
    });

    document.querySelectorAll('[data-admin-ai-prompt]').forEach(function (button) {
        button.addEventListener('click', function () {
            ask(button.getAttribute('data-admin-ai-prompt') || '');
        });
    });

    if (fullAssistant) {
        fullAssistant.addEventListener('click', function () {
            const launcher = document.getElementById('rcsAiLauncher');
            if (launcher) launcher.click();
        });
    }
})();
