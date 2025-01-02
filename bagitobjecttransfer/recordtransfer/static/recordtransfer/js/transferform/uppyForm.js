import Uppy from '@uppy/core';
import DragDrop from '@uppy/drag-drop';

document.addEventListener('DOMContentLoaded', () => {
    new Uppy().use(DragDrop, { target: "#drag-drop" });
});
