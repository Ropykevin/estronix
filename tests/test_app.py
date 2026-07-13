"""Basic application tests."""


def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Estronix" in response.data or b"Premium" in response.data


def test_products_page(client):
    response = client.get("/products/")
    assert response.status_code == 200


def test_login_page(client):
    response = client.get("/auth/login")
    assert response.status_code == 200


def test_register_page(client):
    response = client.get("/auth/register")
    assert response.status_code == 200


def test_robots_txt(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert b"User-agent" in response.data


def test_sitemap(client):
    response = client.get("/sitemap.xml")
    assert response.status_code == 200
    assert b"urlset" in response.data
    assert b"/products/" in response.data


def test_robots_includes_sitemap(client):
    response = client.get("/robots.txt")
    assert response.status_code == 200
    assert b"Sitemap:" in response.data


def test_sitemap_uses_public_domain(app, client):
    app.config["DOMAIN"] = "estronix.co.ke"
    app.config["APP_URL"] = "http://localhost:5000"
    response = client.get("/sitemap.xml", headers={"Host": "estronix.co.ke"})
    assert response.status_code == 200
    assert b"http://estronix.co.ke/" in response.data
    assert b"localhost" not in response.data


def test_admin_requires_auth(client):
    response = client.get("/admin/", follow_redirects=False)
    assert response.status_code in (302, 401, 403)
