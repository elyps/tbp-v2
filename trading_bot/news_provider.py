"""
News Provider für Trading-Bot mit Sentiment-Analyse.
Sammelt Nachrichten und analysiert deren Einfluss auf den Markt.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os
from textblob import TextBlob

# Alternative: Falls TextBlob nicht verfügbar
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logging.warning("TextBlob nicht verfügbar - verwende einfache Sentiment-Analyse")

logger = logging.getLogger(__name__)


class NewsProvider:
    """
    Sammelt und analysiert Nachrichten aus verschiedenen Quellen.
    """
    
    def __init__(self, config: Dict):
        """
        Initialisiert den News Provider.
        
        Args:
            config: Konfiguration mit API Keys
        """
        self.config = config
        
        # API Keys
        self.newsapi_key = config.get('newsapi_key', os.getenv('NEWSAPI_KEY'))
        self.cryptocompare_key = config.get('cryptocompare_key', os.getenv('CRYPTOCOMPARE_KEY'))
        
        # Cache für News (vermeidet zu viele API-Calls)
        self.news_cache = {}
        self.cache_duration = timedelta(minutes=15)
        
        logger.info("NewsProvider initialisiert")
    
    def get_crypto_news(self, symbol: str = 'BTC', limit: int = 10) -> List[Dict]:
        """
        Holt Krypto-Nachrichten von verschiedenen Quellen.
        
        Args:
            symbol: Krypto-Symbol (z.B. 'BTC', 'ETH')
            limit: Maximale Anzahl von News
            
        Returns:
            Liste von News-Artikeln mit Sentiment
        """
        # Prüfe Cache
        cache_key = f"{symbol}_{limit}"
        if cache_key in self.news_cache:
            cached_data, cached_time = self.news_cache[cache_key]
            if datetime.utcnow() - cached_time < self.cache_duration:
                logger.debug(f"Nutze gecachte News für {symbol}")
                return cached_data
        
        news = []
        
        # 1. CryptoCompare News
        if self.cryptocompare_key:
            cc_news = self._get_cryptocompare_news(symbol, limit)
            news.extend(cc_news)
        
        # 2. NewsAPI.org (falls verfügbar)
        if self.newsapi_key:
            newsapi_articles = self._get_newsapi_articles(symbol, limit)
            news.extend(newsapi_articles)
        
        # 3. Fallback: CoinGecko News (kostenlos, kein API Key)
        if not news:
            cg_news = self._get_coingecko_news(symbol, limit)
            news.extend(cg_news)
        
        # Sentiment-Analyse durchführen
        for article in news:
            article['sentiment'] = self._analyze_sentiment(article.get('title', ''), article.get('body', ''))
        
        # Cache aktualisieren
        self.news_cache[cache_key] = (news, datetime.utcnow())
        
        logger.info(f"{len(news)} News-Artikel für {symbol} geladen")
        return news[:limit]
    
    def _get_cryptocompare_news(self, symbol: str, limit: int) -> List[Dict]:
        """Holt News von CryptoCompare."""
        try:
            url = 'https://min-api.cryptocompare.com/data/v2/news/'
            params = {
                'categories': f'{symbol},Trading',
                'excludeCategories': 'Sponsored',
                'lang': 'EN'
            }
            
            headers = {}
            if self.cryptocompare_key:
                headers['authorization'] = f'Apikey {self.cryptocompare_key}'
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data.get('Data', [])[:limit]:
                    articles.append({
                        'source': 'CryptoCompare',
                        'title': item.get('title', ''),
                        'body': item.get('body', ''),
                        'url': item.get('url', ''),
                        'published_at': datetime.fromtimestamp(item.get('published_on', 0)).isoformat(),
                        'categories': item.get('categories', '').split('|'),
                        'image_url': item.get('imageurl', '')
                    })
                
                return articles
            else:
                logger.warning(f"CryptoCompare News API Error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von CryptoCompare News: {e}")
        
        return []
    
    def _get_newsapi_articles(self, symbol: str, limit: int) -> List[Dict]:
        """Holt News von NewsAPI.org."""
        try:
            if not self.newsapi_key:
                return []
            
            # Mapping für bessere Suchbegriffe
            search_terms = {
                'BTC': 'Bitcoin OR BTC',
                'ETH': 'Ethereum OR ETH',
                'SOL': 'Solana OR SOL',
                'XRP': 'Ripple OR XRP',
                'ADA': 'Cardano OR ADA'
            }
            
            query = search_terms.get(symbol, symbol)
            
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': limit,
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                for item in data.get('articles', []):
                    articles.append({
                        'source': item.get('source', {}).get('name', 'NewsAPI'),
                        'title': item.get('title', ''),
                        'body': item.get('description', ''),
                        'url': item.get('url', ''),
                        'published_at': item.get('publishedAt', ''),
                        'categories': ['crypto', symbol],
                        'image_url': item.get('urlToImage', '')
                    })
                
                return articles
            else:
                logger.warning(f"NewsAPI Error: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von NewsAPI: {e}")
        
        return []
    
    def _get_coingecko_news(self, symbol: str, limit: int) -> List[Dict]:
        """
        Fallback: Holt Trending-Infos von CoinGecko (kostenlos).
        Nicht echte News, aber Markt-Sentiment.
        """
        try:
            url = 'https://api.coingecko.com/api/v3/search/trending'
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                articles = []
                
                # Trending Coins als "News"
                for coin in data.get('coins', [])[:limit]:
                    item = coin.get('item', {})
                    articles.append({
                        'source': 'CoinGecko Trending',
                        'title': f"{item.get('name')} is trending (Rank #{coin.get('market_cap_rank', 'N/A')})",
                        'body': f"{item.get('name')} ({item.get('symbol')}) - Score: {item.get('score', 0)}",
                        'url': f"https://www.coingecko.com/en/coins/{item.get('id')}",
                        'published_at': datetime.utcnow().isoformat(),
                        'categories': ['trending', 'crypto'],
                        'image_url': item.get('large', '')
                    })
                
                return articles
        
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von CoinGecko Trending: {e}")
        
        return []
    
    def _analyze_sentiment(self, title: str, body: str) -> Dict:
        """
        Analysiert das Sentiment eines Textes.
        
        Returns:
            Dict mit score (-1 bis +1), label (positive/negative/neutral), confidence
        """
        text = f"{title}. {body}"
        
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 (negativ) bis +1 (positiv)
                subjectivity = blob.sentiment.subjectivity  # 0 (objektiv) bis 1 (subjektiv)
                
                # Label bestimmen
                if polarity > 0.1:
                    label = 'positive'
                elif polarity < -0.1:
                    label = 'negative'
                else:
                    label = 'neutral'
                
                return {
                    'score': polarity,
                    'label': label,
                    'confidence': abs(polarity),
                    'subjectivity': subjectivity,
                    'method': 'textblob'
                }
            except Exception as e:
                logger.warning(f"TextBlob Sentiment-Analyse fehlgeschlagen: {e}")
        
        # Fallback: Einfache Keyword-basierte Analyse
        return self._simple_sentiment(text)
    
    def _simple_sentiment(self, text: str) -> Dict:
        """Einfache Keyword-basierte Sentiment-Analyse als Fallback."""
        text_lower = text.lower()
        
        positive_keywords = [
            'bullish', 'rally', 'surge', 'gain', 'profit', 'up', 'rise', 'high',
            'growth', 'positive', 'success', 'win', 'breakthrough', 'adoption',
            'innovation', 'partnership', 'launch', 'upgrade', 'moon', 'pump'
        ]
        
        negative_keywords = [
            'bearish', 'crash', 'drop', 'fall', 'loss', 'down', 'decline', 'low',
            'risk', 'negative', 'fail', 'hack', 'scam', 'dump', 'panic',
            'regulation', 'ban', 'lawsuit', 'controversy', 'warning'
        ]
        
        pos_count = sum(1 for kw in positive_keywords if kw in text_lower)
        neg_count = sum(1 for kw in negative_keywords if kw in text_lower)
        
        total = pos_count + neg_count
        if total == 0:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0.0, 'method': 'keyword'}
        
        score = (pos_count - neg_count) / total
        
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': score,
            'label': label,
            'confidence': abs(score),
            'method': 'keyword',
            'pos_keywords': pos_count,
            'neg_keywords': neg_count
        }
    
    def get_aggregated_sentiment(self, symbol: str) -> Dict:
        """
        Aggregiert das Sentiment aus mehreren News-Artikeln.
        
        Returns:
            Dict mit durchschnittlichem Sentiment-Score und Verteilung
        """
        news = self.get_crypto_news(symbol, limit=20)
        
        if not news:
            return {
                'avg_score': 0.0,
                'overall_sentiment': 'neutral',
                'confidence': 0.0,
                'article_count': 0,
                'distribution': {'positive': 0, 'neutral': 0, 'negative': 0}
            }
        
        scores = [article['sentiment']['score'] for article in news]
        avg_score = sum(scores) / len(scores)
        
        # Verteilung
        distribution = {
            'positive': sum(1 for a in news if a['sentiment']['label'] == 'positive'),
            'neutral': sum(1 for a in news if a['sentiment']['label'] == 'neutral'),
            'negative': sum(1 for a in news if a['sentiment']['label'] == 'negative')
        }
        
        # Overall Sentiment
        if avg_score > 0.1:
            overall = 'positive'
        elif avg_score < -0.1:
            overall = 'negative'
        else:
            overall = 'neutral'
        
        return {
            'avg_score': avg_score,
            'overall_sentiment': overall,
            'confidence': abs(avg_score),
            'article_count': len(news),
            'distribution': distribution,
            'most_recent': news[0] if news else None
        }
    
    def get_news_features(self, symbol: str) -> Dict:
        """
        Extrahiert ML-Features aus News für das Trading-Modell.
        
        Returns:
            Dict mit News-basierten Features
        """
        sentiment = self.get_aggregated_sentiment(symbol)
        
        features = {
            'news_sentiment_score': sentiment['avg_score'],
            'news_sentiment_positive': 1 if sentiment['overall_sentiment'] == 'positive' else 0,
            'news_sentiment_negative': 1 if sentiment['overall_sentiment'] == 'negative' else 0,
            'news_volume': sentiment['article_count'],
            'news_positive_ratio': sentiment['distribution']['positive'] / max(sentiment['article_count'], 1),
            'news_negative_ratio': sentiment['distribution']['negative'] / max(sentiment['article_count'], 1),
            'news_confidence': sentiment['confidence']
        }
        
        return features
    
    def save_news_to_history(self, symbol: str, news_dir: str = 'news_data'):
        """Speichert News-Artikel für historische Analyse."""
        try:
            os.makedirs(news_dir, exist_ok=True)
            
            news = self.get_crypto_news(symbol, limit=50)
            
            if news:
                filename = os.path.join(news_dir, f'{symbol}_news_{datetime.utcnow().strftime("%Y%m%d")}.json')
                
                with open(filename, 'w') as f:
                    json.dump(news, f, indent=2)
                
                logger.info(f"{len(news)} News-Artikel für {symbol} gespeichert: {filename}")
        
        except Exception as e:
            logger.error(f"Fehler beim Speichern der News: {e}")
