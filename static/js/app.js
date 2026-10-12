/**
 * app.js — HealthBridge Modern Client-Side Controller
 * Powers Chart.js dashboards, What-If simulator, Validation Lab, and HealthBridge Assistant.
 */

document.addEventListener('DOMContentLoaded', () => {
  // ---------------------------------------------------------------------------
  // 1. Mobile Navigation Drawer
  // ---------------------------------------------------------------------------
  const mobileNavToggle = document.getElementById('mobileNavToggle');
  const mobileNavDrawer = document.getElementById('mobileNavDrawer');
  if (mobileNavToggle && mobileNavDrawer) {
    mobileNavToggle.addEventListener('click', () => {
      mobileNavDrawer.classList.toggle('hidden');
    });
  }

  // User Profile Avatar Menu Toggle
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userMenuDropdown = document.getElementById('userMenuDropdown');
  if (userMenuBtn && userMenuDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userMenuDropdown.classList.toggle('hidden');
    });
    document.addEventListener('click', (e) => {
      if (!userMenuDropdown.contains(e.target) && !userMenuBtn.contains(e.target)) {
        userMenuDropdown.classList.add('hidden');
      }
    });
  }

  // ---------------------------------------------------------------------------
  // 2. Generic Modal Dialog Controller
  // ---------------------------------------------------------------------------
  document.addEventListener('click', (e) => {
    // Open modal
    const openBtn = e.target.closest('[data-modal-open]');
    if (openBtn) {
      const modalId = openBtn.getAttribute('data-modal-open');
      const targetModal = document.getElementById(modalId);
      if (targetModal) {
        targetModal.classList.remove('hidden');
        targetModal.classList.add('grid');
        const firstInput = targetModal.querySelector('input:not([type=hidden]), select');
        if (firstInput) setTimeout(() => firstInput.focus(), 50);
      }
      return;
    }

    // Close modal via close button
    const closeBtn = e.target.closest('[data-modal-close]');
    if (closeBtn) {
      const modal = closeBtn.closest('.fixed');
      if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('grid');
      }
      return;
    }

    // Close modal on backdrop click
    if (e.target.classList.contains('fixed') && !e.target.closest('.rounded-2xl')) {
      e.target.classList.add('hidden');
      e.target.classList.remove('grid');
    }
  });

  // ---------------------------------------------------------------------------
  // 3. Chart.js Initializations
  // ---------------------------------------------------------------------------
  if (window.Chart) {
    Chart.defaults.font.family = '"Plus Jakarta Sans", sans-serif';
    Chart.defaults.color = '#94a3b8';

    initDashboardCharts();
    initAnalyticsCharts();
  }

  // ---------------------------------------------------------------------------
  // 4. Interactive What-If Simulator
  // ---------------------------------------------------------------------------
  initWhatIfSimulator();

  // ---------------------------------------------------------------------------
  // 5. Interactive Validation Lab
  // ---------------------------------------------------------------------------
  initValidationLab();

  // ---------------------------------------------------------------------------
  // 6. Floating HealthBridge Assistant Chatbot
  // ---------------------------------------------------------------------------
  initChatbot();
});

// =============================================================================
// Chart Helper Implementations
// =============================================================================
function initDashboardCharts() {
  const trendEl = document.getElementById('dashboardTrendChart');
  if (!trendEl || !trendEl.dataset.series) return;

  try {
    const series = JSON.parse(trendEl.dataset.series);
    const ctx = trendEl.getContext('2d');

    // Create subtle gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, 'rgba(16, 185, 129, 0.25)');
    gradient.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

    new Chart(trendEl, {
      type: 'line',
      data: {
        labels: series.labels,
        datasets: [
          {
            label: 'Composite Score',
            data: series.scores,
            borderColor: '#10b981',
            backgroundColor: gradient,
            borderWidth: 2.5,
            pointBackgroundColor: '#10b981',
            pointRadius: 4,
            pointHoverRadius: 6,
            fill: true,
            tension: 0.35,
          },
          {
            label: '3-Day Rolling Moving Avg',
            data: series.ma_scores,
            borderColor: '#06b6d4',
            borderWidth: 2,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false,
            tension: 0.35,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: {
          legend: {
            position: 'top',
            labels: {
              boxWidth: 12,
              color: '#cbd5e1',
              font: { size: 12, weight: 600 },
            },
          },
          tooltip: {
            backgroundColor: '#1e293b',
            titleColor: '#f8fafc',
            bodyColor: '#cbd5e1',
            borderColor: '#334155',
            borderWidth: 1,
            padding: 10,
            cornerRadius: 10,
          },
        },
        scales: {
          y: {
            min: 0,
            max: 105,
            title: { display: true, text: 'Score (0–100)', color: '#64748b' },
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            ticks: { color: '#94a3b8' },
          },
          x: {
            grid: { display: false },
            ticks: { color: '#94a3b8' },
          },
        },
      },
    });
  } catch (e) {
    console.error('Error initializing dashboard chart:', e);
  }
}

function initAnalyticsCharts() {
  // 1. Multi-Indicator Daily Timeline
  const multiEl = document.getElementById('analyticsMultiChart');
  if (multiEl && multiEl.dataset.series) {
    try {
      const data = JSON.parse(multiEl.dataset.series);
      new Chart(multiEl, {
        type: 'line',
        data: {
          labels: data.labels,
          datasets: [
            {
              label: 'Sleep (hours)',
              data: data.sleep,
              borderColor: '#818cf8',
              backgroundColor: 'rgba(129, 140, 248, 0.1)',
              borderWidth: 2,
              yAxisID: 'ySleep',
              tension: 0.3,
            },
            {
              label: 'Activity (mins)',
              data: data.activity,
              borderColor: '#34d399',
              backgroundColor: 'rgba(52, 211, 153, 0.1)',
              borderWidth: 2,
              yAxisID: 'yActivity',
              tension: 0.3,
            },
            {
              label: 'Hydration (L)',
              data: data.water,
              borderColor: '#22d3ee',
              backgroundColor: 'rgba(34, 211, 238, 0.1)',
              borderWidth: 2,
              yAxisID: 'yWater',
              tension: 0.3,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#cbd5e1', boxWidth: 12 } },
          },
          scales: {
            ySleep: {
              position: 'left',
              min: 0,
              max: 14,
              title: { display: true, text: 'Sleep (hrs)', color: '#818cf8' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
            },
            yActivity: {
              position: 'right',
              min: 0,
              max: 120,
              title: { display: true, text: 'Activity (mins)', color: '#34d399' },
              grid: { display: false },
            },
            yWater: { display: false, min: 0, max: 6 },
            x: { grid: { display: false } },
          },
        },
      });
    } catch (e) {
      console.error('Error initializing analytics multi chart:', e);
    }
  }

  // 2. Lifestyle Balance Radar Chart
  const radarEl = document.getElementById('analyticsRadarChart');
  if (radarEl && radarEl.dataset.radar) {
    try {
      const radarData = JSON.parse(radarEl.dataset.radar);
      new Chart(radarEl, {
        type: 'radar',
        data: {
          labels: ['Sleep Fulfillment', 'Physical Activity', 'Hydration', 'Mood Balance', 'Stress Resilience'],
          datasets: [
            {
              label: 'Balance Wheel (%)',
              data: radarData,
              backgroundColor: 'rgba(16, 185, 129, 0.2)',
              borderColor: '#10b981',
              pointBackgroundColor: '#10b981',
              pointBorderColor: '#fff',
              pointRadius: 4,
              borderWidth: 2,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
          },
          scales: {
            r: {
              min: 0,
              max: 100,
              ticks: { stepSize: 25, backdropColor: 'transparent', color: '#64748b' },
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              angleLines: { color: 'rgba(255, 255, 255, 0.08)' },
              pointLabels: {
                color: '#e2e8f0',
                font: { size: 11, weight: 600 },
              },
            },
          },
        },
      });
    } catch (e) {
      console.error('Error initializing analytics radar chart:', e);
    }
  }
}

// =============================================================================
// What-If Simulator
// =============================================================================
function initWhatIfSimulator() {
  const sleepInput = document.getElementById('simSleep');
  const actInput = document.getElementById('simAct');
  const waterInput = document.getElementById('simWater');
  const scoreOutput = document.getElementById('simScoreOutput');

  if (!sleepInput || !actInput || !waterInput || !scoreOutput) return;

  function recalculate() {
    const s = parseFloat(sleepInput.value) || 0;
    const a = parseFloat(actInput.value) || 0;
    const w = parseFloat(waterInput.value) || 0;

    // Configurable standard targets (8h, 30m, 2L) & weights (0.40, 0.35, 0.25)
    const sNorm = Math.min(s / 8.0, 1.0) * 100 * 0.40;
    const aNorm = Math.min(a / 30.0, 1.0) * 100 * 0.35;
    const wNorm = Math.min(w / 2.0, 1.0) * 100 * 0.25;

    const total = Math.round((sNorm + aNorm + wNorm) * 10) / 10;
    scoreOutput.textContent = total.toFixed(1);

    const sVal = document.getElementById('simSleepVal');
    const aVal = document.getElementById('simActVal');
    const wVal = document.getElementById('simWaterVal');

    if (sVal) sVal.textContent = s + ' hrs';
    if (aVal) aVal.textContent = a + ' mins';
    if (wVal) wVal.textContent = w + ' L';
  }

  [sleepInput, actInput, waterInput].forEach(inp => inp.addEventListener('input', recalculate));
  recalculate();
}

// =============================================================================
// Validation Lab for Judges & Evaluators
// =============================================================================
function initValidationLab() {
  const labButtons = document.querySelectorAll('[data-test-case]');
  const resultBox = document.getElementById('validationResultBox');
  if (!labButtons.length || !resultBox) return;

  labButtons.forEach(btn => {
    btn.addEventListener('click', async () => {
      const testCase = btn.dataset.testCase;
      resultBox.innerHTML = `
        <div class="flex items-center gap-2 text-slate-400 text-xs">
          <div class="w-3.5 h-3.5 border-2 border-brand-500 border-t-transparent rounded-full animate-spin"></div>
          <span>Testing domain invariant validation rule...</span>
        </div>`;

      try {
        const resp = await fetch('/api/test-validation', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario: testCase }),
        });
        const data = await resp.json();

        if (data.rejected) {
          resultBox.innerHTML = `
            <div class="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/30 text-rose-200 text-xs space-y-1.5">
              <div class="flex items-center gap-1.5 font-bold text-rose-400">
                <span>🛡️ STATUS: REJECTED (ZERO-TOLERANCE ENFORCED)</span>
              </div>
              <p><strong>Scenario:</strong> ${data.scenario_title}</p>
              <p><strong>Payload Sent:</strong> <code class="bg-surface-900 px-1.5 py-0.5 rounded text-amber-300 font-mono text-[11px]">${JSON.stringify(data.payload)}</code></p>
              <p class="text-rose-300 font-medium"><strong>Exception Raised:</strong> ${data.error_message}</p>
            </div>`;
        } else {
          resultBox.innerHTML = `
            <div class="p-3.5 rounded-xl bg-brand-950/40 border border-brand-500/30 text-brand-200 text-xs space-y-1.5">
              <div class="flex items-center gap-1.5 font-bold text-brand-400">
                <span>✅ STATUS: ACCEPTED</span>
              </div>
              <p><strong>Scenario:</strong> ${data.scenario_title}</p>
              <p class="text-emerald-300">Valid record satisfied domain invariants and was admitted.</p>
            </div>`;
        }
      } catch (e) {
        resultBox.innerHTML = `<div class="text-rose-400 text-xs">Error executing test case: ${e.message}</div>`;
      }
    });
  });
}

// =============================================================================
// HealthBridge Assistant Chatbot
// =============================================================================
function initChatbot() {
  const toggleBtn = document.getElementById('chatToggleBtn');
  const chatBox = document.getElementById('chatWidgetBox');
  const closeBtn = document.getElementById('chatCloseBtn');
  const form = document.getElementById('chatInputForm');
  const input = document.getElementById('chatTextInput');
  const log = document.getElementById('chatMessagesLog');
  const quickBtns = document.querySelectorAll('.chat-quick-btn');

  if (!toggleBtn || !chatBox || !form || !input || !log) return;

  let isSubmitting = false;

  const appendMsg = (text, isUser = false) => {
    const bubble = document.createElement('div');
    bubble.className = isUser
      ? 'p-3 rounded-2xl rounded-tr-sm bg-brand-600 text-white leading-relaxed ml-6 shadow-md'
      : 'p-3 rounded-2xl rounded-tl-sm bg-surface-800 border border-slate-700/60 text-slate-200 leading-relaxed mr-6 shadow-md';
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  };

  toggleBtn.addEventListener('click', () => {
    chatBox.classList.toggle('hidden');
    chatBox.classList.toggle('flex');
    if (!chatBox.classList.contains('hidden')) {
      input.focus();
    }
  });

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      chatBox.classList.add('hidden');
      chatBox.classList.remove('flex');
    });
  }

  const sendQuery = async (queryText) => {
    const q = queryText.trim();
    if (!q || isSubmitting) return;

    isSubmitting = true;
    appendMsg(q, true);
    input.value = '';

    const thinkingBubble = document.createElement('div');
    thinkingBubble.className = 'p-2.5 rounded-xl bg-surface-800 text-slate-400 text-xs flex items-center gap-2 mr-6';
    thinkingBubble.innerHTML = `
      <div class="w-3 h-3 border-2 border-brand-400 border-t-transparent rounded-full animate-spin"></div>
      <span>Consulting HealthBridge intelligence engine...</span>
    `;
    log.appendChild(thinkingBubble);
    log.scrollTop = log.scrollHeight;

    try {
      const resp = await fetch('/api/chatbot', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q }),
      });
      const data = await resp.json();
      thinkingBubble.remove();
      appendMsg(data.reply || 'No response available.', false);
    } catch (e) {
      thinkingBubble.remove();
      appendMsg('Unable to connect to assistant service. Please check server status.', false);
    } finally {
      isSubmitting = false;
    }
  };

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    sendQuery(input.value);
  });

  quickBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-q');
      if (query) sendQuery(query);
    });
  });
}
