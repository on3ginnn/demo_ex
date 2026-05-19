(function () {
  'use strict';

  var filterForm = document.getElementById('staffFilterForm');
  var resultsEl = document.getElementById('staffResults');
  var metaEl = document.getElementById('staffDashboardMeta');
  var toastContainer = document.getElementById('staffToastContainer');
  var searchDebounceTimer = null;

  function getCookie(name) {
    var parts = document.cookie.split(';');
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i].trim();
      if (p.indexOf(name + '=') === 0) {
        return decodeURIComponent(p.substring(name.length + 1));
      }
    }
    return '';
  }

  function getCsrf() {
    if (metaEl && metaEl.dataset.csrf) {
      return metaEl.dataset.csrf;
    }
    return getCookie('csrftoken');
  }

  function buildFilterQuery(page) {
    if (!filterForm) {
      return '';
    }
    var params = new URLSearchParams(new FormData(filterForm));
    params.delete('page');
    if (page) {
      params.set('page', String(page));
    }
    var qs = params.toString();
    return qs ? '?' + qs : '';
  }

  function updateBrowserUrl(query) {
    var path = window.location.pathname;
    history.replaceState(null, '', path + query);
  }

  function showToast(message, isError) {
    if (!toastContainer || typeof bootstrap === 'undefined') {
      alert(message);
      return;
    }
    var el = document.createElement('div');
    el.className =
      'toast align-items-center border-0 mb-2 fade' +
      (isError ? ' text-bg-danger' : ' text-bg-success');
    el.setAttribute('role', 'alert');
    el.setAttribute('data-bs-delay', '5000');
    el.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body"></div>' +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Закрыть"></button>' +
      '</div>';
    el.querySelector('.toast-body').textContent = message;
    toastContainer.appendChild(el);
    var toast = new bootstrap.Toast(el);
    toast.show();
    el.addEventListener('hidden.bs.toast', function () {
      el.remove();
    });
  }

  function loadResults(page) {
    if (!resultsEl || !filterForm) {
      return;
    }
    var query = buildFilterQuery(page);
    updateBrowserUrl(query);

    fetch(window.location.pathname + query, {
      headers: { 'X-Requested-With': 'XMLHttpRequest' },
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        if (res.ok && res.data.ok) {
          resultsEl.innerHTML = res.data.html;
        } else {
          showToast((res.data && res.data.error) || 'Не удалось загрузить список', true);
        }
      })
      .catch(function () {
        showToast('Ошибка сети при загрузке списка', true);
      });
  }

  function postStatusChange(select, prevStatus) {
    var url = select.getAttribute('data-url');
    var appId = select.getAttribute('data-app-id');
    var newStatus = select.value;
    if (!url || newStatus === prevStatus) {
      return;
    }

    select.disabled = true;
    var body = new URLSearchParams();
    body.append('csrfmiddlewaretoken', getCsrf());
    body.append('status', newStatus);

    fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': getCsrf(),
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: body.toString(),
    })
      .then(function (r) {
        return r.json().then(function (data) {
          return { ok: r.ok, data: data };
        });
      })
      .then(function (res) {
        if (res.ok && res.data.ok) {
          select.dataset.prevStatus = res.data.status;
          showToast('Заявка №' + (res.data.application_id || appId) + ': ' + res.data.status_label, false);
        } else {
          select.value = prevStatus;
          showToast((res.data && res.data.error) || 'Не удалось обновить статус', true);
        }
      })
      .catch(function () {
        select.value = prevStatus;
        showToast('Ошибка сети', true);
      })
      .finally(function () {
        select.disabled = false;
      });
  }

  function resetFilterForm() {
    if (!filterForm) {
      return;
    }
    filterForm.reset();
    var ordering = filterForm.querySelector('[name="ordering"]');
    if (ordering) {
      ordering.value = '-created_at';
    }
    loadResults(null);
  }

  function initFilters() {
    if (!filterForm) {
      return;
    }
    filterForm.addEventListener('submit', function (e) {
      e.preventDefault();
      loadResults(null);
    });

    filterForm.querySelectorAll('.js-filter-control').forEach(function (el) {
      if (el.name === 'q') {
        el.addEventListener('input', function () {
          clearTimeout(searchDebounceTimer);
          searchDebounceTimer = setTimeout(function () {
            loadResults(null);
          }, 400);
        });
      } else {
        el.addEventListener('change', function () {
          loadResults(null);
        });
      }
    });

    var resetBtn = filterForm.querySelector('.js-filter-reset');
    if (resetBtn) {
      resetBtn.addEventListener('click', function (e) {
        e.preventDefault();
        resetFilterForm();
      });
    }
  }

  function initPagination() {
    if (!resultsEl) {
      return;
    }
    resultsEl.addEventListener('click', function (e) {
      var link = e.target.closest('.js-page-link');
      if (!link) {
        return;
      }
      e.preventDefault();
      var page = link.getAttribute('data-page');
      loadResults(page ? parseInt(page, 10) : null);
    });
  }

  function initStatusSelects() {
    if (!resultsEl) {
      return;
    }

    resultsEl.addEventListener('focusin', function (e) {
      var select = e.target.closest('.js-status-select');
      if (select) {
        select.dataset.prevStatus = select.value;
      }
    });

    resultsEl.addEventListener('change', function (e) {
      var select = e.target.closest('.js-status-select');
      if (!select) {
        return;
      }
      var prev = select.dataset.prevStatus || select.value;
      postStatusChange(select, prev);
    });
  }

  initFilters();
  initPagination();
  initStatusSelects();
})();
