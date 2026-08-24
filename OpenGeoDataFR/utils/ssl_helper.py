# -*- coding: utf-8 -*-
"""
Gestionnaire de requêtes réseau sécurisé et conforme aux exigences du dépôt QGIS (Bandit B501).
Utilise QgsNetworkAccessManager / QgsBlockingNetworkRequest pour garantir le respect de la configuration
réseau et proxy de QGIS sans outrepasser la vérification des certificats SSL/TLS.
"""

import ssl
import urllib.request

try:
    from qgis.core import QgsNetworkAccessManager, QgsBlockingNetworkRequest
    from qgis.PyQt.QtCore import QUrl, QByteArray
    from qgis.PyQt.QtNetwork import QNetworkRequest
    HAS_QGIS_NETWORK = True
except ImportError:
    HAS_QGIS_NETWORK = False


def get_secure_ssl_context():
    """
    Retourne un contexte SSL standard sécurisé pour les environnements hors QGIS.
    """
    return ssl.create_default_context()


def fetch_url_bytes(url, timeout_ms=8000, headers=None):
    """
    Effectue une requête HTTP(S) GET de façon synchrone en utilisant le moteur réseau QGIS si disponible.
    Retourne les octets de réponse ou lève une exception en cas d'erreur.
    """
    default_headers = {'User-Agent': 'OpenGeoDataFR-QGIS/1.0'}
    if headers:
        default_headers.update(headers)

    if HAS_QGIS_NETWORK:
        req = QNetworkRequest(QUrl(url))
        for key, val in default_headers.items():
            req.setRawHeader(QByteArray(key.encode('utf-8')), QByteArray(val.encode('utf-8')))
        
        blocking_req = QgsBlockingNetworkRequest()
        err_code = blocking_req.get(req)

        if err_code != QgsBlockingNetworkRequest.ErrorCode.NoError:
            raise RuntimeError(f"Erreur réseau QGIS ({err_code}) pour l'URL: {url} - {blocking_req.errorMessage()}")

        reply = blocking_req.reply()
        return bytes(reply.content())
    else:
        req = urllib.request.Request(url, headers=default_headers)
        with urllib.request.urlopen(req, timeout=int(timeout_ms / 1000), context=get_secure_ssl_context()) as resp:
            return resp.read()
