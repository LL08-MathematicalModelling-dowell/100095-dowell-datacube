/** Browser OAuth2 PKCE helpers for Google / GitHub (authorization code flow). */

import api from "../services/api";

const STORAGE_VERIFIER = "datacube_oauth_code_verifier";
const STORAGE_STATE = "datacube_oauth_state";
const STORAGE_PROVIDER = "datacube_oauth_provider";

/** One in-flight token exchange per authorization code (React Strict Mode safe). */
const inflightExchangeByCode = new Map<string, Promise<OAuthTokenResponse>>();

export type OAuthTokenResponse = {
  access: string;
  refresh: string;
  firstName: string;
};

function base64UrlEncode(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]!);
  }
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

export function generateCodeVerifier(): string {
  const a = new Uint8Array(32);
  crypto.getRandomValues(a);
  return base64UrlEncode(a.buffer);
}

export async function generateCodeChallenge(verifier: string): Promise<string> {
  const enc = new TextEncoder().encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", enc);
  return base64UrlEncode(digest);
}

export function randomState(): string {
  const a = new Uint8Array(16);
  crypto.getRandomValues(a);
  return base64UrlEncode(a.buffer);
}

export function getOAuthRedirectUri(): string {
  const explicit = import.meta.env.VITE_OAUTH_REDIRECT_URI as string | undefined;
  if (explicit?.trim()) return explicit.trim().replace(/\/$/, "");
  return `${window.location.origin.replace(/\/$/, "")}/oauth/callback`;
}

export type OAuthProvider = "google" | "github";

export function persistPkceSession(
  provider: OAuthProvider,
  verifier: string,
  state: string
): void {
  sessionStorage.setItem(STORAGE_VERIFIER, verifier);
  sessionStorage.setItem(STORAGE_STATE, state);
  sessionStorage.setItem(STORAGE_PROVIDER, provider);
}

export function readPkceSession(): {
  verifier: string;
  state: string;
  provider: OAuthProvider;
} | null {
  const verifier = sessionStorage.getItem(STORAGE_VERIFIER);
  const state = sessionStorage.getItem(STORAGE_STATE);
  const provider = sessionStorage.getItem(STORAGE_PROVIDER) as OAuthProvider | null;
  if (!verifier || !state || (provider !== "google" && provider !== "github")) {
    return null;
  }
  return { verifier, state, provider };
}

export function clearPkceSession(): void {
  sessionStorage.removeItem(STORAGE_VERIFIER);
  sessionStorage.removeItem(STORAGE_STATE);
  sessionStorage.removeItem(STORAGE_PROVIDER);
}

/** Exchange code for JWTs once per code, even if React Strict Mode runs the effect twice. */
export function exchangeOAuthTokens(
  provider: OAuthProvider,
  code: string,
  verifier: string
): Promise<OAuthTokenResponse> {
  const existing = inflightExchangeByCode.get(code);
  if (existing) return existing;

  const path =
    provider === "google"
      ? "/core/auth/oauth/google/"
      : "/core/auth/oauth/github/";

  const promise = api
    .post(path, {
      code,
      code_verifier: verifier,
      redirect_uri: getOAuthRedirectUri(),
    })
    .then((data) => data as OAuthTokenResponse)
    .finally(() => {
      inflightExchangeByCode.delete(code);
    });

  inflightExchangeByCode.set(code, promise);
  return promise;
}

export function buildGoogleAuthorizeUrl(opts: {
  clientId: string;
  redirectUri: string;
  state: string;
  codeChallenge: string;
}): string {
  const p = new URLSearchParams({
    client_id: opts.clientId,
    redirect_uri: opts.redirectUri,
    response_type: "code",
    scope: "openid email profile",
    state: opts.state,
    code_challenge: opts.codeChallenge,
    code_challenge_method: "S256",
  });
  return `https://accounts.google.com/o/oauth2/v2/auth?${p.toString()}`;
}

export function buildGitHubAuthorizeUrl(opts: {
  clientId: string;
  redirectUri: string;
  state: string;
  codeChallenge: string;
}): string {
  const p = new URLSearchParams({
    client_id: opts.clientId,
    redirect_uri: opts.redirectUri,
    state: opts.state,
    scope: "user:email",
    code_challenge: opts.codeChallenge,
    code_challenge_method: "S256",
  });
  return `https://github.com/login/oauth/authorize?${p.toString()}`;
}

export async function startOAuthRedirect(provider: OAuthProvider): Promise<void> {
  const googleId = (import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID as string) || "";
  const githubId = (import.meta.env.VITE_GITHUB_OAUTH_CLIENT_ID as string) || "";

  const clientId = provider === "google" ? googleId : githubId;
  if (!clientId) {
    throw new Error(
      provider === "google"
        ? "Google sign-in is not configured (missing VITE_GOOGLE_OAUTH_CLIENT_ID)."
        : "GitHub sign-in is not configured (missing VITE_GITHUB_OAUTH_CLIENT_ID)."
    );
  }

  const verifier = generateCodeVerifier();
  const challenge = await generateCodeChallenge(verifier);
  const state = randomState();
  persistPkceSession(provider, verifier, state);

  const redirectUri = getOAuthRedirectUri();
  const url =
    provider === "google"
      ? buildGoogleAuthorizeUrl({
          clientId,
          redirectUri,
          state,
          codeChallenge: challenge,
        })
      : buildGitHubAuthorizeUrl({
          clientId,
          redirectUri,
          state,
          codeChallenge: challenge,
        });

  window.location.assign(url);
}
