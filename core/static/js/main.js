/* ═══════════════════════════════════════════════════════
   TRAINO v2 — main.js
   Utility functions used across the entire platform.
═══════════════════════════════════════════════════════ */

'use strict';

/* ── DOM READY ────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', function () {
  initToasts();
  initBackToTop();
  initPasswordToggles();
  initStarRating();
  initCharCounters();
  initChatbot();
  initFilePreview();
  initSearchClear();
});

/* ── TOAST AUTO-DISMISS ───────────────────────────────── */
function initToasts() {
  document.querySelectorAll('.t-toast').forEach(function (toast) {
    setTimeout(function () {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all .35s ease';
      setTimeout(function () { toast.remove(); }, 350);
    }, 5000);
  });
}

/* ── BACK TO TOP ──────────────────────────────────────── */
function initBackToTop() {
  var btn = document.getElementById('btt');
  if (!btn) return;
  window.addEventListener('scroll', function () {
    btn.classList.toggle('show', window.scrollY > 400);
  });
  btn.addEventListener('click', function () {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

/* ── PASSWORD SHOW/HIDE ───────────────────────────────── */
function initPasswordToggles() {
  document.querySelectorAll('.pw-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.target;
      var input = targetId
        ? document.getElementById(targetId)
        : btn.previousElementSibling;
      if (!input) return;
      var icon = btn.querySelector('i');
      if (input.type === 'password') {
        input.type = 'text';
        if (icon) { icon.classList.replace('fa-eye', 'fa-eye-slash'); }
      } else {
        input.type = 'password';
        if (icon) { icon.classList.replace('fa-eye-slash', 'fa-eye'); }
      }
    });
  });
}

/* Inline toggle (used in templates directly) */
function togglePw(inputId, iconId) {
  var f = document.getElementById(inputId);
  var e = document.getElementById(iconId);
  if (!f) return;
  if (f.type === 'password') {
    f.type = 'text';
    if (e) { e.classList.replace('fa-eye', 'fa-eye-slash'); }
  } else {
    f.type = 'password';
    if (e) { e.classList.replace('fa-eye-slash', 'fa-eye'); }
  }
}

/* ── PASSWORD STRENGTH METER ──────────────────────────── */
function checkStrength(pw, barId) {
  var bar = document.getElementById(barId);
  if (!bar) return;
  var fill = bar.querySelector('.fill');
  var score = 0;
  if (pw.length >= 8)              score++;
  if (/[A-Z]/.test(pw))           score++;
  if (/[0-9]/.test(pw))           score++;
  if (/[^A-Za-z0-9]/.test(pw))   score++;
  var map = {
    0: ['0%',   '#E5E7EB', ''],
    1: ['25%',  '#DC2626', 'Weak'],
    2: ['50%',  '#D97706', 'Fair'],
    3: ['75%',  '#2563EB', 'Good'],
    4: ['100%', '#16A34A', 'Strong'],
  };
  if (fill) {
    fill.style.width      = map[score][0];
    fill.style.background = map[score][1];
  }
  var label = document.getElementById(barId + '-label');
  if (label) {
    label.textContent = map[score][2];
    label.style.color = map[score][1];
  }
}

/* ── STAR RATING (interactive) ────────────────────────── */
function initStarRating() {
  document.querySelectorAll('.star-input').forEach(function (container) {
    var labels = container.querySelectorAll('label');
    var radio  = container.querySelectorAll('input[type="radio"]');

    function updateStars(val) {
      labels.forEach(function (lbl, i) {
        lbl.classList.toggle('active', i < val);
      });
    }

    labels.forEach(function (lbl, idx) {
      lbl.addEventListener('mouseover', function () { updateStars(idx + 1); });
      lbl.addEventListener('mouseout', function () {
        var checked = container.querySelector('input:checked');
        updateStars(checked ? parseInt(checked.value) : 0);
      });
      lbl.addEventListener('click', function () { updateStars(idx + 1); });
    });

    // Set initial state
    var initial = container.querySelector('input:checked');
    if (initial) updateStars(parseInt(initial.value));
  });
}

/* ── CHARACTER COUNTERS ───────────────────────────────── */
function initCharCounters() {
  document.querySelectorAll('[data-maxlen]').forEach(function (input) {
    var max     = parseInt(input.dataset.maxlen);
    var counterId = input.dataset.counter;
    var counter = counterId ? document.getElementById(counterId) : null;

    function update() {
      var remaining = max - input.value.length;
      if (counter) {
        counter.textContent = remaining + ' characters remaining';
        counter.style.color = remaining < 20 ? '#DC2626' : '#6B7280';
      }
      if (input.value.length > max) {
        input.value = input.value.substring(0, max);
      }
    }

    input.addEventListener('input', update);
    update();
  });
}

/* ── CONFIRM DELETE ───────────────────────────────────── */
function confirmDelete(message) {
  return confirm(message || 'Are you sure you want to delete this? This action cannot be undone.');
}

/* ── FILE PREVIEW ─────────────────────────────────────── */
function initFilePreview() {
  document.querySelectorAll('input[type="file"][data-preview]').forEach(function (input) {
    var previewId = input.dataset.preview;
    var preview   = document.getElementById(previewId);
    if (!preview) return;

    input.addEventListener('change', function () {
      var file = this.files[0];
      if (!file) return;

      if (file.type.startsWith('image/')) {
        var reader = new FileReader();
        reader.onload = function (e) {
          preview.src = e.target.result;
          preview.style.display = 'block';
        };
        reader.readAsDataURL(file);
      } else {
        preview.style.display = 'none';
      }

      // Show filename
      var nameEl = document.getElementById(previewId + '-name');
      if (nameEl) nameEl.textContent = file.name;
    });
  });
}

/* ── SEARCH CLEAR BUTTON ──────────────────────────────── */
function initSearchClear() {
  document.querySelectorAll('[data-clear-search]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = btn.dataset.clearSearch;
      var input    = document.getElementById(targetId);
      if (input) { input.value = ''; input.focus(); }
    });
  });
}

/* ── CSRF HELPER (for AJAX) ───────────────────────────── */
function getCSRF() {
  var cookie = document.cookie.split(';');
  for (var i = 0; i < cookie.length; i++) {
    var c = cookie[i].trim();
    if (c.startsWith('csrftoken=')) return c.substring('csrftoken='.length);
  }
  return '';
}

/* ── AJAX POST HELPER ─────────────────────────────────── */
async function postJSON(url, data) {
  try {
    var res = await fetch(url, {
      method:  'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken':  getCSRF(),
      },
      body: JSON.stringify(data),
    });
    return await res.json();
  } catch (e) {
    console.error('postJSON error:', e);
    return { error: 'Network error' };
  }
}

/* ── CHATBOT ──────────────────────────────────────────── */
function initChatbot() {
  var fab    = document.getElementById('chatbotFab');
  var win    = document.getElementById('chatbotWindow');
  var closeBtn = document.getElementById('chatbotClose');
  var input  = document.getElementById('chatbotInput');
  var sendBtn = document.getElementById('chatbotSend');
  var messages = document.getElementById('chatbotMessages');

  if (!fab || !win) return;

  fab.addEventListener('click', function () {
    win.classList.toggle('open');
    if (win.classList.contains('open') && messages.children.length === 0) {
      addBotMessage('Hi! I\'m Traino Assistant. Ask me anything about courses, enrollment, or the platform.');
    }
  });

  if (closeBtn) closeBtn.addEventListener('click', function () { win.classList.remove('open'); });

  function addBotMessage(text) {
    var div = document.createElement('div');
    div.className = 'cbot-bubble bot';
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function addUserMessage(text) {
    var div = document.createElement('div');
    div.className = 'cbot-bubble user';
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  async function sendMessage() {
    if (!input) return;
    var text = input.value.trim();
    if (!text) return;
    addUserMessage(text);
    input.value = '';

    try {
      var data = await postJSON('/chatbot/ask/', { message: text });
      addBotMessage(data.answer || 'I\'m not sure about that. Please contact our support team.');
    } catch {
      addBotMessage('Sorry, I\'m having trouble responding. Please try again later.');
    }
  }

  if (sendBtn) sendBtn.addEventListener('click', sendMessage);
  if (input) {
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
    });
  }
}

/* ── PROGRESS BAR ANIMATION ───────────────────────────── */
function animateProgress() {
  document.querySelectorAll('.t-progress-bar[data-width]').forEach(function (bar) {
    var target = parseInt(bar.dataset.width) || 0;
    bar.style.width = '0%';
    setTimeout(function () { bar.style.width = target + '%'; }, 200);
  });
}
window.addEventListener('load', animateProgress);

/* ── IMAGE LAZY LOAD ──────────────────────────────────── */
if ('IntersectionObserver' in window) {
  var lazyImages = document.querySelectorAll('img[data-src]');
  var imgObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        var img = entry.target;
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
        imgObserver.unobserve(img);
      }
    });
  });
  lazyImages.forEach(function (img) { imgObserver.observe(img); });
}

/* ── CURRICULUM TOGGLE ────────────────────────────────── */
document.addEventListener('click', function (e) {
  var header = e.target.closest('.cs-header');
  if (!header) return;
  var body = header.nextElementSibling;
  var icon = header.querySelector('.cs-toggle-icon');
  if (!body) return;
  var isOpen = body.style.display === 'block';
  body.style.display = isOpen ? 'none' : 'block';
  if (icon) icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(180deg)';
});

/* ── COPY TO CLIPBOARD ────────────────────────────────── */
function copyToClipboard(text, btnEl) {
  navigator.clipboard.writeText(text).then(function () {
    if (btnEl) {
      var original = btnEl.textContent;
      btnEl.textContent = 'Copied!';
      setTimeout(function () { btnEl.textContent = original; }, 2000);
    }
  });
}

/* ── EXPOSE GLOBALLY ──────────────────────────────────── */
window.Traino = {
  togglePw,
  checkStrength,
  confirmDelete,
  copyToClipboard,
  getCSRF,
  postJSON,
};