if (!$) {
    $ = django.jQuery
}

$(function() {
    // Replace links for media URLs
    let links = document.querySelectorAll('a')
    for(let link of links) {
        let href = link.getAttribute('href')
        if (href.includes('media/')) {
            link.setAttribute('href', '#')
            link.addEventListener('click', function(e) {
                alert('Files can only be downloaded by creating a BagIt Bag for a submission')
            })
        }
    }
})
