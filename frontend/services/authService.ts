import { http, setToken, setUserId } from "./httpClient";
import type { AuthResponse } from "@/types";

export async function register(email: string, password: string): Promise<AuthResponse> {
  const res = await http.post<AuthResponse>("/auth/register", { email, password }, false);
  setToken(res.access_token);
  setUserId(res.user_id);
  return res;
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const res = await http.post<AuthResponse>("/auth/login", { email, password }, false);
  setToken(res.access_token);
  setUserId(res.user_id);
  return res;
}
