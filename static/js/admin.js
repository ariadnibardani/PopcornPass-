document.addEventListener('DOMContentLoaded', function () {

  // Confirm before deleting anything
  document.querySelectorAll('a[href*="/delete/"]').forEach(function (link) {
    link.addEventListener('click', function (e) {
      if (!confirm('Are you sure you want to delete this? This cannot be undone.')) {
        e.preventDefault();
      }
    });
  });

  // Confirm staff toggle
  document.querySelectorAll('.toggle-staff-btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      const username = btn.getAttribute('data-username');
      const isStaff  = btn.getAttribute('data-is-staff') === 'True';
      const action   = isStaff ? 'remove staff from' : 'grant staff to';
      if (!confirm(`Are you sure you want to ${action} "${username}"?`)) {
        e.preventDefault();
        e.stopPropagation();
        btn.closest('form').dispatchEvent(new Event('reset'));
      }
    });
  });

  // Auto-generate slug from title (movie form)
  const titleInput = document.querySelector('input[name="title"]');
  const slugInput  = document.querySelector('input[name="slug"]');
  if (titleInput && slugInput && slugInput.value === '') {
    titleInput.addEventListener('input', function () {
      slugInput.value = titleInput.value
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .trim()
        .replace(/\s+/g, '-');
    });
  }

  // Auto-generate slug from category name
  const nameInput = document.querySelector('input[name="name"]');
  if (nameInput && slugInput && slugInput.value === '') {
    nameInput.addEventListener('input', function () {
      slugInput.value = nameInput.value
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .trim()
        .replace(/\s+/g, '-');
    });
  }

});