from pelican import signals


def replace_underscore(article_generator, content):
    """
    Replace escaped underscores in an Article's thumbnail_url with real
    underscores.
    """
    content.thumbnail_url = content.thumbnail_url.replace('UNDERSCORE', '_')
    content.media_url = content.media_url.replace('UNDERSCORE', '_')


def register():
    signals.article_generator_write_article.connect(replace_underscore)

