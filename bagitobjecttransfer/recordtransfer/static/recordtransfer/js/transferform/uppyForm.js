import Uppy from '@uppy/core';
import DragDrop from '@uppy/drag-drop';

import '@uppy/core/dist/style.min.css';
import '@uppy/drag-drop/dist/style.min.css';

document.addEventListener('DOMContentLoaded', () => {
    new Uppy().use(DragDrop, { target: "#drag-drop" });
});
