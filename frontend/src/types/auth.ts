export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  tenant_id: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}
