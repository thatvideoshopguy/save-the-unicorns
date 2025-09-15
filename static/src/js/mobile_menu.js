document.addEventListener('DOMContentLoaded', function initMobileMenu() {
    const navbarBurgers = Array.prototype.slice.call(
        document.querySelectorAll('.navbar-burger'),
        0,
    );

    navbarBurgers.forEach(function setupBurgerClick(burger) {
        burger.addEventListener('click', function handleBurgerClick() {
            const target = burger.dataset.target;
            const targetElement = document.getElementById(target);

            // Toggle active states
            burger.classList.toggle('is-active');
            targetElement.classList.toggle('is-active');

            // Prevent body scroll when menu is open
            if (burger.classList.contains('is-active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
    });

    // Close mobile menu when clicking on a menu item
    const navbarItems = document.querySelectorAll('.navbar-item');
    navbarItems.forEach(function setupNavItemClick(item) {
        item.addEventListener('click', function handleNavItemClick() {
            if (item.tagName === 'A' && !item.classList.contains('is-logo')) {
                const burger = document.querySelector('.navbar-burger');
                const menu = document.getElementById(burger?.dataset.target);

                if (burger?.classList.contains('is-active')) {
                    burger.classList.remove('is-active');
                    menu?.classList.remove('is-active');
                    document.body.style.overflow = '';
                }
            }
        });
    });

    // Handle escape key to close menu
    document.addEventListener('keydown', function handleEscapeKey(event) {
        if (event.key === 'Escape') {
            const burger = document.querySelector('.navbar-burger');
            const menu = document.getElementById(burger?.dataset.target);

            if (burger?.classList.contains('is-active')) {
                burger.classList.remove('is-active');
                menu?.classList.remove('is-active');
                document.body.style.overflow = '';
            }
        }
    });
});
