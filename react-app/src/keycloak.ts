import Keycloak from 'keycloak-js'

// Public client "cupcakes-spa" (no secret): login with the authorization code flow and PKCE.
// The values can be changed with VITE_KEYCLOAK_URL, VITE_KEYCLOAK_REALM and VITE_KEYCLOAK_CLIENT_ID.
export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? 'http://localhost:8080',
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? 'cupcakes',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? 'cupcakes-spa',
})

/** Sends the user to the Keycloak login page if needed; resolves once logged in. */
export function initKeycloak() {
  return keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
    // The login status iframe needs third-party cookies, which browsers block: not used
    checkLoginIframe: false,
  })
}
