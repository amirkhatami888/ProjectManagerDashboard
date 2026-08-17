(function () {
  function appendText(parent, value) {
    // Create a text node explicitly so user/assistant content is never parsed
    // as markup or HTML.
    parent.appendChild(document.createTextNode(String(value)));
  }

  function externalUrl(value) {
    try {
      const url = new URL(value);
      return (url.protocol === 'http:' || url.protocol === 'https:') ? url.href : null;
    } catch (error) {
      return null;
    }
  }

  function inline(parent, value) {
    const pattern = /(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[[^\]]+\]\(https?:\/\/[^)\s]+\)|\*[^*]+\*|_[^_]+_)/g;
    let last = 0;
    let match;
    while ((match = pattern.exec(value))) {
      if (match.index > last) appendText(parent, value.slice(last, match.index));
      const token = match[0];
      let node;
      if (token.startsWith('**') || token.startsWith('__')) {
        node = document.createElement('strong');
        appendText(node, token.slice(2, -2));
      } else if (token.startsWith('`')) {
        node = document.createElement('code');
        appendText(node, token.slice(1, -1));
      } else if (token.startsWith('[')) {
        const link = token.match(/^\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)$/);
        const href = link && externalUrl(link[2]);
        if (!href) {
          appendText(parent, token);
          last = pattern.lastIndex;
          continue;
        }
        node = document.createElement('a');
        appendText(node, link[1]);
        node.href = href;
        node.target = '_blank';
        node.rel = 'noopener noreferrer';
      } else {
        node = document.createElement('em');
        appendText(node, token.slice(1, -1));
      }
      parent.appendChild(node);
      last = pattern.lastIndex;
    }
    if (last < value.length) appendText(parent, value.slice(last));
  }

  window.renderAiMarkdown = function (container, markdown) {
    container.replaceChildren();
    const lines = String(markdown || '').replace(/\r\n?/g, '\n').split('\n');
    let list = null;
    let listType = null;
    let code = false;
    let codeLines = [];

    function closeList() {
      if (list) container.appendChild(list);
      list = null;
      listType = null;
    }
    function closeCode() {
      if (!codeLines.length) return;
      const pre = document.createElement('pre');
      const codeNode = document.createElement('code');
      codeNode.textContent = codeLines.join('\n');
      pre.appendChild(codeNode);
      container.appendChild(pre);
      codeLines = [];
    }

    lines.forEach((line) => {
      if (line.trim().startsWith('```')) {
        closeList();
        if (code) closeCode();
        code = !code;
        return;
      }
      if (code) {
        codeLines.push(line);
        return;
      }
      if (!line.trim()) {
        closeList();
        return;
      }

      const heading = line.match(/^\s*(#{1,3})\s+(.+)$/);
      const bullet = line.match(/^\s*[-*]\s+(.+)$/);
      const numbered = line.match(/^\s*\d+[.)]\s+(.+)$/);
      if (heading) {
        closeList();
        const h = document.createElement(`h${Math.min(heading[1].length + 2, 5)}`);
        inline(h, heading[2]);
        container.appendChild(h);
      } else if (bullet || numbered) {
        const type = bullet ? 'ul' : 'ol';
        if (!list || listType !== type) {
          closeList();
          list = document.createElement(type);
          listType = type;
        }
        const item = document.createElement('li');
        inline(item, (bullet || numbered)[1]);
        list.appendChild(item);
      } else {
        closeList();
        const paragraph = document.createElement('p');
        inline(paragraph, line);
        container.appendChild(paragraph);
      }
    });
    if (code) closeCode();
    closeList();
  };
})();
