import fetch from "node-fetch";

export type OllamaGenerateRequest = {
  baseUrl: string;
  model: string;
  prompt: string;
  schema: Record<string, unknown>;
  timeoutMs: number;
};

export type OllamaGenerateTextRequest = {
  baseUrl: string;
  model: string;
  prompt: string;
  timeoutMs: number;
  temperature?: number;
  system?: string;
};

export class OllamaError extends Error {
  constructor(
    message: string,
    readonly cause?: unknown,
    readonly rawResponse?: string,
  ) {
    super(message);
    this.name = "OllamaError";
  }
}

type OllamaGenerateResponse = {
  response: string;
  done: boolean;
};

type OllamaVersionResponse = {
  version: string;
};

export async function ollamaHealthCheck(args: {
  baseUrl: string;
  timeoutMs: number;
}): Promise<{ ok: true } | { ok: false; error: string }> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), args.timeoutMs);

  try {
    const url = new URL("/api/version", args.baseUrl).toString();
    const res = await fetch(url, { method: "GET", signal: controller.signal });
    if (!res.ok) return { ok: false, error: `HTTP ${res.status} ${res.statusText}` };
    const data = (await res.json()) as Partial<OllamaVersionResponse>;
    if (!data.version) return { ok: false, error: "Unexpected response from Ollama" };
    return { ok: true };
  } catch (e) {
    if (e instanceof Error && e.name === "AbortError") return { ok: false, error: `Timeout after ${args.timeoutMs}ms` };
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  } finally {
    clearTimeout(timeout);
  }
}

export async function ollamaGenerateJson(request: OllamaGenerateRequest): Promise<unknown> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), request.timeoutMs);

  try {
    const url = new URL("/api/generate", request.baseUrl).toString();
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model: request.model,
        prompt: request.prompt,
        stream: false,
        format: request.schema,
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new OllamaError(`Ollama error (${res.status}): ${text || res.statusText}`);
    }

    const data = (await res.json()) as OllamaGenerateResponse;
    const raw = data.response?.trim();
    if (!raw) throw new OllamaError("Ollama returned empty response");

    try {
      return JSON.parse(raw);
    } catch (e) {
      throw new OllamaError("Ollama returned non-JSON output", e, raw);
    }
  } catch (e) {
    if (e instanceof OllamaError) throw e;
    if (e instanceof Error && e.name === "AbortError") {
      throw new OllamaError(`Ollama request timed out after ${request.timeoutMs}ms`, e);
    }
    throw new OllamaError("Failed calling Ollama (is it running at the configured URL?)", e);
  } finally {
    clearTimeout(timeout);
  }
}

export async function ollamaGenerateText(request: OllamaGenerateTextRequest): Promise<string> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), request.timeoutMs);

  try {
    const url = new URL("/api/generate", request.baseUrl).toString();
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        model: request.model,
        system: request.system,
        prompt: request.prompt,
        stream: false,
        options: request.temperature === undefined ? undefined : { temperature: request.temperature },
      }),
      signal: controller.signal,
    });

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new OllamaError(`Ollama error (${res.status}): ${text || res.statusText}`);
    }

    const data = (await res.json()) as OllamaGenerateResponse;
    const raw = data.response?.trim();
    if (!raw) throw new OllamaError("Ollama returned empty response");
    return raw;
  } catch (e) {
    if (e instanceof OllamaError) throw e;
    if (e instanceof Error && e.name === "AbortError") {
      throw new OllamaError(`Ollama request timed out after ${request.timeoutMs}ms`, e);
    }
    throw new OllamaError("Failed calling Ollama (is it running at the configured URL?)", e);
  } finally {
    clearTimeout(timeout);
  }
}
