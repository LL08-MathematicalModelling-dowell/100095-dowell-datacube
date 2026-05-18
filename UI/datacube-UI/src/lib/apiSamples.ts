/** Generate copy-paste request examples for the in-app API reference. */

export type AuthMode = "none" | "bearer" | "api-key";

export interface RequestSampleInput {
  baseUrl: string;
  method: string;
  path: string;
  auth?: AuthMode;
  query?: string;
  body?: string;
  /** Human-readable multipart hint (not valid JSON). */
  multipart?: boolean;
}

function fullUrl(baseUrl: string, path: string, query?: string): string {
  const base = baseUrl.replace(/\/$/, "");
  const p = path.startsWith("/") ? path : `/${path}`;
  if (!query?.trim()) return `${base}${p}`;
  const q = query.startsWith("?") ? query.slice(1) : query;
  return `${base}${p}?${q}`;
}

function authHeader(auth?: AuthMode): { curl: string; py: string; ts: string } | null {
  if (auth === "bearer") {
    return {
      curl: `-H "Authorization: Bearer $ACCESS_TOKEN"`,
      py: 'headers={"Authorization": f"Bearer {access_token}"}',
      ts: "Authorization: `Bearer ${accessToken}`",
    };
  }
  if (auth === "api-key") {
    return {
      curl: `-H "Authorization: Api-Key $API_KEY"`,
      py: 'headers={"Authorization": f"Api-Key {api_key}"}',
      ts: "Authorization: `Api-Key ${apiKey}`",
    };
  }
  return null;
}

function parseJsonBody(body?: string): object | null {
  if (!body?.trim().startsWith("{")) return null;
  try {
    return JSON.parse(body) as object;
  } catch {
    return null;
  }
}

function jsonLiteral(obj: object, indent = 2): string {
  return JSON.stringify(obj, null, indent);
}

export function curlSample(input: RequestSampleInput): string {
  const url = fullUrl(input.baseUrl, input.path, input.query);
  const method = input.method.toUpperCase().split(/\s/)[0];
  const lines = [`curl -X ${method} "${url}" \\`];
  const auth = authHeader(input.auth);
  if (auth) lines.push(`  ${auth.curl} \\`);

  if (input.multipart) {
    lines.push(`  -F "file=@/path/to/file"`);
    if (input.body) lines.push(`  # ${input.body}`);
    return lines.join("\n");
  }

  const parsed = parseJsonBody(input.body);
  if (parsed) {
    lines.push(`  -H "Content-Type: application/json" \\`);
    lines.push(`  -d '${JSON.stringify(parsed)}'`);
  } else if (input.body && method !== "GET") {
    lines.push(`  # Body: ${input.body}`);
  }
  return lines.join("\n").replace(/ \\\n$/, "");
}

export function pythonSample(input: RequestSampleInput): string {
  const url = fullUrl(input.baseUrl, input.path, input.query);
  const method = input.method.toUpperCase().split(/\s/)[0].toLowerCase();
  const auth = authHeader(input.auth);
  const lines = ["import requests", "", `url = "${url}"`];

  if (auth) {
    lines.push(
      input.auth === "bearer"
        ? 'access_token = "YOUR_ACCESS_TOKEN"'
        : 'api_key = "YOUR_API_KEY"'
    );
    lines.push(`headers = {${auth.py.split("=")[1]}}`);
  } else {
    lines.push("headers = {}");
  }

  if (input.multipart) {
    lines.push('files = {"file": open("/path/to/file", "rb")}');
    lines.push(`response = requests.${method}(url, headers=headers, files=files)`);
  } else {
    const parsed = parseJsonBody(input.body);
    if (parsed && method !== "get") {
      lines.push(`payload = ${jsonLiteral(parsed)}`);
      lines.push(
        `response = requests.${method}(url, headers={**headers, "Content-Type": "application/json"}, json=payload)`
      );
    } else {
      lines.push(`response = requests.${method}(url, headers=headers)`);
    }
  }

  lines.push("response.raise_for_status()");
  lines.push("print(response.json())");
  return lines.join("\n");
}

export function typescriptSample(input: RequestSampleInput): string {
  const url = fullUrl(input.baseUrl, input.path, input.query);
  const method = input.method.toUpperCase().split(/\s/)[0];
  const auth = authHeader(input.auth);
  const lines: string[] = [];

  if (auth?.ts) {
    lines.push(
      input.auth === "bearer"
        ? 'const accessToken = "YOUR_ACCESS_TOKEN";'
        : 'const apiKey = "YOUR_API_KEY";'
    );
  }

  if (input.multipart) {
    lines.push('const form = new FormData();');
    lines.push('form.append("file", fileInput.files[0]);');
    lines.push(`const response = await fetch("${url}", {`);
    lines.push(`  method: "${method}",`);
    if (auth) lines.push(`  headers: { ${auth.ts} },`);
    lines.push("  body: form,");
    lines.push("});");
  } else {
    const parsed = parseJsonBody(input.body);
    if (parsed && method !== "GET") {
      lines.push(`const payload = ${jsonLiteral(parsed)} as const;`);
    }
    lines.push(`const response = await fetch("${url}", {`);
    lines.push(`  method: "${method}",`);
    const hdrs: string[] = [];
    if (auth) hdrs.push(auth.ts);
    if (parsed && method !== "GET") hdrs.push('"Content-Type": "application/json"');
    if (hdrs.length) lines.push(`  headers: { ${hdrs.join(", ")} },`);
    if (parsed && method !== "GET") lines.push("  body: JSON.stringify(payload),");
    lines.push("});");
  }

  lines.push("if (!response.ok) throw new Error(await response.text());");
  lines.push("const data = await response.json();");
  lines.push("console.log(data);");
  return lines.join("\n");
}

export function javascriptSample(input: RequestSampleInput): string {
  return typescriptSample(input).replace(/ as const/g, "");
}
