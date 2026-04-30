import random

class UAGenerator:
    # 다양한 브라우저와 OS 환경의 User-Agent 리스트
    UA_LIST = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (AppleWebKit/537.36; Chrome/123.0.0.0; Safari/537.36; Edge/123.0.0.0)"
    ]

    @classmethod
    def get_random_ua(cls):
        """무작위 User-Agent 반환"""
        return random.choice(cls.UA_LIST)

    @classmethod
    def get_headers(cls, extra_headers=None):
        """기본 헤더에 무작위 UA를 결합하여 반환"""
        headers = {
            "User-Agent": cls.get_random_ua(),
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        if extra_headers:
            headers.update(extra_headers)
        return headers