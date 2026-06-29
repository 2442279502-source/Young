/**
 * 工程算量小助手 v2.0 — Client-side Interactions
 * ==============================================
 * 模式切换、构件类型切换、可选项折叠、成本预算展开
 */

document.addEventListener('DOMContentLoaded', function () {

  // ============ Mode Switching ============
  var modeTabs = document.querySelectorAll('.mode-tab');
  var modeInput = document.getElementById('modeInput');
  var quickForm  = document.getElementById('quickForm');
  var preciseForm = document.getElementById('preciseForm');

  modeTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var mode = this.dataset.mode;

      // Update tabs
      modeTabs.forEach(function (t) { t.classList.remove('active'); });
      this.classList.add('active');

      // Update hidden input
      if (modeInput) modeInput.value = mode;

      // Show/hide forms
      if (mode === 'quick') {
        if (quickForm) quickForm.classList.add('active');
        if (preciseForm) preciseForm.classList.remove('active');
      } else {
        if (quickForm) quickForm.classList.remove('active');
        if (preciseForm) preciseForm.classList.add('active');
      }
    });
  });

  // ============ Type Switching (Precise Mode) ============
  var typeTabs = document.querySelectorAll('.type-tab');
  var typeInput = document.getElementById('typeInput');

  typeTabs.forEach(function (tab) {
    tab.addEventListener('click', function () {
      var compType = this.dataset.type;

      // Update tabs
      typeTabs.forEach(function (t) { t.classList.remove('active'); });
      this.classList.add('active');

      // Update hidden input
      if (typeInput) typeInput.value = compType;

      // Show/hide type-specific forms
      document.querySelectorAll('.form-section').forEach(function (s) {
        s.classList.remove('active');
      });
      var target = document.getElementById('form-' + compType);
      if (target) target.classList.add('active');
    });
  });

  // ============ Cost Toggle ============
  var costToggle = document.getElementById('costToggle');
  var costRow    = document.getElementById('costRow');

  if (costToggle && costRow) {
    costToggle.addEventListener('change', function () {
      costRow.style.display = this.checked ? 'flex' : 'none';
    });
  }

  // ============ Toggle Sections (e.g. top bars, waist bars) ============
  document.querySelectorAll('.toggle-header').forEach(function (header) {
    header.addEventListener('click', function () {
      var body = this.nextElementSibling;
      if (body) {
        var isOpen = body.style.display !== 'none';
        body.style.display = isOpen ? 'none' : 'block';
        this.classList.toggle('collapsed', !isOpen);
      }
    });
  });

  // ============ Detail Row Toggle (Result Table) ============
  document.querySelectorAll('.detail-toggle').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var targetId = this.dataset.target;
      var row = document.getElementById(targetId);
      if (row) {
        var isOpen = row.classList.contains('open');
        if (isOpen) {
          row.classList.remove('open');
          this.textContent = '展开明细';
        } else {
          row.classList.add('open');
          this.textContent = '收起明细';
        }
      }
    });
  });

});
