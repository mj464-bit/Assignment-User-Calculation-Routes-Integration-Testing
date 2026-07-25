from fastapi.testclient import TestClient


class TestCreateCalculation:
    def test_create_addition(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "addition", "inputs": [10, 5, 2]}, headers=auth_headers
        )
        assert response.status_code == 201
        body = response.json()
        assert body["result"] == 17
        assert body["type"] == "addition"
        assert "id" in body and "user_id" in body

    def test_create_subtraction(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "subtraction", "inputs": [10, 3]}, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 7

    def test_create_multiplication(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "multiplication", "inputs": [3, 4]}, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 12

    def test_create_division(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "division", "inputs": [100, 4]}, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["result"] == 25

    def test_create_division_by_zero_rejected(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "division", "inputs": [10, 0]}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_invalid_type_rejected(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "exponent", "inputs": [2, 3]}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_too_few_inputs_rejected(self, client: TestClient, auth_headers):
        response = client.post(
            "/calculations", json={"type": "addition", "inputs": [5]}, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_requires_authentication(self, client: TestClient):
        response = client.post("/calculations", json={"type": "addition", "inputs": [1, 2]})
        assert response.status_code == 403  # HTTPBearer rejects a missing Authorization header

    def test_create_ignores_client_supplied_user_id(self, client: TestClient, auth_headers):
        """user_id must always come from the token, never from the request body."""
        response = client.post(
            "/calculations",
            json={
                "type": "addition",
                "inputs": [1, 2],
                "user_id": "11111111-1111-1111-1111-111111111111",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["user_id"] != "11111111-1111-1111-1111-111111111111"


class TestBrowseCalculations:
    def test_list_empty_for_new_user(self, client: TestClient, auth_headers):
        response = client.get("/calculations", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_created_calculations(self, client: TestClient, auth_headers):
        client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}, headers=auth_headers)
        client.post("/calculations", json={"type": "multiplication", "inputs": [2, 3]}, headers=auth_headers)

        response = client.get("/calculations", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_list_does_not_include_other_users_calculations(
        self, client: TestClient, auth_headers, fake_user_payload
    ):
        client.post("/calculations", json={"type": "addition", "inputs": [1, 2]}, headers=auth_headers)

        other = dict(fake_user_payload)
        other["username"] = fake_user_payload["username"] + "_other"
        other["email"] = "other_" + fake_user_payload["email"]
        client.post("/users/register", json=other)
        login = client.post(
            "/users/login", json={"username": other["username"], "password": other["password"]}
        )
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        response = client.get("/calculations", headers=other_headers)
        assert response.status_code == 200
        assert response.json() == []


class TestReadCalculation:
    def test_read_own_calculation(self, client: TestClient, auth_headers):
        created = client.post(
            "/calculations", json={"type": "addition", "inputs": [4, 6]}, headers=auth_headers
        ).json()

        response = client.get(f"/calculations/{created['id']}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["result"] == 10

    def test_read_nonexistent_calculation_404(self, client: TestClient, auth_headers):
        response = client.get(
            "/calculations/11111111-1111-1111-1111-111111111111", headers=auth_headers
        )
        assert response.status_code == 404

    def test_read_malformed_id_422(self, client: TestClient, auth_headers):
        response = client.get("/calculations/not-a-uuid", headers=auth_headers)
        assert response.status_code == 422

    def test_read_another_users_calculation_404(
        self, client: TestClient, auth_headers, fake_user_payload
    ):
        created = client.post(
            "/calculations", json={"type": "addition", "inputs": [1, 1]}, headers=auth_headers
        ).json()

        other = dict(fake_user_payload)
        other["username"] = fake_user_payload["username"] + "_other2"
        other["email"] = "other2_" + fake_user_payload["email"]
        client.post("/users/register", json=other)
        login = client.post(
            "/users/login", json={"username": other["username"], "password": other["password"]}
        )
        other_headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        response = client.get(f"/calculations/{created['id']}", headers=other_headers)
        assert response.status_code == 404


class TestEditCalculation:
    def test_update_recomputes_result(self, client: TestClient, auth_headers):
        created = client.post(
            "/calculations", json={"type": "addition", "inputs": [1, 1]}, headers=auth_headers
        ).json()

        response = client.put(
            f"/calculations/{created['id']}", json={"inputs": [10, 20, 30]}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["result"] == 60

    def test_update_nonexistent_calculation_404(self, client: TestClient, auth_headers):
        response = client.put(
            "/calculations/11111111-1111-1111-1111-111111111111",
            json={"inputs": [1, 2]},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_with_too_few_inputs_rejected(self, client: TestClient, auth_headers):
        created = client.post(
            "/calculations", json={"type": "addition", "inputs": [1, 1]}, headers=auth_headers
        ).json()

        response = client.put(
            f"/calculations/{created['id']}", json={"inputs": [5]}, headers=auth_headers
        )
        assert response.status_code == 422


class TestDeleteCalculation:
    def test_delete_removes_calculation(self, client: TestClient, auth_headers):
        created = client.post(
            "/calculations", json={"type": "addition", "inputs": [1, 1]}, headers=auth_headers
        ).json()

        response = client.delete(f"/calculations/{created['id']}", headers=auth_headers)
        assert response.status_code == 204

        follow_up = client.get(f"/calculations/{created['id']}", headers=auth_headers)
        assert follow_up.status_code == 404

    def test_delete_nonexistent_calculation_404(self, client: TestClient, auth_headers):
        response = client.delete(
            "/calculations/11111111-1111-1111-1111-111111111111", headers=auth_headers
        )
        assert response.status_code == 404
