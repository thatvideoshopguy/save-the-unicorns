document.addEventListener('DOMContentLoaded', () => {
    // Functions to open and close a modal
    function openModal($el) {
        $el.classList.add('is-active');
        // Trigger HTMX to load the form content
        const modalContent = $el.querySelector('#modal-content');
        if (modalContent && typeof window.htmx !== 'undefined') {
            window.htmx.trigger(modalContent, 'revealed');
        }
    }

    function closeModal($el) {
        $el.classList.remove('is-active');
        // Reset modal content on close
        const modalContent = $el.querySelector('#modal-content');
        if (modalContent) {
            modalContent.innerHTML = `
                <div class="has-text-centered">
                    <div class="button is-loading is-static">Loading...</div>
                </div>
            `;
        }
    }

    function closeAllModals() {
        (document.querySelectorAll('.modal') || []).forEach(($modal) => {
            closeModal($modal);
        });
    }

    // Add a click event on buttons to open a specific modal
    (document.querySelectorAll('.js-modal-trigger') || []).forEach(($trigger) => {
        const modal = $trigger.dataset.target;
        const $target = document.getElementById(modal);

        $trigger.addEventListener('click', () => {
            openModal($target);
        });
    });

    // Add a click event on various child elements to close the parent modal
    (
        document.querySelectorAll('.modal-background, .modal-close, .modal-card-head .delete') ||
        []
    ).forEach(($close) => {
        const $target = $close.closest('.modal');

        $close.addEventListener('click', () => {
            closeModal($target);
        });
    });

    // Add a keyboard event to close all modals
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeAllModals();
        }
    });
});
