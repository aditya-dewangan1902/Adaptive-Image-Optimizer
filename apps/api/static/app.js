// Adaptive Image Optimization System - Interactive Client Application

document.addEventListener('DOMContentLoaded', () => {
  // DOM Element References
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const sourcePreviewCard = document.getElementById('source-preview-card');
  const sourceThumb = document.getElementById('source-thumb');
  const sourceFilename = document.getElementById('source-filename');
  const sourceSpecs = document.getElementById('source-specs');
  const btnRemoveSource = document.getElementById('btn-remove-source');

  const inputMinSize = document.getElementById('input-min-size');
  const inputMaxSize = document.getElementById('input-max-size');
  const unitLabelMin = document.getElementById('unit-label-min');
  const unitLabelMax = document.getElementById('unit-label-max');
  const unitButtons = document.querySelectorAll('.unit-btn');
  const presetButtons = document.querySelectorAll('.preset-btn');
  const sampleChips = document.querySelectorAll('.sample-chip');

  const selectQualityMode = document.getElementById('select-quality-mode');
  const selectDimensionPolicy = document.getElementById('select-dimension-policy');
  const btnOptimize = document.getElementById('btn-optimize');

  const stepperCard = document.getElementById('stepper-card');
  const stepperTitle = document.getElementById('stepper-title');
  const stepperStageText = document.getElementById('stepper-stage-text');
  const progressBarFill = document.getElementById('progress-bar-fill');

  const welcomePlaceholder = document.getElementById('welcome-placeholder');
  const resultsCard = document.getElementById('results-card');

  const resActualSize = document.getElementById('res-actual-size');
  const resSavingsPill = document.getElementById('res-savings-pill');
  const resultStatusText = document.getElementById('result-status-text');
  const resultStatusChip = document.getElementById('result-status-chip');
  const btnDownloadImage = document.getElementById('btn-download-image');
  const btnDownloadAudit = document.getElementById('btn-download-audit');
  const compImgBefore = document.getElementById('comp-img-before');
  const compImgAfter = document.getElementById('comp-img-after');
  const compImgAfterWrap = document.getElementById('comp-img-after-wrap');
  const sliderHandle = document.getElementById('slider-handle');
  const comparisonContainer = document.getElementById('comparison-container');
  const tagAfterFormat = document.getElementById('tag-after-format');

  const metricButteraugli = document.getElementById('metric-butteraugli');
  const metricButteraugliDesc = document.getElementById('metric-butteraugli-desc');
  const metricSsim = document.getElementById('metric-ssim');
  const metricPsnr = document.getElementById('metric-psnr');
  const metricDeltaE = document.getElementById('metric-delta-e');
  const ledgerTableBody = document.getElementById('ledger-table-body');

  // Application State
  let currentFile = null;
  let currentUnit = 'KB';
  let lastResultData = null;

  // Unit multiplier helpers
  function getUnitMultiplier() {
    if (currentUnit === 'MB') return 1024 * 1024;
    if (currentUnit === 'KB') return 1024;
    return 1;
  }

  function formatBytes(bytes) {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return (bytes / Math.pow(k, i)).toFixed(2) + ' ' + sizes[i];
  }

  // Handle Drag & Drop
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    });
  });

  dropZone.addEventListener('drop', (e) => {
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  dropZone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelected(e.target.files[0]);
    }
  });

  btnRemoveSource.addEventListener('click', () => {
    currentFile = null;
    sourcePreviewCard.style.display = 'none';
    btnOptimize.disabled = true;
    fileInput.value = '';
  });

  function handleFileSelected(file) {
    currentFile = file;
    sourceFilename.textContent = file.name;
    sourceSpecs.textContent = `${formatBytes(file.size)} • ${file.type || 'image'}`;

    const reader = new FileReader();
    reader.onload = (e) => {
      sourceThumb.src = e.target.result;
      sourcePreviewCard.style.display = 'flex';
      btnOptimize.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  // Sample Presets Loader
  sampleChips.forEach(chip => {
    chip.addEventListener('click', async () => {
      const sampleName = chip.getAttribute('data-sample');
      try {
        const res = await fetch(`/static/samples/${sampleName}`);
        const blob = await res.blob();
        const file = new File([blob], sampleName, { type: blob.type });
        handleFileSelected(file);
      } catch (err) {
        alert('Could not load sample image: ' + err);
      }
    });
  });

  // Unit Switcher
  unitButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      unitButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const newUnit = btn.getAttribute('data-unit');

      // Convert values
      const oldMult = getUnitMultiplier();
      currentUnit = newUnit;
      const newMult = getUnitMultiplier();

      const rawMin = parseFloat(inputMinSize.value) * oldMult;
      const rawMax = parseFloat(inputMaxSize.value) * oldMult;

      inputMinSize.value = Math.max(1, Math.round(rawMin / newMult));
      inputMaxSize.value = Math.max(1, Math.round(rawMax / newMult));
      unitLabelMin.textContent = currentUnit;
      unitLabelMax.textContent = currentUnit;
    });
  });

  // Interval Presets
  presetButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const pMin = parseFloat(btn.getAttribute('data-min'));
      const pMax = parseFloat(btn.getAttribute('data-max'));
      const pUnit = btn.getAttribute('data-unit');

      // Activate unit
      unitButtons.forEach(b => {
        if (b.getAttribute('data-unit') === pUnit) b.click();
      });

      inputMinSize.value = pMin;
      inputMaxSize.value = pMax;
    });
  });

  // Split-Screen Interactive Slider Logic
  let isSliding = false;

  function updateSlider(clientX) {
    const rect = comparisonContainer.getBoundingClientRect();
    let x = clientX - rect.left;
    x = Math.max(0, Math.min(x, rect.width));
    const percent = (x / rect.width) * 100;
    compImgAfterWrap.style.width = `${percent}%`;
    sliderHandle.style.left = `${percent}%`;
  }

  comparisonContainer.addEventListener('mousedown', (e) => {
    isSliding = true;
    updateSlider(e.clientX);
  });

  window.addEventListener('mousemove', (e) => {
    if (isSliding) {
      updateSlider(e.clientX);
    }
  });

  window.addEventListener('mouseup', () => {
    isSliding = false;
  });

  comparisonContainer.addEventListener('touchstart', (e) => {
    isSliding = true;
    updateSlider(e.touches[0].clientX);
  });

  window.addEventListener('touchmove', (e) => {
    if (isSliding && e.touches[0]) {
      updateSlider(e.touches[0].clientX);
    }
  });

  window.addEventListener('touchend', () => {
    isSliding = false;
  });

  // Copy Checksum
  btnCopyChecksum.addEventListener('click', () => {
    if (lastResultData && lastResultData.sha256_checksum) {
      navigator.clipboard.writeText(lastResultData.sha256_checksum);
      const span = btnCopyChecksum.querySelector('span');
      const originalText = span.textContent;
      span.textContent = 'Copied!';
      setTimeout(() => { span.textContent = originalText; }, 2000);
    }
  });

  // Download Audit Report
  btnDownloadAudit.addEventListener('click', () => {
    if (!lastResultData) return;
    const blob = new Blob([JSON.stringify(lastResultData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit_report_${lastResultData.job_id || 'result'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // Run Constrained Optimization Submit
  btnOptimize.addEventListener('click', async () => {
    if (!currentFile) return;

    const mult = getUnitMultiplier();
    const minBytes = Math.round(parseFloat(inputMinSize.value) * mult);
    const maxBytes = Math.round(parseFloat(inputMaxSize.value) * mult);

    if (minBytes <= 0 || maxBytes <= 0) {
      alert('Target sizes must be positive.');
      return;
    }
    if (minBytes > maxBytes) {
      alert('Minimum target size cannot exceed maximum target size.');
      return;
    }

    const selectedFormat = document.querySelector('input[name="format-opt"]:checked').value;
    const qualityMode = selectQualityMode.value;
    const dimensionPolicy = selectDimensionPolicy.value;

    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('target_min_bytes', minBytes);
    formData.append('target_max_bytes', maxBytes);
    formData.append('requested_format', selectedFormat);
    formData.append('quality_mode', qualityMode);
    formData.append('dimension_policy', dimensionPolicy);
    formData.append('metadata_policy', 'minimal');
    formData.append('budget_profile', qualityMode);

    // UI state transitions
    btnOptimize.disabled = true;
    stepperCard.style.display = 'block';
    welcomePlaceholder.style.display = 'none';

    // Simulate animated stepper progress while optimizing
    const stages = [
      { text: 'VALIDATING & SNIFFING', pct: 15 },
      { text: 'DECODING CANONICAL MASTER', pct: 30 },
      { text: 'ANALYZING & BUILDING FINITE Θ', pct: 45 },
      { text: 'COARSE SWEEP & PARETO PRUNING', pct: 65 },
      { text: 'ADAPTIVE QUALITY BRACKETING', pct: 80 },
      { text: 'FULL-RES BUTTERAUGLI EVALUATION', pct: 90 },
      { text: 'INDEPENDENT ENCODE & VERIFICATION', pct: 96 }
    ];

    let stageIdx = 0;
    const stageInterval = setInterval(() => {
      if (stageIdx < stages.length) {
        stepperStageText.textContent = stages[stageIdx].text;
        progressBarFill.style.width = `${stages[stageIdx].pct}%`;
        stageIdx++;
      }
    }, 400);

    try {
      const response = await fetch('/api/v1/optimization/optimize-sync', {
        method: 'POST',
        body: formData,
      });

      clearInterval(stageInterval);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Optimization failed');
      }

      const result = await response.json();
      lastResultData = result;

      // Finish progress bar
      stepperStageText.textContent = 'COMPLETED';
      progressBarFill.style.width = '100%';
      setTimeout(() => { stepperCard.style.display = 'none'; }, 800);

      renderResults(result);

    } catch (err) {
      clearInterval(stageInterval);
      stepperCard.style.display = 'none';
      alert('Error: ' + err.message);
    } finally {
      btnOptimize.disabled = false;
    }
  });

  // Render Result Presentation
  function renderResults(result) {
    resultsCard.style.display = 'block';

    const isCompleted = result.status === 'COMPLETED';
    resultStatusText.textContent = result.status;

    if (isCompleted) {
      resultStatusChip.style.background = 'rgba(16, 185, 129, 0.15)';
      resultStatusChip.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      resultStatusChip.style.color = '#10b981';

      resActualSize.textContent = `${formatBytes(result.output_size_bytes)} (${result.output_size_bytes.toLocaleString()} bytes)`;
      resSavingsPill.textContent = result.savings_percent ? `Saved ${result.savings_percent}% (${result.compression_ratio}x ratio)` : '';

      // Set comparison images & scale indicators (Issue #9)
      compImgBefore.src = result.source_url || URL.createObjectURL(currentFile);
      compImgAfter.src = result.output_url;

      const compScaleMode = document.getElementById('comparison-scale-mode');
      const compDimsBadge = document.getElementById('comparison-dims-badge');
      const tagBeforeLabel = document.getElementById('tag-before-label');

      // Check if dimensions are identical
      const origImg = new Image();
      origImg.src = compImgBefore.src;
      origImg.onload = () => {
        const origW = origImg.naturalWidth;
        const origH = origImg.naturalHeight;
        tagBeforeLabel.textContent = `Original (${origW}x${origH})`;
        tagAfterFormat.textContent = `Optimized (${result.format.toUpperCase()} ${result.width}x${result.height})`;

        if (origW === result.width && origH === result.height) {
          if (compScaleMode) compScaleMode.textContent = 'Visual comparison at 1:1 pixel geometry (identical dimensions)';
          if (compDimsBadge) compDimsBadge.textContent = `${origW}x${origH} • 100% scale preserved`;
        } else {
          const pct = Math.round((result.width / origW) * 100);
          if (compScaleMode) compScaleMode.textContent = 'Visual comparison at matched display scale (rescaled)';
          if (compDimsBadge) compDimsBadge.textContent = `Original: ${origW}x${origH} • Optimized: ${result.width}x${result.height} (${pct}% scale)`;
        }
      };

      // Setup download button
      btnDownloadImage.href = result.output_url;
      btnDownloadImage.setAttribute('download', result.output_filename || 'optimized_image');
      // Set Perceptual Metrics
      metricButteraugli.textContent = result.butteraugli_distance !== null ? result.butteraugli_distance.toFixed(4) : 'N/A';
      if (result.butteraugli_distance !== null) {
        if (result.butteraugli_distance < 0.5) {
          metricButteraugliDesc.textContent = 'Indistinguishable to human eye';
        } else if (result.butteraugli_distance < 1.0) {
          metricButteraugliDesc.textContent = 'Below Noticeable Difference (JND)';
        } else {
          metricButteraugliDesc.textContent = 'Minor visible difference';
        }
      }

      metricSsim.textContent = result.ssim !== null ? result.ssim.toFixed(4) : 'N/A';
      metricPsnr.textContent = result.psnr_db !== null ? `${result.psnr_db.toFixed(1)} dB` : 'N/A';
      metricDeltaE.textContent = result.delta_e !== null ? result.delta_e.toFixed(2) : 'N/A';

    } else {
      // Unreachable or Budget Exceeded
      resultStatusChip.style.background = 'rgba(244, 63, 94, 0.15)';
      resultStatusChip.style.borderColor = 'rgba(244, 63, 94, 0.3)';
      resultStatusChip.style.color = '#f43f5e';

      resActualSize.textContent = result.message || 'No candidate found in target interval';
      resSavingsPill.textContent = '';
      btnDownloadImage.style.display = 'none';

      metricButteraugli.textContent = '-';
      metricSsim.textContent = '-';
      metricPsnr.textContent = '-';
      metricDeltaE.textContent = '-';
    }

    // Populate Candidate Ledger Table
    ledgerTableBody.innerHTML = '';
    const ledger = result.candidates_ledger || [];

    ledger.forEach(c => {
      const tr = document.createElement('tr');
      const isWinner = isCompleted && c.actual_bytes === result.output_size_bytes && c.format === result.format;
      if (isWinner) {
        tr.classList.add('winner-row');
      }

      const isFeasible = c.feasible;
      const statusPill = isFeasible 
        ? `<span class="feasible-pill yes">FEASIBLE</span>`
        : `<span class="feasible-pill no">OUT OF BOUNDS</span>`;

      tr.innerHTML = `
        <td><strong>${(c.format || '').toUpperCase()}</strong></td>
        <td>${c.width}x${c.height} (${Math.round(c.scale*100)}%)</td>
        <td>q=${c.quality}</td>
        <td>${c.actual_bytes ? c.actual_bytes.toLocaleString() + ' B' : '-'}</td>
        <td>${statusPill}</td>
        <td>${c.butteraugli_distance !== null && c.butteraugli_distance !== undefined ? c.butteraugli_distance.toFixed(4) : (c.proxy_quality ? c.proxy_quality.toFixed(1) + ' (proxy)' : '-')}</td>
        <td>${c.ssim !== null && c.ssim !== undefined ? c.ssim.toFixed(4) : '-'}</td>
        <td>${c.psnr_db !== null && c.psnr_db !== undefined ? c.psnr_db.toFixed(1) + ' dB' : '-'}</td>
        <td>${c.duration_ms || 0} ms</td>
      `;
      ledgerTableBody.appendChild(tr);
    });
  }

  // Keyboard shortcut Ctrl+Enter to trigger optimization
  window.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (!btnOptimize.disabled) {
        btnOptimize.click();
      }
    }
  });
});
