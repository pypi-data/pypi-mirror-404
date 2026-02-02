import itertools
import lzma
import os

import httpx
import parsel
import py3_logger
import py3_web


class Frida:
    def __init__(
            self,
            dir_path: str | None = None,
            use_logger: bool = False
    ):
        if dir_path is None:
            dir_path: str = str(os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                os.path.splitext(os.path.basename(os.path.abspath(__file__)))[0]
            ))
        self.dir_path = dir_path
        os.makedirs(self.dir_path, exist_ok=True)

        self.use_logger = use_logger

        self.logger = py3_logger.logger.get_logger(__name__)

    def get_frida_versions(self, limit: int = 10) -> list[str]:
        def gen_frida_versions():
            url = "https://github.com/frida/frida/releases"
            headers = py3_web.headers.get_default()
            if self.use_logger:
                self.logger.debug(f"url: {url}")
            response = httpx.get(url, headers=headers)
            if self.use_logger:
                self.logger.debug(f"response: {response}")
            yield from parse_response(response)

            sel = parsel.Selector(response.text)
            text = sel.xpath("//a[@class='next_page']/preceding-sibling::a[1]/text()").get()
            if text is not None and (pages := int(text)) and pages > 1:
                for page in range(2, pages + 1):
                    url = f"https://github.com/frida/frida/releases?page={page}"
                    if self.use_logger:
                        self.logger.debug(f"url: {url}")
                    response = httpx.get(url, headers=headers)
                    if self.use_logger:
                        self.logger.debug(f"response: {response}")
                    yield from parse_response(response)

        def parse_response(response):
            sel = parsel.Selector(response.text)
            urls = list(map(lambda x: py3_web.url.join_url("https://github.com/", x),
                            sel.xpath("//a[@class='Link--primary Link']/@href").getall()))
            for url in urls:
                frida_version = py3_web.url.get_furl_obj(url).path.segments[-1]
                if self.use_logger:
                    self.logger.success(f"frida_version: {frida_version}")
                yield frida_version

        def run():
            return list(itertools.islice(gen_frida_versions(), limit))

        return run()

    def get_frida_urls(self, frida_version: str = "12.8.0") -> list[str]:
        def gen_frida_url(url):
            headers = py3_web.headers.get_default()
            if self.use_logger:
                self.logger.debug(f"url: {url}")
            response = httpx.get(url, headers=headers)
            if self.use_logger:
                self.logger.debug(f"response: {response}")
            sel = parsel.Selector(response.text)
            urls = list(map(lambda x: py3_web.url.join_url("https://github.com/", x),
                            sel.xpath("//a[@class='Truncate']/@href").getall()))
            if not urls:
                url = sel.xpath("//div[@data-view-component='true']/include-fragment[@loading='lazy' "
                                "and @data-view-component='true']/@src").get()
                yield from gen_frida_url(url)
                return

            for frida_url in urls:
                if self.use_logger:
                    self.logger.success(f"frida_url: {frida_url}")
                yield frida_url

        def run():
            url = "https://github.com/frida/frida/releases/tag/" + frida_version
            frida_urls = list(gen_frida_url(url))
            return frida_urls

        return run()

    def download_frida_server(
            self,
            frida_url: str = "https://github.com/frida/frida/releases/download/12.8.0/frida-server-12.8.0-android-arm64.xz"
    ) -> str:
        def run():
            url = frida_url
            headers = py3_web.headers.get_default()

            file_name = os.path.basename(url)
            xz_file_path = os.path.join(self.dir_path, file_name)
            execute_file_path = os.path.join(self.dir_path, file_name.rstrip(".xz"))

            if os.path.exists(execute_file_path):
                return execute_file_path

            if not os.path.exists(xz_file_path):
                with open(xz_file_path, "wb") as file:
                    if self.use_logger:
                        self.logger.debug(f"url: {url}")
                    response = httpx.get(url, headers=headers, follow_redirects=True)
                    if self.use_logger:
                        self.logger.debug(f"response: {response}")
                    file.write(response.content)
                if self.use_logger:
                    self.logger.success(f"xz_file_path: {xz_file_path}")

            if not os.path.exists(execute_file_path):
                with lzma.open(xz_file_path, "rb") as f_in, open(execute_file_path, "wb") as f_out:
                    f_out.write(f_in.read())
                if self.use_logger:
                    self.logger.success(f"execute_file_path: {execute_file_path}")

            os.remove(xz_file_path)

            return execute_file_path

        return run()
