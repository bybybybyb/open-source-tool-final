import PyRSS2Gen

def to_rss(resource):
    rss = PyRSS2Gen.RSS2(
        title=resource.name
    )
    return rss.to_xml()

