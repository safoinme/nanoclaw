import { logger } from '../logger.js';

const DEFAULT_STORE_URL = 'https://11870fb5-zenml.cloudinfra.zenml.io';

interface TokenCache {
  token: string;
  expiresAt: number;
}

interface PipelineResponse {
  id: string;
  name: string;
  [key: string]: unknown;
}

interface SnapshotResponse {
  id: string;
  [key: string]: unknown;
}

interface PipelineRunResponse {
  id: string;
  status: string;
  [key: string]: unknown;
}

interface ListResponse<T> {
  items: T[];
  total: number;
  [key: string]: unknown;
}

export class ZenMLClient {
  private storeUrl: string;
  private apiKey: string;
  private tokenCache: TokenCache | null = null;

  constructor() {
    this.storeUrl = (
      process.env.ZENML_STORE_URL || DEFAULT_STORE_URL
    ).replace(/\/+$/, '');
    this.apiKey = process.env.ZENML_STORE_API_KEY || '';
    if (!this.apiKey) {
      logger.warn('ZENML_STORE_API_KEY not set — ZenML client will not work');
    }
  }

  private async login(): Promise<string> {
    if (this.tokenCache && Date.now() < this.tokenCache.expiresAt) {
      return this.tokenCache.token;
    }

    logger.debug('Logging in to ZenML Cloud');
    const res = await fetch(`${this.storeUrl}/api/v1/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ password: this.apiKey }),
    });

    if (!res.ok) {
      const body = await res.text();
      throw new Error(`ZenML login failed (${res.status}): ${body}`);
    }

    const data = (await res.json()) as { access_token: string };
    // Cache token for 55 minutes (tokens typically expire in 1 hour)
    this.tokenCache = {
      token: data.access_token,
      expiresAt: Date.now() + 55 * 60 * 1000,
    };
    logger.info('ZenML Cloud login successful');
    return this.tokenCache.token;
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    let token = await this.login();

    const doFetch = async (bearerToken: string): Promise<Response> => {
      const opts: RequestInit = {
        method,
        headers: {
          Authorization: `Bearer ${bearerToken}`,
          'Content-Type': 'application/json',
        },
      };
      if (body !== undefined) {
        opts.body = JSON.stringify(body);
      }
      return fetch(`${this.storeUrl}${path}`, opts);
    };

    let res = await doFetch(token);

    // Auto-refresh on 401
    if (res.status === 401) {
      logger.debug('ZenML token expired, refreshing');
      this.tokenCache = null;
      token = await this.login();
      res = await doFetch(token);
    }

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`ZenML API ${method} ${path} failed (${res.status}): ${text}`);
    }

    return res.json() as Promise<T>;
  }

  async listPipelines(): Promise<ListResponse<PipelineResponse>> {
    return this.request<ListResponse<PipelineResponse>>(
      'GET',
      '/api/v1/pipelines',
    );
  }

  async listSnapshots(
    pipelineId: string,
  ): Promise<ListResponse<SnapshotResponse>> {
    return this.request<ListResponse<SnapshotResponse>>(
      'GET',
      `/api/v1/pipeline_snapshots?pipeline=${encodeURIComponent(pipelineId)}`,
    );
  }

  async triggerSnapshot(
    snapshotId: string,
    runConfig?: Record<string, unknown>,
  ): Promise<PipelineRunResponse> {
    return this.request<PipelineRunResponse>(
      'POST',
      `/api/v1/pipeline_snapshots/${encodeURIComponent(snapshotId)}/runs`,
      runConfig ?? {},
    );
  }

  async getPipelineRun(runId: string): Promise<PipelineRunResponse> {
    return this.request<PipelineRunResponse>(
      'GET',
      `/api/v1/pipeline_runs/${encodeURIComponent(runId)}`,
    );
  }

  async listPipelineRuns(
    pipelineName?: string,
  ): Promise<ListResponse<PipelineRunResponse>> {
    const params = pipelineName
      ? `?pipeline_name=${encodeURIComponent(pipelineName)}`
      : '';
    return this.request<ListResponse<PipelineRunResponse>>(
      'GET',
      `/api/v1/pipeline_runs${params}`,
    );
  }
}
