document.addEventListener('DOMContentLoaded', function () {

  const starBtns     = document.querySelectorAll('.star-btn');
  const scoreInput   = document.querySelector('#selected-score');
  const submitBtn    = document.querySelector('#submit-rating');
  const deleteBtn    = document.querySelector('#delete-rating');
  const reviewText   = document.querySelector('#review-text');
  const ratingMsg    = document.querySelector('#rating-message');
  const reviewsList  = document.querySelector('#reviews-list');
  const avgScore     = document.querySelector('#avg-score');
  const avgStars     = document.querySelector('#avg-stars');
  const ratingCount  = document.querySelector('#rating-count');

  if (!starBtns.length) return;

  const csrf = window.POPCORNPASS.csrfToken;

  // ── Initialise stars from existing rating ──────────────────
  let currentScore = parseInt(scoreInput ? scoreInput.value : 0);
  paintStars(currentScore);

  // ── Hover effect ───────────────────────────────────────────
  starBtns.forEach(function (star) {
    star.addEventListener('mouseenter', function () {
      const hovered = parseInt(star.getAttribute('data-score'));
      paintStars(hovered);
    });

    star.addEventListener('mouseleave', function () {
      paintStars(currentScore);
    });

    star.addEventListener('click', function () {
      currentScore = parseInt(star.getAttribute('data-score'));
      scoreInput.value = currentScore;
      paintStars(currentScore);
    });
  });

  // ── Paint star row ─────────────────────────────────────────
  function paintStars(score) {
    starBtns.forEach(function (s) {
      const val = parseInt(s.getAttribute('data-score'));
      if (val <= score) {
        s.classList.remove('bi-star');
        s.classList.add('bi-star-fill');
        s.style.color = 'var(--gold)';
      } else {
        s.classList.remove('bi-star-fill');
        s.classList.add('bi-star');
        s.style.color = '#ccc';
      }
    });
  }

  // ── Update the avg star display ────────────────────────────
  function updateAvgDisplay(avg, count) {
    if (!avgScore || !avgStars || !ratingCount) return;

    avgScore.textContent = avg;
    ratingCount.textContent = '(' + count + ' review' + (count !== 1 ? 's' : '') + ')';

    const stars = avgStars.querySelectorAll('i');
    stars.forEach(function (s, idx) {
      if (idx < Math.round(avg)) {
        s.classList.remove('bi-star');
        s.classList.add('bi-star-fill');
      } else {
        s.classList.remove('bi-star-fill');
        s.classList.add('bi-star');
      }
    });
  }

  // ── Show message ───────────────────────────────────────────
  function showMsg(text, type) {
    if (!ratingMsg) return;
    ratingMsg.textContent = text;
    ratingMsg.className   = 'mt-2 small text-' + type;
    ratingMsg.classList.remove('d-none');
    setTimeout(function () {
      ratingMsg.classList.add('d-none');
    }, 3000);
  }

  // ── Submit rating ──────────────────────────────────────────
  if (submitBtn) {
    submitBtn.addEventListener('click', function () {
      const score  = parseInt(scoreInput.value);
      const review = reviewText ? reviewText.value.trim() : '';
      const url    = submitBtn.getAttribute('data-url');

      if (score < 1 || score > 5) {
        showMsg('Please select a star rating first.', 'danger');
        return;
      }

      submitBtn.disabled    = true;
      submitBtn.textContent = 'Submitting...';

      fetch(url, {
        method:  'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken':  csrf,
        },
        body: JSON.stringify({ score: score, review: review }),
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(data.created ? '✅ Review submitted!' : '✅ Review updated!', 'success');
          updateAvgDisplay(data.avg, data.count);
          submitBtn.textContent = 'Update Review';

          // Update or prepend the review card in the list
          const existing = document.querySelector(
            '.review-item[data-review-id="user-' + data.username + '"]'
          );

          const noMsg = document.querySelector('#no-reviews-msg');
          if (noMsg) noMsg.remove();

          const starsHtml = buildStarsHtml(data.score);
          const reviewHtml = data.review
            ? '<p class="mb-0 mt-2 text-muted">' + escHtml(data.review) + '</p>'
            : '';

          const cardHtml = `
            <div class="card border-0 shadow-sm mb-3 review-item"
                 data-review-id="user-${escHtml(data.username)}">
              <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                  <div>
                    <strong>${escHtml(data.username)}</strong>
                    <span class="text-muted small ms-2">Just now</span>
                  </div>
                  <div>${starsHtml}</div>
                </div>
                ${reviewHtml}
              </div>
            </div>`;

          if (existing) {
            existing.outerHTML = cardHtml;
          } else {
            reviewsList.insertAdjacentHTML('afterbegin', cardHtml);
          }

          // Show delete button if not already there
          if (!deleteBtn) {
            submitBtn.insertAdjacentHTML(
              'afterend',
              `<button id="delete-rating" class="btn btn-outline-danger w-100 mt-2"
                       data-url="${url}/delete/">
                 <i class="bi bi-trash me-1"></i>Delete My Review
               </button>`
            );
            attachDeleteListener();
          }
        } else {
          showMsg('Error: ' + (data.error || 'Something went wrong.'), 'danger');
        }
      })
      .catch(function () {
        showMsg('Network error. Please try again.', 'danger');
      })
      .finally(function () {
        submitBtn.disabled = false;
        if (submitBtn.textContent === 'Submitting...') {
          submitBtn.textContent = 'Update Review';
        }
      });
    });
  }

  // ── Delete rating ──────────────────────────────────────────
  function attachDeleteListener() {
    const btn = document.querySelector('#delete-rating');
    if (!btn) return;

    btn.addEventListener('click', function () {
      if (!confirm('Delete your review?')) return;

      const url = btn.getAttribute('data-url');
      btn.disabled = true;

      fetch(url, {
        method:  'POST',
        headers: { 'X-CSRFToken': csrf },
      })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        if (data.success) {
          // Remove the user's review card
          const userCard = document.querySelector(
            '.review-item[data-review-id^="user-"]'
          );
          if (userCard) userCard.remove();

          // Reset stars
          currentScore     = 0;
          scoreInput.value = 0;
          paintStars(0);
          if (reviewText) reviewText.value = '';

          updateAvgDisplay(data.avg, data.count);
          showMsg('Review deleted.', 'secondary');
          btn.remove();

          if (reviewsList && !reviewsList.querySelector('.review-item')) {
            reviewsList.innerHTML =
              '<div id="no-reviews-msg"><p class="text-muted">No reviews yet. Be the first!</p></div>';
          }
        }
      })
      .catch(function () {
        showMsg('Error deleting review.', 'danger');
      })
      .finally(function () {
        if (btn) btn.disabled = false;
      });
    });
  }

  attachDeleteListener();

  // ── Helpers ────────────────────────────────────────────────
  function buildStarsHtml(score) {
    let html = '';
    for (let i = 1; i <= 5; i++) {
      const cls = i <= score ? 'bi-star-fill' : 'bi-star';
      html += `<i class="bi ${cls}" style="color:var(--gold);font-size:0.9rem;"></i>`;
    }
    return html;
  }

  function escHtml(str) {
    return String(str)
      .replace(/&/g,  '&amp;')
      .replace(/</g,  '&lt;')
      .replace(/>/g,  '&gt;')
      .replace(/"/g,  '&quot;')
      .replace(/'/g,  '&#039;');
  }

});