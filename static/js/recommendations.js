document.addEventListener('DOMContentLoaded', function () {

  // Animate cards in on load
  const cards = document.querySelectorAll('#recommendations-grid .movie-card');
  cards.forEach(function (card, index) {
    card.style.opacity  = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';

    setTimeout(function () {
      card.style.opacity   = '1';
      card.style.transform = 'translateY(0)';
    }, index * 80);
  });

});