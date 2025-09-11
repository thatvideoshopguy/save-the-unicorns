const navbar = document.querySelector('.navbar');
let lastScrollY = window.scrollY;

// Create a sentinel element at the top
const sentinel = document.createElement('div');
sentinel.style.height = '1px';
document.body.insertBefore(sentinel, document.body.firstChild);

const observer = new IntersectionObserver(
    ([entry]) => {
        const currentScrollY = window.scrollY;

        if (currentScrollY > lastScrollY && currentScrollY > 100) {
            // Scrolling down
            navbar.classList.add('navbar-hidden');
        } else {
            // Scrolling up
            navbar.classList.remove('navbar-hidden');
        }

        lastScrollY = currentScrollY;
    },
    {threshold: 0}
);

observer.observe(sentinel);
