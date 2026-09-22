import base64
import html
import re
import urllib.parse
import urllib.request
from datetime import datetime


class SearchTool:

    name = "SEARCH"

    def __init__(self, max_results=5):
        self.max_results = max_results

    # ============================================================
    # PUBLIC SEARCH
    # ============================================================

    def run(self, query):

        if not query.strip():
            query = "NEXORA AI"

        query = query.strip()

        results = self._search_bing(query)

        if results:

            return self._build_response(
                query=query,
                results=results,
                engine="bing"
            )

        return {
            "tool": self.name,
            "query": query,
            "result": (
                "No useful web search results "
                f"were found for: {query}"
            ),
            "results": [],
            "success": False,
            "engine": None,
            "error": "",
            "timestamp": datetime.now().isoformat()
        }

    # ============================================================
    # BING SEARCH
    # ============================================================

    def _search_bing(self, query):

        encoded_query = urllib.parse.quote_plus(query)

        url = (
            "https://www.bing.com/search"
            f"?q={encoded_query}"
            "&count=10"
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/153.0.0.0 "
                    "Safari/537.36"
                ),
                "Accept": (
                    "text/html,"
                    "application/xhtml+xml,"
                    "application/xml;q=0.9,"
                    "image/avif,"
                    "image/webp,"
                    "*/*;q=0.8"
                ),
                "Accept-Language":
                    "en-US,en;q=0.9"
            }
        )

        try:

            with urllib.request.urlopen(
                request,
                timeout=15
            ) as response:

                page = (
                    response.read()
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                )

        except Exception:

            return []

        return self._parse_bing_results(page)

    # ============================================================
    # BING RESULT PARSER
    # ============================================================

    def _parse_bing_results(self, page):

        results = []

        pattern = re.compile(
            r'<li[^>]+class="[^"]*\bb_algo\b[^"]*"'
            r'[^>]*>'
            r'(.*?)'
            r'</li>',
            re.IGNORECASE |
            re.DOTALL
        )

        blocks = pattern.findall(page)

        seen_urls = set()

        for block in blocks:

            title_match = re.search(
                r'<h2[^>]*>'
                r'.*?'
                r'<a[^>]+href="([^"]+)"'
                r'[^>]*>'
                r'(.*?)'
                r'</a>'
                r'.*?'
                r'</h2>',
                block,
                re.IGNORECASE |
                re.DOTALL
            )

            if not title_match:
                continue

            raw_url = title_match.group(1)
            raw_title = title_match.group(2)

            url = self._decode_bing_url(
                raw_url
            )

            title = self._clean_text(
                raw_title
            )

            snippet = ""

            snippet_match = re.search(
                r'<p[^>]*>'
                r'(.*?)'
                r'</p>',
                block,
                re.IGNORECASE |
                re.DOTALL
            )

            if snippet_match:

                snippet = self._clean_text(
                    snippet_match.group(1)
                )

            if not url:
                continue

            if not url.startswith("http"):
                continue

            if not title:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            results.append(
                {
                    "title": title,
                    "snippet": snippet,
                    "url": url
                }
            )

            if len(results) >= self.max_results:
                break

        return results

    # ============================================================
    # BING URL DECODER
    # ============================================================

    def _decode_bing_url(self, raw_url):

        raw_url = html.unescape(
            raw_url
        )

        parsed = urllib.parse.urlparse(
            raw_url
        )

        # --------------------------------------------------------
        # Normal URL.
        # --------------------------------------------------------

        if (
            parsed.scheme in
            ["http", "https"]
            and "bing.com" not in
            parsed.netloc.lower()
        ):
            return raw_url

        # --------------------------------------------------------
        # Bing redirect URL.
        #
        # Example:
        #
        # https://www.bing.com/ck/a?...&u=a1aHR0cHM6...
        # --------------------------------------------------------

        query_values = urllib.parse.parse_qs(
            parsed.query
        )

        encoded_target = query_values.get(
            "u",
            [None]
        )[0]

        if not encoded_target:
            return raw_url

        encoded_target = (
            urllib.parse.unquote(
                encoded_target
            )
        )

        # --------------------------------------------------------
        # Bing commonly prefixes its Base64 URL
        # with "a1".
        # --------------------------------------------------------

        if encoded_target.startswith("a1"):

            encoded_target = (
                encoded_target[2:]
            )

        # --------------------------------------------------------
        # Try URL-safe Base64 decoding.
        # --------------------------------------------------------

        try:

            padding = (
                "="
                * (
                    -len(encoded_target)
                    % 4
                )
            )

            decoded_bytes = (
                base64.urlsafe_b64decode(
                    encoded_target
                    + padding
                )
            )

            decoded_url = (
                decoded_bytes
                .decode(
                    "utf-8",
                    errors="ignore"
                )
            )

            if decoded_url.startswith(
                "http://"
            ) or decoded_url.startswith(
                "https://"
            ):

                return decoded_url

        except Exception:

            pass

        # --------------------------------------------------------
        # Sometimes the value is already URL encoded.
        # --------------------------------------------------------

        if encoded_target.startswith(
            "http://"
        ) or encoded_target.startswith(
            "https://"
        ):

            return encoded_target

        # --------------------------------------------------------
        # If decoding fails, retain original URL.
        # --------------------------------------------------------

        return raw_url

    # ============================================================
    # RESPONSE BUILDER
    # ============================================================

    def _build_response(
        self,
        query,
        results,
        engine
    ):

        lines = []

        for index, item in enumerate(
            results,
            start=1
        ):

            lines.append(
                f"{index}. "
                f"{item['title']}\n"
                f"   {item['snippet']}\n"
                f"   URL: {item['url']}"
            )

        return {
            "tool": self.name,
            "query": query,
            "result": "\n".join(lines),
            "results": results,
            "success": True,
            "engine": engine,
            "error": "",
            "timestamp": datetime.now().isoformat()
        }

    # ============================================================
    # TEXT CLEANING
    # ============================================================

    def _clean_text(self, text):

        text = html.unescape(
            text
        )

        text = re.sub(
            r"<script.*?</script>",
            "",
            text,
            flags=re.IGNORECASE |
                  re.DOTALL
        )

        text = re.sub(
            r"<style.*?</style>",
            "",
            text,
            flags=re.IGNORECASE |
                  re.DOTALL
        )

        text = re.sub(
            r"<[^>]+>",
            "",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()