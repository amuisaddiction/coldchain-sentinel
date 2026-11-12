/**
 * ColdChain Sentinel - Client API SDK
 * Connects frontend UI to real backend endpoints with automatic Bearer token handling.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_API_BASE_URL || 'https://coldchain-sentinel-7ax3.onrender.com/api';

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== 'undefined') {
      this.token = localStorage.getItem('ccs_access_token');
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('ccs_access_token', token);
      } else {
        localStorage.removeItem('ccs_access_token');
      }
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE}${endpoint}`;
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    };

    if (this.token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const resp = await fetch(url, {
      ...options,
      headers,
    });

    if (!resp.ok) {
      let errorDetail = `Request failed: ${resp.statusText}`;
      try {
        const errJson = await resp.json();
        errorDetail = errJson.detail || errorDetail;
      } catch {}
      throw new Error(errorDetail);
    }

    return resp.json();
  }

  // Authentication
  getGoogleAuthUrl(returnUrl?: string): string {
    const query = returnUrl ? `?return_url=${encodeURIComponent(returnUrl)}` : '';
    return `${API_BASE}/auth/google${query}`;
  }

  async login(email: string, password: string) {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      }
    );
    this.setToken(data.access_token);
    return data;
  }

  async getMe() {
    return this.request<{
      id: string;
      email: string;
      full_name: string;
      role: string;
      organization_id: string;
      organization_name: string;
    }>('/auth/me');
  }

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' });
    } finally {
      this.setToken(null);
    }
  }

  // Health
  async checkHealth() {
    return this.request<{
      status: string;
      version: string;
      database_connected: boolean;
      paypal_mode: string;
    }>('/health');
  }

  // Shipments
  async listShipments() {
    return this.request<any[]>('/shipments/');
  }

  async getShipment(id: string) {
    return this.request<any>(`/shipments/${id}`);
  }

  async updateShipmentStatus(id: string, status: string) {
    return this.request<any>(`/shipments/${id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Temperature
  async getReadings(shipmentId: string) {
    return this.request<any[]>(`/shipments/${shipmentId}/temperature/readings`);
  }

  async getTemperatureSummary(shipmentId: string) {
    return this.request<any>(`/shipments/${shipmentId}/temperature/summary`);
  }

  async evaluateCompliance(shipmentId: string) {
    return this.request<any>(`/shipments/${shipmentId}/temperature/evaluate`, {
      method: 'POST',
    });
  }

  // Evidence
  async listEvidence(shipmentId: string) {
    return this.request<any[]>(`/shipments/${shipmentId}/evidence`);
  }

  async verifyEvidence(evidenceId: string) {
    return this.request<any>(`/evidence/${evidenceId}/verify`, {
      method: 'POST',
    });
  }

  // Custody
  async listCustodyEvents(shipmentId: string) {
    return this.request<any[]>(`/shipments/${shipmentId}/custody/`);
  }

  // Payment
  async getShipmentPayment(shipmentId: string) {
    return this.request<any>(`/shipments/${shipmentId}/payment`);
  }

  async capturePayment(paymentId: string) {
    return this.request<any>(`/payments/${paymentId}/capture`, {
      method: 'POST',
    });
  }

  // Carrier Intelligence
  async getCarrierIntelligence() {
    return this.request<{
      total_carriers_tracked: number;
      carriers: any[];
    }>('/carrier-intelligence/');
  }

  // Sentinel Challenge
  async getChallengeScenarios() {
    return this.request<any[]>('/challenge/scenarios');
  }

  async resetChallenge() {
    return this.request<{ message: string; scenarios: any[] }>('/challenge/reset', {
      method: 'POST',
    });
  }

  // Investigations
  async listInvestigations() {
    return this.request<any[]>('/investigations/');
  }

  // AI Settlement Intelligence
  async getSampleContracts() {
    return this.request<any[]>('/settlement/contracts/samples');
  }

  async extractContract(payload: { contract_text?: string; sample_id?: string }) {
    return this.request<any>('/settlement/contracts/extract', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async runSettlementInvestigation(shipmentIdentifier: string, contractId?: string) {
    const query = contractId ? `?contract_id=${encodeURIComponent(contractId)}` : '';
    return this.request<any>(`/settlement/investigate/${encodeURIComponent(shipmentIdentifier)}${query}`, {
      method: 'POST',
    });
  }

  async approveSettlement(payload: {
    investigation_id: string;
    shipment_id: string;
    approved: boolean;
    approved_amount: number;
    reviewer_notes: string;
    reviewer_id?: string;
  }) {
    return this.request<any>('/settlement/approve', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getInvestigationReport(id: string) {
    return this.request<any>(`/investigations/${id}/report`);
  }
}

export const api = new ApiClient();
