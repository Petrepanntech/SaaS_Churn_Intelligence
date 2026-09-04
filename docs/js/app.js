/**
 * SaaS Customer Churn & Revenue Retention Intelligence
 * Dashboard Application Logic & Chart Rendering
 * Author: Peter Akpan (Petre Pann) - Pann Labs
 */

document.addEventListener('DOMContentLoaded', () => {
  let telemetryData = null;
  let activeFilter = 'All';
  let activeTier = 'All';
  let searchQuery = '';

  // Initialize
  fetchTelemetry();

  async function fetchTelemetry() {
    try {
      const res = await fetch('data/telemetry.json');
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      telemetryData = await res.json();
      
      renderKPIs(telemetryData.summary);
      renderCharts(telemetryData);
      renderTable(telemetryData.customers);
      initTableListeners();
      initSqlWorkbench(telemetryData.sql_catalog);
    } catch (err) {
      console.error('Failed to load telemetry:', err);
      document.getElementById('kpi-container').innerHTML = `
        <div style="grid-column: 1/-1; padding: 20px; background: rgba(239,68,68,0.1); border: 1px solid #ef4444; border-radius: 8px; color: #fca5a5;">
          <strong>Error Loading Telemetry Data:</strong> Please ensure telemetry.json is present in data/ folder.
        </div>
      `;
    }
  }

  function formatCurrency(val) {
    return '$' + Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function renderKPIs(summary) {
    document.getElementById('val-active-mrr').textContent = formatCurrency(summary.active_mrr);
    document.getElementById('val-active-accts').textContent = `${summary.active_accounts.toLocaleString()} active (${summary.total_customers.toLocaleString()} total)`;

    document.getElementById('val-churn-rate').textContent = `${summary.churn_rate_pct}%`;
    document.getElementById('val-churn-accts').textContent = `${summary.churned_accounts.toLocaleString()} total exits`;

    document.getElementById('val-risk-mrr').textContent = formatCurrency(summary.high_risk_mrr);
    document.getElementById('val-risk-accts').textContent = `${summary.high_risk_accounts.toLocaleString()} accounts in critical band`;

    document.getElementById('val-avg-tenure').textContent = `${summary.avg_tenure_months} mo`;
    document.getElementById('val-adoption').textContent = `${summary.avg_feature_adoption}% adoption avg`;
  }

  // Pure Canvas Chart Renderers
  function renderCharts(data) {
    drawCohortLineChart('canvas-cohort', data.cohorts.slice(-14));
    drawContractBarChart('canvas-contract', data.contracts);
    drawTierBarChart('canvas-tier', data.tiers);
  }

  function drawCohortLineChart(canvasId, cohorts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    const height = canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
    const padX = 45;
    const padY = 30;

    ctx.clearRect(0, 0, w, h);

    // Axes & grid
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padY + (i * (h - padY * 2) / 4);
      ctx.beginPath();
      ctx.moveTo(padX, y);
      ctx.lineTo(w - 20, y);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px sans-serif';
      ctx.fillText(`${100 - i * 25}%`, 10, y + 3);
    }

    if (!cohorts || cohorts.length === 0) return;

    const stepX = (w - padX - 20) / (cohorts.length - 1);
    const points = cohorts.map((c, i) => {
      const x = padX + i * stepX;
      const rate = c.retention_rate_pct || 75;
      const y = padY + ((100 - rate) / 100) * (h - padY * 2);
      return { x, y, cohort: c.signup_cohort, rate };
    });

    // Gradient fill under curve
    const grad = ctx.createLinearGradient(0, padY, 0, h - padY);
    grad.addColorStop(0, 'rgba(0, 242, 254, 0.35)');
    grad.addColorStop(1, 'rgba(0, 242, 254, 0.0)');

    ctx.beginPath();
    ctx.moveTo(points[0].x, h - padY);
    points.forEach(pt => ctx.lineTo(pt.x, pt.y));
    ctx.lineTo(points[points.length - 1].x, h - padY);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    points.forEach(pt => ctx.lineTo(pt.x, pt.y));
    ctx.strokeStyle = '#00f2fe';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Data points & labels
    points.forEach((pt, idx) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = '#0a0d14';
      ctx.fill();
      ctx.strokeStyle = '#00f2fe';
      ctx.lineWidth = 2;
      ctx.stroke();

      if (idx % 2 === 0) {
        ctx.fillStyle = '#94a3b8';
        ctx.font = '9px sans-serif';
        ctx.fillText(pt.cohort.slice(2), pt.x - 10, h - 10);
      }
    });
  }

  function drawContractBarChart(canvasId, contracts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    const height = canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
    const padX = 40;
    const padY = 30;

    ctx.clearRect(0, 0, w, h);

    // Gridlines
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padY + (i * (h - padY * 2) / 4);
      ctx.beginPath();
      ctx.moveTo(padX, y);
      ctx.lineTo(w - 20, y);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px sans-serif';
      ctx.fillText(`${40 - i * 10}%`, 10, y + 3);
    }

    const barWidth = Math.min(60, (w - padX - 40) / contracts.length - 24);
    const spacing = (w - padX - 40) / contracts.length;

    contracts.forEach((c, i) => {
      const x = padX + 20 + i * spacing;
      const rate = c.churn_rate_pct;
      const barH = (rate / 40) * (h - padY * 2);
      const y = h - padY - barH;

      // Gradient bar
      const grad = ctx.createLinearGradient(0, y, 0, h - padY);
      if (c.contract_type.includes('Month')) {
        grad.addColorStop(0, '#ef4444');
        grad.addColorStop(1, 'rgba(239, 68, 68, 0.2)');
      } else if (c.contract_type.includes('1-Year')) {
        grad.addColorStop(0, '#f59e0b');
        grad.addColorStop(1, 'rgba(245, 158, 11, 0.2)');
      } else {
        grad.addColorStop(0, '#10b981');
        grad.addColorStop(1, 'rgba(16, 185, 129, 0.2)');
      }

      ctx.fillStyle = grad;
      ctx.fillRect(x, y, barWidth, barH);

      // Percentage label on top of bar
      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`${rate}%`, x + barWidth / 2, y - 6);

      // Category label below
      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.fillText(c.contract_type, x + barWidth / 2, h - 12);
    });
    ctx.textAlign = 'left';
  }

  function drawTierBarChart(canvasId, tiers) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const width = canvas.width = canvas.parentElement.clientWidth * window.devicePixelRatio;
    const height = canvas.height = canvas.parentElement.clientHeight * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const w = canvas.parentElement.clientWidth;
    const h = canvas.parentElement.clientHeight;
    const padX = 40;
    const padY = 30;

    ctx.clearRect(0, 0, w, h);

    // Gridlines
    ctx.strokeStyle = '#1e293b';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
      const y = padY + (i * (h - padY * 2) / 4);
      ctx.beginPath();
      ctx.moveTo(padX, y);
      ctx.lineTo(w - 20, y);
      ctx.stroke();

      ctx.fillStyle = '#64748b';
      ctx.font = '10px sans-serif';
      ctx.fillText(`${40 - i * 10}%`, 10, y + 3);
    }

    const barWidth = Math.min(60, (w - padX - 40) / tiers.length - 24);
    const spacing = (w - padX - 40) / tiers.length;

    tiers.forEach((t, i) => {
      const x = padX + 20 + i * spacing;
      const rate = t.churn_rate_pct;
      const barH = (rate / 40) * (h - padY * 2);
      const y = h - padY - barH;

      const grad = ctx.createLinearGradient(0, y, 0, h - padY);
      grad.addColorStop(0, '#6366f1');
      grad.addColorStop(1, 'rgba(99, 102, 241, 0.2)');

      ctx.fillStyle = grad;
      ctx.fillRect(x, y, barWidth, barH);

      ctx.fillStyle = '#f8fafc';
      ctx.font = 'bold 11px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(`${rate}%`, x + barWidth / 2, y - 6);

      ctx.fillStyle = '#94a3b8';
      ctx.font = '11px sans-serif';
      ctx.fillText(t.subscription_tier, x + barWidth / 2, h - 12);
    });
    ctx.textAlign = 'left';
  }

  // Interactive Table Rendering
  function renderTable(customers) {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    const filtered = customers.filter(c => {
      const matchesSearch = c.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            c.customer_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
                            c.industry.toLowerCase().includes(searchQuery.toLowerCase());
      
      const matchesRisk = activeFilter === 'All' || c.risk_tier === activeFilter;
      const matchesTier = activeTier === 'All' || c.subscription_tier === activeTier;

      return matchesSearch && matchesRisk && matchesTier;
    });

    document.getElementById('filtered-count').textContent = `Showing ${filtered.length} matching accounts`;

    if (filtered.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 32px;">No customer records match your filter criteria.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(c => {
      let riskBadge = '';
      if (c.risk_tier === 'High Risk') riskBadge = `<span class="badge badge-high">High (${c.churn_risk_score}%)</span>`;
      else if (c.risk_tier === 'Medium Risk') riskBadge = `<span class="badge badge-med">Med (${c.churn_risk_score}%)</span>`;
      else riskBadge = `<span class="badge badge-low">Low (${c.churn_risk_score}%)</span>`;

      return `
        <tr>
          <td>
            <strong>${c.company_name}</strong>
            <div style="font-size: 11px; color: var(--text-muted);">${c.customer_id} · ${c.industry}</div>
          </td>
          <td><span class="badge badge-tier">${c.subscription_tier}</span></td>
          <td>${c.contract_type}</td>
          <td><strong>${formatCurrency(c.monthly_charges)}</strong></td>
          <td>${c.days_since_last_login} days ago</td>
          <td>${riskBadge}</td>
          <td>
            <div class="action-text">${c.recommended_action}</div>
          </td>
        </tr>
      `;
    }).join('');
  }

  function initTableListeners() {
    const searchEl = document.getElementById('search-accounts');
    if (searchEl) {
      searchEl.addEventListener('input', (e) => {
        searchQuery = e.target.value.trim();
        renderTable(telemetryData.customers);
      });
    }

    const riskButtons = document.querySelectorAll('.filter-risk-btn');
    riskButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        riskButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeFilter = btn.dataset.filter;
        renderTable(telemetryData.customers);
      });
    });

    const tierButtons = document.querySelectorAll('.filter-tier-btn');
    tierButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        tierButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeTier = btn.dataset.tier;
        renderTable(telemetryData.customers);
      });
    });
  }

  // Interactive SQL Workbench Logic
  function initSqlWorkbench(sqlCatalog) {
    const tabsContainer = document.getElementById('sql-tabs');
    const codeBox = document.getElementById('sql-code-box');
    const metaBox = document.getElementById('sql-meta-desc');
    const resultsTable = document.getElementById('sql-results');

    if (!tabsContainer || !sqlCatalog) return;

    tabsContainer.innerHTML = sqlCatalog.map((q, i) => `
      <button class="sql-tab ${i === 0 ? 'active' : ''}" data-idx="${i}">
        ${q.title}
      </button>
    `).join('');

    function loadQuery(idx) {
      const q = sqlCatalog[idx];
      codeBox.textContent = q.sql;
      metaBox.textContent = q.description;

      // Render tabular results
      if (!q.results || q.results.length === 0) {
        resultsTable.innerHTML = '<tr><td style="padding:16px;">No rows returned.</td></tr>';
        return;
      }

      const headers = q.columns.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('');
      const rows = q.results.map(r => {
        const cells = q.columns.map(c => {
          let val = r[c];
          if (typeof val === 'number' && String(val).includes('.')) {
            val = val.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 2 });
          }
          return `<td>${val}</td>`;
        }).join('');
        return `<tr>${cells}</tr>`;
      }).join('');

      resultsTable.innerHTML = `
        <table>
          <thead><tr>${headers}</tr></thead>
          <tbody>${rows}</tbody>
        </table>
      `;
    }

    // Load initial
    loadQuery(0);

    // Tab clicks
    const tabs = tabsContainer.querySelectorAll('.sql-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        loadQuery(parseInt(tab.dataset.idx, 10));
      });
    });
  }

  // Window resize handler for responsive canvas redraw
  window.addEventListener('resize', () => {
    if (telemetryData) {
      renderCharts(telemetryData);
    }
  });
});
