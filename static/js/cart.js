document.addEventListener('DOMContentLoaded', function () {

  // Auto-submit qty form on input change (debounced)
  let debounceTimer;
  document.querySelectorAll('.qty-input').forEach(function (input) {
    input.addEventListener('change', function () {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(function () {
        input.closest('form').submit();
      }, 400);
    });
  });

  // Confirm before removing item
  document.querySelectorAll('.remove-item').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      const title = btn.getAttribute('data-title');
      if (!confirm('Remove "' + title + '" from your cart?')) {
        e.preventDefault();
      }
    });
  });

});