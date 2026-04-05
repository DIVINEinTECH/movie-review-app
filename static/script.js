document.addEventListener('DOMContentLoaded', () => {

    const textarea = document.getElementById('review_text');
    const counter  = document.getElementById('charCount');
    if (textarea && counter) {
        const update = () => {
            const len = textarea.value.length;
            counter.textContent = `${len} / 1000`;
            counter.style.color = len > 900 ? '#e08080' : '';
        };
        textarea.addEventListener('input', update);
        update();
    }

    const flashes = document.querySelectorAll('.flash');
    flashes.forEach(el => {
        setTimeout(() => {
            el.style.transition = 'opacity 0.5s ease';
            el.style.opacity = '0';
            setTimeout(() => el.remove(), 500);
        }, 4000);
    });

    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let timer;
        searchInput.addEventListener('input', () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                searchInput.closest('form').submit();
            }, 450);
        });
    }

    const stars = document.querySelectorAll('.star-pick');
    stars.forEach((star, i) => {
        star.addEventListener('mouseenter', () => {
            stars.forEach((s, j) => {
                s.style.color = j >= (stars.length - 1 - i) ? 'var(--gold)' : 'var(--border-hi)';
            });
        });
    });

    const starPicker = document.getElementById('starPicker');
    if (starPicker) {
        starPicker.addEventListener('mouseleave', () => {
            const checked = starPicker.querySelector('input:checked');
            if (checked) {
                const val = parseInt(checked.value);
                stars.forEach((s, j) => {
                    s.style.color = j >= (stars.length - val) ? 'var(--gold)' : 'var(--border-hi)';
                });
            } else {
                stars.forEach(s => s.style.color = '');
            }
        });
    }

    const cards = document.querySelectorAll('.review-card');
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(14px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, 60 + i * 40);
    });

});