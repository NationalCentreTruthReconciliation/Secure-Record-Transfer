import Uppy from '@uppy/core';
import Dashboard from '@uppy/dashboard';

document.addEventListener('DOMContentLoaded', () => {
    new Uppy().use(Dashboard, {
        inline: true,
        target: '#uppy-dashboard' ,
        hideUploadButton: true,
        singleFileFullScreen: false,
        proudlyDisplayPoweredByUppy: false,
        width: '100%',
    });
});
