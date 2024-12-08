import IMask from 'imask';

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[id$=phone_number]').forEach((el) => {
        IMask(el, {
            mask: '+0 (000) 000-0000',
        });
    });
});
