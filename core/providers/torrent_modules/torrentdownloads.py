import logging
from xml.etree.cElementTree import fromstring
from xmljson import yahoo
import core
from core.helpers import Url

logging = logging.getLogger(__name__)

def base_url():
    url = core.CONFIG['Indexers']['Torrent']['torrentdownloads']['url']
    if not url:
        url = 'https://www.torrentdownloads.me'
    elif url[-1] == '/':
        url = url[:-1]
    return url

def search(imdbid, term, ignore_if_imdbid_cap = False):
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Performing backlog search on TorrentDownloads for {}.'.format(imdbid))

    host = base_url()
    url = '{}/rss.xml?type=search&search={}'.format(host, term)

    try:
        if proxy_enabled and core.proxy.whitelist(host) is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            return _parse(response, imdbid)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('TorrentDownloads search failed.', exc_info=True)
        return []


def get_rss():
    proxy_enabled = core.CONFIG['Server']['Proxy']['enabled']

    logging.info('Fetching latest RSS from TorrentDownloads.')

    host = base_url()
    url = '{}/rss2/last/4'.format(host)

    try:
        if proxy_enabled and core.proxy.whitelist(host) is True:
            response = Url.open(url, proxy_bypass=True).text
        else:
            response = Url.open(url).text

        if response:
            return _parse(response, None)
        else:
            return []
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        logging.error('TorrentDownloads RSS fetch failed.', exc_info=True)
        return []


def _parse(xml, imdbid):
    logging.info('Parsing TorrentDownloads results.')

    try:
        items = yahoo.data(fromstring(xml))['rss']['channel']['item']
    except Exception as e:
        logging.error('Unexpected XML format from TorrentDownloads.', exc_info=True)
        return []

    host = base_url()
    results = []
    for i in items:
        result = {}
        try:
            result['score'] = 0
            result['size'] = int(i['size'])
            result['status'] = 'Available'
            result['pubdate'] = None
            result['title'] = i['title']['content'] if isinstance(i['title'], dict) else i['title']
            result['imdbid'] = imdbid
            result['indexer'] = 'TorrentDownloads'
            result['info_link'] = '{}{}'.format(host, i['link'])
            result['torrentfile'] = core.providers.torrent.magnet(i['info_hash'], i['title'])
            result['guid'] = i['info_hash']
            result['type'] = 'magnet'
            result['downloadid'] = None
            result['freeleech'] = 0
            result['download_client'] = None
            result['seeders'] = int(i['seeders'])
            result['leechers'] = int(i['leechers'])

            results.append(result)
        except Exception as e:
            logging.error('Error parsing TorrentDownloads XML.', exc_info=True)
            continue

    logging.info('Found {} results from TorrentDownloads.'.format(len(results)))
    return results
