from bs4 import BeautifulSoup


def get_plain_text_from_html(html):
    soup = BeautifulSoup(html, 'html5lib')

    for a in soup.findAll('a'):
        href = a.attrs['href']
        if a.text != href:
            link_text_repr = '%s (%s)' % (a.text, href)
        else:
            link_text_repr = href
        a.replaceWith(link_text_repr)

    for li in soup.findAll('li'):
        list_text_repr = '* %s' % (li.text)
        li.replaceWith(list_text_repr)

    for strong in soup.findAll('strong'):
        strong_text_repr = '*%s*' % (strong.text)
        strong.replaceWith(strong_text_repr)

    for b in soup.findAll('b'):
        bold_text_repr = '*%s*' % (b.text)
        b.replaceWith(bold_text_repr)

    for em in soup.findAll('em'):
        emphasis_text_repr = '_%s_' % (em.text)
        em.replaceWith(emphasis_text_repr)

    for i in soup.findAll('i'):
        italic_text_repr = '_%s_' % (i.text)
        i.replaceWith(italic_text_repr)

    return soup.text
