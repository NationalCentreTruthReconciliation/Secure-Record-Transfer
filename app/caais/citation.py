from django.utils.safestring import mark_safe

CAAIS_DOC_LINK='https://archivescanada.ca/wp-content/uploads/2022/12/CAAIS_2019May15_EN.pdf'
CAAIS_ANCHOR_TAG = f'<a href="{CAAIS_DOC_LINK}" target="_blank">CAAIS</a>'

def cite_caais(text, section: tuple, html=True):
    ''' Add CAAIS citation to end of text, with link to CAAIS document.
    '''
    section_str = '.'.join(map(str, section))
    if html:
        cited = f'{text.strip()} [{CAAIS_ANCHOR_TAG} {section_str}]'
        return mark_safe(cited)
    return f'{text.strip()} [CAAIS {section_str}]'
