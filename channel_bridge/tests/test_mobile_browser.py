"""Real Chromium UI test, with a test-only signed IdP and real ASGI backend."""

import json
import os
from urllib.parse import parse_qs, urlsplit

import pytest
from test_mobile import intake, signed


def test_mobile_browser_login_presence_and_xss(mobile, tmp_path):
    executable = os.environ.get("HUB_TEST_CHROMIUM")
    if not executable:
        pytest.skip("Set HUB_TEST_CHROMIUM to run mandatory browser qualification")
    from playwright.sync_api import sync_playwright

    g, client, key, _ = mobile
    intake(g, "<img src=x onerror=alert(1)>")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=executable,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = browser.new_context(viewport={"width": 390, "height": 844})

        def route(request_route):
            req = request_route.request
            if req.url.startswith("https://identity.test/"):
                challenge = json.loads(parse_qs(urlsplit(req.url).query)["challenge"][0])
                proof = {
                    **challenge["binding"],
                    "nonce": challenge["nonce"],
                    "method": "passkey",
                    "assurance": 2,
                    "session_expires": 4000,
                }
                payload = json.dumps({"proof": proof, "signature": signed(key, proof)})
                request_route.fulfill(
                    content_type="text/html",
                    body="<script>opener.postMessage(" + payload + ',"https://hub.test");</script>',
                )
                return
            response = client.request(
                req.method, req.url, headers=req.headers, content=req.post_data_buffer
            )
            request_route.fulfill(
                status=response.status_code, headers=dict(response.headers), body=response.content
            )

        context.route("https://**/*", route)
        page = context.new_page()
        dialogs = []
        page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.dismiss()))
        page.goto("https://hub.test/mobile")
        page.locator("[name=user]").fill("user")
        page.locator("[name=project]").fill("project")
        page.locator("[name=workstation]").fill("phone")
        page.get_by_role("button", name="Войти через провайдера идентификации").click()
        page.locator("#workspace").wait_for(state="visible")
        page.get_by_role("button", name="Offline", exact=True).click()
        page.wait_for_function(
            "document.querySelector('#notice').textContent.includes('Offline установлен')"
        )
        assert g.get("presence", "human")["online"] is False
        assert page.locator("#requests").inner_text().find("<img src=x onerror=alert(1)>") >= 0
        assert page.locator("#requests img").count() == 0 and not dialogs
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(tmp_path / "mobile.png"), full_page=True)
        page.get_by_role("button", name="Завершить сеанс").click()
        page.locator("#login").wait_for(state="visible")
        browser.close()
