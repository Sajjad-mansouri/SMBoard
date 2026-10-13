class Auth {
	constructor() {

		this.baseAPIUrl = origin + "/api";
		this.loginAPIUrl = origin + "/api/login/";


		this.refreshToken = localStorage.getItem("refreshToken");
		this.accessToken = localStorage.getItem("accessToken");


	}

	async login(username, password) {
		let data = await this.getToken(username, password)

		return data

	}
	async fetchPost(method, url, body, headers = {}, contentType = "application/json") {

		const response = await fetch(url, {
			method: method,
			headers: {
				"Content-Type": contentType,
				...headers,
			},
			body: body
		})

		return response


	}

	async fetchFormPost(method, url, body, headers = {}) {

		const response = await fetch(url, {
			method: method,
			headers: {
				...headers,
			},
			body: body
		})

		return response


	}
	async fetchGET(method, url, body, headers = {}) {

		const response = await fetch(url, {
			method: method,
			headers: {
				...headers,
			},
		})

		return response


	}
	async fetchDELETE(method, url, body, headers = {}) {

		const response = await fetch(url, {
			method: method,
			headers: {
				...headers,
			},
		})

		return response


	}
	async getToken(username, password) {
		const tokenUrl = `${this.baseAPIUrl}/token/`;

		const body = JSON.stringify({
			"username": username,
			"password": password
		})
		try {

			const response = await this.fetchPost("POST", this.loginAPIUrl, body)
			const data = await response.json()
			if (!response.ok) {

				return {
					"ok": false,
					"data": data
				}
			}
			this.setToken(data.access, data.refresh)


			return {
				"ok": true,
			}
		} catch (error) {
			return {
				"ok": false,
			}

		}


	}

	async setToken(accessToken, refreshToken) {
		this.refreshToken = refreshToken;
		this.accessToken = accessToken;
		localStorage.setItem("refreshToken", refreshToken);
		localStorage.setItem("accessToken", accessToken);

	}
	async setAccessToken(accessToken) {
		this.accessToken = accessToken;
		localStorage.setItem("accessToken", accessToken);

	}
	async refreshAccessToken() {
		const refreshUrl = `${this.baseAPIUrl}/token/refresh/`;

		const body = JSON.stringify({
			"refresh": this.refreshToken
		})

		try {
			const response = await this.fetchPost("POST", refreshUrl, body)
			const data = await response.json()

			if (!response.ok) {

				throw new Error('Token refresh failed');
			}
			this.setAccessToken(data.access)
			return true


		} catch (error) {

			this.logout()
			return false

		}
	}
	async authenticatedRequest(url, body, fetchType = "POST", header_kwargs = {}, contentType = "application/json") {

		let fetchObject = this.fetchPost
		if (fetchType == "GET") {

			fetchObject = this.fetchGET
		} else if (fetchType == "DELETE") {
			fetchObject = this.fetchDELETE
		} else if (fetchType == "PATCH" || fetchType == "POST") {
			if (contentType == "multipart/form-data") {

				fetchObject = this.fetchFormPost
			} else {
				fetchObject = this.fetchPost
			}
		}

		let headers = {
			"Authorization": `Bearer ${this.accessToken}`,
			...header_kwargs
		}

		let response = await fetchObject(fetchType, url, body, headers)

		if (response.status === 401) {
			const refreshed = await this.refreshAccessToken();

			if (refreshed) {

				headers = {
					"Authorization": `Bearer ${this.accessToken}`
				}
				response = await fetchObject(fetchType, url, body, headers, contentType)


			} else {

				this.logout()

				throw new Error('Session expired');
			}
		}

		return response
	}
	async logout() {

		if (this.refreshToken) {
			try {
				const url = `${this.baseAPIUrl}/logout/`
				const jsonBody = JSON.stringify({
					"refresh": this.refreshToken
				})
				const response = await this.authenticatedRequest(url, jsonBody, "POST")

			} catch (error) {
				console.log("logout error", error)
			}
		}

		this.clearTokens()
		window.location.href = origin

	}

	async clearTokens() {
		this.accessToken = null
		this.refreshToken = null
		localStorage.removeItem("accessToken")
		localStorage.removeItem("refreshToken")

	}
}
